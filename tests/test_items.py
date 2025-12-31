# -*- coding: utf-8 -*-
"""测试脚本 - 检查物品数据加载"""
import os
os.chdir('h:\\code\\vibe-fridge')

from app.utils.logger import setup_logger
from app.services.database import init_database
from app.services.item_service import item_service

logger = setup_logger(__name__)

# 初始化数据库
init_database()

# 获取所有物品
items = item_service.get_items()
logger.info(f'获取到 {len(items)} 个物品')

for item in items:
    logger.info(f'ID: {item.id}, Name: {item.name!r}, Category: {item.category.value}')

if items:
    # 检查第一个物品的属性
    item = items[0]
    logger.info(f'第一个物品详情:')
    logger.info(f'  has name: {hasattr(item, "name")}')
    logger.info(f'  name value: {item.name!r}')
    logger.info(f'  has category: {hasattr(item, "category")}')
    logger.info(f'  category value: {item.category}')
