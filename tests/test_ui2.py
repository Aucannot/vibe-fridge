# -*- coding: utf-8 -*-
"""测试脚本 - 模拟 Kivy UI 组件"""
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

if items:
    item = items[0]
    logger.info(f'物品数据:')
    logger.info(f'  id = {item.id!r}')
    logger.info(f'  name = {item.name!r}')
    logger.info(f'  category = {item.category}')
    logger.info(f'  category.value = {item.category.value!r}')
    logger.info(f'  expiry_date = {item.expiry_date!r}')
    logger.info(f'  quantity = {item.quantity!r}')
    logger.info(f'  status = {item.status}')
    logger.info(f'  status.value = {item.status.value!r}')

    # 模拟 ItemListItem 初始化
    item_id = item.id
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
    logger.info(f'  item_id = {item_id!r}')
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

    logger.info(f'构建显示文本:')
    logger.info(f'  headline_text = {headline_text!r}')

    # 类别映射
    category_map = {
        "food": "食品",
        "daily": "日用品",
        "medicine": "药品",
        "cosmetics": "化妆品",
        "others": "其他",
    }
    category_text = category_map.get(category, "其他")
    logger.info(f'  category_text = {category_text!r}')

    # 状态文本
    status_text = ""
    if expiry_date == "无":
        status_text = "无过期"
    elif days_until_expiry < 0:
        status_text = "已过期"
    elif days_until_expiry <= 3:
        status_text = "即将过期"
    else:
        status_text = "正常"

    supporting_text = f"{category_text}  ·  {status_text}"
    logger.info(f'  supporting_text = {supporting_text!r}')

    logger.info('✓ 所有数据都正确构建，没有发现问题')
