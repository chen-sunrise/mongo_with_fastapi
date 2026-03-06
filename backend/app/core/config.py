from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", case_sensitive=True)

    API_V1_STR: str = "/api/v1"
    API_V2_STR: str = "/api/v2"
    SECRET_KEY: str

    MONGO_DB_URI: str
    MONGO_DB_DATABASE: str
    MONGO_DB_USER_COLLECTION: str
    MONGO_DB_ITEM_COLLECTION: str
    MONGO_MAX_POOL_SIZE: int = 80
    MONGO_MIN_POOL_SIZE: int = 10
    MONGO_SERVER_SELECTION_TIMEOUT_MS: int = 2000
    MONGO_MAX_IDLE_TIME_MS: int = 60000
    MONGO_CONNECT_TIMEOUT_MS: int = 2000
    MONGO_SOCKET_TIMEOUT_MS: int = 5000

    REDIS_URL: str | None = None
    REDIS_SOCKET_TIMEOUT_SECONDS: float = 1.0
    CACHE_TTL_SECONDS: int = 30
    CACHE_LOCK_SECONDS: int = 2
    CACHE_LOCK_RETRY_COUNT: int = 4
    CACHE_LOCK_RETRY_DELAY_MS: int = 50

    RATE_LIMIT_PER_MINUTE: int = 120
    LOGIN_RATE_LIMIT_PER_MINUTE: int = 20

    REQUEST_TIMEOUT_MS: int = 5000
    MAX_PAGE_SIZE: int = 100
    DEFAULT_PAGE_SIZE: int = 20

    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_SECONDS: int = 15

    ACCESS_TOKEN_EXPIRE_MINUTES: int = 24 * 60 * 30

    PROMETHEUS_METRICS_PATH: str = "/metrics"
    INTERNAL_ROUTE_PREFIXES: tuple[str, ...] = Field(default=("/health", "/metrics"))


settings = Settings()
