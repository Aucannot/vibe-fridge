# -*- coding: utf-8 -*-
"""get_logger 行为测试"""
import logging

from app.utils.logger import get_logger, setup_logger


def test_get_logger_returns_default_logger_when_name_missing(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    setup_logger('vibe-fridge', level=logging.INFO)

    logger = get_logger()

    assert logger.name == 'vibe-fridge'


def test_get_logger_returns_named_logger(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    setup_logger('custom.logger', level=logging.INFO)

    logger = get_logger('custom.logger')

    assert logger.name == 'custom.logger'
