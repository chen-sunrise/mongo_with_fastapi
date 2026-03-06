from fastapi import APIRouter, Depends, Request, status
from fastapi.security import OAuth2PasswordRequestForm

from app import schemas
from app.api.deps import (
    AuthServiceDep,
    CurrentUserV2,
    RateLimiterDep,
    UserServiceDep,
)
from app.core import settings
from app.core.request_context import get_request_id

router = APIRouter()


@router.post("/access-token", response_model=schemas.ApiResponse[schemas.Token])
async def login_access_token(
    request: Request,
    auth_service: AuthServiceDep,
    limiter: RateLimiterDep,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    client_ip = request.client.host if request.client is not None else "unknown"
    await limiter.enforce(
        key=f"login:{client_ip}:{form_data.username}",
        limit=settings.LOGIN_RATE_LIMIT_PER_MINUTE,
        window_seconds=60,
        message="Too many login attempts",
    )

    token = await auth_service.login(email=form_data.username, password=form_data.password)
    return schemas.ApiResponse[schemas.Token](
        data=token,
        meta=schemas.ResponseMeta(request_id=get_request_id()),
        error=None,
    )


@router.post("/register", response_model=schemas.ApiResponse[schemas.Token], status_code=status.HTTP_201_CREATED)
async def register_in_public_scope(
    user_in: schemas.IUserCreate,
    auth_service: AuthServiceDep,
):
    token = await auth_service.register(user_in=user_in)
    return schemas.ApiResponse[schemas.Token](
        data=token,
        meta=schemas.ResponseMeta(request_id=get_request_id()),
        error=None,
    )


@router.get("/me", response_model=schemas.ApiResponse[schemas.IUserDetail])
async def get_me(
    request: Request,
    current_user: CurrentUserV2,
    user_service: UserServiceDep,
    limiter: RateLimiterDep,
):
    client_ip = request.client.host if request.client is not None else "unknown"
    await limiter.enforce(
        key=f"read:{client_ip}:{current_user.id}",
        limit=settings.RATE_LIMIT_PER_MINUTE,
        window_seconds=60,
        message="Rate limit exceeded",
    )

    user, cache_hit = await user_service.get_me(user_id=str(current_user.id))
    return schemas.ApiResponse[schemas.IUserDetail](
        data=user,
        meta=schemas.ResponseMeta(request_id=get_request_id(), cache_hit=cache_hit),
        error=None,
    )


@router.put("/obj", response_model=schemas.ApiResponse[schemas.IUserDetail])
async def update_user(
    obj_in: schemas.IUserUpdate,
    current_user: CurrentUserV2,
    user_service: UserServiceDep,
):
    user = await user_service.update_me(user_id=str(current_user.id), obj_in=obj_in)
    return schemas.ApiResponse[schemas.IUserDetail](
        data=user,
        meta=schemas.ResponseMeta(request_id=get_request_id()),
        error=None,
    )


@router.put("/reset_password", response_model=schemas.ApiResponse[schemas.IUserDetail])
async def reset_password(
    password: str,
    current_user: CurrentUserV2,
    user_service: UserServiceDep,
):
    user = await user_service.reset_password(
        user_id=str(current_user.id),
        current_hash=current_user.hashed_password,
        password=password,
    )
    return schemas.ApiResponse[schemas.IUserDetail](
        data=user,
        meta=schemas.ResponseMeta(request_id=get_request_id()),
        error=None,
    )


@router.delete("/obj", response_model=schemas.ApiResponse[dict], status_code=status.HTTP_200_OK)
async def delete_user(
    current_user: CurrentUserV2,
    user_service: UserServiceDep,
):
    await user_service.delete_me(user_id=str(current_user.id))
    return schemas.ApiResponse[dict](
        data={"deleted": True},
        meta=schemas.ResponseMeta(request_id=get_request_id()),
        error=None,
    )
