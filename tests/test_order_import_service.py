# -*- coding: utf-8 -*-
"""Order import service tests."""

import json
import os
from datetime import date, datetime, timedelta
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.models.item import Item
from app.services.database import db_service, init_database
from app.services.order_import_service import (
    LEGACY_SILICONFLOW_API_KEY_ENV,
    LEGACY_SILICONFLOW_MODEL_ENV,
    SILICONFLOW_API_KEY_ENV,
    SILICONFLOW_API_KEY_SETTING,
    SILICONFLOW_MODEL_ENV,
    SILICONFLOW_MODEL_SETTING,
    order_import_service,
)
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
    monkeypatch.setenv(SILICONFLOW_API_KEY_ENV, "test-key")
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


def test_normalize_review_item_links_exact_wiki_defaults():
    category = wiki_service.create_category(name="日用品", icon="home", sort_order=10)
    wiki_service.create_wiki(
        name="水果刀",
        category_id=category.id,
        default_unit="把",
        suggested_expiry_days=365,
    )

    normalized = order_import_service.normalize_review_item(
        {
            "name": "水果刀",
            "quantity": 1,
            "unit": "",
            "category": "食品",
            "purchase_date": "2026-04-01",
            "expiry_date": None,
            "confidence": 0.88,
            "warnings": [],
        },
        default_purchase_date=None,
    )

    assert normalized["wiki_name"] == "水果刀"
    assert normalized["unit"] == "把"
    assert normalized["category"] == "日用品"
    assert normalized["expiry_date"] == (
        date(2026, 4, 1) + timedelta(days=365)
    ).isoformat()
    assert normalized["expiry_date_source"] == "wiki_estimate"
    assert any("物品 Wiki" in warning for warning in normalized["warnings"])


def test_normalize_review_item_groups_product_name_to_wiki_class():
    category = wiki_service.create_category(name="食品", icon="food-apple", sort_order=1)
    wiki_service.create_wiki(
        name="香蕉",
        category_id=category.id,
        default_unit="根",
        suggested_expiry_days=3,
    )

    normalized = order_import_service.normalize_review_item(
        {
            "name": "进口香蕉 700g/份",
            "quantity": 1,
            "unit": "",
            "category": "食品",
            "purchase_date": "2026-04-27",
            "expiry_date": None,
            "confidence": 0.91,
            "warnings": [],
        },
        default_purchase_date=None,
    )

    assert normalized["name"] == "进口香蕉 700g/份"
    assert normalized["wiki_name"] == "香蕉"
    assert normalized["wiki_match_type"] == "contains"
    assert normalized["unit"] == "根"
    assert normalized["expiry_date"] == "2026-04-30"
    assert any("归并到物品 Wiki「香蕉」" in warning for warning in normalized["warnings"])


def test_normalize_review_item_matches_common_alias_to_wiki_class():
    category = wiki_service.create_category(name="食品", icon="food-apple", sort_order=1)
    wiki_service.create_wiki(
        name="香蕉",
        category_id=category.id,
        default_unit="根",
        suggested_expiry_days=3,
    )

    normalized = order_import_service.normalize_review_item(
        {
            "name": "DOLE 进口甜蕉 700g/份",
            "quantity": 1,
            "unit": "份",
            "category": "食品",
            "purchase_date": "2026-04-27",
            "expiry_date": None,
            "confidence": 0.91,
            "warnings": [],
        },
        default_purchase_date=None,
    )

    assert normalized["wiki_name"] == "香蕉"
    assert normalized["wiki_match_type"] == "alias"
    assert normalized["unit"] == "份"
    assert normalized["expiry_date"] == "2026-04-30"


