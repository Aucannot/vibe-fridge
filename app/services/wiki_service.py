# -*- coding: utf-8 -*-
"""
物品Wiki服务
"""

import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import desc, or_, func
from sqlalchemy.orm import Session

from app.models.item_wiki import ItemWiki, ItemWikiCategory
from app.services.database import db_service
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


class WikiService:
    """物品Wiki服务类"""

    @staticmethod
    def create_wiki(
        name: str,
        description: str = None,
        default_unit: str = None,
        suggested_expiry_days: int = None,
        storage_location: str = None,
        notes: str = None,
        **kwargs
    ) -> Optional[ItemWiki]:
        """
        创建新物品Wiki

        Args:
            name: 物品名称
            description: 描述
            default_unit: 默认单位
            suggested_expiry_days: 建议保质期（天）
            storage_location: 存放位置
            notes: 备注
            **kwargs: 其他参数

        Returns:
            Optional[ItemWiki]: 创建的Wiki对象，失败返回None
        """
        try:
            with db_service.session_scope() as session:
                wiki = ItemWiki(
                    name=name,
                    description=description,
                    default_unit=default_unit,
                    suggested_expiry_days=suggested_expiry_days,
                    storage_location=storage_location,
                    notes=notes,
                    **kwargs
                )

                session.add(wiki)
                session.flush()

                logger.info(f"物品Wiki创建成功: {wiki.name} (ID: {wiki.id})")
                session.expunge(wiki)
                return wiki

        except Exception as e:
            logger.error(f"创建物品Wiki失败: {str(e)}")
            return None

    @staticmethod
    def get_wiki(wiki_id: str) -> Optional[ItemWiki]:
        """
        获取物品Wiki

        Args:
            wiki_id: Wiki ID

        Returns:
            Optional[ItemWiki]: Wiki对象，不存在返回None
        """
        try:
            with db_service.session_scope() as session:
                wiki = session.query(ItemWiki).filter(ItemWiki.id == wiki_id).first()
                if wiki:
                    session.expunge(wiki)
                return wiki

        except Exception as e:
            logger.error(f"获取物品Wiki失败: {str(e)}")
            return None

    @staticmethod
    def get_wiki_by_name(name: str) -> Optional[ItemWiki]:
        """
        根据名称获取物品Wiki

        Args:
            name: Wiki名称

        Returns:
            Optional[ItemWiki]: Wiki对象，不存在返回None
        """
        try:
            with db_service.session_scope() as session:
                wiki = session.query(ItemWiki).filter(
                    func.lower(ItemWiki.name) == func.lower(name)
                ).first()
                if wiki:
                    session.expunge(wiki)
                return wiki

        except Exception as e:
            logger.error(f"根据名称获取物品Wiki失败: {str(e)}")
            return None

    @staticmethod
    def update_wiki(wiki_id: str, **updates) -> bool:
        """
        更新物品Wiki

        Args:
            wiki_id: Wiki ID
            **updates: 更新字段

        Returns:
            bool: 是否更新成功
        """
        try:
            with db_service.session_scope() as session:
                wiki = session.query(ItemWiki).filter(ItemWiki.id == wiki_id).first()
                if not wiki:
                    logger.warning(f"物品Wiki不存在: {wiki_id}")
                    return False

                for key, value in updates.items():
                    if hasattr(wiki, key):
                        setattr(wiki, key, value)

                logger.info(f"物品Wiki更新成功: {wiki.name} (ID: {wiki_id})")
                return True

        except Exception as e:
            logger.error(f"更新物品Wiki失败: {str(e)}")
            return False

    @staticmethod
    def delete_wiki(wiki_id: str, force: bool = False) -> Dict[str, Any]:
        """
        删除物品Wiki

        Args:
            wiki_id: Wiki ID
            force: 是否强制删除（即使有关联库存）

        Returns:
            Dict[str, Any]: 删除结果信息
        """
        try:
            from app.models.item import Item, ItemStatus

            with db_service.session_scope() as session:
                wiki = session.query(ItemWiki).filter(ItemWiki.id == wiki_id).first()
                if not wiki:
                    logger.warning(f"物品Wiki不存在: {wiki_id}")
                    return {'success': False, 'message': 'Wiki不存在'}

                inventory_count = session.query(Item).filter(
                    Item.wiki_id == wiki_id,
                    Item.status != ItemStatus.CONSUMED
                ).count()

                if inventory_count > 0 and not force:
                    return {
                        'success': False,
                        'message': f'该Wiki下有 {inventory_count} 条库存记录，无法删除',
                        'inventory_count': inventory_count
                    }

                wiki_name = wiki.name
                session.delete(wiki)
                logger.info(f"物品Wiki删除成功: {wiki_name} (ID: {wiki_id})")
                return {'success': True, 'message': f'已删除Wiki: {wiki_name}'}

        except Exception as e:
            logger.error(f"删除物品Wiki失败: {str(e)}")
            return {'success': False, 'message': str(e)}

    @staticmethod
    def get_all_wikis(
        keyword: str = None,
        limit: int = 100,
        offset: int = 0,
        include_inventory_count: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取所有物品Wiki

        Args:
            keyword: 关键词搜索
            limit: 限制数量
            offset: 偏移量
            include_inventory_count: 是否包含库存数量

        Returns:
            List[Dict]: Wiki字典列表
        """
        try:
            with db_service.session_scope() as session:
                query = session.query(ItemWiki)

                if keyword:
                    query = query.filter(
                        or_(
                            ItemWiki.name.ilike(f'%{keyword}%'),
                            ItemWiki.description.ilike(f'%{keyword}%')
                        )
                    )

                wikis = query.order_by(ItemWiki.name).limit(limit).offset(offset).all()

                result = []
                for wiki in wikis:
                    wiki_dict = {
                        'id': wiki.id,
                        'name': wiki.name,
                        'description': wiki.description,
                        'default_unit': wiki.default_unit,
                        'suggested_expiry_days': wiki.suggested_expiry_days,
                        'storage_location': wiki.storage_location,
                        'notes': wiki.notes,
                        'created_at': wiki.created_at.isoformat() if wiki.created_at else None,
                        'updated_at': wiki.updated_at.isoformat() if wiki.updated_at else None,
                    }

                    if include_inventory_count:
                        from app.models.item import Item, ItemStatus
                        count = session.query(Item).filter(
                            Item.wiki_id == wiki.id,
                            Item.status != ItemStatus.CONSUMED
                        ).count()
                        wiki_dict['inventory_count'] = count

                    session.expunge(wiki)
                    result.append(wiki_dict)

                return result

        except Exception as e:
            logger.error(f"获取物品Wiki列表失败: {str(e)}")
            return []

    @staticmethod
    def search_wikis(keyword: str, limit: int = 20) -> List[Dict[str, Any]]:
        """
        搜索物品Wiki

        Args:
            keyword: 搜索关键词
            limit: 限制数量

        Returns:
            List[Dict]: 匹配的Wiki列表
        """
        return WikiService.get_all_wikis(keyword=keyword, limit=limit)

    @staticmethod
    def get_or_create_wiki(
        name: str,
        description: str = None,
        default_unit: str = None,
        suggested_expiry_days: int = None,
        storage_location: str = None,
        notes: str = None
    ) -> ItemWiki:
        """
        获取或创建物品Wiki（如果不存在则创建）

        Args:
            name: 物品名称
            description: 描述
            default_unit: 默认单位
            suggested_expiry_days: 建议保质期（天）
            storage_location: 存放位置
            notes: 备注

        Returns:
            ItemWiki: Wiki对象
        """
        existing = WikiService.get_wiki_by_name(name)
        if existing:
            return existing

        return WikiService.create_wiki(
            name=name,
            description=description,
            default_unit=default_unit,
            suggested_expiry_days=suggested_expiry_days,
            storage_location=storage_location,
            notes=notes
        ) or WikiService.get_wiki_by_name(name)

    @staticmethod
    def get_statistics() -> Dict[str, Any]:
        """
        获取Wiki统计信息

        Returns:
            Dict[str, Any]: 统计信息
        """
        try:
            with db_service.session_scope() as session:
                total_wikis = session.query(ItemWiki).count()

                wikis_with_inventory = session.query(ItemWiki).join(ItemWiki.items).filter(
                    Item.status != 'consumed'
                ).distinct().count()

                return {
                    'total_wikis': total_wikis,
                    'wikis_with_inventory': wikis_with_inventory,
                    'wikis_without_inventory': total_wikis - wikis_with_inventory
                }

        except Exception as e:
            logger.error(f"获取Wiki统计失败: {str(e)}")
            return {}


def seed_example_wikis():
    """在数据库为空时插入一些示例物品Wiki"""
    try:
        existing_wikis = WikiService.get_all_wikis(limit=1)
        if existing_wikis:
            logger.info("物品Wiki已存在，跳过示例数据插入")
            return

        examples = [
            {
                "name": "鲜牛奶",
                "description": "巴氏杀菌鲜牛奶，需要冷藏保存",
                "default_unit": "盒",
                "suggested_expiry_days": 7,
                "storage_location": "冷藏",
            },
            {
                "name": "鸡蛋",
                "description": "新鲜鸡蛋，建议冷藏保存以延长保质期",
                "default_unit": "个",
                "suggested_expiry_days": 30,
                "storage_location": "冷藏",
            },
            {
                "name": "面包",
                "description": "切片面包，常温保存",
                "default_unit": "袋",
                "suggested_expiry_days": 7,
                "storage_location": "常温",
            },
            {
                "name": "矿泉水",
                "description": "瓶装饮用水",
                "default_unit": "瓶",
                "suggested_expiry_days": 365,
                "storage_location": "常温",
            },
            {
                "name": "可口可乐",
                "description": "罐装可乐饮料",
                "default_unit": "罐",
                "suggested_expiry_days": 365,
                "storage_location": "常温",
            },
            {
                "name": "口红",
                "description": "日常化妆品",
                "default_unit": "支",
                "suggested_expiry_days": 365,
                "storage_location": "常温",
            },
            {
                "name": "牙膏",
                "description": "口腔清洁用品",
                "default_unit": "支",
                "suggested_expiry_days": 365,
                "storage_location": "常温",
            },
            {
                "name": "感冒药",
                "description": "常用感冒药",
                "default_unit": "盒",
                "suggested_expiry_days": 730,
                "storage_location": "常温",
            },
            {
                "name": "酸奶",
                "description": "低温酸奶饮品",
                "default_unit": "瓶",
                "suggested_expiry_days": 21,
                "storage_location": "冷藏",
            },
            {
                "name": "水果",
                "description": "新鲜水果",
                "default_unit": "个",
                "suggested_expiry_days": 14,
                "storage_location": "冷藏",
            },
        ]

        for data in examples:
            WikiService.create_wiki(**data)

        logger.info("已插入示例物品Wiki数据")

    except Exception as e:
        logger.error(f"插入示例Wiki数据失败: {e}")
