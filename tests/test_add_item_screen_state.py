# -*- coding: utf-8 -*-
"""AddItemScreen state and callback tests (logic-level, no manual UI interaction)."""

import os
from datetime import date

import pytest

os.environ.setdefault("KIVY_NO_ARGS", "1")

from kivy_test_utils import ensure_kivymd_app

ensure_kivymd_app()

from kivy.graphics import Color

from app.ui.screens.add_item_screen import AddItemScreen, FridgeTextInput


class DummyPicker:
    def __init__(self, should_raise=False):
        self.dismiss_called = False
        self.should_raise = should_raise

    def dismiss(self):
        self.dismiss_called = True
        if self.should_raise:
            raise RuntimeError("dismiss failed")


def build_screen():
    screen = AddItemScreen()
    # 避免测试中真实弹窗
    screen._show_error_dialog = lambda *_args, **_kwargs: None
    return screen


def test_fridge_text_input_redraw_preserves_text_canvas_instructions():
    widget = FridgeTextInput(text="识别内容")
    sentinel = Color(1, 0, 0, 0)
    widget.canvas.before.add(sentinel)

    widget._redraw()

    assert widget.text == "识别内容"
    assert sentinel in widget.canvas.before.children


def test_reset_form_keeps_ui_and_form_data_in_sync():
    screen = build_screen()

    screen.name_input.text = "鸡蛋"
    screen.quantity_input.text = "5"
    screen.tag_input.text = "早餐"
    screen.reminder_checkbox.active = False

    screen._reset_form()

    assert screen.name_input.text == ""
    assert screen.quantity_input.text == "1"
    assert screen.form_data["enable_reminder"] is True
    assert screen.reminder_checkbox.active is True
    assert screen.form_data["category"] == "食品"


def test_select_category_updates_label_and_form_data():
    screen = build_screen()

    screen._select_category("药品")

    assert screen.category_button.text == "药品"
    assert screen.form_data["category"] == "药品"


def test_on_date_selected_updates_purchase_and_expiry():
    screen = build_screen()
    purchase = date(2026, 1, 2)
    expiry = date(2026, 1, 9)

    screen._on_date_selected(purchase, "purchase")
    screen._on_date_selected(expiry, "expiry")

    assert screen.purchase_date_button.text == "2026-01-02"
    assert screen.expiry_date_button.text == "2026-01-09"
    assert screen.form_data["purchase_date"] == purchase
    assert screen.form_data["expiry_date"] == expiry


def test_on_date_ok_uses_picker_fields_and_dismisses_picker():
    screen = build_screen()
    picker = DummyPicker()
    picker.sel_year = 2026
    picker.sel_month = 6
    picker.sel_day = 3
    screen.date_picker = picker

    screen._on_date_ok(picker, date_type="purchase")

    assert screen.purchase_date_button.text == "2026-06-03"
    assert screen.form_data["purchase_date"] == date(2026, 6, 3)
    assert picker.dismiss_called is True
    assert screen.date_picker is None


def test_date_picker_cancel_dismisses_picker():
    screen = build_screen()
    picker = DummyPicker()
    screen.date_picker = picker

    screen._dismiss_date_picker(picker)

    assert picker.dismiss_called is True
    assert screen.date_picker is None


def test_on_leave_dismisses_and_clears_date_picker():
    screen = build_screen()
    picker = DummyPicker()
    screen.date_picker = picker

    screen.on_leave()

    assert picker.dismiss_called is True
    assert screen.date_picker is None


def test_on_leave_ignores_dismiss_exception_and_still_clears_picker():
    screen = build_screen()
    picker = DummyPicker(should_raise=True)
    screen.date_picker = picker

    screen.on_leave()

    assert picker.dismiss_called is True
    assert screen.date_picker is None


def test_validate_form_rejects_expiry_before_purchase_date():
    screen = build_screen()
    screen.name_input.text = "牛奶"
    screen.quantity_input.text = "2"
    screen.form_data["purchase_date"] = date(2026, 5, 10)
    screen.form_data["expiry_date"] = date(2026, 5, 1)

    assert screen._validate_form() is False
