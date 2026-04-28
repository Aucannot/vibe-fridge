# -*- coding: utf-8 -*-
"""Database migration compatibility tests."""

import sqlite3

from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import sessionmaker

from app.services.database import db_service, init_database
from app.services.order_import_service import SILICONFLOW_MODEL_SETTING


def test_init_database_adds_order_import_columns(tmp_path, monkeypatch):
    db_file = tmp_path / "legacy.db"
    db_url = f"sqlite:///{db_file}"

    conn = sqlite3.connect(db_file)
    conn.execute(
        """
        CREATE TABLE items (
            id VARCHAR(36) PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            status VARCHAR(20),
            created_at DATETIME,
            updated_at DATETIME
        )
        """
    )
    conn.commit()
    conn.close()

    monkeypatch.setenv("DATABASE_URL", db_url)
    engine = create_engine(db_url)
    monkeypatch.setattr(db_service, "engine", engine)
    monkeypatch.setattr(
        db_service,
        "SessionLocal",
        sessionmaker(bind=engine, expire_on_commit=False),
    )

    init_database()

    inspector = inspect(engine)
    item_columns = {column["name"] for column in inspector.get_columns("items")}

    assert "image_path" in item_columns
    assert "source_app" in item_columns
    assert "source_order_id" in item_columns
    assert "source_order_time" in item_columns
    assert "source_order_time_source" in item_columns
    assert "predicted_expiry_date" in item_columns
    assert "prediction_confidence" in item_columns


def test_database_service_can_persist_app_settings(tmp_path, monkeypatch):
    db_file = tmp_path / "settings.db"
    db_url = f"sqlite:///{db_file}"

    monkeypatch.setenv("DATABASE_URL", db_url)
    engine = create_engine(db_url)
    monkeypatch.setattr(db_service, "engine", engine)
    monkeypatch.setattr(
        db_service,
        "SessionLocal",
        sessionmaker(bind=engine, expire_on_commit=False),
    )

    init_database()

    assert db_service.set_setting(
        SILICONFLOW_MODEL_SETTING, "Qwen/Qwen2-VL-72B-Instruct"
    )
    assert (
        db_service.get_setting(SILICONFLOW_MODEL_SETTING)
        == "Qwen/Qwen2-VL-72B-Instruct"
    )
