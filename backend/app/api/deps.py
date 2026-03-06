from typing import Annotated

import jwt
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import OAuth2PasswordBearer
from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from pydantic import ValidationError

from app import crud, models, schemas
from app.core import security, settings
from app.infra import RateLimiter, RedisCache
from app.repositories import ItemRepository, UserRepository
from app.services import AuthService, ItemService, UserService

reusable_oauth2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/users/access-token")
reusable_oauth2_v2 = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V2_STR}/users/access-token")


def get_async_mongo(request: Request) -> AsyncIOMotorClient:
    return request.app.state.mongo_client


def get_read_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.read_db


def get_write_db(request: Request) -> AsyncIOMotorDatabase:
    return request.app.state.write_db


def get_cache(request: Request) -> RedisCache:
    return request.app.state.cache


def get_rate_limiter(request: Request) -> RateLimiter:
    return request.app.state.rate_limiter


def get_user_repository(
    read_db: AsyncIOMotorDatabase = Depends(get_read_db),
    write_db: AsyncIOMotorDatabase = Depends(get_write_db),
) -> UserRepository:
    return UserRepository(read_db=read_db, write_db=write_db)


def get_item_repository(
    read_db: AsyncIOMotorDatabase = Depends(get_read_db),
    write_db: AsyncIOMotorDatabase = Depends(get_write_db),
) -> ItemRepository:
    return ItemRepository(read_db=read_db, write_db=write_db)


def get_auth_service(user_repository: UserRepository = Depends(get_user_repository)) -> AuthService:
    return AuthService(user_repository=user_repository)


def get_user_service(
    user_repository: UserRepository = Depends(get_user_repository),
    cache: RedisCache = Depends(get_cache),
) -> UserService:
    return UserService(user_repository=user_repository, cache=cache)


def get_item_service(
    item_repository: ItemRepository = Depends(get_item_repository),
    cache: RedisCache = Depends(get_cache),
) -> ItemService:
    return ItemService(item_repository=item_repository, cache=cache)


async def get_current_user(
    db: AsyncIOMotorClient = Depends(get_async_mongo),
    token: str = Depends(reusable_oauth2),
) -> models.User:
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
        token_data = schemas.TokenPayload(**payload)
    except (jwt.PyJWTError, ValidationError):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Could not validate credentials",
        )

    if token_data.sub is None:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Could not validate credentials")

    user = await crud.user.first_by_id(db, _id=token_data.sub)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return user


async def get_current_user_v2(
    auth_service: AuthService = Depends(get_auth_service),
    token: str = Depends(reusable_oauth2_v2),
) -> models.User:
    return await auth_service.get_current_user(token=token)


async def enforce_user_read_rate_limit(
    current_user: models.User = Depends(get_current_user_v2),
    limiter: RateLimiter = Depends(get_rate_limiter),
) -> None:
    await limiter.enforce(
        key=f"read:user:{current_user.id}",
        limit=settings.RATE_LIMIT_PER_MINUTE,
        window_seconds=60,
        message="Rate limit exceeded",
    )


AsyncMongoClient = Annotated[AsyncIOMotorClient, Depends(get_async_mongo)]
CurrentUser = Annotated[models.User, Depends(get_current_user)]
CurrentUserV2 = Annotated[models.User, Depends(get_current_user_v2)]
AuthServiceDep = Annotated[AuthService, Depends(get_auth_service)]
UserServiceDep = Annotated[UserService, Depends(get_user_service)]
ItemServiceDep = Annotated[ItemService, Depends(get_item_service)]
RateLimiterDep = Annotated[RateLimiter, Depends(get_rate_limiter)]
