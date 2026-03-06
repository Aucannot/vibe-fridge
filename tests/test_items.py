# -*- coding: utf-8 -*-
"""Item service smoke tests."""

from datetime import date, timedelta

import pytest


pytest.importorskip("sqlalchemy")
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.services.database import db_service, init_database
from app.services.item_service import item_service


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    """Use an isolated sqlite database for each test."""
    db_file = tmp_path / "test_items.db"
    db_url = f"sqlite:///{db_file}"
    monkeypatch.setenv("DATABASE_URL", db_url)

    # `db_service` is created at import time, so we must rebind its engine/session
    # after overriding DATABASE_URL. Otherwise tests may accidentally hit real data.
    engine = create_engine(db_url)
    monkeypatch.setattr(db_service, "engine", engine)
    monkeypatch.setattr(db_service, "SessionLocal", sessionmaker(bind=engine))

    init_database()
    yield
    engine.dispose()


def test_create_item_and_query_list():
    created = item_service.create_item(
        name="苹果",
        quantity=2,
        expiry_date=date.today() + timedelta(days=3),
        category="食品",
    )

    assert created is not None
    assert created.name == "苹果"
    assert created.quantity == 2

    items = item_service.get_items(limit=20)
    assert len(items) >= 1
    assert any(i.name == "苹果" for i in items)
