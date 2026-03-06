from datetime import datetime, timezone

from motor.motor_asyncio import AsyncIOMotorDatabase

from app import models, schemas
from app.core import security, settings
from app.repositories.base import parse_model, parse_object_id


class UserRepository:
    def __init__(self, read_db: AsyncIOMotorDatabase, write_db: AsyncIOMotorDatabase):
        self.read_db = read_db
        self.write_db = write_db

    @property
    def read_collection(self):
        return self.read_db[settings.MONGO_DB_USER_COLLECTION]

    @property
    def write_collection(self):
        return self.write_db[settings.MONGO_DB_USER_COLLECTION]

    async def get_by_id(self, user_id: str) -> models.User | None:
        user = await self.read_collection.find_one({"_id": parse_object_id(user_id)})
        return parse_model(models.User, user)

    async def get_by_email(self, email: str) -> models.User | None:
        user = await self.read_collection.find_one({"email": email})
        return parse_model(models.User, user)

    async def get_by_username(self, username: str) -> models.User | None:
        user = await self.read_collection.find_one({"username": username})
        return parse_model(models.User, user)

    async def create(self, user_in: schemas.IUserCreate) -> models.User:
        payload = {
            "email": user_in.email,
            "username": user_in.username,
            "hashed_password": security.get_password_hash(user_in.password),
            "created": datetime.now(timezone.utc),
            "updated": datetime.now(timezone.utc),
        }
        insert_result = await self.write_collection.insert_one(payload)
        created = await self.read_collection.find_one({"_id": insert_result.inserted_id})
        parsed = parse_model(models.User, created)
        if parsed is None:
            raise ValueError("newly_created_user_not_found")
        return parsed

    async def update(self, user_id: str, obj_in: schemas.IUserUpdate | dict) -> models.User | None:
        if isinstance(obj_in, dict):
            update_data = obj_in
        else:
            update_data = obj_in.model_dump(exclude_unset=True)

        if not update_data:
            return await self.get_by_id(user_id)

        update_data["updated"] = datetime.now(timezone.utc)
        await self.write_collection.update_one(
            {"_id": parse_object_id(user_id)},
            {"$set": update_data},
        )
        return await self.get_by_id(user_id)

    async def delete(self, user_id: str) -> bool:
        result = await self.write_collection.delete_one({"_id": parse_object_id(user_id)})
        return result.deleted_count > 0
