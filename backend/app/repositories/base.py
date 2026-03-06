from typing import TypeVar

from bson import ObjectId
from pydantic import BaseModel

ModelType = TypeVar("ModelType", bound=BaseModel)


def parse_object_id(value: str | ObjectId) -> ObjectId:
    if isinstance(value, ObjectId):
        return value
    return ObjectId(value)


def parse_model(model: type[ModelType], document: dict | None) -> ModelType | None:
    if document is None:
        return None
    return model(**document)
