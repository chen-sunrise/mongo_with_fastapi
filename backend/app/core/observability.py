from starlette.responses import Response

try:
    from prometheus_client import CONTENT_TYPE_LATEST, Counter, Gauge, Histogram, generate_latest
except ModuleNotFoundError:
    CONTENT_TYPE_LATEST = "text/plain; version=0.0.4; charset=utf-8"

    class _NoopMetric:
        def labels(self, **_: str):
            return self

        def inc(self, amount: float = 1.0) -> None:
            _ = amount

        def observe(self, value: float) -> None:
            _ = value

        def set(self, value: float) -> None:
            _ = value

    def Counter(*args, **kwargs):  # type: ignore[misc]
        _ = (args, kwargs)
        return _NoopMetric()

    def Gauge(*args, **kwargs):  # type: ignore[misc]
        _ = (args, kwargs)
        return _NoopMetric()

    def Histogram(*args, **kwargs):  # type: ignore[misc]
        _ = (args, kwargs)
        return _NoopMetric()

    def generate_latest() -> bytes:
        return b""

REQUEST_COUNT = Counter(
    "http_requests_total",
    "Total number of HTTP requests",
    ["method", "path", "status"],
)
REQUEST_LATENCY_SECONDS = Histogram(
    "http_request_latency_seconds",
    "HTTP request latency in seconds",
    ["method", "path"],
)
REQUEST_ERRORS = Counter(
    "http_request_errors_total",
    "Total number of failed requests",
    ["method", "path", "status"],
)
MONGO_OPERATION_SECONDS = Histogram(
    "mongo_operation_seconds",
    "MongoDB operation latency in seconds",
    ["operation"],
)
REDIS_OPERATION_SECONDS = Histogram(
    "redis_operation_seconds",
    "Redis operation latency in seconds",
    ["operation"],
)
MONGO_ACTIVE_CONNECTIONS = Gauge(
    "mongo_connections_current",
    "Current number of MongoDB connections",
)


def metrics_response() -> Response:
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)
