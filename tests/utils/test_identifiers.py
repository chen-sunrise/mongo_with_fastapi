from uuid import UUID, uuid4

import pytest
from bson import Binary, ObjectId
from pydantic import BaseModel

from app.utils import PydanticObjectId, PydanticUuid
from app.utils._objectid import ObjectIdAnnotation
from app.utils._uuid import UUIDAnnotation


class IdentityModel(BaseModel):
    object_id: PydanticObjectId
    uuid_value: PydanticUuid


def test_objectid_validator_accepts_valid_hex():
    object_id = ObjectId()

    parsed = ObjectIdAnnotation.validate(str(object_id))

    assert isinstance(parsed, ObjectId)
    assert parsed == object_id


def test_objectid_validator_rejects_invalid_value():
    with pytest.raises(ValueError, match="Invalid id"):
        ObjectIdAnnotation.validate("not-an-object-id")


def test_uuid_validator_accepts_uuid_string_and_binary():
    uuid_value = uuid4()

    parsed_from_string = UUIDAnnotation.validate(str(uuid_value))
    parsed_from_binary = UUIDAnnotation.validate(Binary(uuid_value.bytes))

    assert isinstance(parsed_from_string, UUID)
    assert parsed_from_string == uuid_value
    assert parsed_from_binary == uuid_value


def test_uuid_validator_rejects_invalid_value():
    with pytest.raises(ValueError, match="Invalid UUID value"):
        UUIDAnnotation.validate(123)


def test_pydantic_identifier_types_parse_and_serialize():
    object_id = ObjectId()
    uuid_value = uuid4()

    model = IdentityModel(object_id=str(object_id), uuid_value=str(uuid_value))
    serialized = model.model_dump(mode="json")

    assert model.object_id == object_id
    assert model.uuid_value == uuid_value
    assert serialized["object_id"] == str(object_id)
    assert serialized["uuid_value"] == str(uuid_value)
