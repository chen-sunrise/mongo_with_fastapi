from datetime import timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, HTTPException
from fastapi.security import OAuth2PasswordRequestForm

from app import crud, schemas
from app.api.deps import AsyncMongoClient, CurrentUser
from app.core import security
from app.core.config import settings

router = APIRouter()


@router.post("/access-token", response_model=schemas.Token, include_in_schema=False)
async def login_access_token(db: AsyncMongoClient, form_data: OAuth2PasswordRequestForm = Depends()) -> Any:
    user = await crud.user.authenticate(db, email=form_data.username, password=form_data.password)
    if not user:
        raise HTTPException(status_code=400, detail="Incorrect email or password")
    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
    return schemas.Token(access_token=access_token, token_type="bearer")


@router.post("/register", response_model=Optional[schemas.Token], summary="User Register")
async def register_in_public_scope(*, db: AsyncMongoClient, user_in: schemas.IUserCreate) -> Any:
    user_res = await crud.user.create(db, obj_in=user_in)
    user_obj = await crud.user.first_by_id(db, _id=user_res.inserted_id)
    if user_obj is None:
        raise HTTPException(status_code=500, detail="User registration failed")

    access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    access_token = security.create_access_token(user_obj.id, expires_delta=access_token_expires)
    return schemas.Token(access_token=access_token, token_type="bearer")


@router.get("/me", response_model=schemas.IUserDetail)
async def get_me(*, current_user: CurrentUser):
    return current_user


@router.put("/obj", response_model=schemas.IUserDetail)
async def update_user(*, db: AsyncMongoClient, current_user: CurrentUser, obj_in: schemas.IUserUpdate):
    await crud.user.update(db, _id=current_user.id, obj_in=obj_in)
    updated_user = await crud.user.first_by_id(db, _id=current_user.id)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user


@router.put("/reset_password", response_model=schemas.IUserDetail)
async def reset_password(*, db: AsyncMongoClient, current_user: CurrentUser, password: str):
    verify_res = security.verify_password(password, current_user.hashed_password)
    if verify_res is True:
        return current_user

    await crud.user.update(db, _id=current_user.id, obj_in={"hashed_password": security.get_password_hash(password)})
    updated_user = await crud.user.first_by_id(db, _id=current_user.id)
    if updated_user is None:
        raise HTTPException(status_code=404, detail="User not found")
    return updated_user


@router.delete("/obj", response_model=bool)
async def delete_user(*, db: AsyncMongoClient, current_user: CurrentUser):
    await crud.user.delete(db, _id=current_user.id)
    return True
