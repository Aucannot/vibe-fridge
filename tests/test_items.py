# -*- coding: utf-8 -*-
"""Item service smoke tests."""

from datetime import date, timedelta

import pytest


sqlalchemy = pytest.importorskip("sqlalchemy")

from app.services.database import init_database
from app.services.item_service import item_service


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Use an isolated sqlite database for each test."""
    db_file = tmp_path / "test_items.db"
    monkeypatch.setenv("DATABASE_URL", f"sqlite:///{db_file}")
    init_database()


def test_create_item_and_query_list():
    created = item_service.create_item(
        name="苹果",
        quantity=2,
        expiry_date=date.today() + timedelta(days=3),
        category="食品",
    )

    assert created is not None
    assert created.name == "苹果"

    items = item_service.get_items(limit=20)
    assert len(items) >= 1
    assert any(i.name == "苹果" for i in items)
