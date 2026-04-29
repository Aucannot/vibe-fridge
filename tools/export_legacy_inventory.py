#!/usr/bin/env python3
"""Export the legacy Kivy/SQLAlchemy SQLite database for Flutter import."""

from __future__ import annotations

import argparse
import json
import sqlite3
import uuid
from pathlib import Path
from typing import Any


STATUS_MAP = {
    "ACTIVE": "active",
    "EXPIRED": "expired",
    "CONSUMED": "consumed",
    "WASTED": "wasted",
    "active": "active",
    "expired": "expired",
    "consumed": "consumed",
    "wasted": "wasted",
}


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Export legacy vibe-fridge SQLite data to Flutter JSON format.",
    )
    parser.add_argument(
        "--source",
        default="data/vibe_fridge.db",
        help="Path to the legacy SQLite database.",
    )
    parser.add_argument(
        "--output",
        default="mobile/assets/import/legacy_inventory.local.json",
        help="Path to write the JSON export.",
    )
    args = parser.parse_args()

    source = Path(args.source)
    if not source.exists():
        raise SystemExit(f"Legacy database not found: {source}")

    payload = export_database(source)
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(payload, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(
        "Exported "
        f"{len(payload['categories'])} categories, "
        f"{len(payload['wikis'])} wikis, "
        f"{len(payload['items'])} items, "
        f"{len(payload['tags'])} tags to {output}"
    )


def export_database(path: Path) -> dict[str, Any]:
    connection = sqlite3.connect(path)
    connection.row_factory = sqlite3.Row
    try:
        tables = set(_table_names(connection))
        categories = _rows(connection, "item_wiki_categories") if "item_wiki_categories" in tables else []
        wikis = _rows(connection, "item_wikis") if "item_wikis" in tables else []
        items = _rows(connection, "items") if "items" in tables else []
        tags = _rows(connection, "tags") if "tags" in tables else []
        item_tags = _rows(connection, "item_tags") if "item_tags" in tables else []

        wiki_by_id = {row["id"]: dict(row) for row in wikis if row.get("id")}
        wiki_by_name = {
            str(row["name"]).strip().lower(): dict(row)
            for row in wikis
            if row.get("name")
        }

        normalized_items = []
        for item in items:
            row = dict(item)
            name = str(row.get("name") or "").strip()
            wiki_id = row.get("wiki_id")
            if not wiki_id or wiki_id not in wiki_by_id:
                key = name.lower()
                wiki = wiki_by_name.get(key)
                if wiki is None:
                    wiki_id = str(uuid.uuid5(uuid.NAMESPACE_URL, f"vibe-fridge:item-wiki:{key}"))
                    wiki = {
                        "id": wiki_id,
                        "name": name or "未命名物品",
                        "icon": None,
                        "description": row.get("description"),
                        "category_id": None,
                        "default_unit": row.get("unit"),
                        "suggested_expiry_days": None,
                        "storage_location": None,
                        "notes": None,
                        "image_path": row.get("image_path"),
                        "created_at": row.get("created_at"),
                        "updated_at": row.get("updated_at"),
                    }
                    wiki_by_id[wiki_id] = wiki
                    wiki_by_name[key] = wiki
                row["wiki_id"] = wiki["id"]
            row["status"] = STATUS_MAP.get(str(row.get("status")), "active")
            normalized_items.append(row)

        return {
            "format": "vibe-fridge-legacy-export",
            "version": 1,
            "categories": [_normalize_category(dict(row)) for row in categories],
            "wikis": [_normalize_wiki(dict(row)) for row in wiki_by_id.values()],
            "items": [_normalize_item(dict(row)) for row in normalized_items],
            "tags": [_normalize_tag(dict(row)) for row in tags],
            "item_tags": [_normalize_item_tag(dict(row)) for row in item_tags],
        }
    finally:
        connection.close()


def _table_names(connection: sqlite3.Connection) -> list[str]:
    rows = connection.execute("SELECT name FROM sqlite_master WHERE type = 'table'").fetchall()
    return [row["name"] for row in rows]


def _rows(connection: sqlite3.Connection, table: str) -> list[dict[str, Any]]:
    return [dict(row) for row in connection.execute(f"SELECT * FROM {table}").fetchall()]


def _normalize_category(row: dict[str, Any]) -> dict[str, Any]:
    return _pick(
        row,
        {
            "id": None,
            "name": "其他",
            "icon": None,
            "color": None,
            "sort_order": 0,
            "created_at": None,
            "updated_at": None,
        },
    )


def _normalize_wiki(row: dict[str, Any]) -> dict[str, Any]:
    return _pick(
        row,
        {
            "id": None,
            "name": "未命名物品",
            "icon": None,
            "description": None,
            "category_id": None,
            "default_unit": None,
            "suggested_expiry_days": None,
            "storage_location": None,
            "notes": None,
            "image_path": None,
            "created_at": None,
            "updated_at": None,
        },
    )


def _normalize_item(row: dict[str, Any]) -> dict[str, Any]:
    return _pick(
        row,
        {
            "id": None,
            "wiki_id": None,
            "name": "未命名物品",
            "description": None,
            "quantity": 1,
            "unit": None,
            "purchase_date": None,
            "expiry_date": None,
            "reminder_date": None,
            "status": "active",
            "is_reminder_enabled": 1,
            "consumed_at": None,
            "predicted_expiry_date": None,
            "prediction_confidence": None,
            "image_path": None,
            "source_app": None,
            "source_order_id": None,
            "created_at": None,
            "updated_at": None,
        },
    )


def _normalize_tag(row: dict[str, Any]) -> dict[str, Any]:
    return _pick(
        row,
        {
            "id": None,
            "name": "",
            "color": None,
            "created_at": None,
        },
    )


def _normalize_item_tag(row: dict[str, Any]) -> dict[str, Any]:
    return _pick(
        row,
        {
            "item_id": None,
            "tag_id": None,
            "created_at": None,
        },
    )


def _pick(row: dict[str, Any], defaults: dict[str, Any]) -> dict[str, Any]:
    return {key: row.get(key, default) for key, default in defaults.items()}


if __name__ == "__main__":
    main()
