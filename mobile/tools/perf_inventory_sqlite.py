#!/usr/bin/env python3
"""SQLite performance smoke check for inventory dashboard and catalog queries.

This script mirrors the core SQL shapes used by InventoryRepository for the
home dashboard, today-action reminders, and item catalog search. It is useful
when the Flutter SDK is unavailable locally, and it complements the Dart
repository test in mobile/test/inventory_repository_test.dart.
"""

from __future__ import annotations

import argparse
import sqlite3
import statistics
import time
from datetime import datetime, timedelta
from pathlib import Path


ACTIVE = "active"
CONSUMED = "consumed"
IGNORED = "ignored"
SNOOZED = "snoozed"


def date_text(value: datetime) -> str:
    return datetime(value.year, value.month, value.day).isoformat()


def create_schema(conn: sqlite3.Connection) -> None:
    conn.executescript(
        """
        PRAGMA foreign_keys = ON;

        CREATE TABLE item_wiki_categories (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL UNIQUE,
          icon TEXT,
          color TEXT,
          sort_order INTEGER NOT NULL DEFAULT 0,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );

        CREATE TABLE item_wikis (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          icon TEXT,
          description TEXT,
          category_id TEXT REFERENCES item_wiki_categories(id) ON DELETE SET NULL,
          default_unit TEXT,
          suggested_expiry_days INTEGER,
          storage_location TEXT,
          default_reminder_days INTEGER NOT NULL DEFAULT 3,
          notes TEXT,
          image_path TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );

        CREATE TABLE items (
          id TEXT PRIMARY KEY,
          wiki_id TEXT NOT NULL REFERENCES item_wikis(id) ON DELETE CASCADE,
          name TEXT NOT NULL,
          description TEXT,
          quantity INTEGER NOT NULL DEFAULT 1,
          unit TEXT,
          purchase_date TEXT,
          expiry_date TEXT,
          reminder_date TEXT,
          status TEXT NOT NULL DEFAULT 'active',
          is_reminder_enabled INTEGER NOT NULL DEFAULT 1,
          reminder_days_before INTEGER NOT NULL DEFAULT 3,
          consumed_at TEXT,
          predicted_expiry_date TEXT,
          prediction_confidence REAL,
          recognition_confidence REAL,
          image_path TEXT,
          storage_location TEXT,
          source_app TEXT,
          source_order_id TEXT,
          import_batch_id TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );

        CREATE TABLE tags (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL UNIQUE,
          color TEXT,
          created_at TEXT NOT NULL
        );

        CREATE TABLE item_tags (
          item_id TEXT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
          tag_id TEXT NOT NULL REFERENCES tags(id) ON DELETE CASCADE,
          created_at TEXT NOT NULL,
          PRIMARY KEY (item_id, tag_id)
        );

        CREATE TABLE reminder_logs (
          id TEXT PRIMARY KEY,
          item_id TEXT NOT NULL REFERENCES items(id) ON DELETE CASCADE,
          reminder_type TEXT NOT NULL,
          message TEXT NOT NULL,
          sent_at TEXT NOT NULL,
          is_success INTEGER NOT NULL DEFAULT 1,
          error_message TEXT
        );

        CREATE TABLE shopping_list_items (
          id TEXT PRIMARY KEY,
          name TEXT NOT NULL,
          category_id TEXT REFERENCES item_wiki_categories(id) ON DELETE SET NULL,
          source_wiki_id TEXT REFERENCES item_wikis(id) ON DELETE SET NULL,
          source_item_id TEXT REFERENCES items(id) ON DELETE SET NULL,
          quantity INTEGER NOT NULL DEFAULT 1,
          unit TEXT,
          note TEXT,
          source TEXT NOT NULL DEFAULT 'manual',
          is_checked INTEGER NOT NULL DEFAULT 0,
          checked_at TEXT,
          converted_at TEXT,
          created_at TEXT NOT NULL,
          updated_at TEXT NOT NULL
        );

        CREATE INDEX idx_item_wikis_name ON item_wikis(lower(name));
        CREATE INDEX idx_item_wikis_category ON item_wikis(category_id);
        CREATE INDEX idx_items_wiki ON items(wiki_id);
        CREATE INDEX idx_items_status ON items(status);
        CREATE INDEX idx_items_expiry ON items(expiry_date);
        CREATE INDEX idx_items_reminder ON items(reminder_date);
        CREATE INDEX idx_items_import_batch ON items(import_batch_id);
        CREATE INDEX idx_shopping_list_category ON shopping_list_items(category_id);
        CREATE INDEX idx_shopping_list_open ON shopping_list_items(converted_at, is_checked);
        CREATE INDEX idx_shopping_list_source_wiki ON shopping_list_items(source_wiki_id);
        CREATE INDEX idx_items_status_expiry ON items(status, expiry_date);
        CREATE INDEX idx_items_status_reminder
          ON items(status, is_reminder_enabled, reminder_date);
        CREATE INDEX idx_items_wiki_status ON items(wiki_id, status);
        CREATE INDEX idx_reminder_logs_item_type_sent
          ON reminder_logs(item_id, reminder_type, sent_at);
        CREATE INDEX idx_item_wikis_category_name
          ON item_wikis(category_id, lower(name));
        """
    )


