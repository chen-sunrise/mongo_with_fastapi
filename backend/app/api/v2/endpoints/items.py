from fastapi import APIRouter, Body, Query, Request, status

from app import schemas
from app.api.deps import CurrentUserV2, ItemServiceDep, RateLimiterDep
from app.core import settings
from app.core.request_context import get_request_id

router = APIRouter()


@router.post("/obj", response_model=schemas.ApiResponse[schemas.IItemDetail], status_code=status.HTTP_201_CREATED)
async def create_item(
    current_user: CurrentUserV2,
    item_service: ItemServiceDep,
    item_in: schemas.IItemCreate = Body(...),
):
    item = await item_service.create_item(user_id=str(current_user.id), item_in=item_in)
    return schemas.ApiResponse[schemas.IItemDetail](
        data=item,
        meta=schemas.ResponseMeta(request_id=get_request_id()),
        error=None,
    )


@router.get("/list", response_model=schemas.ApiResponse[schemas.CursorPage[schemas.IItemDetail]])
async def get_items(
    request: Request,
    current_user: CurrentUserV2,
    item_service: ItemServiceDep,
    limiter: RateLimiterDep,
    cursor: str | None = Query(default=None),
    limit: int = Query(default=settings.DEFAULT_PAGE_SIZE, ge=1, le=settings.MAX_PAGE_SIZE),
):
    client_ip = request.client.host if request.client is not None else "unknown"
    await limiter.enforce(
        key=f"read:{client_ip}:{current_user.id}",
        limit=settings.RATE_LIMIT_PER_MINUTE,
        window_seconds=60,
        message="Rate limit exceeded",
    )

    page, cache_hit = await item_service.list_items(user_id=str(current_user.id), cursor=cursor, limit=limit)
    return schemas.ApiResponse[schemas.CursorPage[schemas.IItemDetail]](
        data=page,
        meta=schemas.ResponseMeta(request_id=get_request_id(), cache_hit=cache_hit),
        error=None,
    )


@router.put("/obj/{item_id}", response_model=schemas.ApiResponse[schemas.IItemDetail])
async def update_item(
    item_id: str,
    current_user: CurrentUserV2,
    item_service: ItemServiceDep,
    item_in: schemas.IIUserUpdate = Body(...),
):
    item = await item_service.update_item(user_id=str(current_user.id), item_id=item_id, item_in=item_in)
    return schemas.ApiResponse[schemas.IItemDetail](
        data=item,
        meta=schemas.ResponseMeta(request_id=get_request_id()),
        error=None,
    )


@router.delete("/obj/{item_id}", response_model=schemas.ApiResponse[dict], status_code=status.HTTP_200_OK)
async def delete_item(
    item_id: str,
    current_user: CurrentUserV2,
    item_service: ItemServiceDep,
):
    await item_service.delete_item(user_id=str(current_user.id), item_id=item_id)
    return schemas.ApiResponse[dict](
        data={"deleted": True},
        meta=schemas.ResponseMeta(request_id=get_request_id()),
        error=None,
    )
