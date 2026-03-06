import pytest
from pymongo import ASCENDING, DESCENDING

from app.utils import QueryBase


def test_get_sort_returns_none_when_order_by_is_missing_or_empty():
    assert QueryBase().get_sort() is None
    assert QueryBase(order_by=[]).get_sort() is None


def test_get_sort_returns_sort_pairs_when_order_by_is_valid():
    sort_pairs = [("created", DESCENDING), ("title", ASCENDING)]

    query = QueryBase(order_by=sort_pairs)

    assert query.get_sort() == sort_pairs


@pytest.mark.parametrize(
    "order_by",
    [
        "created",
        [("created",)],
        [("created", DESCENDING, "extra")],
        [("created", 999)],
        [["created", DESCENDING]],
    ],
)
def test_get_sort_raises_assertion_for_invalid_input(order_by):
    query = QueryBase(order_by=order_by)

    with pytest.raises(ValueError):
        query.get_sort()
