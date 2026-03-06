from app.schemas import ApiResponse, CursorPage, IItemDetail, ResponseMeta


def test_api_response_supports_meta_and_data():
    response = ApiResponse[dict](data={"ok": True}, meta=ResponseMeta(request_id="r1"), error=None)

    payload = response.model_dump()

    assert payload["data"] == {"ok": True}
    assert payload["meta"]["request_id"] == "r1"
    assert payload["error"] is None


def test_cursor_page_serializes_items_and_cursor():
    page = CursorPage[IItemDetail](items=[], next_cursor="abc", has_more=True)

    payload = page.model_dump()

    assert payload["next_cursor"] == "abc"
    assert payload["has_more"] is True
