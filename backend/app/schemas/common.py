from typing import Any, Generic, TypeVar

from pydantic import BaseModel


class ResponseMeta(BaseModel):
    request_id: str
    cache_hit: bool | None = None


class ApiError(BaseModel):
    code: str
    message: str
    request_id: str
    details: dict[str, Any] | None = None


T = TypeVar("T")


class ApiResponse(BaseModel, Generic[T]):
    data: T | None = None
    meta: ResponseMeta | None = None
    error: ApiError | None = None


class CursorPage(BaseModel, Generic[T]):
    items: list[T]
    next_cursor: str | None = None
    has_more: bool