def seed(conn: sqlite3.Connection, count: int) -> None:
    now = datetime.now()
    now_text = now.isoformat()
    today = datetime(now.year, now.month, now.day)
    categories = [
        ("cat-food", "食品", 1),
        ("cat-daily", "日用品", 2),
        ("cat-medicine", "药品", 3),
        ("cat-other", "其他", 4),
    ]
    conn.executemany(
        """
        INSERT INTO item_wiki_categories
          (id, name, icon, color, sort_order, created_at, updated_at)
        VALUES (?, ?, 'category', '#1B8B7A', ?, ?, ?)
        """,
        [(cat_id, name, order, now_text, now_text) for cat_id, name, order in categories],
    )
    wiki_rows = []
    item_rows = []
    reminder_rows = []
    for index in range(count):
        category_id = categories[index % len(categories)][0]
        wiki_id = f"perf-wiki-{index}"
        item_id = f"perf-item-{index}"
        name = f"性能测试苹果{index:04d}"
        expiry_date = today + timedelta(days=index % 21 - 5)
        reminder_date = expiry_date - timedelta(days=3)
        wiki_rows.append(
            (
                wiki_id,
                name,
                "inventory_2",
                "性能测试数据",
                category_id,
                "个",
                14,
                "冷藏",
                3,
                None,
                None,
                now_text,
                now_text,
            )
        )
        item_rows.append(
            (
                item_id,
                wiki_id,
                name,
                None,
                index % 5 + 1,
                "个",
                date_text(today - timedelta(days=2)),
                date_text(expiry_date),
                date_text(reminder_date),
                ACTIVE if index % 12 else CONSUMED,
                1,
                3,
                now_text if index % 12 == 0 else None,
                None,
                None,
                None,
                None,
                "冷藏",
                None,
                None,
                None,
                now_text,
                now_text,
            )
        )
        if index % 10 == 0:
            reminder_rows.append(
                (
                    f"perf-reminder-{index}",
                    item_id,
                    IGNORED,
                    "性能测试忽略",
                    (today + timedelta(hours=8)).isoformat(),
                    1,
                    None,
                )
            )
    conn.executemany(
        """
        INSERT INTO item_wikis
          (id, name, icon, description, category_id, default_unit,
           suggested_expiry_days, storage_location, default_reminder_days,
           notes, image_path, created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        wiki_rows,
    )
    conn.executemany(
        """
        INSERT INTO items
          (id, wiki_id, name, description, quantity, unit, purchase_date,
           expiry_date, reminder_date, status, is_reminder_enabled,
           reminder_days_before, consumed_at, predicted_expiry_date,
           prediction_confidence, recognition_confidence, image_path,
           storage_location, source_app, source_order_id, import_batch_id,
           created_at, updated_at)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        item_rows,
    )
    conn.executemany(
        """
        INSERT INTO reminder_logs
          (id, item_id, reminder_type, message, sent_at, is_success, error_message)
        VALUES (?, ?, ?, ?, ?, ?, ?)
        """,
        reminder_rows,
    )
    conn.commit()


def timed(conn: sqlite3.Connection, sql: str, args: tuple[object, ...], loops: int) -> tuple[float, int]:
    durations = []
    rows_count = 0
    for _ in range(loops):
        start = time.perf_counter()
        rows = conn.execute(sql, args).fetchall()
        durations.append((time.perf_counter() - start) * 1000)
        rows_count = len(rows)
    return statistics.median(durations), rows_count


REGISTERED_SQL = """
SELECT
  w.id AS wiki_id,
  w.name,
  w.icon,
  w.description,
  w.category_id,
  w.default_unit,
  w.storage_location,
  c.name AS category_name,
  COUNT(i.id) AS active_batch_count,
  COALESCE(SUM(i.quantity), 0) AS total_quantity,
  MIN(i.expiry_date) AS next_expiry_date
FROM item_wikis w
LEFT JOIN item_wiki_categories c ON c.id = w.category_id
LEFT JOIN items i ON i.wiki_id = w.id AND i.status = ?
WHERE (w.name LIKE ? OR w.description LIKE ?)
GROUP BY w.id
ORDER BY w.name COLLATE NOCASE ASC
"""

