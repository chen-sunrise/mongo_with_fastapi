from typing import Optional

from pydantic import BaseModel, EmailStr

from .base import MongoObjectBase, SchemaBase


class UserBase(BaseModel):
    username: Optional[str] = None
    email: EmailStr
    hashed_password: str


class User(MongoObjectBase, SchemaBase, UserBase): ...
