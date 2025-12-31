# -*- coding: utf-8 -*-
"""测试脚本 - 检查 ItemListItem UI 组件"""
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

if items:
    item = items[0]
    logger.info(f'测试 ItemListItem 组件:')
    logger.info(f'  item.id = {item.id!r}')
    logger.info(f'  item.name = {item.name!r}')
    logger.info(f'  item.category = {item.category!r}')
    logger.info(f'  item.category.value = {item.category.value!r}')
    logger.info(f'  item.expiry_date = {item.expiry_date!r}')
    logger.info(f'  item.quantity = {item.quantity!r}')
    logger.info(f'  item.status = {item.status!r}')

    # 模拟 ItemListItem 的初始化逻辑
    item_name = item.name
    category = item.category.value
    expiry_date = item.expiry_date.strftime('%Y-%m-%d') if item.expiry_date else '无'

    if item.expiry_date:
        from datetime import date
        today = date.today()
        delta = item.expiry_date - today
        days_until_expiry = delta.days
    else:
        days_until_expiry = 0

    quantity = item.quantity
    status = item.status.value
    is_consumed = status == 'consumed'

    logger.info(f'模拟 ItemListItem 初始化:')
    logger.info(f'  item_name = {item_name!r}')
    logger.info(f'  category = {category!r}')
    logger.info(f'  expiry_date = {expiry_date!r}')
    logger.info(f'  days_until_expiry = {days_until_expiry}')
    logger.info(f'  quantity = {quantity!r}')
    logger.info(f'  status = {status!r}')
    logger.info(f'  is_consumed = {is_consumed}')

    # 构建 headline_text
    headline_text = f"{item_name}"
    if quantity > 1:
        headline_text += f" ×{quantity}"

    logger.info(f'  headline_text = {headline_text!r}')