CATEGORY_SQL = """
SELECT
  w.id AS wiki_id,
  w.name,
  c.name AS category_name,
  COUNT(i.id) AS active_batch_count,
  COALESCE(SUM(i.quantity), 0) AS total_quantity,
  MIN(i.expiry_date) AS next_expiry_date
FROM item_wikis w
LEFT JOIN item_wiki_categories c ON c.id = w.category_id
LEFT JOIN items i ON i.wiki_id = w.id AND i.status = ?
WHERE w.category_id = ?
GROUP BY w.id
ORDER BY w.name COLLATE NOCASE ASC
"""

TODAY_ACTION_SQL = """
SELECT i.id, i.name, i.expiry_date, i.reminder_date
FROM items i
LEFT JOIN item_wikis w ON w.id = i.wiki_id
LEFT JOIN item_wiki_categories c ON c.id = w.category_id
WHERE i.status = ?
  AND (
    (i.expiry_date IS NOT NULL AND i.expiry_date <= ?)
    OR (
      i.is_reminder_enabled = 1
      AND i.reminder_date IS NOT NULL
      AND i.reminder_date <= ?
    )
  )
  AND NOT EXISTS (
    SELECT 1
    FROM reminder_logs rl
    WHERE rl.item_id = i.id
      AND rl.reminder_type IN (?, ?)
      AND rl.sent_at >= ?
      AND rl.sent_at < ?
  )
ORDER BY
  CASE
    WHEN i.expiry_date IS NOT NULL AND i.expiry_date < ? THEN 0
    WHEN i.expiry_date IS NOT NULL AND i.expiry_date = ? THEN 1
    ELSE 2
  END,
  i.expiry_date IS NULL ASC,
  i.expiry_date ASC,
  i.reminder_date ASC,
  i.created_at DESC
LIMIT ?
"""

STATS_QUERIES = [
    (
        "active totals",
        "SELECT COUNT(*) AS active_batch_count, COALESCE(SUM(quantity), 0) AS total_quantity FROM items WHERE status = ?",
    ),
    (
        "wiki count",
        "SELECT COUNT(*) FROM item_wikis",
    ),
    (
        "category counts",
        """
        SELECT c.name AS category_name, COALESCE(SUM(i.quantity), 0) AS total_count
        FROM item_wiki_categories c
        LEFT JOIN item_wikis w ON w.category_id = c.id
        LEFT JOIN items i ON i.wiki_id = w.id AND i.status = ?
        GROUP BY c.id
        HAVING total_count > 0
        ORDER BY c.sort_order ASC
        """,
    ),
]


def run(args: argparse.Namespace) -> int:
    db_path = args.database
    if db_path.exists():
        db_path.unlink()
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    create_schema(conn)
    seed(conn, args.items)

    today = datetime.now()
    today = datetime(today.year, today.month, today.day)
    tomorrow = today + timedelta(days=1)
    checks = []
    checks.append(
        (
            "catalog exact search",
            *timed(conn, REGISTERED_SQL, (ACTIVE, "%性能测试苹果1499%", "%性能测试苹果1499%"), args.loops),
            args.search_threshold_ms,
        )
    )
    checks.append(
        (
            "catalog category filter",
            *timed(conn, CATEGORY_SQL, (ACTIVE, "cat-food"), args.loops),
            args.category_threshold_ms,
        )
    )
    checks.append(
        (
            "today action items",
            *timed(
                conn,
                TODAY_ACTION_SQL,
                (
                    ACTIVE,
                    today.isoformat(),
                    today.isoformat(),
                    IGNORED,
                    SNOOZED,
                    today.isoformat(),
                    tomorrow.isoformat(),
                    today.isoformat(),
                    today.isoformat(),
                    20,
                ),
                args.loops,
            ),
            args.today_threshold_ms,
        )
    )
    for label, sql in STATS_QUERIES:
        query_args = (ACTIVE,) if "?" in sql else ()
        checks.append(
            (
                f"stats {label}",
                *timed(conn, sql, query_args, args.loops),
                args.stats_threshold_ms,
            )
        )

    failed = []
    for label, median_ms, rows_count, threshold in checks:
        status = "PASS" if median_ms <= threshold else "FAIL"
        print(f"{status:4} {label:24} {median_ms:8.3f} ms rows={rows_count} threshold={threshold:g} ms")
        if median_ms > threshold:
            failed.append(label)
    conn.close()
    if failed:
        print("Failed checks:", ", ".join(failed))
        return 1
    return 0


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--items", type=int, default=5000)
    parser.add_argument("--loops", type=int, default=10)
    parser.add_argument(
        "--database",
        type=Path,
        default=Path("/tmp/vibe-fridge-perf.sqlite3"),
    )
    parser.add_argument("--search-threshold-ms", type=float, default=50)
    parser.add_argument("--category-threshold-ms", type=float, default=120)
    parser.add_argument("--today-threshold-ms", type=float, default=80)
    parser.add_argument("--stats-threshold-ms", type=float, default=80)
    return run(parser.parse_args())


if __name__ == "__main__":
    raise SystemExit(main())
