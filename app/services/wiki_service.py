# -*- coding: utf-8 -*-
"""
物品Wiki服务
"""

import os
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import desc, or_, func
from sqlalchemy.orm import Session, make_transient, joinedload, noload

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
    ) -> Optional[Dict[str, Any]]:
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
            Optional[Dict]: 创建的Wiki字典，失败返回None
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

                result = {
                    'id': wiki.id,
                    'name': wiki.name,
                    'category_id': wiki.category_id,
                    'category_name': wiki.category.name if wiki.category else None,
                    'description': wiki.description,
                    'default_unit': wiki.default_unit,
                    'suggested_expiry_days': wiki.suggested_expiry_days,
                    'storage_location': wiki.storage_location,
                    'notes': wiki.notes,
                    'image_path': wiki.image_path,
                    'created_at': wiki.created_at.isoformat() if wiki.created_at else None,
                    'updated_at': wiki.updated_at.isoformat() if wiki.updated_at else None,
                }

                logger.info(f"物品Wiki创建成功: {wiki.name} (ID: {wiki.id})")
                return result

        except Exception as e:
            logger.error(f"创建物品Wiki失败: {str(e)}")
            return None

    @staticmethod
    def get_wiki(wiki_id: str) -> Optional[Dict[str, Any]]:
        """
        获取物品Wiki

        Args:
            wiki_id: Wiki ID

        Returns:
            Optional[Dict]: Wiki字典，不存在返回None
        """
        try:
            with db_service.session_scope() as session:
                wiki = session.query(ItemWiki).options(
                    joinedload(ItemWiki.category)
                ).filter(ItemWiki.id == wiki_id).first()
                
                if not wiki:
                    return None
                
                result = {
                    'id': wiki.id,
                    'name': wiki.name,
                    'category_id': wiki.category_id,
                    'category_name': wiki.category.name if wiki.category else None,
                    'description': wiki.description,
                    'default_unit': wiki.default_unit,
                    'suggested_expiry_days': wiki.suggested_expiry_days,
                    'storage_location': wiki.storage_location,
                    'notes': wiki.notes,
                    'image_path': wiki.image_path,
                    'created_at': wiki.created_at.isoformat() if wiki.created_at else None,
                    'updated_at': wiki.updated_at.isoformat() if wiki.updated_at else None,
                }
                return result

        except Exception as e:
            logger.error(f"获取物品Wiki失败: {str(e)}")
            return None

    @staticmethod
    def get_wiki_by_name(name: str) -> Optional[Dict[str, Any]]:
        """
        根据名称获取物品Wiki

        Args:
            name: Wiki名称

        Returns:
            Optional[Dict]: Wiki字典，不存在返回None
        """
        try:
            with db_service.session_scope() as session:
                wiki = session.query(ItemWiki).options(
                    joinedload(ItemWiki.category)
                ).filter(
                    func.lower(ItemWiki.name) == func.lower(name)
                ).first()
                
                if not wiki:
                    return None
                
                result = {
                    'id': wiki.id,
                    'name': wiki.name,
                    'category_id': wiki.category_id,
                    'category_name': wiki.category.name if wiki.category else None,
                    'description': wiki.description,
                    'default_unit': wiki.default_unit,
                    'suggested_expiry_days': wiki.suggested_expiry_days,
                    'storage_location': wiki.storage_location,
                    'notes': wiki.notes,
                    'image_path': wiki.image_path,
                    'created_at': wiki.created_at.isoformat() if wiki.created_at else None,
                    'updated_at': wiki.updated_at.isoformat() if wiki.updated_at else None,
                }
                return result

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
            logger.info(f"开始更新Wiki: wiki_id={wiki_id}, updates={updates}")
            with db_service.session_scope() as session:
                wiki = session.query(ItemWiki).filter(ItemWiki.id == wiki_id).first()
                if not wiki:
                    logger.warning(f"物品Wiki不存在: {wiki_id}")
                    return False

                logger.info(f"找到Wiki对象: {wiki}")
                for key, value in updates.items():
                    if hasattr(wiki, key):
                        logger.info(f"设置属性: {key} = {value}")
                        setattr(wiki, key, value)
                    else:
                        logger.warning(f"Wiki对象没有属性: {key}")

                session.flush()
                logger.info(f"物品Wiki更新成功: {wiki.name} (ID: {wiki_id})")
                return True

        except Exception as e:
            logger.error(f"更新物品Wiki失败: {str(e)}", exc_info=True)
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
    def create_category(
        name: str,
        icon: str = None,
        color: str = None,
        sort_order: int = 0
    ) -> Optional[ItemWikiCategory]:
        """
        创建物品分类

        Args:
            name: 分类名称
            icon: 图标名称
            color: 颜色（十六进制）
            sort_order: 排序顺序

        Returns:
            Optional[ItemWikiCategory]: 创建的分类对象，失败返回None
        """
        try:
            with db_service.session_scope() as session:
                category = ItemWikiCategory(
                    name=name,
                    icon=icon,
                    color=color,
                    sort_order=sort_order
                )
                session.add(category)
                session.flush()
                session.expunge(category)
                logger.info(f"物品分类创建成功: {name} (ID: {category.id})")
                return category
        except Exception as e:
            logger.error(f"创建物品分类失败: {str(e)}")
            return None

    @staticmethod
    def get_category(category_id: str) -> Optional[ItemWikiCategory]:
        """
        获取物品分类

        Args:
            category_id: 分类ID

        Returns:
            Optional[ItemWikiCategory]: 分类对象，不存在返回None
        """
        try:
            with db_service.session_scope() as session:
                category = session.query(ItemWikiCategory).filter(
                    ItemWikiCategory.id == category_id
                ).first()
                if category:
                    session.expunge(category)
                return category
        except Exception as e:
            logger.error(f"获取物品分类失败: {str(e)}")
            return None

    @staticmethod
    def get_all_categories() -> List[ItemWikiCategory]:
        """
        获取所有物品分类（按排序顺序）

        Returns:
            List[ItemWikiCategory]: 分类列表
        """
        try:
            with db_service.session_scope() as session:
                categories = session.query(ItemWikiCategory).order_by(
                    ItemWikiCategory.sort_order, ItemWikiCategory.name
                ).all()
                for category in categories:
                    make_transient(category)
                return categories
        except Exception as e:
            logger.error(f"获取所有物品分类失败: {str(e)}")
            return []

    @staticmethod
    def update_category(category_id: str, **updates) -> bool:
        """
        更新物品分类

        Args:
            category_id: 分类ID
            **updates: 更新字段

        Returns:
            bool: 是否更新成功
        """
        try:
            with db_service.session_scope() as session:
                category = session.query(ItemWikiCategory).filter(
                    ItemWikiCategory.id == category_id
                ).first()
                if not category:
                    logger.warning(f"物品分类不存在: {category_id}")
                    return False

                for key, value in updates.items():
                    if hasattr(category, key):
                        setattr(category, key, value)

                logger.info(f"物品分类更新成功: {category.name} (ID: {category_id})")
                return True
        except Exception as e:
            logger.error(f"更新物品分类失败: {str(e)}")
            return False

    @staticmethod
    def delete_category(category_id: str, force: bool = False) -> Dict[str, Any]:
        """
        删除物品分类

        Args:
            category_id: 分类ID
            force: 是否强制删除（即使有关联物品）

        Returns:
            Dict[str, Any]: 删除结果信息
        """
        try:
            with db_service.session_scope() as session:
                category = session.query(ItemWikiCategory).filter(
                    ItemWikiCategory.id == category_id
                ).first()
                if not category:
                    logger.warning(f"物品分类不存在: {category_id}")
                    return {'success': False, 'message': '分类不存在'}

                item_count = session.query(ItemWiki).filter(
                    ItemWiki.category_id == category_id
                ).count()

                if item_count > 0 and not force:
                    return {
                        'success': False,
                        'message': f'该分类下有 {item_count} 个物品，无法删除',
                        'item_count': item_count
                    }

                category_name = category.name
                session.delete(category)
                logger.info(f"物品分类删除成功: {category_name} (ID: {category_id})")
                return {'success': True, 'message': f'已删除分类: {category_name}'}
        except Exception as e:
            logger.error(f"删除物品分类失败: {str(e)}")
            return {'success': False, 'message': str(e)}

    @staticmethod
    def get_all_wikis(
        keyword: str = None,
        category_id: str = None,
        limit: int = 100,
        offset: int = 0,
        include_inventory_count: bool = True
    ) -> List[Dict[str, Any]]:
        """
        获取所有物品Wiki

        Args:
            keyword: 关键词搜索
            category_id: 分类ID（可选）
            limit: 限制数量
            offset: 偏移量
            include_inventory_count: 是否包含库存数量

        Returns:
            List[Dict]: Wiki字典列表
        """
        try:
            from sqlalchemy.orm import joinedload

            with db_service.session_scope() as session:
                # 预加载category关系
                query = session.query(ItemWiki).options(joinedload(ItemWiki.category))

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
                        'category_id': wiki.category_id,
                        'category_name': wiki.category.name if wiki.category else None,
                        'description': wiki.description,
                        'default_unit': wiki.default_unit,
                        'suggested_expiry_days': wiki.suggested_expiry_days,
                        'storage_location': wiki.storage_location,
                        'notes': wiki.notes,
                        'image_path': wiki.image_path,
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
    ) -> Dict[str, Any]:
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
            Dict: Wiki字典
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

                from app.models.item import Item, ItemStatus
                wikis_with_inventory = session.query(ItemWiki).join(ItemWiki.items).filter(
                    Item.status != ItemStatus.CONSUMED
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
    """在数据库为空时插入一些示例物品Wiki和分类"""
    try:
        existing_wikis = WikiService.get_all_wikis(limit=1)
        if existing_wikis:
            logger.info("物品Wiki已存在，跳过示例数据插入")
            return

        # 确保有默认分类
        categories = WikiService.get_all_categories()
        category_map = {}
        
        # 如果没有分类，创建默认分类
        if not categories:
            default_categories = [
                {"name": "食品", "icon": "food-apple", "sort_order": 1},
                {"name": "日用品", "icon": "home", "sort_order": 2},
                {"name": "化妆品", "icon": "palette", "sort_order": 3},
                {"name": "药品", "icon": "medical-bag", "sort_order": 4},
            ]
            for cat_data in default_categories:
                category = WikiService.create_category(**cat_data)
                if category:
                    category_map[cat_data["name"]] = category.id
        else:
            for category in categories:
                category_map[category.name] = category.id

        # 示例物品Wiki数据
        examples = [
            {
                "name": "鲜牛奶",
                "description": "巴氏杀菌鲜牛奶，需要冷藏保存",
                "default_unit": "盒",
                "suggested_expiry_days": 7,
                "storage_location": "冷藏",
                "category_id": category_map.get("食品")
            },
            {
                "name": "鸡蛋",
                "description": "新鲜鸡蛋，建议冷藏保存以延长保质期",
                "default_unit": "个",
                "suggested_expiry_days": 30,
                "storage_location": "冷藏",
                "category_id": category_map.get("食品")
            },
            {
                "name": "面包",
                "description": "切片面包，常温保存",
                "default_unit": "袋",
                "suggested_expiry_days": 7,
                "storage_location": "常温",
                "category_id": category_map.get("食品")
            },
            {
                "name": "矿泉水",
                "description": "瓶装饮用水",
                "default_unit": "瓶",
                "suggested_expiry_days": 365,
                "storage_location": "常温",
                "category_id": category_map.get("食品")
            },
            {
                "name": "可口可乐",
                "description": "罐装可乐饮料",
                "default_unit": "罐",
                "suggested_expiry_days": 365,
                "storage_location": "常温",
                "category_id": category_map.get("食品")
            },
            {
                "name": "口红",
                "description": "日常化妆品",
                "default_unit": "支",
                "suggested_expiry_days": 365,
                "storage_location": "常温",
                "category_id": category_map.get("化妆品")
            },
            {
                "name": "牙膏",
                "description": "口腔清洁用品",
                "default_unit": "支",
                "suggested_expiry_days": 365,
                "storage_location": "常温",
                "category_id": category_map.get("日用品")
            },
            {
                "name": "感冒药",
                "description": "常用感冒药",
                "default_unit": "盒",
                "suggested_expiry_days": 730,
                "storage_location": "常温",
                "category_id": category_map.get("药品")
            },
            {
                "name": "酸奶",
                "description": "低温酸奶饮品",
                "default_unit": "瓶",
                "suggested_expiry_days": 21,
                "storage_location": "冷藏",
                "category_id": category_map.get("食品")
            },
            {
                "name": "水果",
                "description": "新鲜水果",
                "default_unit": "个",
                "suggested_expiry_days": 14,
                "storage_location": "冷藏",
                "category_id": category_map.get("食品")
            },
        ]

        for data in examples:
            WikiService.create_wiki(**data)

        logger.info("已插入示例物品Wiki数据")

    except Exception as e:
        logger.error(f"插入示例Wiki数据失败: {e}")


# 全局服务实例
wiki_service = WikiService()
