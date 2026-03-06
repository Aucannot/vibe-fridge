#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
迁移脚本：为没有 wiki_id 的 Item 创建 ItemWiki 并关联
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.database import db_service, init_database
from app.services.wiki_service import wiki_service
from app.models.item import Item, ItemStatus
from app.models.item_wiki import ItemWiki


def migrate_items_to_wiki():
    """迁移没有 wiki_id 的 Item 到 ItemWiki"""
    print("开始迁移 Item 到 ItemWiki...")

    with db_service.session_scope() as session:
        # 查找所有 wiki_id 为 None 的 Item
        items_without_wiki = session.query(Item).filter(
            Item.wiki_id.is_(None)
        ).all()

        print(f"找到 {len(items_without_wiki)} 个需要迁移的 Item")

        # 按名称分组，去重
        unique_names = {}
        for item in items_without_wiki:
            if item.name not in unique_names:
                unique_names[item.name] = []
            unique_names[item.name].append(item)

        print(f"需要创建 {len(unique_names)} 个 ItemWiki")

        # 为每个唯一名称创建一个 ItemWiki
        migrated_count = 0
        for name, items in unique_names.items():
            # 检查是否已存在同名 ItemWiki
            existing_wiki = session.query(ItemWiki).filter(
                ItemWiki.name == name
            ).first()

            if existing_wiki:
                print(f"  ItemWiki 已存在: {name}，关联现有...")
                wiki_id = existing_wiki.id
            else:
                # 创建新的 ItemWiki
                wiki = ItemWiki(
                    name=name,
                    default_unit=items[0].unit if items[0].unit else None,
                    description=f"{name}的Wiki条目"
                )
                session.add(wiki)
                session.flush()
                wiki_id = wiki.id
                print(f"  创建 ItemWiki: {name} (ID: {wiki_id})")

            # 关联所有同名的 Item 到这个 Wiki
            for item in items:
                item.wiki_id = wiki_id
                migrated_count += 1

        print(f"\n迁移完成！")
        print(f"  创建/关联的 Item: {migrated_count}")
        print(f"  涉及的唯一物品名称: {len(unique_names)}")


def cleanup_duplicates():
    """
    清理重复的 Item：同一 wiki_id 下的同状态 Item 保留数量最多的一个，其他的标记为已消耗
    """
    print("\n开始清理重复的 Item...")

    with db_service.session_scope() as session:
        # 查找所有已关联 wiki 的 Item
        items_with_wiki = session.query(Item).filter(
            Item.wiki_id.isnot(None)
        ).all()

        # 按 wiki_id 分组
        wiki_groups = {}
        for item in items_with_wiki:
            if item.wiki_id not in wiki_groups:
                wiki_groups[item.wiki_id] = []
            wiki_groups[item.wiki_id].append(item)

        deleted_count = 0
        for wiki_id, items in wiki_groups.items():
            active_items = [i for i in items if i.status == ItemStatus.ACTIVE]
            if len(active_items) > 1:
                # 保留数量最多的，其他的标记为已消耗
                active_items.sort(key=lambda x: x.quantity, reverse=True)
                keep_item = active_items[0]
                consumed_items = active_items[1:]
                for item in consumed_items:
                    item.status = ItemStatus.CONSUMED
                    deleted_count += 1
                name = keep_item.name
                print(f"  {name}: 保留 x{keep_item.quantity}，消耗了 {len(consumed_items)} 条记录")

        print(f"\n清理完成！标记了 {deleted_count} 条重复记录为已消耗")


if __name__ == '__main__':
    init_database()
    migrate_items_to_wiki()
    cleanup_duplicates()
    print("\n所有迁移操作已完成！")
