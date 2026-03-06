# -*- coding: utf-8 -*-
"""setup_logger 行为测试"""
import logging
from pathlib import Path

from app.utils.logger import setup_logger


def test_setup_logger_creates_log_dir_and_file_handler(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    logger_name = 'test.logger.create'

    logger = setup_logger(logger_name, level=logging.INFO)

    assert Path('logs').exists()
    file_handlers = [h for h in logger.handlers if isinstance(h, logging.FileHandler)]
    stream_handlers = [h for h in logger.handlers if isinstance(h, logging.StreamHandler)]
    assert file_handlers
    assert stream_handlers


def test_setup_logger_does_not_duplicate_handlers_on_second_call(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    logger_name = 'test.logger.idempotent'

    logger = setup_logger(logger_name, level=logging.INFO)
    first_count = len(logger.handlers)

    logger_again = setup_logger(logger_name, level=logging.INFO)
    second_count = len(logger_again.handlers)

    assert logger is logger_again
    assert second_count == first_count
