"""
物品服务
"""

import os
from datetime import datetime, date, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import desc, or_, and_
from sqlalchemy.orm import Session, object_session

from app.models.item import Item, ItemCategory, ItemStatus, Tag
from app.services.database import db_service
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class ItemService:
    """物品服务类"""

    @staticmethod
    def create_item(
        name: str,
        category: ItemCategory,
        quantity: int = 1,
        expiry_date: date = None,
        purchase_date: date = None,
        description: str = None,
        unit: str = None,
        tags: List[str] = None,
        **kwargs
    ) -> Optional[Item]:
        """
        创建新物品

        Args:
            name: 物品名称
            category: 物品类别
            quantity: 数量
            expiry_date: 过期日期
            purchase_date: 购买日期
            description: 描述
            unit: 单位
            tags: 标签列表
            **kwargs: 其他参数

        Returns:
            Optional[Item]: 创建的物品对象，失败返回None
        """
        try:
            with db_service.session_scope() as session:
                # 创建物品对象
                item = Item(
                    name=name,
                    category=category,
                    quantity=quantity,
                    expiry_date=expiry_date,
                    purchase_date=purchase_date,
                    description=description,
                    unit=unit,
                    **kwargs
                )

                # 设置提醒日期
                if expiry_date:
                    reminder_days = int(os.getenv('REMINDER_DAYS_BEFORE', 3))
                    item.reminder_date = expiry_date - timedelta(days=reminder_days)

                # 先保存到数据库，确保物品在会话中
                session.add(item)
                session.flush()  # 获取ID但不提交

                # 处理标签（现在item已经在会话中）
                if tags:
                    ItemService._add_tags_to_item(session, item, tags)

                logger.info(f"物品创建成功: {item.name} (ID: {item.id})")
                # 此处不再手动 expunge；在 with 块结束时会话会提交并关闭，
                # item 会自然变为 detached，对调用方读取基础字段是安全的，
                # 且不会影响关系同步，避免在提交阶段出现 SAWarning。
                return item

        except Exception as e:
            logger.error(f"创建物品失败: {str(e)}")
            return None

    @staticmethod
    def get_item(item_id: str) -> Optional[Item]:
        """
        获取物品

        Args:
            item_id: 物品ID

        Returns:
            Optional[Item]: 物品对象，不存在返回None
        """
        try:
            from sqlalchemy.orm import joinedload

            with db_service.session_scope() as session:
                # 预加载标签，避免 Session 关闭后懒加载错误
                item = (
                    session.query(Item)
                    .options(joinedload(Item.tags))
                    .filter(Item.id == item_id)
                    .first()
                )
                if item:
                    # 将标签也从会话中分离，防止访问时再触发懒加载
                    for tag in item.tags:
                        session.expunge(tag)
                    session.expunge(item)  # 从会话中移除，避免detached错误
                return item
        except Exception as e:
            logger.error(f"获取物品失败: {str(e)}")
            return None

    @staticmethod
    def update_item(item_id: str, **updates) -> bool:
        """
        更新物品

        Args:
            item_id: 物品ID
            **updates: 更新字段

        Returns:
            bool: 是否更新成功
        """
        try:
            with db_service.session_scope() as session:
                item = session.query(Item).filter(Item.id == item_id).first()
                if not item:
                    logger.warning(f"物品不存在: {item_id}")
                    return False

                # 更新字段
                for key, value in updates.items():
                    if hasattr(item, key):
                        setattr(item, key, value)

                # 如果过期日期更新，重新计算提醒日期
                if 'expiry_date' in updates and updates['expiry_date']:
                    reminder_days = int(db_service.get_reminder_days_before())
                    item.reminder_date = updates['expiry_date'] - timedelta(days=reminder_days)

                # 更新状态
                item.update_status()

                logger.info(f"物品更新成功: {item.name} (ID: {item_id})")
                return True

        except Exception as e:
            logger.error(f"更新物品失败: {str(e)}")
            return False

    @staticmethod
    def delete_item(item_id: str) -> bool:
        """
        删除物品

        Args:
            item_id: 物品ID

        Returns:
            bool: 是否删除成功
        """
        try:
            with db_service.session_scope() as session:
                item = session.query(Item).filter(Item.id == item_id).first()
                if not item:
                    logger.warning(f"物品不存在: {item_id}")
                    return False

                session.delete(item)
                logger.info(f"物品删除成功: {item.name} (ID: {item_id})")
                return True

        except Exception as e:
            logger.error(f"删除物品失败: {str(e)}")
            return False

    @staticmethod
    def get_items(
        category: ItemCategory = None,
        status: ItemStatus = None,
        keyword: str = None,
        limit: int = 50,
        offset: int = 0
    ) -> List[Item]:
        """
        获取物品列表

        Args:
            category: 筛选类别
            status: 筛选状态
            keyword: 关键词搜索
            limit: 限制数量
            offset: 偏移量

        Returns:
            List[Item]: 物品列表
        """
        try:
            with db_service.session_scope() as session:
                query = session.query(Item)

                # 应用筛选条件
                if category:
                    query = query.filter(Item.category == category)
                if status:
                    query = query.filter(Item.status == status)
                if keyword:
                    query = query.filter(
                        or_(
                            Item.name.ilike(f'%{keyword}%'),
                            Item.description.ilike(f'%{keyword}%')
                        )
                    )

                # 排序和分页
                items = query.order_by(
                    desc(Item.expiry_date.is_(None)),
                    Item.expiry_date,
                    desc(Item.created_at)
                ).limit(limit).offset(offset).all()

                # 将所有返回的项目从会话中移除，避免detached错误
                for item in items:
                    session.expunge(item)

                return items

        except Exception as e:
            logger.error(f"获取物品列表失败: {str(e)}")
            return []

    @staticmethod
    def get_expiring_items(days: int = 7) -> List[Item]:
        """
        获取即将过期的物品

        Args:
            days: 天数阈值

        Returns:
            List[Item]: 即将过期的物品列表
        """
        try:
            with db_service.session_scope() as session:
                today = date.today()
                expiry_threshold = today + timedelta(days=days)

                items = session.query(Item).filter(
                    and_(
                        Item.expiry_date.isnot(None),
                        Item.expiry_date >= today,
                        Item.expiry_date <= expiry_threshold,
                        Item.status == ItemStatus.ACTIVE
                    )
                ).order_by(Item.expiry_date).all()

                # 将所有返回的项目从会话中移除，避免detached错误
                for item in items:
                    session.expunge(item)

                return items

        except Exception as e:
            logger.error(f"获取即将过期物品失败: {str(e)}")
            return []

    @staticmethod
    def get_items_needing_reminder() -> List[Item]:
        """
        获取需要提醒的物品

        Returns:
            List[Item]: 需要提醒的物品列表
        """
        try:
            with db_service.session_scope() as session:
                today = date.today()

                items = session.query(Item).filter(
                    and_(
                        Item.reminder_date.isnot(None),
                        Item.reminder_date <= today,
                        Item.is_reminder_enabled == True,
                        Item.status == ItemStatus.ACTIVE
                    )
                ).all()

                # 将所有返回的项目从会话中移除，避免detached错误
                for item in items:
                    session.expunge(item)

                return items

        except Exception as e:
            logger.error(f"获取需要提醒的物品失败: {str(e)}")
            return []

    @staticmethod
    def update_item_quantity(item_id: str, delta: int) -> bool:
        """
        更新物品数量

        Args:
            item_id: 物品ID
            delta: 数量变化（正数增加，负数减少）

        Returns:
            bool: 是否更新成功
        """
        try:
            with db_service.session_scope() as session:
                item = session.query(Item).filter(Item.id == item_id).first()
                if not item:
                    logger.warning(f"物品不存在: {item_id}")
                    return False

                new_quantity = item.quantity + delta
                if new_quantity < 0:
                    logger.warning(f"物品数量不能为负数: {item.name}")
                    return False

                item.quantity = new_quantity
                item.update_status()

                logger.info(f"物品数量更新: {item.name} {delta:+d} (当前: {item.quantity})")
                return True

        except Exception as e:
            logger.error(f"更新物品数量失败: {str(e)}")
            return False

    @staticmethod
    def _add_tags_to_item(session: Session, item: Item, tag_names: List[str]) -> None:
        """
        为物品添加标签

        Args:
            session: 数据库会话
            item: 物品对象
            tag_names: 标签名称列表
        """
        # 确保物品绑定到当前会话
        # 使用 object_session 判断 item 当前隶属的会话，而不是使用 "item in session" 这种不可靠的方式，
        # 避免在向 item.tags 追加标签时触发 SAWarning（对象不在会话中）。
        current_session = object_session(item)
        if current_session is not session:
            item = session.merge(item)

        for tag_name in tag_names:
            tag = session.query(Tag).filter(Tag.name == tag_name).first()
            if not tag:
                tag = Tag(name=tag_name)
                session.add(tag)
                session.flush()  # 获取tag的ID

            if tag not in item.tags:
                item.tags.append(tag)


