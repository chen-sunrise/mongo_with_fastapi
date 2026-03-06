from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse
from starlette import status

from app.infra import ping_mongo

router = APIRouter()


@router.get("/live")
async def liveness() -> dict:
    return {"status": "alive"}


@router.get("/ready", status_code=status.HTTP_200_OK)
async def readiness(request: Request) -> JSONResponse:
    mongo_ok = await ping_mongo(request.app.state.mongo_client)
    redis_ok = await request.app.state.cache.ping()

    status_value = "ready" if mongo_ok else "degraded"
    payload = {
        "status": status_value,
        "mongo": mongo_ok,
        "redis": redis_ok,
    }
    status_code = status.HTTP_200_OK if mongo_ok else status.HTTP_503_SERVICE_UNAVAILABLE
    return JSONResponse(status_code=status_code, content=payload)
