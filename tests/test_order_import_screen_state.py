# -*- coding: utf-8 -*-
"""OrderImportScreen state and callback tests."""

import os
from datetime import date
from types import SimpleNamespace

import pytest

os.environ.setdefault("KIVY_NO_ARGS", "1")

from kivy_test_utils import ensure_kivymd_app

ensure_kivymd_app()

from kivy.uix.anchorlayout import AnchorLayout
from kivymd.uix.label import MDIcon

from app.ui.screens.order_import_screen import OrderImportScreen


class DummyDialog:
    def __init__(self):
        self.dismiss_called = False

    def dismiss(self):
        self.dismiss_called = True


def build_screen():
    return OrderImportScreen()


def test_commit_import_marks_created_rows_and_keeps_failed_rows_editable(monkeypatch):
    screen = build_screen()
    screen.draft.load_review_payload(
        {
            "source_app": "盒马",
            "source_order_id": "HM-2026",
            "purchase_date": "2026-04-01",
            "image_path": "/tmp/order.png",
            "items": [
                {
                    "name": "牛奶",
                    "quantity": 2,
                    "unit": "盒",
                    "category": "食品",
                    "selected": True,
                    "can_import": True,
                },
                {
                    "name": "面包",
                    "quantity": 1,
                    "unit": "袋",
                    "category": "食品",
                    "selected": True,
                    "can_import": True,
                },
            ],
        }
    )

    captured_payloads = []

    def fake_commit(payload):
        captured_payloads.append(payload)
        return {
            "created_count": 1,
            "skipped_count": 0,
            "failed_rows": [{"row": 2, "name": "面包", "reason": "创建库存记录失败"}],
            "created_rows": [{"row": 1, "name": "牛奶", "item_id": "item-1"}],
        }

    dialogs = []
    renders = []
    monkeypatch.setattr(
        "app.ui.screens.order_import_screen.order_import_service.commit_import",
        fake_commit,
    )
    screen._show_success_dialog = lambda result: dialogs.append(result)
    screen._show_error_dialog = lambda message: pytest.fail(message)
    screen._render_current_state = lambda: renders.append(True)

    screen._commit_import(None)

    assert [item["name"] for item in captured_payloads[0]["items"]] == ["牛奶", "面包"]
    assert screen.draft.import_payload["items"][0]["imported"] is True
    assert screen.draft.import_payload["items"][0]["selected"] is False
    assert screen.draft.import_payload["items"][1].get("imported") is not True
    assert screen.draft.import_payload["items"][1]["selected"] is True
    assert screen.draft.selected_importable_count() == 1
    assert dialogs and dialogs[0]["created_count"] == 1
    assert renders

    retry_payload = screen.draft.build_commit_payload()
    assert [item["name"] for item in retry_payload["items"]] == ["面包"]
    assert retry_payload["items"][0]["_row_number"] == 2


def test_confirm_file_selection_updates_draft_and_starts_parse(monkeypatch, tmp_path):
    screen = build_screen()
    image_path = tmp_path / "order.jpg"
    image_path.write_bytes(b"fake-image")
    dialog = DummyDialog()
    started = []

    screen._start_parse_flow = lambda: started.append(screen.draft.image_path)
    screen._show_error_dialog = lambda message: pytest.fail(message)

    screen._confirm_file_selection(dialog, [str(image_path)])

    assert dialog.dismiss_called is True
    assert screen._file_dialog is None
    assert screen.draft.image_path == str(image_path.resolve())
    assert started == [str(image_path.resolve())]


