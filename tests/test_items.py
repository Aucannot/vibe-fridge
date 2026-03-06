# -*- coding: utf-8 -*-
"""logger formatter 行为测试"""
import logging

from app.utils.logger import ColoredFormatter


def test_colored_formatter_wraps_message_with_level_color_and_reset():
    formatter = ColoredFormatter('%(levelname)s:%(message)s')
    record = logging.LogRecord(
        name='test',
        level=logging.WARNING,
        pathname=__file__,
        lineno=1,
        msg='hello',
        args=(),
        exc_info=None,
    )

    output = formatter.format(record)

    assert output.startswith(ColoredFormatter.COLORS['WARNING'])
    assert output.endswith(ColoredFormatter.COLORS['RESET'])
    assert 'WARNING:hello' in output


def test_colored_formatter_uses_reset_color_for_unknown_levelname():
    formatter = ColoredFormatter('%(levelname)s:%(message)s')
    record = logging.LogRecord(
        name='test',
        level=logging.INFO,
        pathname=__file__,
        lineno=1,
        msg='world',
        args=(),
        exc_info=None,
    )
    record.levelname = 'CUSTOM'

    output = formatter.format(record)

    assert output.startswith(ColoredFormatter.COLORS['RESET'])
    assert output.endswith(ColoredFormatter.COLORS['RESET'])
    assert 'CUSTOM:world' in output
