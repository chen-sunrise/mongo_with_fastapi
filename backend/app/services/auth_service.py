from datetime import timedelta

import jwt
from pydantic import ValidationError

from app import models, schemas
from app.core import security, settings
from app.core.errors import ApiException
from app.repositories import UserRepository


class AuthService:
    def __init__(self, user_repository: UserRepository):
        self.user_repository = user_repository

    async def login(self, *, email: str, password: str) -> schemas.Token:
        user = await self.user_repository.get_by_email(email)
        if user is None or not security.verify_password(password, user.hashed_password):
            raise ApiException(
                status_code=400,
                code="AUTH_INVALID_CREDENTIALS",
                message="Incorrect email or password",
            )
        return self._build_access_token(user)

    async def register(self, *, user_in: schemas.IUserCreate) -> schemas.Token:
        existing_email = await self.user_repository.get_by_email(user_in.email)
        if existing_email is not None:
            raise ApiException(
                status_code=409,
                code="USER_EMAIL_EXISTS",
                message="Email is already registered",
            )

        if user_in.username is not None:
            existing_username = await self.user_repository.get_by_username(user_in.username)
            if existing_username is not None:
                raise ApiException(
                    status_code=409,
                    code="USER_USERNAME_EXISTS",
                    message="Username is already registered",
                )

        user = await self.user_repository.create(user_in)
        return self._build_access_token(user)

    async def get_current_user(self, *, token: str) -> models.User:
        try:
            payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[security.ALGORITHM])
            token_data = schemas.TokenPayload(**payload)
        except (jwt.PyJWTError, ValidationError):
            raise ApiException(
                status_code=403,
                code="AUTH_INVALID_TOKEN",
                message="Could not validate credentials",
            )

        if token_data.sub is None:
            raise ApiException(status_code=403, code="AUTH_INVALID_TOKEN", message="Token subject is missing")

        user = await self.user_repository.get_by_id(token_data.sub)
        if user is None:
            raise ApiException(status_code=404, code="USER_NOT_FOUND", message="User not found")
        return user

    def _build_access_token(self, user: models.User) -> schemas.Token:
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        access_token = security.create_access_token(user.id, expires_delta=access_token_expires)
        return schemas.Token(access_token=access_token, token_type="bearer")
