# -*- coding: utf-8 -*-
"""
数据模型: 物品
"""

import uuid
import logging
from datetime import datetime, date
from enum import Enum
from typing import Optional
from sqlalchemy import (
    Column, String, Integer, Float, Date, DateTime,
    Text, Boolean, Enum as SQLEnum, ForeignKey
)
from sqlalchemy.orm import declarative_base, relationship

Base = declarative_base()


class ItemCategory(Enum):
    """物品类别枚举"""
    FOOD = "food"               # 食品
    DAILY_NECESSITIES = "daily"  # 日用品
    MEDICINE = "medicine"       # 药品
    COSMETICS = "cosmetics"     # 化妆品
    OTHERS = "others"           # 其他


class ItemStatus(Enum):
    """物品状态枚举"""
    ACTIVE = "active"           # 使用中
    EXPIRED = "expired"         # 已过期
    CONSUMED = "consumed"       # 已消耗
    WASTED = "wasted"          # 已丢弃


class Item(Base):
    """
    物品模型
    """
    __tablename__ = 'items'

    # 主键
    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))

    # 基本信息
    name = Column(String(100), nullable=False, index=True)
    description = Column(Text, nullable=True)
    category = Column(SQLEnum(ItemCategory), nullable=False, index=True)

    # 数量信息
    quantity = Column(Integer, nullable=False, default=1)
    unit = Column(String(20), nullable=True)  # 单位：个、盒、瓶等

    # 日期信息
    purchase_date = Column(Date, nullable=True, index=True)
    expiry_date = Column(Date, nullable=True, index=True)
    reminder_date = Column(Date, nullable=True, index=True)

    # 状态信息
    status = Column(SQLEnum(ItemStatus), nullable=False, default=ItemStatus.ACTIVE, index=True)
    is_reminder_enabled = Column(Boolean, nullable=False, default=True)

    # AI 预测信息
    predicted_expiry_date = Column(Date, nullable=True)
    prediction_confidence = Column(Float, nullable=True)  # 预测置信度 0-1

    # 图片和来源
    image_path = Column(String(255), nullable=True)
    source_app = Column(String(50), nullable=True)  # 来源应用：盒马、淘宝等
    source_order_id = Column(String(100), nullable=True)  # 来源订单ID

    # 元数据
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    updated_at = Column(DateTime, nullable=False, default=datetime.utcnow, onupdate=datetime.utcnow)

    # 标签关系（多对多）
    tags = relationship('Tag', secondary='item_tags', back_populates='items')

    def __repr__(self):
        return f"<Item(id='{self.id}', name='{self.name}', category='{self.category.value}')>"

    @property
    def is_expired(self) -> bool:
        """检查是否过期"""
        if not self.expiry_date:
            return False
        return date.today() > self.expiry_date

    @property
    def days_until_expiry(self) -> Optional[int]:
        """距离过期天数（负数表示已过期）"""
        try:
            if not self.expiry_date:
                return None
            delta = self.expiry_date - date.today()
            return delta.days
        except Exception as e:
            logging.error(f"日期计算错误: {e}, expiry_date类型: {type(self.expiry_date)}")
            return None

    @property
    def should_remind(self) -> bool:
        """是否应该发送提醒"""
        if not self.is_reminder_enabled or not self.reminder_date:
            return False
        return date.today() >= self.reminder_date

    def update_status(self) -> None:
        """更新物品状态"""
        if self.is_expired:
            self.status = ItemStatus.EXPIRED
        elif self.quantity <= 0:
            self.status = ItemStatus.CONSUMED


class Tag(Base):
    """
    标签模型
    """
    __tablename__ = 'tags'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = Column(String(50), nullable=False, unique=True, index=True)
    color = Column(String(20), nullable=True)  # 标签颜色（十六进制）
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)

    items = relationship('Item', secondary='item_tags', back_populates='tags')

    def __repr__(self):
        return f"<Tag(id='{self.id}', name='{self.name}')>"


class ItemTag(Base):
    """
    物品-标签关联表
    """
    __tablename__ = 'item_tags'

    item_id = Column(String(36), ForeignKey('items.id'), primary_key=True)
    tag_id = Column(String(36), ForeignKey('tags.id'), primary_key=True)
    created_at = Column(DateTime, nullable=False, default=datetime.utcnow)


class ReminderLog(Base):
    """
    提醒日志
    """
    __tablename__ = 'reminder_logs'

    id = Column(String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    item_id = Column(String(36), ForeignKey('items.id'), nullable=False, index=True)
    reminder_type = Column(String(50), nullable=False)  # 提醒类型：expiry_reminder, low_stock等
    message = Column(Text, nullable=False)
    sent_at = Column(DateTime, nullable=False, default=datetime.utcnow)
    is_success = Column(Boolean, nullable=False, default=True)
    error_message = Column(Text, nullable=True)

    item = relationship('Item', backref='reminder_logs')

    def __repr__(self):
        return f"<ReminderLog(item_id='{self.item_id}', sent_at='{self.sent_at}')>"