def test_save_item_edits_revalidates_item_and_rerenders():
    screen = build_screen()
    screen.draft.load_review_payload(
        {
            "source_app": "盒马",
            "items": [
                {
                    "name": "旧名称",
                    "quantity": 1,
                    "unit": "件",
                    "category": "食品",
                    "selected": True,
                    "can_import": True,
                    "confidence": 0.72,
                }
            ],
        }
    )
    dialog = DummyDialog()
    renders = []
    screen._render_current_state = lambda: renders.append(True)

    screen._save_item_edits(
        dialog,
        0,
        {
            "name": "新牛奶",
            "quantity": "3",
            "unit": "盒",
            "category": "食品",
            "purchase_date": "2026-04-01",
            "expiry_date": "2026-04-08",
            "selected": True,
            "confidence": 0.72,
            "warnings": [],
        },
    )

    item = screen.draft.import_payload["items"][0]
    assert item["name"] == "新牛奶"
    assert item["quantity"] == 3
    assert item["unit"] == "盒"
    assert item["purchase_date"] == "2026-04-01"
    assert item["expiry_date"] == "2026-04-08"
    assert item["confidence"] == 0.72
    assert item["selected"] is True
    assert dialog.dismiss_called is True
    assert renders


def test_edit_dialog_inputs_are_prefilled_from_recognized_values():
    screen = build_screen()

    name_input = screen._create_prefilled_text_input("盒马烘焙三明治", hint_text="物品名称")
    quantity_input = screen._create_prefilled_text_input(2, hint_text="数量")
    empty_input = screen._create_prefilled_text_input(None, hint_text="过期日期")

    assert name_input.text == "盒马烘焙三明治"
    assert quantity_input.text == "2"
    assert empty_input.text == ""


def test_wiki_match_display_distinguishes_raw_name_and_wiki_class():
    screen = build_screen()

    display = screen._format_wiki_match_display(
        {
            "name": "进口香蕉 700g/份",
            "wiki_name": "香蕉",
            "wiki_match_type": "contains",
        }
    )

    assert display == "归属 Wiki：香蕉（名称归并）"
    assert screen._format_wiki_match_display({}) == "归属 Wiki：未匹配，导入时会新建"


def test_centered_icon_box_anchors_md_icon():
    screen = build_screen()

    icon_box = screen._create_centered_icon_box(
        icon="image-outline",
        icon_color=(0, 0, 0, 1),
        icon_size=20,
        box_size=42,
        radius=12,
        bg_color=(1, 1, 1, 1),
    )
    icon_widget = icon_box.children[0]

    assert isinstance(icon_box, AnchorLayout)
    assert icon_box.anchor_x == "center"
    assert icon_box.anchor_y == "center"
    assert icon_box.size_hint_y == 1
    assert isinstance(icon_widget, MDIcon)
    assert icon_widget.size_hint == [None, None]
    assert icon_widget.width > icon_widget.font_size
    assert icon_widget.height > icon_widget.font_size
    assert icon_widget.width <= icon_box.width
    assert icon_widget.halign == "center"
    assert icon_widget.valign == "middle"
    assert icon_widget.text_size == icon_widget.size
    assert screen._icon_drawable_size(30, 48) == 42


def test_wiki_selector_value_and_auto_clear():
    screen = build_screen()
    row, wiki_button = screen._create_wiki_selector(
        "香蕉",
        name_getter=lambda: "进口香蕉",
        category_getter=lambda: "食品",
        unit_getter=lambda: "份",
    )
    auto_button = next(child for child in row.children if child.text == "自动")

    assert wiki_button.text == "香蕉"
    assert screen._wiki_button_value(wiki_button) == "香蕉"

    auto_button.dispatch("on_release")

    assert wiki_button.text == "自动匹配 / 选择 Wiki"
    assert screen._wiki_button_value(wiki_button) == ""


def test_wiki_selector_result_format_includes_useful_metadata():
    screen = build_screen()

    assert (
        screen._format_wiki_selector_option(
            {
                "name": "香蕉",
                "category_name": "食品",
                "default_unit": "根",
                "suggested_expiry_days": 3,
            }
        )
        == "香蕉  ·  食品 / 根 / 3天"
    )


