# -*- coding: utf-8 -*-
"""UI-adjacent data formatting tests (no GUI dependency)."""

from dataclasses import dataclass
from datetime import date, timedelta


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


def test_headline_text_with_quantity():
    item = ItemViewModel(name="牛奶", quantity=3, expiry_date=None)
    assert build_headline_text(item) == "牛奶 ×3"


def test_status_text_expiring_soon():
    item = ItemViewModel(name="鸡蛋", quantity=1, expiry_date=date.today() + timedelta(days=2))
    assert compute_status_text(item) == "即将过期"