def test_wiki_match_avoids_category_conflicting_generic_substring():
    category = wiki_service.create_category(name="食品", icon="food-apple", sort_order=1)
    wiki_service.create_wiki(
        name="水果",
        category_id=category.id,
        default_unit="个",
        suggested_expiry_days=7,
    )

    normalized = order_import_service.normalize_review_item(
        {
            "name": "水果刀",
            "quantity": 1,
            "unit": "把",
            "category": "日用品",
            "purchase_date": "2026-04-27",
            "expiry_date": None,
            "confidence": 0.91,
            "warnings": [],
        },
        default_purchase_date=None,
    )

    assert normalized["wiki_name"] is None
    assert normalized["category"] == "日用品"


def test_parse_order_screenshot_uses_order_time_for_fuzzy_expiry(
    monkeypatch, screenshot_file
):
    monkeypatch.setenv(SILICONFLOW_API_KEY_ENV, "test-key")
    model_json = {
        "source_app": "盒马",
        "source_order_id": None,
        "purchase_date": None,
        "order_time": "2026-04-27 23:12",
        "items": [
            {
                "name": "盒马烘焙 0酱溏心蛋三明治 170g",
                "quantity": 1,
                "unit": "盒",
                "category": "食品",
                "purchase_date": None,
                "expiry_date": None,
                "confidence": 0.9,
                "warnings": [],
            },
            {
                "name": "HM 盒马中号生物降解购物袋-HC",
                "quantity": 1,
                "unit": "个",
                "category": "日用品",
                "purchase_date": None,
                "expiry_date": None,
                "confidence": 0.9,
                "warnings": [],
            },
        ],
    }
    monkeypatch.setattr(
        "app.services.order_import_service.requests.post",
        lambda *args, **kwargs: FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(model_json, ensure_ascii=False)
                        }
                    }
                ]
            }
        ),
    )

    parsed = order_import_service.parse_order_screenshot(screenshot_file)

    assert parsed["purchase_date"] == "2026-04-27"
    assert parsed["order_time"] == "2026-04-27 23:12"
    assert parsed["order_time_source"] == "model"
    sandwich = parsed["items"][0]
    assert sandwich["purchase_date"] == "2026-04-27"
    assert sandwich["purchase_date_source"] == "default"
    assert sandwich["expiry_date"] == "2026-04-28"
    assert sandwich["expiry_date_source"] == "fuzzy_estimate"
    assert any("模糊估计过期日期" in warning for warning in sandwich["warnings"])
    assert parsed["items"][1]["expiry_date"] is None


def test_parse_order_screenshot_falls_back_to_image_mtime_for_missing_order_time(
    monkeypatch, screenshot_file
):
    monkeypatch.setenv(SILICONFLOW_API_KEY_ENV, "test-key")
    image_mtime = datetime(2026, 4, 27, 23, 12).timestamp()
    os.utime(screenshot_file, (image_mtime, image_mtime))
    model_json = {
        "source_app": "盒马",
        "source_order_id": None,
        "purchase_date": None,
        "order_time": None,
        "items": [
            {
                "name": "DOLE 进口甜蕉 700g/份",
                "quantity": 1,
                "unit": "份",
                "category": "食品",
                "purchase_date": None,
                "expiry_date": None,
                "confidence": 0.95,
                "warnings": [],
            }
        ],
    }
    monkeypatch.setattr(
        "app.services.order_import_service.requests.post",
        lambda *args, **kwargs: FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(model_json, ensure_ascii=False)
                        }
                    }
                ]
            }
        ),
    )

    parsed = order_import_service.parse_order_screenshot(screenshot_file)

    assert parsed["purchase_date"] == "2026-04-27"
    assert parsed["order_time"] == "2026-04-27 23:12"
    assert parsed["order_time_source"] == "image_file_mtime"
    assert parsed["items"][0]["expiry_date"] == "2026-04-30"
    assert parsed["items"][0]["expiry_date_source"] == "fuzzy_estimate"


