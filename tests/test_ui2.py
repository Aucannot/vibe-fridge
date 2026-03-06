# -*- coding: utf-8 -*-
"""Additional UI data mapping tests."""

import pytest

CATEGORY_MAP = {
    "food": "食品",
    "daily": "日用品",
    "medicine": "药品",
    "cosmetics": "化妆品",
    "others": "其他",
}


def map_category_text(category: str) -> str:
    return CATEGORY_MAP.get(category, "其他")


@pytest.mark.parametrize(
    ("category", "expected"),
    [
        ("food", "食品"),
        ("daily", "日用品"),
        ("medicine", "药品"),
        ("cosmetics", "化妆品"),
        ("others", "其他"),
        ("unknown", "其他"),
    ],
)
def test_category_mapping(category, expected):
    assert map_category_text(category) == expected
