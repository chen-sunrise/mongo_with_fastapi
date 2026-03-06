from typing import List, Optional

from app import models, schemas
from app.core import settings
from app.utils import QueryBase
from bson import ObjectId
from motor.motor_asyncio import AsyncIOMotorClient

from .base import CRUDBase


class CRUDItem(CRUDBase[models.Item, schemas.IItemCreate, schemas.IIUserUpdate]):
    async def get_multi_by_user(
        self, db: AsyncIOMotorClient, *, user: models.User, limit: int = 10, offset: int = 0
    ) -> List[models.Item]:
        owner_id = ObjectId(str(user.id))
        return await self.get_multi(
            db,
            query=QueryBase(filters={"owner": {"$in": [owner_id, str(user.id)]}}, limit=limit, offset=offset),
        )

    async def first_by_user(self, db: AsyncIOMotorClient, *, user: models.User, _id: str) -> Optional[models.Item]:
        owner_id = ObjectId(str(user.id))
        return await self.first(
            db,
            query=QueryBase(
                filters={"$and": [{"_id": ObjectId(_id)}, {"owner": {"$in": [owner_id, str(user.id)]}}]}
            ),
        )


item = CRUDItem(models.Item, database=settings.MONGO_DB_DATABASE, collection=settings.MONGO_DB_ITEM_COLLECTION)
