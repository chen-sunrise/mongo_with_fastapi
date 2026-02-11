from pydantic import BaseModel

from app.utils import optional


def test_optional_decorator_makes_all_fields_optional():
    @optional()
    class UserPatch(BaseModel):
        email: str
        username: str

    patch = UserPatch()

    assert patch.email is None
    assert patch.username is None


def test_optional_decorator_keeps_original_model_name():
    @optional()
    class StatusPatch(BaseModel):
        active: bool

    assert StatusPatch.__name__ == "StatusPatch"


def test_optional_decorator_can_skip_fields_with_without_fields():
    @optional(without_fields=["id"])
    class ItemPatch(BaseModel):
        id: int
        title: str

    patch = ItemPatch()

    assert "id" not in ItemPatch.model_fields
    assert patch.title is None
