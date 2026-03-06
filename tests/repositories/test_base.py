from bson import ObjectId
from pydantic import BaseModel

from app.repositories.base import parse_model, parse_object_id


class DemoModel(BaseModel):
    name: str


def test_parse_object_id_accepts_string_and_object_id():
    value = ObjectId()

    assert parse_object_id(str(value)) == value
    assert parse_object_id(value) == value


def test_parse_model_returns_none_for_empty_doc():
    assert parse_model(DemoModel, None) is None


def test_parse_model_builds_model_for_document():
    parsed = parse_model(DemoModel, {"name": "alice"})

    assert parsed is not None
    assert parsed.name == "alice"
