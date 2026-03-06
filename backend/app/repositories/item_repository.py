from datetime import datetime, timezone

from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorDatabase
from pymongo import DESCENDING

from app import models, schemas
from app.core import settings
from app.repositories.base import parse_model, parse_object_id


class ItemRepository:
    def __init__(self, read_db: AsyncIOMotorDatabase, write_db: AsyncIOMotorDatabase):
        self.read_db = read_db
        self.write_db = write_db

    @property
    def read_collection(self):
        return self.read_db[settings.MONGO_DB_ITEM_COLLECTION]

    @property
    def write_collection(self):
        return self.write_db[settings.MONGO_DB_ITEM_COLLECTION]

    async def create(self, *, user_id: str, item_in: schemas.IItemCreate) -> models.Item:
        payload = item_in.model_dump(exclude_unset=True)
        payload["owner"] = parse_object_id(user_id)
        payload["created"] = datetime.now(timezone.utc)
        payload["updated"] = datetime.now(timezone.utc)

        insert_result = await self.write_collection.insert_one(payload)
        document = await self.read_collection.find_one({"_id": insert_result.inserted_id})
        parsed = parse_model(models.Item, document)
        if parsed is None:
            raise ValueError("newly_created_item_not_found")
        return parsed

    async def get_by_id_and_owner(self, *, item_id: str, user_id: str) -> models.Item | None:
        document = await self.read_collection.find_one(
            {
                "_id": parse_object_id(item_id),
                "owner": parse_object_id(user_id),
            }
        )
        return parse_model(models.Item, document)

    async def list_by_owner_cursor(
        self,
        *,
        user_id: str,
        cursor: str | None,
        limit: int,
    ) -> tuple[list[models.Item], str | None, bool]:
        query: dict[str, ObjectId | dict[str, ObjectId]] = {"owner": parse_object_id(user_id)}
        if cursor is not None:
            query["_id"] = {"$lt": parse_object_id(cursor)}

        db_cursor = self.read_collection.find(query).sort("_id", DESCENDING).limit(limit + 1)
        documents = await db_cursor.to_list(length=limit + 1)

        has_more = len(documents) > limit
        current_page = documents[:limit]

        next_cursor: str | None = None
        if has_more and current_page:
            next_cursor = str(current_page[-1]["_id"])

        return [models.Item(**item) for item in current_page], next_cursor, has_more

    async def update(
        self,
        *,
        item_id: str,
        user_id: str,
        obj_in: schemas.IIUserUpdate,
    ) -> models.Item | None:
        update_data = obj_in.model_dump(exclude_unset=True)
        if "owner" in update_data and update_data["owner"] is not None:
            update_data["owner"] = parse_object_id(str(update_data["owner"]))

        if update_data:
            update_data["updated"] = datetime.now(timezone.utc)
            await self.write_collection.update_one(
                {
                    "_id": parse_object_id(item_id),
                    "owner": parse_object_id(user_id),
                },
                {"$set": update_data},
            )

        return await self.get_by_id_and_owner(item_id=item_id, user_id=user_id)

    async def delete(self, *, item_id: str, user_id: str) -> bool:
        result = await self.write_collection.delete_one(
            {
                "_id": parse_object_id(item_id),
                "owner": parse_object_id(user_id),
            }
        )
        return result.deleted_count > 0
