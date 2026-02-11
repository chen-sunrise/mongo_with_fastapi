from app.schemas import IIUserUpdate, IUserUpdate


def test_user_update_schema_accepts_partial_payload():
    payload = IUserUpdate()

    assert payload.email is None
    assert payload.username is None


def test_item_update_schema_accepts_partial_payload():
    payload = IIUserUpdate()

    assert payload.title is None
    assert payload.description is None
    assert payload.owner is None
