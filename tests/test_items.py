# -*- coding: utf-8 -*-
"""测试脚本 - 检查物品数据加载"""
import os
os.chdir('h:\\code\\vibe-fridge')

from app.services.database import init_database
from app.services.item_service import item_service

# 初始化数据库
init_database()

# 获取所有物品
items = item_service.get_items()
print(f'获取到 {len(items)} 个物品')

for item in items:
    print(f'ID: {item.id}, Name: {item.name!r}, Category: {item.category.value}')

if items:
    # 检查第一个物品的属性
    item = items[0]
    print(f'\n第一个物品详情:')
    print(f'  has name: {hasattr(item, "name")}')
    print(f'  name value: {item.name!r}')
    print(f'  has category: {hasattr(item, "category")}')
    print(f'  category value: {item.category}')
