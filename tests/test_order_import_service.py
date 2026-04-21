# -*- coding: utf-8 -*-
"""Order import service tests."""

import json
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.item import Item
from app.services.database import db_service, init_database
from app.services.order_import_service import order_import_service
from app.services.wiki_service import wiki_service


class FakeResponse:
    def __init__(self, payload):
        self._payload = payload

    def raise_for_status(self):
        return None

    def json(self):
        return self._payload


@pytest.fixture(autouse=True)
def isolated_db(tmp_path, monkeypatch):
    db_file = tmp_path / "test_order_import.db"
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
    yield
    engine.dispose()


@pytest.fixture
def screenshot_file(tmp_path) -> str:
    image_path = tmp_path / "order.png"
    image_path.write_bytes(b"fake-image-data")
    return str(image_path)


def test_parse_order_screenshot_normalizes_missing_fields(monkeypatch, screenshot_file):
    monkeypatch.setenv("SILICON_FLOW_API_KEY", "test-key")
    wiki_service.create_wiki(
        name="鲜牛奶",
        default_unit="盒",
        suggested_expiry_days=7,
    )

    model_json = {
        "source_app": "盒马",
        "source_order_id": "HM-20260401",
        "purchase_date": "2026/04/01",
        "items": [
            {
                "name": "鲜牛奶",
                "quantity": "",
                "unit": "",
                "category": "",
                "purchase_date": None,
                "expiry_date": None,
                "confidence": "0.82",
                "warnings": ["OCR 行有截断"],
            }
        ],
    }
    response_payload = {
        "choices": [
            {
                "message": {
                    "content": f"```json\n{json.dumps(model_json, ensure_ascii=False)}\n```"
                }
            }
        ]
    }
    monkeypatch.setattr(
        "app.services.order_import_service.requests.post",
        lambda *args, **kwargs: FakeResponse(response_payload),
    )

    parsed = order_import_service.parse_order_screenshot(screenshot_file)

    assert parsed["source_app"] == "盒马"
    assert parsed["source_order_id"] == "HM-20260401"
    assert parsed["purchase_date"] == "2026-04-01"
    assert parsed["image_path"] == str(Path(screenshot_file).resolve())

    first_item = parsed["items"][0]
    assert first_item["name"] == "鲜牛奶"
    assert first_item["quantity"] == 1
    assert first_item["unit"] == "盒"
    assert first_item["category"] == "食品"
    assert first_item["purchase_date"] == "2026-04-01"
    assert first_item["expiry_date"] == "2026-04-08"
    assert first_item["selected"] is True
    assert first_item["can_import"] is True
    assert "OCR 行有截断" in first_item["warnings"]
    assert any("Wiki 默认单位" in warning for warning in first_item["warnings"])


def test_parse_order_screenshot_requires_api_key(screenshot_file, monkeypatch):
    monkeypatch.delenv("SILICON_FLOW_API_KEY", raising=False)

    with pytest.raises(RuntimeError, match="未配置 API Key"):
        order_import_service.parse_order_screenshot(screenshot_file)


def test_parse_order_screenshot_rejects_invalid_json(monkeypatch, screenshot_file):
    monkeypatch.setenv("SILICON_FLOW_API_KEY", "test-key")
    monkeypatch.setattr(
        "app.services.order_import_service.requests.post",
        lambda *args, **kwargs: FakeResponse(
            {"choices": [{"message": {"content": "not-json-response"}}]}
        ),
    )

    with pytest.raises(RuntimeError, match="JSON"):
        order_import_service.parse_order_screenshot(screenshot_file)


