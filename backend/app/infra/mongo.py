import time
from logging import getLogger

from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pymongo import ASCENDING, DESCENDING, IndexModel
from pymongo.write_concern import WriteConcern

from app.core.config import settings
from app.core.observability import MONGO_ACTIVE_CONNECTIONS, MONGO_OPERATION_SECONDS

logger = getLogger(__name__)


def create_mongo_client() -> AsyncIOMotorClient:
    return AsyncIOMotorClient(
        settings.MONGO_DB_URI,
        uuidRepresentation="standard",
        maxPoolSize=settings.MONGO_MAX_POOL_SIZE,
        minPoolSize=settings.MONGO_MIN_POOL_SIZE,
        serverSelectionTimeoutMS=settings.MONGO_SERVER_SELECTION_TIMEOUT_MS,
        maxIdleTimeMS=settings.MONGO_MAX_IDLE_TIME_MS,
        connectTimeoutMS=settings.MONGO_CONNECT_TIMEOUT_MS,
        socketTimeoutMS=settings.MONGO_SOCKET_TIMEOUT_MS,
    )


def get_read_db(client: AsyncIOMotorClient) -> AsyncIOMotorDatabase:
    return client[settings.MONGO_DB_DATABASE]


def get_write_db(client: AsyncIOMotorClient) -> AsyncIOMotorDatabase:
    return client.get_database(settings.MONGO_DB_DATABASE, write_concern=WriteConcern("majority"))


async def ensure_indexes(client: AsyncIOMotorClient) -> None:
    database = client[settings.MONGO_DB_DATABASE]
    users_collection = database[settings.MONGO_DB_USER_COLLECTION]
    items_collection = database[settings.MONGO_DB_ITEM_COLLECTION]

    user_indexes = [
        IndexModel([("email", ASCENDING)], unique=True, name="users_email_unique"),
        IndexModel([("username", ASCENDING)], unique=True, sparse=True, name="users_username_unique_sparse"),
    ]
    item_indexes = [
        IndexModel([("owner", ASCENDING), ("created", DESCENDING)], name="items_owner_created_idx"),
        IndexModel([("owner", ASCENDING), ("_id", DESCENDING)], name="items_owner_id_idx"),
    ]

    await users_collection.create_indexes(user_indexes)
    await items_collection.create_indexes(item_indexes)


async def ping_mongo(client: AsyncIOMotorClient) -> bool:
    started_at = time.perf_counter()
    try:
        response = await client.admin.command("ping")
        ok = bool(response.get("ok"))
        return ok
    finally:
        MONGO_OPERATION_SECONDS.labels(operation="admin_ping").observe(time.perf_counter() - started_at)


async def refresh_connection_metrics(client: AsyncIOMotorClient) -> None:
    started_at = time.perf_counter()
    try:
        status = await client.admin.command("serverStatus")
        connections = status.get("connections", {})
        current = connections.get("current")
        if isinstance(current, (int, float)):
            MONGO_ACTIVE_CONNECTIONS.set(current)
    except Exception:
        logger.exception("failed_to_refresh_mongo_connection_metrics")
    finally:
        MONGO_OPERATION_SECONDS.labels(operation="server_status").observe(time.perf_counter() - started_at)
