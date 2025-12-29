# -*- coding: utf-8 -*-
"""
数据模型: 物品Wiki - 物品的类定义
"""

import uuid
import logging
from datetime import datetime
from typing import Optional
from sqlalchemy import Column, String, Text, DateTime, Integer
from app.models import Base


class ItemWiki(Base):
    """
    物品Wiki模型 - 物品的类定义

    存储物品的通用属性，作为物品库存记录的模板。
    每个库存记录(Item)关联到一个Wiki条目。
    """
    __tablename__ = 'item_wikis'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)

    default_unit = Column(String(20), nullable=True)  # 默认单位：个、盒、瓶等

    suggested_expiry_days = Column(Integer, nullable=True)  # 建议保质期（天）

    storage_location = Column(String(100), nullable=True)  # 建议存放位置：冷藏、冷冻、常温

    notes = Column(Text, nullable=True)  # 备注信息

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    def __repr__(self):
        return f"<ItemWiki(id='{self.id}', name='{self.name}')>"

    @property
    def inventory_count(self) -> int:
        """获取该Wiki下的库存记录数量"""
        try:
            from app.services.database import db_service
            from app.models.item import ItemStatus

            with db_service.session_scope() as session:
                count = session.query(Item).filter(
                    Item.wiki_id == self.id,
                    Item.status != ItemStatus.CONSUMED
                ).count()
                return count
        except Exception as e:
            logging.error(f"获取Wiki库存数量失败: {e}")
            return 0


class ItemWikiCategory(Base):
    """
    物品Wiki分类模型
    """
    __tablename__ = 'item_wiki_categories'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    name = Column(String(50), nullable=False, unique=True, index=True)

    icon = Column(String(50), nullable=True)  # 图标名称

    color = Column(String(20), nullable=True)  # 颜色（十六进制）

    sort_order = Column(Integer, nullable=False, default=0)  # 排序顺序

    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    def __repr__(self):
        return f"<ItemWikiCategory(id='{self.id}', name='{self.name}')>"