class ItemStatisticsService:
    """物品统计服务"""

    @staticmethod
    def get_category_stats() -> Dict[str, int]:
        """
        获取类别统计

        Returns:
            Dict[str, int]: 类别统计字典
        """
        try:
            with db_service.session_scope() as session:
                result = {}
                for category in ItemCategory:
                    count = session.query(Item).filter(
                        Item.category == category,
                        Item.status == ItemStatus.ACTIVE
                    ).count()
                    result[category.value] = count

                return result
        except Exception as e:
            logger.error(f"获取类别统计失败: {str(e)}")
            return {}

    @staticmethod
    def get_expiry_stats() -> Dict[str, Any]:
        """
        获取过期统计

        Returns:
            Dict[str, Any]: 过期统计字典
        """
        try:
            with db_service.session_scope() as session:
                today = date.today()

                # 已过期
                expired = session.query(Item).filter(
                    and_(
                        Item.expiry_date.isnot(None),
                        Item.expiry_date < today,
                        Item.status != ItemStatus.CONSUMED
                    )
                ).count()

                # 即将过期（7天内）
                soon_expiring = len(ItemService.get_expiring_items(days=7))

                # 过期趋势（按周）
                weekly_stats = ItemStatisticsService._get_weekly_expiry_stats()

                return {
                    'expired': expired,
                    'soon_expiring': soon_expiring,
                    'weekly_stats': weekly_stats
                }
        except Exception as e:
            logger.error(f"获取过期统计失败: {str(e)}")
            return {}

    @staticmethod
    def _get_weekly_expiry_stats() -> List[Dict[str, Any]]:
        """
        获取每周过期统计

        Returns:
            List[Dict[str, Any]]: 每周统计列表
        """
        stats = []
        today = date.today()

        for i in range(4):  # 未来4周
            week_start = today + timedelta(weeks=i)
            week_end = week_start + timedelta(days=6)

            try:
                with db_service.session_scope() as session:
                    count = session.query(Item).filter(
                        and_(
                            Item.expiry_date.isnot(None),
                            Item.expiry_date >= week_start,
                            Item.expiry_date <= week_end
                        )
                    ).count()

                    stats.append({
                        'week': week_start.strftime('%Y-%m-%d'),
                        'count': count
                    })
            except Exception:
                stats.append({
                    'week': week_start.strftime('%Y-%m-%d'),
                    'count': 0
                })

        return stats


