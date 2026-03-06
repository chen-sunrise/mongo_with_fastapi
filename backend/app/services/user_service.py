from app import schemas
from app.core import security, settings
from app.core.errors import ApiException
from app.repositories import UserRepository
from app.infra.redis_cache import RedisCache


class UserService:
    def __init__(self, user_repository: UserRepository, cache: RedisCache):
        self.user_repository = user_repository
        self.cache = cache

    async def get_me(self, *, user_id: str) -> tuple[schemas.IUserDetail, bool]:
        cache_key = f"users:me:{user_id}"

        async def fetcher() -> dict:
            user = await self.user_repository.get_by_id(user_id)
            if user is None:
                raise ApiException(status_code=404, code="USER_NOT_FOUND", message="User not found")
            return schemas.IUserDetail(**user.model_dump()).model_dump(mode="json")

        payload, cache_hit = await self.cache.get_or_set_singleflight(
            key=cache_key,
            ttl_seconds=settings.CACHE_TTL_SECONDS,
            fetcher=fetcher,
        )
        return schemas.IUserDetail(**payload), cache_hit

    async def update_me(self, *, user_id: str, obj_in: schemas.IUserUpdate) -> schemas.IUserDetail:
        updated = await self.user_repository.update(user_id, obj_in)
        if updated is None:
            raise ApiException(status_code=404, code="USER_NOT_FOUND", message="User not found")

        await self.cache.delete(f"users:me:{user_id}")
        return schemas.IUserDetail(**updated.model_dump())

    async def reset_password(self, *, user_id: str, current_hash: str, password: str) -> schemas.IUserDetail:
        if security.verify_password(password, current_hash):
            user = await self.user_repository.get_by_id(user_id)
            if user is None:
                raise ApiException(status_code=404, code="USER_NOT_FOUND", message="User not found")
            return schemas.IUserDetail(**user.model_dump())

        updated = await self.user_repository.update(user_id, {"hashed_password": security.get_password_hash(password)})
        if updated is None:
            raise ApiException(status_code=404, code="USER_NOT_FOUND", message="User not found")

        await self.cache.delete(f"users:me:{user_id}")
        return schemas.IUserDetail(**updated.model_dump())

    async def delete_me(self, *, user_id: str) -> None:
        deleted = await self.user_repository.delete(user_id)
        if not deleted:
            raise ApiException(status_code=404, code="USER_NOT_FOUND", message="User not found")
        await self.cache.delete(f"users:me:{user_id}")
