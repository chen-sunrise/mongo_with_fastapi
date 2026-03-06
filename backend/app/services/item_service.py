from app import schemas
from app.core import settings
from app.core.errors import ApiException
from app.infra.redis_cache import RedisCache
from app.repositories import ItemRepository


class ItemService:
    def __init__(self, item_repository: ItemRepository, cache: RedisCache):
        self.item_repository = item_repository
        self.cache = cache

    async def create_item(self, *, user_id: str, item_in: schemas.IItemCreate) -> schemas.IItemDetail:
        created = await self.item_repository.create(user_id=user_id, item_in=item_in)
        await self._invalidate_list_cache(user_id)
        return schemas.IItemDetail(**created.model_dump())

    async def list_items(
        self,
        *,
        user_id: str,
        cursor: str | None,
        limit: int,
    ) -> tuple[schemas.CursorPage[schemas.IItemDetail], bool]:
        safe_limit = min(max(limit, 1), settings.MAX_PAGE_SIZE)
        cursor_label = cursor or "root"
        cache_key = f"items:list:{user_id}:{cursor_label}:{safe_limit}"

        async def fetcher() -> dict:
            items, next_cursor, has_more = await self.item_repository.list_by_owner_cursor(
                user_id=user_id,
                cursor=cursor,
                limit=safe_limit,
            )
            payload_items = [schemas.IItemDetail(**item.model_dump()).model_dump(mode="json") for item in items]
            return {
                "items": payload_items,
                "next_cursor": next_cursor,
                "has_more": has_more,
            }

        payload, cache_hit = await self.cache.get_or_set_singleflight(
            key=cache_key,
            ttl_seconds=settings.CACHE_TTL_SECONDS,
            fetcher=fetcher,
        )

        page = schemas.CursorPage[schemas.IItemDetail](
            items=[schemas.IItemDetail(**item) for item in payload["items"]],
            next_cursor=payload["next_cursor"],
            has_more=payload["has_more"],
        )
        return page, cache_hit

    async def update_item(
        self,
        *,
        user_id: str,
        item_id: str,
        item_in: schemas.IIUserUpdate,
    ) -> schemas.IItemDetail:
        updated = await self.item_repository.update(item_id=item_id, user_id=user_id, obj_in=item_in)
        if updated is None:
            raise ApiException(status_code=404, code="ITEM_NOT_FOUND", message="Item not found")

        await self._invalidate_list_cache(user_id)
        return schemas.IItemDetail(**updated.model_dump())

    async def delete_item(self, *, user_id: str, item_id: str) -> None:
        deleted = await self.item_repository.delete(item_id=item_id, user_id=user_id)
        if not deleted:
            raise ApiException(status_code=404, code="ITEM_NOT_FOUND", message="Item not found")
        await self._invalidate_list_cache(user_id)

    async def _invalidate_list_cache(self, user_id: str) -> None:
        await self.cache.delete_pattern(f"items:list:{user_id}:*")
