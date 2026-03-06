#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据库迁移：为 ItemWiki 添加 icon 列
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.database import db_service
import sqlite3


def migrate_add_icon_column():
    """为 item_wikis 表添加 icon 列"""
    db_path = "data/vibe_fridge.db"

    print("开始迁移：添加 icon 列到 item_wikis 表...")

    # 使用 sqlite3 直接执行 SQL
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    # 检查列是否已存在
    cursor.execute("PRAGMA table_info(item_wikis)")
    columns = {row[1]: row for row in cursor.fetchall()}

    if 'icon' in columns:
        print("  icon 列已存在，跳过")
    else:
        print("  添加 icon 列...")
        cursor.execute("ALTER TABLE item_wikis ADD COLUMN icon VARCHAR(50)")
        print("  icon 列添加成功")

    conn.commit()
    conn.close()

    print("迁移完成！")


if __name__ == '__main__':
    migrate_add_icon_column()