def test_create_wiki_from_selector_uses_category_and_unit(monkeypatch):
    screen = build_screen()
    created = {}
    monkeypatch.setattr(
        "app.ui.screens.order_import_screen.wiki_service.get_wiki_by_name",
        lambda _name: None,
    )
    monkeypatch.setattr(
        "app.ui.screens.order_import_screen.wiki_service.get_all_categories",
        lambda: [SimpleNamespace(name="食品", id="cat-food")],
    )
    def fake_create_wiki(**kwargs):
        created["kwargs"] = kwargs
        return {"id": "wiki-banana", "name": kwargs["name"]}

    monkeypatch.setattr(
        "app.ui.screens.order_import_screen.wiki_service.create_wiki",
        fake_create_wiki,
    )

    wiki_item = screen._create_wiki_from_selector("香蕉", "食品", "根")

    assert wiki_item["name"] == "香蕉"
    assert created["kwargs"]["category_id"] == "cat-food"
    assert created["kwargs"]["default_unit"] == "根"


def test_load_wiki_selector_results_searches_existing_wikis(monkeypatch):
    screen = build_screen()
    calls = []
    monkeypatch.setattr(
        "app.ui.screens.order_import_screen.wiki_service.search_wikis",
        lambda keyword, limit: calls.append((keyword, limit)) or [{"name": "香蕉"}],
    )

    results = screen._load_wiki_selector_results("香蕉")

    assert results == [{"name": "香蕉"}]
    assert calls == [("香蕉", 30)]


def test_load_wiki_selector_results_shows_all_when_query_is_empty(monkeypatch):
    screen = build_screen()
    calls = []
    monkeypatch.setattr(
        "app.ui.screens.order_import_screen.wiki_service.get_all_wikis",
        lambda limit, include_inventory_count: calls.append(
            (limit, include_inventory_count)
        )
        or [{"name": "香蕉"}, {"name": "牛奶"}],
    )

    results = screen._load_wiki_selector_results("")

    assert results == [{"name": "香蕉"}, {"name": "牛奶"}]
    assert calls == [(50, False)]


def test_wiki_selector_context_explains_all_items_default():
    screen = build_screen()
    _, wiki_button = screen._create_wiki_selector(
        "香蕉",
        name_getter=lambda: "进口香蕉",
        category_getter=lambda: "食品",
        unit_getter=lambda: "份",
    )

    assert (
        screen._format_wiki_selector_context(wiki_button, "进口香蕉")
        == "当前归属：香蕉。清空搜索时显示全部 Wiki。"
    )
    screen._clear_wiki_button(wiki_button)
    assert (
        screen._format_wiki_selector_context(wiki_button, "进口香蕉")
        == "当前识别：进口香蕉。清空搜索时显示全部 Wiki。"
    )


def test_open_edit_dialog_builds_wiki_selector(monkeypatch):
    screen = build_screen()
    screen.draft.load_review_payload(
        {
            "source_app": "盒马",
            "items": [
                {
                    "name": "进口香蕉 700g/份",
                    "wiki_name": "香蕉",
                    "quantity": 1,
                    "unit": "份",
                    "category": "食品",
                    "purchase_date": "2026-04-27",
                    "expiry_date": "2026-04-30",
                    "selected": True,
                    "can_import": True,
                    "confidence": 0.91,
                    "warnings": [],
                }
            ],
        }
    )
    opened = []
    monkeypatch.setattr(
        "app.ui.screens.order_import_screen.ModalView.open",
        lambda dialog: opened.append(dialog),
    )

    screen._open_edit_dialog(0)

    assert opened


def test_edit_date_selector_prefills_and_can_be_cleared():
    screen = build_screen()

    row, date_button = screen._create_edit_date_selector("2026-04-27")
    clear_button = next(child for child in row.children if child.text == "清空")

    assert date_button.text == "2026-04-27"
    assert screen._edit_date_button_value(date_button) == "2026-04-27"

    clear_button.dispatch("on_release")

    assert date_button.text == "点击选择日期"
    assert screen._edit_date_button_value(date_button) == ""


def test_edit_date_picker_ok_updates_target_button():
    screen = build_screen()
    _, date_button = screen._create_edit_date_selector(None)
    picker = SimpleNamespace(
        date=date(2026, 5, 2),
        dismissed=False,
    )
    picker.dismiss = lambda: setattr(picker, "dismissed", True)

    screen._on_edit_date_ok(picker, target_button=date_button)

    assert date_button.text == "2026-05-02"
    assert picker.dismissed is True


