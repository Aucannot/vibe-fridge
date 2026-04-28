# -*- coding: utf-8 -*-
"""Bottom navigation layout regression tests."""

import os

os.environ.setdefault("KIVY_NO_ARGS", "1")

from kivy_test_utils import ensure_kivymd_app

ensure_kivymd_app()

from app.main import VibeFridgeApp


def test_bottom_nav_uses_five_equal_slots_with_fixed_width_buttons():
    app = VibeFridgeApp()

    nav = app._create_bottom_nav_bar()
    slots = list(reversed(nav.children))
    buttons = [slot.children[0] for slot in slots]

    assert len(slots) == 5
    assert all(slot.size_hint_x == 1 for slot in slots)
    assert all(button.size_hint_x is None for button in buttons)
    assert buttons[0].width == buttons[1].width == buttons[3].width == buttons[4].width
    assert buttons[2].width > buttons[1].width
    assert buttons[2].width <= buttons[1].width * 1.2
