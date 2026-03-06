from typing import List

from fastapi import APIRouter, Body, HTTPException

from app import crud, models, schemas
from app.api.deps import AsyncMongoClient, CurrentUser

router = APIRouter()


@router.post("/obj", response_model=schemas.IItemDetail)
async def create_item(*, db: AsyncMongoClient, current_user: CurrentUser, item_in: schemas.IItemCreate = Body(...)):
    item_in.owner = current_user.id
    create_res = await crud.item.create(db, obj_in=models.Item(**item_in.model_dump()))
    item = await crud.item.first_by_id(db, _id=create_res.inserted_id)
    if item is None:
        raise HTTPException(status_code=500, detail="Item creation failed")
    return item


@router.get("/list", response_model=List[schemas.IItemDetail])
async def get_items(*, db: AsyncMongoClient, current_user: CurrentUser, limit: int = 10, offset: int = 0):
    return await crud.item.get_multi_by_user(db, user=current_user, limit=limit, offset=offset)


@router.put("/obj/{item_id}", response_model=bool)
async def update_item(
    *, db: AsyncMongoClient, current_user: CurrentUser, item_id: str, item_in: schemas.IIUserUpdate = Body(...)
):
    db_item = await crud.item.first_by_user(db, user=current_user, _id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail=f"Not found item {item_id}")
    await crud.item.update(db, _id=item_id, obj_in=item_in)
    return True


@router.delete("/obj/{item_id}", response_model=bool)
async def delete_item(*, db: AsyncMongoClient, current_user: CurrentUser, item_id: str):
    db_item = await crud.item.first_by_user(db, user=current_user, _id=item_id)
    if db_item is None:
        raise HTTPException(status_code=404, detail=f"Not found item {item_id}")
    return await crud.item.delete(db, _id=item_id)