def test_edit_date_picker_cancel_dismisses_picker():
    screen = build_screen()
    picker = SimpleNamespace(dismissed=False)
    picker.dismiss = lambda: setattr(picker, "dismissed", True)

    screen._on_edit_date_cancel(picker)

    assert picker.dismissed is True
    assert screen._edit_date_picker is None


def test_edit_date_picker_falls_back_to_selected_picker_fields():
    screen = build_screen()
    picker = SimpleNamespace(sel_year=2026, sel_month=4, sel_day=30)

    assert screen._date_picker_selected_date(picker) == date(2026, 4, 30)


def test_save_order_metadata_applies_order_time_and_fuzzy_expiry(tmp_path):
    screen = build_screen()
    image_path = tmp_path / "order.jpg"
    image_path.write_bytes(b"fake-image")
    screen.draft.load_review_payload(
        {
            "source_app": "盒马",
            "purchase_date": None,
            "order_time": None,
            "image_path": str(image_path),
            "items": [
                {
                    "name": "盒马烘焙 0酱溏心蛋三明治 170g",
                    "quantity": 1,
                    "unit": "盒",
                    "category": "食品",
                    "purchase_date": None,
                    "expiry_date": None,
                    "selected": True,
                    "can_import": True,
                    "confidence": 0.9,
                    "warnings": [],
                }
            ],
        }
    )
    dialog = DummyDialog()
    renders = []
    screen._render_current_state = lambda: renders.append(True)

    screen._save_order_metadata(
        dialog,
        {
            "purchase_date": None,
            "order_time": "2026-04-27 23:12",
            "order_time_source": "manual",
        },
    )

    assert screen.draft.import_payload["purchase_date"] == "2026-04-27"
    assert screen.draft.import_payload["order_time"] == "2026-04-27 23:12"
    assert screen.draft.import_payload["order_time_source"] == "manual"
    item = screen.draft.import_payload["items"][0]
    assert item["purchase_date"] == "2026-04-27"
    assert item["expiry_date"] == "2026-04-28"
    assert item["expiry_date_source"] == "fuzzy_estimate"
    assert item["selected"] is True
    assert dialog.dismiss_called is True
    assert renders


def test_order_time_display_surfaces_uncertain_source():
    screen = build_screen()
    screen.draft.load_review_payload(
        {
            "source_app": "盒马",
            "purchase_date": "2026-04-27",
            "order_time": "2026-04-27 23:12",
            "order_time_source": "model_time_image_date",
            "items": [],
        }
    )

    assert screen._format_order_time_display() == "2026-04-27 23:12（识别时间+截图日期估算）"


def test_file_picker_prefers_downloads_over_photos_permission_trap(monkeypatch):
    screen = build_screen()
    home = "/Users/example"

    monkeypatch.setattr(
        "app.ui.screens.order_import_screen.os.path.expanduser",
        lambda value: value.replace("~", home),
    )
    monkeypatch.setattr(
        "app.ui.screens.order_import_screen.os.path.isdir",
        lambda value: value == f"{home}/Downloads",
    )

    assert screen._default_file_picker_path() == f"{home}/Downloads"


def test_finish_after_success_resets_draft_and_routes_to_items():
    app = ensure_kivymd_app()
    app.screen_manager = SimpleNamespace(current="order_import")
    screen = build_screen()
    screen.draft.load_review_payload(
        {
            "source_app": "盒马",
            "image_path": "/tmp/order.jpg",
            "items": [
                {
                    "name": "牛奶",
                    "quantity": 1,
                    "unit": "盒",
                    "category": "食品",
                    "selected": True,
                    "can_import": True,
                }
            ],
        }
    )
    dialog = DummyDialog()
    renders = []
    screen._render_current_state = lambda: renders.append(True)

    screen._finish_after_success(dialog)

    assert dialog.dismiss_called is True
    assert screen.draft.view_state == "pick"
    assert screen.draft.image_path == ""
    assert screen.draft.import_payload["items"] == []
    assert app.screen_manager.current == "items"
    assert renders