def test_parse_order_screenshot_uses_saved_model_config(monkeypatch, screenshot_file):
    monkeypatch.setenv("SILICON_FLOW_API_KEY", "test-key")
    monkeypatch.delenv("SILICON_FLOW_VISION_MODEL", raising=False)
    assert db_service.set_setting(
        "silicon_flow_vision_model", "zai-org/GLM-4.1V-9B-Thinking"
    )

    captured = {}
    model_json = {
        "source_app": "盒马",
        "source_order_id": "HM-100",
        "purchase_date": "2026-04-01",
        "items": [],
    }

    def fake_post(*args, **kwargs):
        captured["model"] = kwargs["json"]["model"]
        return FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(model_json, ensure_ascii=False)
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("app.services.order_import_service.requests.post", fake_post)

    parsed = order_import_service.parse_order_screenshot(screenshot_file)

    assert captured["model"] == "zai-org/GLM-4.1V-9B-Thinking"
    assert parsed["source_order_id"] == "HM-100"


def test_parse_order_screenshot_uses_saved_api_key_when_env_missing(monkeypatch, screenshot_file):
    monkeypatch.delenv("SILICON_FLOW_API_KEY", raising=False)
    assert db_service.set_setting("silicon_flow_api_key", "app-saved-key")

    captured = {}
    model_json = {
        "source_app": "盒马",
        "source_order_id": "HM-200",
        "purchase_date": "2026-04-02",
        "items": [],
    }

    def fake_post(*args, **kwargs):
        captured["authorization"] = kwargs["headers"]["Authorization"]
        return FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(model_json, ensure_ascii=False)
                        }
                    }
                ]
            }
        )

    monkeypatch.setattr("app.services.order_import_service.requests.post", fake_post)

    parsed = order_import_service.parse_order_screenshot(screenshot_file)

    assert captured["authorization"] == "Bearer app-saved-key"
    assert parsed["source_order_id"] == "HM-200"


def test_commit_import_persists_source_fields_and_continues_on_failures(screenshot_file):
    payload = {
        "source_app": "盒马",
        "source_order_id": "HM-42",
        "purchase_date": "2026-04-02",
        "image_path": screenshot_file,
        "items": [
            {
                "name": "苹果",
                "quantity": 3,
                "unit": "个",
                "category": "食品",
                "purchase_date": "2026-04-02",
                "expiry_date": None,
                "confidence": 0.9,
                "warnings": [],
                "selected": True,
            },
            {
                "name": "",
                "quantity": 1,
                "unit": "件",
                "category": "食品",
                "purchase_date": "2026-04-02",
                "expiry_date": None,
                "confidence": 0.1,
                "warnings": [],
                "selected": True,
            },
            {
                "name": "酸奶",
                "quantity": 2,
                "unit": "瓶",
                "category": "食品",
                "purchase_date": "2026-04-02",
                "expiry_date": None,
                "confidence": 0.6,
                "warnings": [],
                "selected": False,
            },
        ],
    }

    result = order_import_service.commit_import(payload)

    assert result["created_count"] == 1
    assert result["skipped_count"] == 1
    assert len(result["failed_rows"]) == 1
    assert result["failed_rows"][0]["row"] == 2

    with db_service.session_scope() as session:
        stored = session.query(Item).filter(Item.name == "苹果").one()
        assert stored.quantity == 3
        assert stored.source_app == "盒马"
        assert stored.source_order_id == "HM-42"
        assert stored.image_path == screenshot_file


def test_commit_import_uses_edited_values(screenshot_file):
    payload = {
        "source_app": "美团买菜",
        "source_order_id": "MT-100",
        "purchase_date": "2026-04-03",
        "image_path": screenshot_file,
        "items": [
            {
                "name": "鸡蛋",
                "quantity": 5,
                "unit": "枚",
                "category": "食品",
                "purchase_date": "2026-04-03",
                "expiry_date": "2026-04-10",
                "confidence": 0.75,
                "warnings": [],
                "selected": True,
            }
        ],
    }

    result = order_import_service.commit_import(payload)

    assert result["created_count"] == 1
    with db_service.session_scope() as session:
        stored = session.query(Item).filter(Item.name == "鸡蛋").one()
        assert stored.quantity == 5
        assert stored.unit == "枚"
        assert stored.source_app == "美团买菜"
