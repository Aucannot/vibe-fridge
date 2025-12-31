# -*- coding: utf-8 -*-
"""
日志工具
"""

import logging
import os
from datetime import datetime
from pathlib import Path


class ColoredFormatter(logging.Formatter):
    """彩色日志格式化器"""

    COLORS = {
        'DEBUG': '\033[94m',  # 蓝色
        'INFO': '\033[92m',   # 绿色
        'WARNING': '\033[93m',  # 黄色
        'ERROR': '\033[91m',  # 红色
        'CRITICAL': '\033[95m',  # 洋红色
        'RESET': '\033[0m',   # 重置颜色
    }

    def format(self, record):
        """格式化日志记录"""
        log_message = super().format(record)
        color = self.COLORS.get(record.levelname, self.COLORS['RESET'])
        return f"{color}{log_message}{self.COLORS['RESET']}"


def setup_logger(name='vibe-fridge', level=logging.INFO):
    """
    设置日志记录器

    Args:
        name: 日志记录器名称
        level: 日志级别

    Returns:
        logging.Logger: 配置好的日志记录器
    """
    # 创建日志目录
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)

    # 创建日志文件名（按日期）
    log_filename = f"{datetime.now().strftime('%Y%m%d')}.log"
    log_file = log_dir / log_filename

    # 创建日志记录器
    logger = logging.getLogger(name)
    logger.setLevel(level)

    # 避免重复添加处理器
    if logger.handlers:
        return logger

    # 创建控制台处理器
    console_handler = logging.StreamHandler()
    console_handler.setLevel(level)

    # 创建文件处理器
    file_handler = logging.FileHandler(log_file, encoding='utf-8')
    file_handler.setLevel(level)

    # 创建格式化器
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # 设置格式化器
    console_handler.setFormatter(console_formatter)
    file_handler.setFormatter(file_formatter)

    # 添加处理器到记录器
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


def get_logger(name=None):
    """
    获取日志记录器

    Args:
        name: 日志记录器名称，如果为 None 则使用默认名称

    Returns:
        logging.Logger: 日志记录器
    """
    name = name or 'vibe-fridge'
    return logging.getLogger(name)


if __name__ == '__main__':
    # 测试日志功能
    logger = setup_logger()
    logger.debug('这是一条调试信息')
    logger.info('这是一条普通信息')
    logger.warning('这是一条警告信息')
    logger.error('这是一条错误信息')