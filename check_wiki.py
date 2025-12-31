from app.utils.logger import setup_logger
from app.services.database import db_service
from app.models.item_wiki import ItemWiki

logger = setup_logger(__name__)

with db_service.session_scope() as session:
    items = session.query(ItemWiki).all()
    logger.info('物品Wiki记录:')
    for item in items:
        category_name = item.category.name if item.category else "无"
        logger.info(f'- {item.name} (分类: {category_name})')
