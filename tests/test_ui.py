# -*- coding: utf-8 -*-
"""UI-adjacent data formatting tests (no GUI dependency)."""

from dataclasses import dataclass
from datetime import date, timedelta

import pytest


@dataclass
class ItemViewModel:
    name: str
    quantity: int
    expiry_date: date | None


def build_headline_text(item: ItemViewModel) -> str:
    text = item.name
    if item.quantity > 1:
        text += f" ×{item.quantity}"
    return text


def compute_status_text(item: ItemViewModel) -> str:
    if item.expiry_date is None:
        return "无过期"

    delta = (item.expiry_date - date.today()).days
    if delta < 0:
        return "已过期"
    if delta <= 3:
        return "即将过期"
    return "正常"


@pytest.mark.parametrize(
    ("quantity", "expected"),
    [
        (1, "牛奶"),
        (3, "牛奶 ×3"),
    ],
)
def test_headline_text(quantity, expected):
    item = ItemViewModel(name="牛奶", quantity=quantity, expiry_date=None)
    assert build_headline_text(item) == expected


@pytest.mark.parametrize(
    ("days", "expected"),
    [
        (None, "无过期"),
        (-1, "已过期"),
        (0, "即将过期"),
        (2, "即将过期"),
        (4, "正常"),
    ],
)
def test_status_text(days, expected):
    expiry_date = None if days is None else date.today() + timedelta(days=days)
    item = ItemViewModel(name="鸡蛋", quantity=1, expiry_date=expiry_date)
    assert compute_status_text(item) == expected