def test_parse_order_screenshot_treats_status_bar_like_time_as_image_mtime(
    monkeypatch, screenshot_file
):
    monkeypatch.setenv(SILICONFLOW_API_KEY_ENV, "test-key")
    image_mtime = datetime(2026, 4, 27, 23, 12).timestamp()
    os.utime(screenshot_file, (image_mtime, image_mtime))
    model_json = {
        "source_app": "盒马",
        "source_order_id": None,
        "purchase_date": None,
        "order_time": "2026-04-27 23:12",
        "items": [
            {
                "name": "盒马烘焙 0酱溏心蛋三明治 170g",
                "quantity": 1,
                "unit": "盒",
                "category": "食品",
                "purchase_date": None,
                "expiry_date": None,
                "confidence": 0.9,
                "warnings": [],
            }
        ],
    }
    monkeypatch.setattr(
        "app.services.order_import_service.requests.post",
        lambda *args, **kwargs: FakeResponse(
            {
                "choices": [
                    {
                        "message": {
                            "content": json.dumps(model_json, ensure_ascii=False)
                        }
                    }
                ]
            }
        ),
    )

    parsed = order_import_service.parse_order_screenshot(screenshot_file)

    assert parsed["order_time"] == "2026-04-27 23:12"
    assert parsed["order_time_source"] == "image_file_mtime"
    assert parsed["items"][0]["expiry_date"] == "2026-04-28"


def test_prompt_excludes_phone_status_bar_time():
    prompt = order_import_service._build_user_prompt()

    assert "不要把手机状态栏时间" in prompt
    assert "如果订单正文没有明确下单时间，请填 null" in prompt


def test_media_timestamp_parser_accepts_android_milliseconds():
    expected = datetime(2026, 4, 27, 23, 12)
    timestamp_ms = int(expected.timestamp() * 1000)

    parsed = order_import_service._datetime_from_media_timestamp(timestamp_ms)

    assert parsed == expected


def test_parse_order_screenshot_requires_api_key(screenshot_file, monkeypatch):
    monkeypatch.delenv(SILICONFLOW_API_KEY_ENV, raising=False)
    monkeypatch.delenv(LEGACY_SILICONFLOW_API_KEY_ENV, raising=False)

    with pytest.raises(RuntimeError, match="未配置 API Key"):
        order_import_service.parse_order_screenshot(screenshot_file)


def test_parse_order_screenshot_rejects_invalid_json(monkeypatch, screenshot_file):
    monkeypatch.setenv(SILICONFLOW_API_KEY_ENV, "test-key")
    monkeypatch.setattr(
        "app.services.order_import_service.requests.post",
        lambda *args, **kwargs: FakeResponse(
            {"choices": [{"message": {"content": "not-json-response"}}]}
        ),
    )

    with pytest.raises(RuntimeError, match="JSON"):
        order_import_service.parse_order_screenshot(screenshot_file)


