# -*- coding: utf-8 -*-
"""Additional UI data mapping tests."""

CATEGORY_MAP = {
    "food": "食品",
    "daily": "日用品",
    "medicine": "药品",
    "cosmetics": "化妆品",
    "others": "其他",
}


def map_category_text(category: str) -> str:
    return CATEGORY_MAP.get(category, "其他")


def test_category_mapping_known_value():
    assert map_category_text("medicine") == "药品"


def test_category_mapping_fallback_value():
    assert map_category_text("unknown") == "其他"
