#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
初始化 Wiki 数据：清理测试数据并创建常用物品条目
"""

import sys
from pathlib import Path

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.database import db_service, init_database
from app.services.wiki_service import wiki_service
from app.models.item_wiki import ItemWiki
from app.models.item import Item


def cleanup_test_items():
    """清理测试相关的 ItemWiki 和 Item"""
    print("清理测试物品...")

    test_keywords = ['测试', 'debug', 'get_item', '调试']
    to_delete = []

    with db_service.session_scope() as session:
        wikis = session.query(ItemWiki).all()
        for wiki in wikis:
            if any(kw in wiki.name.lower() for kw in test_keywords):
                to_delete.append(wiki.id)
                print(f"  标记删除: {wiki.name}")

        if not to_delete:
            print("  没有找到测试物品")
            return 0

        # 先删除关联的 Item
        deleted_items = session.query(Item).filter(
            Item.wiki_id.in_(to_delete)
        ).delete(synchronize_session=False)
        print(f"  删除了 {deleted_items} 条库存记录")

        # 再删除 ItemWiki
        deleted_wikis = session.query(ItemWiki).filter(
            ItemWiki.id.in_(to_delete)
        ).delete(synchronize_session=False)
        print(f"  删除了 {deleted_wikis} 个 Wiki 条目")

        return deleted_wikis + deleted_items


def get_category_id(category_name: str) -> str:
    """获取分类 ID"""
    categories = wiki_service.get_all_categories()
    for cat in categories:
        if cat.name == category_name:
            return cat.id
    return None


def populate_food_items():
    """创建常见食品物品"""
    print("\n创建食品物品...")

    food_items = [
        {"name": "鲜牛奶", "unit": "盒", "expiry_days": 7, "location": "冷藏", "desc": "巴氏杀菌鲜牛奶", "icon": "bottle-tonic"},
        {"name": "鸡蛋", "unit": "个", "expiry_days": 30, "location": "冷藏", "desc": "新鲜鸡蛋", "icon": "egg"},
        {"name": "面包", "unit": "袋", "expiry_days": 5, "location": "常温", "desc": "切片面包", "icon": "hamburger"},
        {"name": "酸奶", "unit": "杯", "expiry_days": 21, "location": "冷藏", "desc": "风味酸奶", "icon": "cup-water"},
        {"name": "苹果", "unit": "个", "expiry_days": 14, "location": "冷藏", "desc": "新鲜苹果", "icon": "food-apple"},
        {"name": "香蕉", "unit": "根", "expiry_days": 5, "location": "常温", "desc": "成熟香蕉", "icon": "fruit-cherries"},
        {"name": "橙子", "unit": "个", "expiry_days": 21, "location": "冷藏", "desc": "新鲜橙子", "icon": "orange"},
        {"name": "西红柿", "unit": "个", "expiry_days": 7, "location": "冷藏", "desc": "新鲜西红柿", "icon": "fruit-pineapple"},
        {"name": "黄瓜", "unit": "根", "expiry_days": 7, "location": "冷藏", "desc": "新鲜黄瓜", "icon": "vegetable"},
        {"name": "胡萝卜", "unit": "根", "expiry_days": 14, "location": "冷藏", "desc": "新鲜胡萝卜", "icon": "carrot"},
        {"name": "土豆", "unit": "个", "expiry_days": 30, "location": "常温", "desc": "新鲜土豆", "icon": "food-turkey"},
        {"name": "洋葱", "unit": "个", "expiry_days": 21, "location": "常温", "desc": "新鲜洋葱", "icon": "fruit-pear"},
        {"name": "青菜", "unit": "把", "expiry_days": 3, "location": "冷藏", "desc": "新鲜绿叶菜", "icon": "grass"},
        {"name": "猪肉", "unit": "kg", "expiry_days": 3, "location": "冷藏", "desc": "新鲜猪肉", "icon": "food-variant"},
        {"name": "鸡肉", "unit": "kg", "expiry_days": 2, "location": "冷藏", "desc": "新鲜鸡胸肉", "icon": "food-drumstick"},
        {"name": "大米", "unit": "袋", "expiry_days": 365, "location": "常温", "desc": "精米", "icon": "rice"},
        {"name": "食用油", "unit": "瓶", "expiry_days": 540, "location": "常温", "desc": "食用油", "icon": "bottle-t"},
        {"name": "豆腐", "unit": "块", "expiry_days": 2, "location": "冷藏", "desc": "新鲜豆腐", "icon": "food"},
        {"name": "火锅底料", "unit": "袋", "expiry_days": 365, "location": "常温", "desc": "火锅底料", "icon": "pot"},
        {"name": "可乐", "unit": "罐", "expiry_days": 365, "location": "常温", "desc": "罐装可乐", "icon": "bottle-soda"},
    ]

    count = 0
    food_category_id = get_category_id("食品")

    for item in food_items:
        existing = wiki_service.get_wiki_by_name(item["name"])
        if not existing:
            wiki_service.create_wiki(
                name=item["name"],
                description=item["desc"],
                default_unit=item["unit"],
                suggested_expiry_days=item["expiry_days"],
                storage_location=item["location"],
                icon=item.get("icon"),
                category_id=food_category_id
            )
            count += 1
            print(f"  创建: {item['name']}")
        else:
            # 更新现有 Wiki 的信息（包括图标）
            wiki_service.update_wiki(
                existing['id'],
                description=item["desc"],
                default_unit=item["unit"],
                suggested_expiry_days=item["expiry_days"],
                storage_location=item["location"],
                icon=item.get("icon"),
                category_id=food_category_id
            )
            print(f"  更新: {item['name']}")

    return count


def populate_daily_items():
    """创建日用品物品"""
    print("\n创建日用品物品...")

    daily_items = [
        {"name": "洗发水", "unit": "瓶", "expiry_days": 730, "location": "卫生间", "desc": "洗发用品", "icon": "brush"},
        {"name": "沐浴露", "unit": "瓶", "expiry_days": 730, "location": "卫生间", "desc": "沐浴用品", "icon": "shower"},
        {"name": "牙膏", "unit": "支", "expiry_days": 365, "location": "卫生间", "desc": "牙膏", "icon": "tooth"},
        {"name": "洗衣液", "unit": "瓶", "expiry_days": 730, "location": "阳台", "desc": "洗衣液", "icon": "washing-machine"},
        {"name": "卫生纸", "unit": "卷", "expiry_days": 1095, "location": "卫生间", "desc": "卷纸", "icon": "paper-roll"},
        {"name": "抽纸", "unit": "包", "expiry_days": 730, "location": "各处", "desc": "抽纸", "icon": "paper-roll"},
        {"name": "洗洁精", "unit": "瓶", "expiry_days": 365, "location": "厨房", "desc": "洗洁精", "icon": "bottle-tonic"},
        {"name": "垃圾袋", "unit": "卷", "expiry_days": 1095, "location": "厨房", "desc": "垃圾袋", "icon": "archive"},
        {"name": "保鲜膜", "unit": "卷", "expiry_days": 730, "location": "厨房", "desc": "保鲜膜", "icon": "archive-outline"},
        {"name": "保鲜袋", "unit": "盒", "expiry_days": 730, "location": "厨房", "desc": "保鲜袋", "icon": "box"},
    ]

    count = 0
    daily_category_id = get_category_id("日用品")

    for item in daily_items:
        existing = wiki_service.get_wiki_by_name(item["name"])
        if not existing:
            wiki_service.create_wiki(
                name=item["name"],
                description=item["desc"],
                default_unit=item["unit"],
                suggested_expiry_days=item["expiry_days"],
                storage_location=item["location"],
                icon=item.get("icon"),
                category_id=daily_category_id
            )
            count += 1
            print(f"  创建: {item['name']}")
        else:
            wiki_service.update_wiki(
                existing['id'],
                description=item["desc"],
                default_unit=item["unit"],
                suggested_expiry_days=item["expiry_days"],
                storage_location=item["location"],
                icon=item.get("icon"),
                category_id=daily_category_id
            )
            print(f"  更新: {item['name']}")

    return count


def populate_cosmetic_items():
    """创建化妆品物品"""
    print("\n创建化妆品物品...")

    cosmetic_items = [
        {"name": "口红", "unit": "支", "expiry_days": 365, "location": "梳妆台", "desc": "口红", "icon": "lipstick"},
        {"name": "面霜", "unit": "瓶", "expiry_days": 365, "location": "梳妆台", "desc": "面霜", "icon": "bottle-tonic-plus"},
        {"name": "洗面奶", "unit": "瓶", "expiry_days": 365, "location": "卫生间", "desc": "洗面奶", "icon": "bottle-tonic"},
        {"name": "防晒霜", "unit": "支", "expiry_days": 365, "location": "包", "desc": "防晒霜", "icon": "sun-thermometer"},
        {"name": "面膜", "unit": "片", "expiry_days": 730, "location": "梳妆台", "desc": "面膜", "icon": "file"},
        {"name": "眼影", "unit": "盘", "expiry_days": 1095, "location": "梳妆台", "desc": "眼影", "icon": "palette"},
        {"name": "香水", "unit": "瓶", "expiry_days": 1825, "location": "梳妆台", "desc": "香水", "icon": "bottle-wine"},
        {"name": "美瞳", "unit": "盒", "expiry_days": 365, "location": "梳妆台", "desc": "美瞳", "icon": "eye"},
    ]

    count = 0
    cosmetic_category_id = get_category_id("化妆品")

    for item in cosmetic_items:
        existing = wiki_service.get_wiki_by_name(item["name"])
        if not existing:
            wiki_service.create_wiki(
                name=item["name"],
                description=item["desc"],
                default_unit=item["unit"],
                suggested_expiry_days=item["expiry_days"],
                storage_location=item["location"],
                icon=item.get("icon"),
                category_id=cosmetic_category_id
            )
            count += 1
            print(f"  创建: {item['name']}")
        else:
            wiki_service.update_wiki(
                existing['id'],
                description=item["desc"],
                default_unit=item["unit"],
                suggested_expiry_days=item["expiry_days"],
                storage_location=item["location"],
                icon=item.get("icon"),
                category_id=cosmetic_category_id
            )
            print(f"  更新: {item['name']}")

    return count


def populate_medicine_items():
    """创建药品物品"""
    print("\n创建药品物品...")

    medicine_items = [
        {"name": "感冒药", "unit": "盒", "expiry_days": 1095, "location": "药箱", "desc": "感冒药", "icon": "pill"},
        {"name": "退烧药", "unit": "盒", "expiry_days": 1095, "location": "药箱", "desc": "退烧药", "icon": "pills"},
        {"name": "创可贴", "unit": "盒", "expiry_days": 730, "location": "药箱", "desc": "创可贴", "icon": "bandage"},
        {"name": "维生素", "unit": "瓶", "expiry_days": 730, "location": "药箱", "desc": "维生素片", "icon": "medical-bag"},
        {"name": "碘伏", "unit": "瓶", "expiry_days": 1095, "location": "药箱", "desc": "碘伏", "icon": "bottle-tonic"},
        {"name": "棉签", "unit": "包", "expiry_days": 730, "location": "药箱", "desc": "棉签", "icon": "pencil"},
        {"name": "体温计", "unit": "支", "expiry_days": 1825, "location": "药箱", "desc": "体温计", "icon": "thermometer"},
    ]

    count = 0
    medicine_category_id = get_category_id("药品")

    for item in medicine_items:
        existing = wiki_service.get_wiki_by_name(item["name"])
        if not existing:
            wiki_service.create_wiki(
                name=item["name"],
                description=item["desc"],
                default_unit=item["unit"],
                suggested_expiry_days=item["expiry_days"],
                storage_location=item["location"],
                icon=item.get("icon"),
                category_id=medicine_category_id
            )
            count += 1
            print(f"  创建: {item['name']}")
        else:
            wiki_service.update_wiki(
                existing['id'],
                description=item["desc"],
                default_unit=item["unit"],
                suggested_expiry_days=item["expiry_days"],
                storage_location=item["location"],
                icon=item.get("icon"),
                category_id=medicine_category_id
            )
            print(f"  更新: {item['name']}")

    return count


def merge_duplicate_wikis():
    """合并重复的 Wiki（如可能存在名称相似的条目）"""
    print("\n合并重复的 Wiki...")

    with db_service.session_scope() as session:
        # 查找可能重复的（相同 name 不同大小写）
        all_wikis = session.query(ItemWiki).all()
        name_map = {}

        for wiki in all_wikis:
            name_lower = wiki.name.lower()
            if name_lower not in name_map:
                name_map[name_lower] = []
            name_map[name_lower].append(wiki)

        merged = 0
        for name_lower, wikis in name_map.items():
            if len(wikis) > 1:
                # 保留第一个，将其余的 Item 关联到第一个
                keep = wikis[0]
                print(f"  合并: {'/'.join(w.name for w in wikis)} -> {keep.name}")
                for wiki in wikis[1:]:
                    # 将这个 wiki 的所有 item 关联到 keep
                    session.query(Item).filter(
                        Item.wiki_id == wiki.id
                    ).update({'wiki_id': keep.id}, synchronize_session=False)
                    # 删除重复的 wiki
                    session.delete(wiki)
                    merged += 1

        if merged == 0:
            print("  没有找到重复的 Wiki")
        else:
            print(f"  合并了 {merged} 个重复 Wiki")


if __name__ == '__main__':
    init_database()
    print("=" * 50)
    print("Wiki 数据初始化")
    print("=" * 50)

    # 清理测试数据
    cleanup_test_items()

    # 合并重复的 Wiki
    merge_duplicate_wikis()

    # 创建各类物品
    food_count = populate_food_items()
    daily_count = populate_daily_items()
    cosmetic_count = populate_cosmetic_items()
    medicine_count = populate_medicine_items()

    print("\n" + "=" * 50)
    print("初始化完成！")
    print(f"  食品: {food_count} 条")
    print(f"  日用品: {daily_count} 条")
    print(f"  化妆品: {cosmetic_count} 条")
    print(f"  药品: {medicine_count} 条")
    print("=" * 50)