def test_parse_order_screenshot_uses_saved_model_config(monkeypatch, screenshot_file):
    monkeypatch.setenv(SILICONFLOW_API_KEY_ENV, "test-key")
    monkeypatch.delenv(SILICONFLOW_MODEL_ENV, raising=False)
    monkeypatch.delenv(LEGACY_SILICONFLOW_MODEL_ENV, raising=False)
    assert db_service.set_setting(
        SILICONFLOW_MODEL_SETTING, "zai-org/GLM-4.1V-9B-Thinking"
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
    monkeypatch.delenv(SILICONFLOW_API_KEY_ENV, raising=False)
    monkeypatch.delenv(LEGACY_SILICONFLOW_API_KEY_ENV, raising=False)
    assert db_service.set_setting(SILICONFLOW_API_KEY_SETTING, "app-saved-key")

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
        "order_time": "2026-04-02 20:30",
        "order_time_source": "manual",
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
    assert len(result["created_rows"]) == 1
    assert result["created_rows"][0]["row"] == 1
    assert result["created_rows"][0]["name"] == "苹果"

    with db_service.session_scope() as session:
        stored = session.query(Item).filter(Item.name == "苹果").one()
        assert stored.quantity == 3
        assert stored.source_app == "盒马"
        assert stored.source_order_id == "HM-42"
        assert stored.source_order_time == datetime(2026, 4, 2, 20, 30)
        assert stored.source_order_time_source == "manual"
        assert stored.image_path == screenshot_file
        assert stored.predicted_expiry_date == date(2026, 4, 9)
        assert stored.prediction_confidence == 0.9
        assert result["created_rows"][0]["item_id"] == stored.id


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
    assert result["created_rows"][0]["row"] == 1
    with db_service.session_scope() as session:
        stored = session.query(Item).filter(Item.name == "鸡蛋").one()
        assert stored.quantity == 5
        assert stored.unit == "枚"
        assert stored.source_app == "美团买菜"
        assert stored.predicted_expiry_date == date(2026, 4, 10)
        assert stored.prediction_confidence == 0.75


def test_commit_import_uses_matched_wiki_class_as_inventory_name(screenshot_file):
    category = wiki_service.create_category(name="食品", icon="food-apple", sort_order=1)
    wiki_service.create_wiki(
        name="香蕉",
        category_id=category.id,
        default_unit="根",
        suggested_expiry_days=3,
    )
    payload = {
        "source_app": "盒马",
        "source_order_id": "HM-301",
        "purchase_date": "2026-04-27",
        "image_path": screenshot_file,
        "items": [
            {
                "name": "进口香蕉 700g/份",
                "quantity": 1,
                "unit": "",
                "category": "食品",
                "purchase_date": "2026-04-27",
                "expiry_date": None,
                "confidence": 0.91,
                "warnings": [],
                "selected": True,
            }
        ],
    }

    result = order_import_service.commit_import(payload)

    assert result["created_rows"][0]["name"] == "香蕉"
    with db_service.session_scope() as session:
        stored = session.query(Item).filter(Item.name == "香蕉").one()
        assert stored.unit == "根"
        assert stored.expiry_date == date(2026, 4, 30)


def test_commit_import_does_not_invent_source_order_time(screenshot_file):
    image_mtime = datetime(2026, 4, 27, 23, 12).timestamp()
    os.utime(screenshot_file, (image_mtime, image_mtime))
    payload = {
        "source_app": "盒马",
        "source_order_id": "HM-300",
        "purchase_date": "2026-04-03",
        "image_path": screenshot_file,
        "items": [
            {
                "name": "牛奶",
                "quantity": 1,
                "unit": "盒",
                "category": "食品",
                "purchase_date": "2026-04-03",
                "expiry_date": "2026-04-10",
                "confidence": 0.8,
                "warnings": [],
                "selected": True,
            }
        ],
    }

    order_import_service.commit_import(payload)

    with db_service.session_scope() as session:
        stored = session.query(Item).filter(Item.name == "牛奶").one()
        assert stored.purchase_date == date(2026, 4, 3)
        assert stored.source_order_time is None


def test_commit_import_persists_confirmed_screenshot_time_estimate(screenshot_file):
    payload = {
        "source_app": "盒马",
        "source_order_id": None,
        "purchase_date": "2026-04-27",
        "order_time": "2026-04-27 23:12",
        "order_time_source": "image_file_mtime",
        "image_path": screenshot_file,
        "items": [
            {
                "name": "甜蕉",
                "quantity": 1,
                "unit": "份",
                "category": "食品",
                "purchase_date": "2026-04-27",
                "expiry_date": "2026-04-30",
                "confidence": 0.95,
                "warnings": [],
                "selected": True,
            }
        ],
    }

    order_import_service.commit_import(payload)

    with db_service.session_scope() as session:
        stored = session.query(Item).filter(Item.name == "甜蕉").one()
        assert stored.source_order_time == datetime(2026, 4, 27, 23, 12)
        assert stored.source_order_time_source == "image_file_mtime"
