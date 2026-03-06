import asyncio
import time
import uuid
from contextlib import asynccontextmanager
from logging import getLogger

import uvloop
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api import api_router, api_router_v2
from app.api.health import router as health_router
from app.core.config import settings
from app.core.errors import ApiException
from app.core.logging import configure_logging
from app.core.observability import (
    REQUEST_COUNT,
    REQUEST_ERRORS,
    REQUEST_LATENCY_SECONDS,
    metrics_response,
)
from app.core.request_context import get_request_id, set_request_id
from app.infra import (
    RateLimiter,
    RedisCache,
    create_mongo_client,
    create_redis_client,
    ensure_indexes,
    get_read_db,
    get_write_db,
    refresh_connection_metrics,
)

asyncio.set_event_loop_policy(uvloop.EventLoopPolicy())
logger = getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_logging()

    mongo_client = create_mongo_client()
    await ensure_indexes(mongo_client)
    await refresh_connection_metrics(mongo_client)

    redis_client = await create_redis_client()
    cache = RedisCache(redis_client)
    rate_limiter = RateLimiter(cache)

    app.state.mongo_client = mongo_client
    app.state.read_db = get_read_db(mongo_client)
    app.state.write_db = get_write_db(mongo_client)
    app.state.cache = cache
    app.state.rate_limiter = rate_limiter

    try:
        yield
    finally:
        if redis_client is not None:
            await redis_client.aclose()
        mongo_client.close()


app = FastAPI(lifespan=lifespan)


def _is_v2_request(request: Request) -> bool:
    return request.url.path.startswith(settings.API_V2_STR)


def _v2_error_response(
    *,
    status_code: int,
    code: str,
    message: str,
    details: dict | list | None = None,
) -> JSONResponse:
    request_id = get_request_id()
    payload = {
        "data": None,
        "meta": {"request_id": request_id},
        "error": {
            "code": code,
            "message": message,
            "request_id": request_id,
            "details": details,
        },
    }
    return JSONResponse(status_code=status_code, content=payload)


@app.middleware("http")
async def add_global_http_process(request: Request, call_next):
    request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())
    set_request_id(request_id)

    started_at = time.perf_counter()
    path = request.url.path
    method = request.method

    try:
        async with asyncio.timeout(settings.REQUEST_TIMEOUT_MS / 1000):
            response = await call_next(request)
    except TimeoutError:
        if _is_v2_request(request):
            response = _v2_error_response(
                status_code=504,
                code="REQUEST_TIMEOUT",
                message="Request timed out",
            )
        else:
            response = JSONResponse(status_code=504, content={"detail": "Request timed out"})
    except Exception:
        logger.exception("request_failed")
        raise
    finally:
        elapsed = time.perf_counter() - started_at
        REQUEST_LATENCY_SECONDS.labels(method=method, path=path).observe(elapsed)

    response.headers["X-Process-Time"] = str(time.perf_counter() - started_at)
    response.headers["X-Request-ID"] = request_id

    status_code = str(response.status_code)
    REQUEST_COUNT.labels(method=method, path=path, status=status_code).inc()
    if response.status_code >= 400:
        REQUEST_ERRORS.labels(method=method, path=path, status=status_code).inc()

    return response


@app.exception_handler(ApiException)
async def api_exception_handler(request: Request, exc: ApiException):
    if _is_v2_request(request):
        return _v2_error_response(
            status_code=exc.status_code,
            code=exc.code,
            message=exc.message,
            details=exc.details,
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if _is_v2_request(request):
        code = f"HTTP_{exc.status_code}"
        return _v2_error_response(
            status_code=exc.status_code,
            code=code,
            message=str(exc.detail),
        )
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.detail})


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    if _is_v2_request(request):
        return _v2_error_response(
            status_code=422,
            code="VALIDATION_ERROR",
            message="Request payload validation failed",
            details=exc.errors(),
        )
    return JSONResponse(status_code=422, content={"detail": exc.errors()})


@app.exception_handler(Exception)
async def unhandled_exception_handler(request: Request, exc: Exception):
    logger.exception("unhandled_exception", exc_info=exc)
    if _is_v2_request(request):
        return _v2_error_response(
            status_code=500,
            code="INTERNAL_ERROR",
            message="Internal server error",
        )
    return JSONResponse(status_code=500, content={"detail": "Internal server error"})


@app.get(settings.PROMETHEUS_METRICS_PATH, include_in_schema=False)
async def metrics():
    return metrics_response()


app.include_router(health_router, prefix="/health", tags=["health"])
app.include_router(api_router, prefix=settings.API_V1_STR)
app.include_router(api_router_v2, prefix=settings.API_V2_STR)
