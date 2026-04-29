# -*- coding: utf-8 -*-
"""Executable layout regression tests for ItemsScreen."""

import os

os.environ.setdefault("KIVY_NO_ARGS", "1")

from kivy.metrics import dp
from kivy.uix.label import Label

from kivy_test_utils import ensure_kivymd_app

ensure_kivymd_app()

from app.ui.screens.items_screen import ItemsScreen


def test_short_item_list_uses_viewport_height_to_stay_top_aligned(monkeypatch):
    monkeypatch.setattr(ItemsScreen, "_load_categories", lambda self: None)
    monkeypatch.setattr(ItemsScreen, "_load_wiki_items", lambda self: None)

    screen = ItemsScreen()
    screen._item_scroll.height = dp(640)
    screen._item_list_box.add_widget(
        Label(text="水果刀", size_hint_y=None, height=dp(60))
    )

    screen._set_item_list_content_height(dp(60))

    assert screen._item_list_box.height >= screen._item_scroll.height
    assert screen._item_scroll.scroll_y == 1
