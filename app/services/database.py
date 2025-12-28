# -*- coding: utf-8 -*-
"""
数据库服务
"""

import os
from pathlib import Path
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.exc import SQLAlchemyError
from contextlib import contextmanager

from app.models.item import Base
from app.utils.logger import setup_logger

logger = setup_logger(__name__)


def get_database_url() -> str:
    """
    获取数据库URL

    Returns:
        str: 数据库URL
    """
    # 从环境变量获取数据库URL
    db_url = os.getenv('DATABASE_URL', 'sqlite:///data/vibe_fridge.db')
    
    # 确保SQLite使用UTF-8编码
    if db_url.startswith('sqlite:///') and '?' not in db_url:
        db_url += '?charset=utf8'
    
    return db_url


def init_database() -> None:
    """
    初始化数据库
    """
    try:
        # 获取数据库URL
        db_url = get_database_url()

        # 如果是SQLite，确保数据目录存在
        if db_url.startswith('sqlite:///'):
            db_path = db_url.replace('sqlite:///', '')
            db_dir = Path(db_path).parent
            db_dir.mkdir(parents=True, exist_ok=True)

        # 创建数据库引擎
        engine = create_engine(db_url)

        # 创建表
        Base.metadata.create_all(engine)

        logger.info(f"数据库初始化成功: {db_url}")

    except Exception as e:
        logger.error(f"数据库初始化失败: {str(e)}")
        raise


def get_session() -> Session:
    """
    获取数据库会话

    Returns:
        Session: SQLAlchemy会话
    """
    db_url = get_database_url()
    engine = create_engine(db_url)
    SessionLocal = sessionmaker(bind=engine)
    return SessionLocal()


@contextmanager
def get_session_ctx():
    """
    数据库会话上下文管理器

    Yields:
        Session: SQLAlchemy会话
    """
    session = get_session()
    try:
        yield session
        session.commit()
    except Exception as e:
        session.rollback()
        logger.error(f"数据库操作失败: {str(e)}")
        raise
    finally:
        session.close()


class DatabaseService:
    """数据库服务类"""

    def __init__(self):
        self.engine = create_engine(get_database_url())
        self.SessionLocal = sessionmaker(bind=self.engine)

    def get_session(self) -> Session:
        """获取数据库会话"""
        return self.SessionLocal()

    @contextmanager
    def session_scope(self):
        """数据库会话作用域"""
        session = self.get_session()
        try:
            yield session
            session.commit()
        except Exception as e:
            session.rollback()
            logger.error(f"数据库操作失败: {str(e)}")
            raise
        finally:
            session.close()

    def execute_raw_sql(self, sql: str, params: dict = None):
        """
        执行原始SQL

        Args:
            sql: SQL语句
            params: 参数

        Returns:
            执行结果
        """
        try:
            with self.session_scope() as session:
                result = session.execute(sql, params or {})
                return result
        except SQLAlchemyError as e:
            logger.error(f"SQL执行失败: {str(e)}")
            raise

    def get_table_count(self, table_name: str) -> int:
        """
        获取表记录数

        Args:
            table_name: 表名

        Returns:
            int: 记录数
        """
        from sqlalchemy import text
        sql = text(f"SELECT COUNT(*) FROM {table_name}")
        try:
            with self.session_scope() as session:
                result = session.execute(sql).scalar()
                return result or 0
        except SQLAlchemyError as e:
            logger.error(f"获取表记录数失败: {str(e)}")
            return 0

    def backup_database(self, backup_path: str = None) -> bool:
        """
        备份数据库

        Args:
            backup_path: 备份文件路径

        Returns:
            bool: 是否备份成功
        """
        try:
            db_url = get_database_url()
            if db_url.startswith('sqlite:///'):
                # SQLite备份
                original_db = db_url.replace('sqlite:///', '')
                backup_path = backup_path or f"{original_db}.backup"

                # 简单的文件复制备份
                import shutil
                shutil.copy2(original_db, backup_path)
                logger.info(f"数据库备份成功: {backup_path}")
                return True
            else:
                logger.warning(f"暂不支持此数据库类型的备份: {db_url.split(':')[0]}")
                return False

        except Exception as e:
            logger.error(f"数据库备份失败: {str(e)}")
            return False


# 全局数据库服务实例
db_service = DatabaseService()


if __name__ == '__main__':
    # 测试数据库功能
    init_database()
    logger.info("数据库测试完成")

    # 获取数据库统计信息
    count = db_service.get_table_count('items')
    logger.info(f"items表记录数: {count}")