# 示例数据工具
def seed_example_items():
    """在数据库为空时插入一些真实示例物品，方便首次体验"""
    try:
        # 如果已有物品，则不再插入示例数据
        if item_service.get_items(limit=1):
            return

        today = date.today()

        examples = [
            {
                "name": "鲜牛奶",
                "category": ItemCategory.FOOD,
                "quantity": 2,
                "unit": "盒",
                "expiry_date": today + timedelta(days=3),
                "description": "早餐用鲜牛奶",
            },
            {
                "name": "鸡蛋",
                "category": ItemCategory.FOOD,
                "quantity": 12,
                "unit": "个",
                "expiry_date": today + timedelta(days=10),
                "description": "普通鸡蛋，一盒",
            },
            {
                "name": "感冒药",
                "category": ItemCategory.MEDICINE,
                "quantity": 1,
                "unit": "盒",
                "expiry_date": today + timedelta(days=365),
                "description": "家用备用感冒药",
            },
        ]

        for data in examples:
            item_service.create_item(**data)

        logger.info("已插入示例物品数据，用于首次体验")
    except Exception as e:
        logger.error(f"插入示例数据失败: {e}")


# 全局服务实例
item_service = ItemService()
statistics_service = ItemStatisticsService()


if __name__ == '__main__':
    # 测试服务功能
    from app.models.item import ItemCategory

    # 创建测试物品
    test_item = item_service.create_item(
        name="测试牛奶",
        category=ItemCategory.FOOD,
        quantity=2,
        expiry_date=date.today() + timedelta(days=5),
        description="测试用物品"
    )

    if test_item:
        print(f"创建成功: {test_item.name}")
        print(f"物品ID: {test_item.id}")
        print(f"过期天数: {test_item.days_until_expiry}")

        # 获取即将过期物品
        expiring = item_service.get_expiring_items(days=7)
        print(f"即将过期物品数量: {len(expiring)}")

        # 获取统计信息
        stats = statistics_service.get_category_stats()
        print(f"类别统计: {stats}")