# -*- coding: utf-8 -*-
"""
订单截图批量导入屏幕
"""

import copy
import os
import threading
from datetime import date, datetime
from typing import Any, Dict, Optional

from kivy.clock import Clock
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserListView
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.button import MDIconButton
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDIcon
from kivymd.uix.selectioncontrol import MDCheckbox

from app.services.order_import_service import (
    DEFAULT_SOURCE_APP,
    OrderImportDraft,
    SUPPORTED_IMAGE_EXTENSIONS,
    order_import_service,
)
from app.services.wiki_service import wiki_service
from app.ui.screens.add_item_screen import (
    ChineseMDModalDatePicker,
    FridgeButton,
    FridgeTextInput,
    _bind_label_text,
)
from app.ui.theme.design_tokens import COLOR_PALETTE, get_card_style, get_font_size
from app.utils.font_helper import CHINESE_FONT_NAME as CHINESE_FONT
from app.utils.font_helper import apply_font_to_widget
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

COLORS = COLOR_PALETTE
SECTION_CARD = get_card_style("section")
DATE_BUTTON_PLACEHOLDER = "点击选择日期"
WIKI_BUTTON_PLACEHOLDER = "自动匹配 / 选择 Wiki"


class OrderImportScreen(Screen):
    """从订单截图导入库存。"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "order_import"
        self.draft = OrderImportDraft()
        self._file_dialog: Optional[ModalView] = None
        self._edit_date_picker: Optional[ChineseMDModalDatePicker] = None
        self._build_ui()

        try:
            import app.main as main_module

            runtime_font = getattr(main_module, "CHINESE_FONT_NAME", None)
        except Exception:
            runtime_font = None
        if runtime_font:
            apply_font_to_widget(self, runtime_font)

    def _build_ui(self):
        root = BoxLayout(orientation="vertical")
        with root.canvas.before:
            Color(*COLORS["background"])
            self._bg_rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(
            pos=lambda inst, _val: setattr(self._bg_rect, "pos", inst.pos),
            size=lambda inst, _val: setattr(self._bg_rect, "size", inst.size),
        )

        self.header = self._create_header()
        root.add_widget(self.header)

        self.scroll_view = ScrollView(do_scroll_x=False, bar_width=0)
        self.content_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=(dp(16), dp(14), dp(16), dp(20)),
            spacing=dp(14),
        )
        self.content_layout.bind(minimum_height=self.content_layout.setter("height"))
        self.scroll_view.add_widget(self.content_layout)
        root.add_widget(self.scroll_view)

        self.footer_bar = self._create_footer_bar()
        root.add_widget(self.footer_bar)

        self.add_widget(root)
        self._render_current_state()

    def _create_header(self) -> BoxLayout:
        header = BoxLayout(
            size_hint_y=None,
            height=dp(92),
            padding=(dp(12), dp(14), dp(16), dp(14)),
            spacing=dp(8),
        )
        with header.canvas.before:
            Color(*COLORS["surface"])
            self._header_bg = Rectangle(pos=header.pos, size=header.size)
        with header.canvas.after:
            Color(*COLORS["divider"])
            self._header_divider = Line(points=[])
        header.bind(
            pos=lambda inst, _val: setattr(self._header_bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(self._header_bg, "size", inst.size),
        )
        header.bind(pos=self._update_header_divider, size=self._update_header_divider)

        back_btn = MDIconButton(
            icon="arrow-left",
            on_release=self._on_back_click,
            font_name="Roboto",
        )
        header.add_widget(back_btn)

        title_box = BoxLayout(orientation="vertical", spacing=dp(2))
        self.title_label = Label(
            text="订单截图导入",
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("headline_small")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(self.title_label)
        if CHINESE_FONT:
            self.title_label.font_name = CHINESE_FONT
        title_box.add_widget(self.title_label)

        self.subtitle_label = Label(
            text="选择截图，识别后批量确认并导入库存。",
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(self.subtitle_label)
        if CHINESE_FONT:
            self.subtitle_label.font_name = CHINESE_FONT
        title_box.add_widget(self.subtitle_label)
        header.add_widget(title_box)
        return header

    def _create_footer_bar(self) -> BoxLayout:
        bar = BoxLayout(
            size_hint_y=None,
            height=dp(84),
            padding=(dp(16), dp(12), dp(16), dp(16)),
            spacing=dp(10),
        )
        with bar.canvas.before:
            Color(*COLORS["surface"])
            bar._bg = Rectangle(pos=bar.pos, size=bar.size)
        with bar.canvas.after:
            Color(*COLORS["divider"])
            bar._line = Line(points=[])
        bar.bind(
            pos=lambda inst, _val: setattr(inst._bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(inst._bg, "size", inst.size),
        )
        bar.bind(pos=self._update_footer_divider, size=self._update_footer_divider)
        return bar

    def _update_header_divider(self, instance, _value):
        self._header_divider.points = [instance.x, instance.y, instance.right, instance.y]

    def _update_footer_divider(self, instance, _value):
        instance._line.points = [instance.x, instance.top, instance.right, instance.top]

    def _render_current_state(self):
        self.content_layout.clear_widgets()
        self.footer_bar.clear_widgets()

        if self.draft.view_state == "pick":
            self.subtitle_label.text = "点按上传区域，选好截图后会自动开始识别。"
            self._render_pick_state()
            self._render_pick_footer()
            return

        if self.draft.view_state == "parsing":
            self.subtitle_label.text = "正在调用硅基流动解析订单截图。"
            self._render_parsing_state()
            self._render_parsing_footer()
            return

        self.subtitle_label.text = "逐条确认识别结果后，再一次性写入库存。"
        self._render_review_state()
        self._render_review_footer()

    def _render_pick_state(self):
        hero_card, body = self._create_section_card(
            title="选择订单截图",
            icon="image-search-outline",
            subtitle="点按整张卡片，选好后会自动开始识别。",
            interactive=True,
            on_release=self._open_file_dialog,
        )
        body.add_widget(
            self._create_hint_box(
                "建议选择订单列表页或结算页截图，商品名、数量和订单日期越清晰，识别结果越稳定。",
                tone="secondary",
            )
        )

        if self.draft.image_path:
            body.add_widget(self._create_preview_card(self.draft.image_path))

        self.content_layout.add_widget(hero_card)

    def _render_parsing_state(self):
        card, body = self._create_section_card(
            title="正在解析",
            icon="progress-clock",
            subtitle="这一步会读取截图、调用视觉模型并规范化商品条目。",
        )

        status_row = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(72),
            padding=(dp(12), dp(10), dp(12), dp(10)),
            spacing=dp(12),
        )
        with status_row.canvas.before:
            Color(*COLORS["surface_variant"])
            status_row._bg = RoundedRectangle(
                pos=status_row.pos,
                size=status_row.size,
                radius=[dp(14)],
            )
        status_row.bind(
            pos=lambda inst, _val: setattr(inst._bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(inst._bg, "size", inst.size),
        )
        status_row.add_widget(
            self._create_centered_icon_box(
                icon="text-box-search-outline",
                icon_color=COLORS["secondary"],
                icon_size=30,
                box_size=48,
                radius=0,
                bg_color=None,
            )
        )

        progress_text = Label(
            text="正在识别商品名称、数量、订单日期和可推导的保质期线索。",
            size_hint_x=1,
            size_hint_y=None,
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_medium")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(progress_text)
        progress_text.bind(
            texture_size=lambda inst, val: (
                setattr(inst, "height", max(dp(28), val[1])),
                setattr(status_row, "height", max(dp(72), val[1] + dp(20))),
            )
        )
        if CHINESE_FONT:
            progress_text.font_name = CHINESE_FONT
        status_row.add_widget(progress_text)
        body.add_widget(status_row)

        if self.draft.image_path:
            body.add_widget(self._create_preview_card(self.draft.image_path, compact=True))

        self.content_layout.add_widget(card)

    def _render_review_state(self):
        items = self.draft.import_payload.get("items") or []
        selected_count = self.draft.selected_importable_count()
        summary_card, summary_body = self._create_section_card(
            title="订单概览",
            icon="receipt-text-outline",
            subtitle=f"共识别 {len(items)} 条商品，当前选中 {selected_count} 条。",
        )
        summary_body.add_widget(
            self._create_key_value_row(
                "来源应用",
                self.draft.import_payload.get("source_app") or DEFAULT_SOURCE_APP,
            )
        )
        summary_body.add_widget(
            self._create_key_value_row(
                "订单编号",
                self.draft.import_payload.get("source_order_id") or "未识别到订单号",
            )
        )
        summary_body.add_widget(
            self._create_key_value_row(
                "下单日期",
                self.draft.import_payload.get("purchase_date") or "未识别到日期",
            )
        )
        summary_body.add_widget(
            self._create_key_value_row(
                "下单时间",
                self._format_order_time_display(),
            )
        )
        summary_body.add_widget(
            FridgeButton(
                text="编辑下单时间",
                variant="tonal",
                size_hint=(1, None),
                height=dp(44),
                on_release=self._open_order_metadata_dialog,
            )
        )
        if self.draft.import_payload.get("order_time_source") in {
            "image_file_mtime",
            "model_time_image_date",
        }:
            summary_body.add_widget(
                self._create_hint_box(
                    "已用截图时间预估下单时间，用于保质期估算。确认导入即表示接受该估计，也可以先编辑修正。",
                    tone="warning",
                )
            )
        self.content_layout.add_widget(summary_card)

        if not items:
            empty_card, empty_body = self._create_section_card(
                title="没有可确认的商品",
                icon="playlist-remove",
            )
            empty_body.add_widget(
                self._create_hint_box(
                    "截图里没有识别出可导入的商品条目。可以重新选择更清晰的订单截图再试一次。",
                    tone="warning",
                )
            )
            self.content_layout.add_widget(empty_card)
            return

        for index, item in enumerate(items):
            self.content_layout.add_widget(self._create_review_item_card(index, item))

    def _render_pick_footer(self):
        back_btn = FridgeButton(
            text="返回",
            size_hint_x=1,
            on_release=self._on_back_click,
        )
        self.footer_bar.add_widget(back_btn)

    def _render_parsing_footer(self):
        wait_btn = FridgeButton(
            text="处理中…",
            variant="tonal",
            size_hint_x=1,
        )
        self.footer_bar.add_widget(wait_btn)

    def _render_review_footer(self):
        reset_btn = FridgeButton(
            text="重新选择",
            size_hint_x=0.38,
            on_release=self._reset_to_pick,
        )
        selected_count = self.draft.selected_importable_count()
        commit_btn = FridgeButton(
            text=f"批量导入 ({selected_count})",
            variant="primary",
            size_hint_x=0.6,
            on_release=self._commit_import,
        )
        commit_btn.disabled = selected_count <= 0
        self.footer_bar.add_widget(reset_btn)
        self.footer_bar.add_widget(commit_btn)

    def _create_review_item_card(self, index: int, item: Dict[str, Any]) -> MDCard:
        title = item.get("name") or f"条目 {index + 1}"
        is_imported = bool(item.get("imported"))
        can_import = bool(item.get("can_import", True))
        if is_imported:
            subtitle = "已导入"
        elif not can_import:
            subtitle = "不可导入"
        elif not item.get("selected"):
            subtitle = "已忽略"
        else:
            subtitle = "待导入"
        card, body = self._create_section_card(
            title=title,
            icon="basket-outline",
            subtitle=subtitle,
        )

        detail_lines = [
            f"数量：{item.get('quantity', 1)} {item.get('unit') or ''}",
            f"类别：{item.get('category') or '未设置'}",
            f"购买日期：{item.get('purchase_date') or '未识别'}",
            f"过期日期：{item.get('expiry_date') or '未识别'}",
            f"置信度：{(item.get('confidence') or 0) * 100:.0f}%",
        ]
        detail_lines.append(self._format_wiki_match_display(item))
        detail_text = "\n".join(detail_lines)
        detail_label = Label(
            text=detail_text,
            size_hint_y=None,
            halign="left",
            valign="top",
            font_size=dp(get_font_size("body_medium")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(detail_label)
        detail_label.bind(
            texture_size=lambda inst, val: setattr(inst, "height", max(dp(132), val[1]))
        )
        if CHINESE_FONT:
            detail_label.font_name = CHINESE_FONT
        body.add_widget(detail_label)

        warnings = item.get("warnings") or []
        if warnings:
            body.add_widget(
                self._create_hint_box("；".join(warnings), tone="warning")
            )
        if is_imported:
            body.add_widget(
                self._create_hint_box("此条已写入库存，不会再次提交。", tone="secondary")
            )

        action_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))

        checkbox_shell = BoxLayout(
            orientation="horizontal",
            size_hint_x=0.48,
            spacing=dp(6),
            padding=(0, 0, 0, 0),
        )
        checkbox = MDCheckbox(
            active=item.get("selected", True),
            disabled=is_imported or not can_import,
            size_hint=(None, None),
        )
        checkbox.bind(
            active=lambda _checkbox, active, row=index: self._toggle_item_selected(
                row, active
            )
        )
        checkbox_shell.add_widget(checkbox)

        checkbox_label = Label(
            text=(
                "已导入"
                if is_imported
                else ("导入此条" if can_import else "名称缺失")
            ),
            halign="left",
            valign="middle",
            color=(
                COLORS["success_dark"]
                if is_imported
                else (COLORS["text_primary"] if can_import else COLORS["error_dark"])
            ),
            font_size=dp(get_font_size("body_medium")),
        )
        checkbox_label.bind(
            size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1]))
        )
        if CHINESE_FONT:
            checkbox_label.font_name = CHINESE_FONT
        checkbox_shell.add_widget(checkbox_label)
        action_row.add_widget(checkbox_shell)

        edit_btn = FridgeButton(
            text="编辑",
            size_hint_x=0.52,
            on_release=lambda _instance, row=index: self._open_edit_dialog(row),
        )
        edit_btn.disabled = is_imported
        action_row.add_widget(edit_btn)
        body.add_widget(action_row)
        return card

    def _format_wiki_match_display(self, item: Dict[str, Any]) -> str:
        wiki_name = item.get("wiki_name")
        if not wiki_name:
            return "归属 Wiki：未匹配，导入时会新建"

        match_label = {
            "manual": "手动指定",
            "exact": "精确匹配",
            "contains": "名称归并",
            "alias": "别名归并",
            "similar": "相似匹配",
        }.get(item.get("wiki_match_type"), "已匹配")
        return f"归属 Wiki：{wiki_name}（{match_label}）"

    def _create_preview_card(self, image_path: str, compact: bool = False) -> MDCard:
        card, body = self._create_section_card(
            title="已选截图",
            icon="image-outline",
            subtitle=image_path.split("/")[-1],
        )

        image_box = BoxLayout(size_hint_y=None, height=dp(120 if compact else 180))
        with image_box.canvas.before:
            Color(*COLORS["surface_variant"])
            image_box._bg = RoundedRectangle(
                pos=image_box.pos,
                size=image_box.size,
                radius=[dp(14)],
            )
        image_box.bind(
            pos=lambda inst, _val: setattr(inst._bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(inst._bg, "size", inst.size),
        )
        preview = Image(source=image_path, allow_stretch=True, keep_ratio=True)
        image_box.add_widget(preview)
        body.add_widget(image_box)

        path_label = Label(
            text=image_path,
            size_hint_y=None,
            halign="left",
            valign="middle",
            color=COLORS["text_secondary"],
            font_size=dp(get_font_size("body_small")),
        )
        _bind_label_text(path_label)
        path_label.bind(
            texture_size=lambda inst, val: setattr(inst, "height", max(dp(24), val[1]))
        )
        if CHINESE_FONT:
            path_label.font_name = CHINESE_FONT
        body.add_widget(path_label)
        return card

    def _create_section_card(
        self,
        title: str,
        icon: str,
        subtitle: str | None = None,
        interactive: bool = False,
        on_release=None,
    ):
        card = MDCard(
            size_hint_y=None,
            padding=0,
            radius=[dp(SECTION_CARD["radius"])] * 4,
            style="elevated",
            md_bg_color=COLORS[SECTION_CARD["background"]],
        )
        if interactive and on_release is not None:
            card.ripple_behavior = True
            card.bind(on_release=on_release)
        content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(SECTION_CARD["gap"]),
            padding=dp(SECTION_CARD["padding"]),
        )
        content.bind(minimum_height=content.setter("height"))
        content.bind(height=lambda inst, val: setattr(card, "height", val))

        header = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(12))
        icon_box = self._create_centered_icon_box(
            icon=icon,
            icon_color=COLORS["primary"],
            icon_size=18,
            box_size=42,
            radius=12,
            bg_color=COLORS["primary_container"],
        )
        header.add_widget(icon_box)

        text_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(2))
        text_box.bind(minimum_height=text_box.setter("height"))
        title_label = Label(
            text=title,
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_medium")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(title_label)
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        text_box.add_widget(title_label)

        if subtitle:
            subtitle_label = Label(
                text=subtitle,
                size_hint_y=None,
                height=dp(18),
                halign="left",
                valign="middle",
                font_size=dp(get_font_size("body_small")),
                color=COLORS["text_secondary"],
            )
            _bind_label_text(subtitle_label)
            if CHINESE_FONT:
                subtitle_label.font_name = CHINESE_FONT
            text_box.add_widget(subtitle_label)

        header.add_widget(text_box)
        content.add_widget(header)

        body = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(12))
        body.bind(minimum_height=body.setter("height"))
        content.add_widget(body)
        card.add_widget(content)
        card._content = content
        self._apply_card_outline(card, SECTION_CARD["radius"])
        return card, body

    def _create_centered_icon_box(
        self,
        icon: str,
        icon_color,
        icon_size: int,
        box_size: int,
        radius: int = 0,
        bg_color=None,
    ) -> AnchorLayout:
        box = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint=(None, 1),
            width=dp(box_size),
            height=dp(box_size),
        )
        if bg_color is not None:
            with box.canvas.before:
                Color(*bg_color)
                box._bg = RoundedRectangle(
                    pos=box.pos,
                    size=box.size,
                    radius=[dp(radius)],
                )
            box.bind(
                pos=lambda inst, _val: setattr(inst._bg, "pos", inst.pos),
                size=lambda inst, _val: setattr(inst._bg, "size", inst.size),
            )

        icon_widget = MDIcon(
            icon=icon,
            size_hint=(None, None),
            width=dp(self._icon_drawable_size(icon_size, box_size)),
            height=dp(self._icon_drawable_size(icon_size, box_size)),
            theme_text_color="Custom",
            text_color=icon_color,
            halign="center",
            valign="middle",
            font_size=dp(icon_size),
        )
        icon_widget.text_size = icon_widget.size
        icon_widget.bind(size=lambda inst, value: setattr(inst, "text_size", value))
        box.add_widget(icon_widget)
        return box

    def _icon_drawable_size(self, icon_size: int, box_size: int) -> int:
        return min(box_size, max(icon_size + 12, int(icon_size * 1.35)))

    def _apply_card_outline(self, widget, radius: int):
        with widget.canvas.after:
            Color(*COLORS["divider"])
            widget._outline = Line(
                width=dp(1), rounded_rectangle=(0, 0, 0, 0, dp(radius))
            )

        def _update_outline(instance, _value):
            widget._outline.rounded_rectangle = (
                instance.x,
                instance.y,
                instance.width,
                instance.height,
                dp(radius),
            )

        widget.bind(pos=_update_outline, size=_update_outline)
        _update_outline(widget, None)

    def _create_hint_box(self, text: str, tone: str = "secondary") -> BoxLayout:
        container = BoxLayout(size_hint_y=None, padding=(dp(12), dp(10), dp(12), dp(10)))
        fill = COLORS["info_container"] if tone == "secondary" else COLORS["warning_container"]
        text_color = COLORS["secondary_dark"] if tone == "secondary" else COLORS["warning_dark"]
        with container.canvas.before:
            Color(*fill)
            container._bg = RoundedRectangle(
                pos=container.pos, size=container.size, radius=[dp(14)]
            )
        container.bind(
            pos=lambda inst, _val: setattr(inst._bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(inst._bg, "size", inst.size),
        )
        hint = Label(
            text=text,
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=text_color,
            size_hint_y=None,
        )
        _bind_label_text(hint)
        hint.bind(
            texture_size=lambda inst, val: setattr(container, "height", max(dp(44), val[1] + dp(20)))
        )
        if CHINESE_FONT:
            hint.font_name = CHINESE_FONT
        container.add_widget(hint)
        return container

    def _create_key_value_row(self, key: str, value: str) -> BoxLayout:
        row = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(12))
        key_label = Label(
            text=key,
            size_hint_x=0.34,
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_medium")),
            color=COLORS["text_secondary"],
        )
        value_label = Label(
            text=value,
            size_hint_x=0.66,
            halign="right",
            valign="middle",
            font_size=dp(get_font_size("body_medium")),
            color=COLORS["text_primary"],
        )
        key_label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        value_label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        if CHINESE_FONT:
            key_label.font_name = CHINESE_FONT
            value_label.font_name = CHINESE_FONT
        row.add_widget(key_label)
        row.add_widget(value_label)
        return row

    def _format_order_time_display(self) -> str:
        order_time = self.draft.import_payload.get("order_time")
        if not order_time:
            return "未识别，可编辑补充"

        source_label = {
            "model": "模型识别",
            "image_file_mtime": "截图时间估算",
            "model_time_image_date": "识别时间+截图日期估算",
            "manual": "手动填写",
        }.get(self.draft.import_payload.get("order_time_source"), "")
        return f"{order_time}（{source_label}）" if source_label else order_time

    def _open_order_metadata_dialog(self, _instance):
        dialog_height = dp(390)
        dialog = ModalView(
            size_hint=(0.88, None),
            height=dialog_height,
            auto_dismiss=False,
        )
        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
            size_hint=(1, None),
            height=dialog_height,
        )
        self._decorate_modal_panel(root)

        title = Label(
            text="编辑订单时间",
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_large")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(title)
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        root.add_widget(title)

        purchase_row, purchase_button = self._create_edit_date_selector(
            self.draft.import_payload.get("purchase_date")
        )
        order_time_input = FridgeTextInput(
            text=self.draft.import_payload.get("order_time") or "",
            hint_text="YYYY-MM-DD HH:MM 或 HH:MM",
        )
        root.add_widget(self._create_field_block("下单日期", purchase_row))
        root.add_widget(self._create_field_block("下单时间", order_time_input))
        root.add_widget(
            self._create_hint_box(
                "下单日期点开日历选择；可保留截图时间作为估计，订单正文有更准确时间时再修正。",
                tone="secondary",
            )
        )

        button_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        cancel_btn = FridgeButton(
            text="取消",
            size_hint_x=0.36,
            on_release=lambda _btn: dialog.dismiss(),
        )
        save_btn = FridgeButton(
            text="保存时间",
            variant="primary",
            size_hint_x=0.64,
            on_release=lambda _btn: self._save_order_metadata(
                dialog,
                {
                    "purchase_date": self._edit_date_button_value(purchase_button)
                    or None,
                    "order_time": order_time_input.text.strip() or None,
                    "order_time_source": "manual" if order_time_input.text.strip() else None,
                },
            ),
        )
        button_row.add_widget(cancel_btn)
        button_row.add_widget(save_btn)
        root.add_widget(button_row)

        dialog.add_widget(root)
        dialog.open()

    def _save_order_metadata(self, dialog: ModalView, updates: Dict[str, Any]):
        payload = copy.deepcopy(self.draft.import_payload)
        payload.update(updates)
        normalized_payload = order_import_service._normalize_import_payload(
            payload,
            image_path=payload.get("image_path") or self.draft.image_path,
        )
        if updates.get("order_time"):
            normalized_payload["order_time_source"] = "manual"
        self.draft.load_review_payload(normalized_payload)
        dialog.dismiss()
        self._render_current_state()

    def _open_file_dialog(self, _instance):
        dialog = ModalView(size_hint=(0.92, 0.88), auto_dismiss=False)

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
        )
        self._decorate_modal_panel(root)

        title = Label(
            text="选择订单截图",
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_large")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(title)
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        root.add_widget(title)

        path_label = Label(
            text="",
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(path_label)
        if CHINESE_FONT:
            path_label.font_name = CHINESE_FONT
        root.add_widget(path_label)

        chooser = FileChooserListView(
            path=self._default_file_picker_path(),
            filters=[f"*{ext}" for ext in sorted(SUPPORTED_IMAGE_EXTENSIONS)],
            multiselect=False,
            show_hidden=False,
            font_name=CHINESE_FONT or "Roboto",
        )
        self._configure_file_chooser(chooser)
        chooser.bind(
            path=lambda _chooser, value: setattr(path_label, "text", f"当前目录：{value}")
        )
        path_label.text = f"当前目录：{chooser.path}"
        root.add_widget(self._wrap_file_chooser(chooser))

        button_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        cancel_btn = FridgeButton(
            text="取消",
            size_hint_x=0.36,
            on_release=lambda _btn: dialog.dismiss(),
        )
        confirm_btn = FridgeButton(
            text="使用此文件",
            variant="primary",
            size_hint_x=0.64,
            on_release=lambda _btn: self._confirm_file_selection(dialog, chooser.selection),
        )
        button_row.add_widget(cancel_btn)
        button_row.add_widget(confirm_btn)
        root.add_widget(button_row)

        dialog.add_widget(root)
        dialog.bind(on_dismiss=lambda *_args: setattr(self, "_file_dialog", None))
        dialog.open()
        self._file_dialog = dialog

    def _default_file_picker_path(self) -> str:
        if self.draft.image_path:
            return os.path.dirname(self.draft.image_path)

        for candidate in (
            os.path.expanduser("~/Downloads"),
            os.path.expanduser("~"),
        ):
            if os.path.isdir(candidate):
                return candidate
        return "."

    def _wrap_file_chooser(self, chooser: FileChooserListView) -> BoxLayout:
        shell = BoxLayout(size_hint_y=1, padding=dp(6))
        with shell.canvas.before:
            Color(*COLORS["surface_variant"])
            shell._bg = RoundedRectangle(pos=shell.pos, size=shell.size, radius=[dp(18)])
        with shell.canvas.after:
            Color(*COLORS["divider"])
            shell._outline = Line(width=dp(1), rounded_rectangle=(0, 0, 0, 0, dp(18)))

        def _update_shell(instance, _value):
            instance._bg.pos = instance.pos
            instance._bg.size = instance.size
            instance._outline.rounded_rectangle = (
                instance.x,
                instance.y,
                instance.width,
                instance.height,
                dp(18),
            )

        shell.bind(pos=_update_shell, size=_update_shell)
        shell.add_widget(chooser)
        return shell

    def _configure_file_chooser(self, chooser: FileChooserListView):
        chooser.bind(
            files=lambda *_args: Clock.schedule_once(
                lambda _dt: self._refresh_file_chooser_styles(chooser), 0
            ),
            selection=lambda *_args: Clock.schedule_once(
                lambda _dt: self._refresh_file_chooser_styles(chooser), 0
            ),
            path=lambda *_args: Clock.schedule_once(
                lambda _dt: self._refresh_file_chooser_styles(chooser), 0
            ),
        )
        Clock.schedule_once(lambda _dt: self._refresh_file_chooser_styles(chooser), 0)

    def _refresh_file_chooser_styles(self, chooser: FileChooserListView):
        layout = getattr(chooser, "layout", None)
        if layout is None:
            return

        treeview = layout.ids.get("treeview")
        if treeview is None:
            return

        container = layout.children[0] if layout.children else None
        if container is not None:
            header_row = container.children[-1] if container.children else None
            if header_row is not None:
                header_row.height = 0
                header_row.opacity = 0
                header_row.disabled = True

        for node in treeview.iterate_all_nodes():
            if getattr(treeview, "root", None) is node:
                continue
            node.color_selected = COLORS["primary_container"]
            node.odd_color = COLORS["surface_variant"]
            node.even_color = COLORS["surface_variant"]
            self._apply_file_chooser_text_style(node)

    def _apply_file_chooser_text_style(self, widget):
        for child in widget.children:
            if isinstance(child, Label):
                child.color = (
                    COLORS["text_secondary"]
                    if child.halign == "right"
                    else COLORS["text_primary"]
                )
                if CHINESE_FONT:
                    child.font_name = CHINESE_FONT
            self._apply_file_chooser_text_style(child)

    def _confirm_file_selection(self, dialog: ModalView, selection):
        if not selection:
            self._show_error_dialog("请选择一个图片文件")
            return

        self.draft.select_image(selection[0])
        dialog.dismiss()
        self._file_dialog = None
        self._start_parse_flow()

    def _on_parse_click(self, _instance):
        self._start_parse_flow()

    def _start_parse_flow(self):
        if not self.draft.image_path:
            self._show_error_dialog("请先选择订单截图")
            return

        self.draft.start_parsing()
        self._render_current_state()

        threading.Thread(target=self._parse_in_background, daemon=True).start()

    def _parse_in_background(self):
        try:
            payload = order_import_service.parse_order_screenshot(self.draft.image_path)
        except Exception as exc:
            logger.error(f"订单截图解析失败: {exc}")
            Clock.schedule_once(lambda _dt: self._handle_parse_error(str(exc)), 0)
            return

        Clock.schedule_once(lambda _dt: self._handle_parse_success(payload), 0)

    def _handle_parse_success(self, payload: Dict[str, Any]):
        self.draft.load_review_payload(payload)
        self._render_current_state()

    def _handle_parse_error(self, message: str):
        self.draft.view_state = "pick"
        self._render_current_state()
        self._show_error_dialog(message)

    def _toggle_item_selected(self, index: int, selected: bool):
        self.draft.set_item_selected(index, selected)
        self._render_current_state()

    def _open_edit_dialog(self, index: int):
        item = self.draft.import_payload["items"][index]
        if item.get("imported"):
            self._show_error_dialog("已导入的条目不能再次编辑")
            return
        dialog = ModalView(size_hint=(0.88, 0.86), auto_dismiss=False)

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
            size_hint=(1, 1),
        )
        self._decorate_modal_panel(root)

        title = Label(
            text="编辑识别条目",
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_large")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(title)
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        root.add_widget(title)

        scroll = ScrollView(do_scroll_x=False, bar_width=0, size_hint=(1, 1))
        fields = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(10),
        )
        fields.bind(minimum_height=fields.setter("height"))
        name_input = self._create_prefilled_text_input(
            item.get("name"), hint_text="物品名称"
        )
        quantity_input = self._create_prefilled_text_input(
            item.get("quantity") or 1,
            hint_text="数量",
            input_filter="int",
        )
        unit_input = self._create_prefilled_text_input(item.get("unit"), hint_text="单位")
        category_input = self._create_prefilled_text_input(
            item.get("category"), hint_text="类别，例如：食品"
        )
        wiki_row, wiki_button = self._create_wiki_selector(
            item.get("wiki_name"),
            name_getter=lambda: name_input.text.strip(),
            category_getter=lambda: category_input.text.strip(),
            unit_getter=lambda: unit_input.text.strip(),
        )
        purchase_row, purchase_button = self._create_edit_date_selector(
            item.get("purchase_date")
        )
        expiry_row, expiry_button = self._create_edit_date_selector(
            item.get("expiry_date")
        )

        for label_text, widget in (
            ("物品名称", name_input),
            ("归属 Wiki", wiki_row),
            ("数量", quantity_input),
            ("单位", unit_input),
            ("类别", category_input),
            ("购买日期", purchase_row),
            ("过期日期", expiry_row),
        ):
            fields.add_widget(self._create_field_block(label_text, widget))

        fields.add_widget(
            self._create_hint_box(
                "点击日期字段打开日历；清空后按服务层规则重新回退。",
                tone="secondary",
            )
        )
        fields.add_widget(
            self._create_hint_box(
                "订单商品名可保留完整识别结果；归属 Wiki 用来决定库存目录、默认单位和保质期。",
                tone="secondary",
            )
        )
        scroll.add_widget(fields)
        root.add_widget(scroll)

        button_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        cancel_btn = FridgeButton(
            text="取消",
            size_hint_x=0.36,
            on_release=lambda _btn: dialog.dismiss(),
        )
        save_btn = FridgeButton(
            text="保存修改",
            variant="primary",
            size_hint_x=0.64,
            on_release=lambda _btn: self._save_item_edits(
                dialog,
                index,
                {
                    "name": name_input.text.strip(),
                    "wiki_name": self._wiki_button_value(wiki_button),
                    "quantity": quantity_input.text.strip() or "1",
                    "unit": unit_input.text.strip(),
                    "category": category_input.text.strip(),
                    "purchase_date": self._edit_date_button_value(purchase_button),
                    "expiry_date": self._edit_date_button_value(expiry_button),
                    "selected": item.get("selected", True),
                    "confidence": item.get("confidence", 0.0),
                    "imported": item.get("imported", False),
                    "warnings": [],
                },
            ),
        )
        button_row.add_widget(cancel_btn)
        button_row.add_widget(save_btn)
        root.add_widget(button_row)

        dialog.add_widget(root)
        dialog.open()

    def _create_wiki_selector(
        self,
        value,
        name_getter,
        category_getter,
        unit_getter,
    ) -> tuple[BoxLayout, FridgeButton]:
        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        wiki_button = FridgeButton(
            text=self._format_wiki_button_text(value),
            halign="left",
            size_hint_x=1,
        )
        wiki_button.bind(
            on_release=lambda _btn: self._open_wiki_selector_dialog(
                wiki_button,
                name_getter=name_getter,
                category_getter=category_getter,
                unit_getter=unit_getter,
            )
        )
        auto_button = FridgeButton(
            text="自动",
            size_hint_x=None,
            width=dp(70),
            on_release=lambda _btn: self._clear_wiki_button(wiki_button),
        )
        row.add_widget(wiki_button)
        row.add_widget(auto_button)
        return row, wiki_button

    def _format_wiki_button_text(self, value) -> str:
        text = str(value or "").strip()
        return text or WIKI_BUTTON_PLACEHOLDER

    def _wiki_button_value(self, button: FridgeButton) -> str:
        text = (button.text or "").strip()
        if text == WIKI_BUTTON_PLACEHOLDER:
            return ""
        return text

    def _clear_wiki_button(self, button: FridgeButton):
        button.text = WIKI_BUTTON_PLACEHOLDER

    def _open_wiki_selector_dialog(
        self,
        target_button: FridgeButton,
        name_getter,
        category_getter,
        unit_getter,
    ):
        dialog = ModalView(size_hint=(0.9, 0.82), auto_dismiss=False)
        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
            size_hint=(1, 1),
        )
        self._decorate_modal_panel(root)

        title = Label(
            text="选择归属 Wiki",
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_large")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(title)
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        root.add_widget(title)

        query_input = self._create_prefilled_text_input(
            "",
            hint_text="搜索现有 Wiki，或输入新 Wiki 名称",
        )
        root.add_widget(query_input)
        root.add_widget(
            self._create_hint_box(
                self._format_wiki_selector_context(target_button, name_getter()),
                tone="secondary",
            )
        )

        actions = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        search_btn = FridgeButton(text="搜索", size_hint_x=0.34)
        create_btn = FridgeButton(text="新建 Wiki", variant="primary", size_hint_x=0.66)
        actions.add_widget(search_btn)
        actions.add_widget(create_btn)
        root.add_widget(actions)

        result_scroll = ScrollView(do_scroll_x=False, bar_width=0, size_hint=(1, 1))
        result_list = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8),
        )
        result_list.bind(minimum_height=result_list.setter("height"))
        result_scroll.add_widget(result_list)
        root.add_widget(result_scroll)

        footer = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        cancel_btn = FridgeButton(
            text="取消",
            size_hint_x=1,
            on_release=lambda _btn: dialog.dismiss(),
        )
        footer.add_widget(cancel_btn)
        root.add_widget(footer)

        def _select_wiki(wiki_item):
            target_button.text = wiki_item["name"]
            dialog.dismiss()

        def _render_results(_btn=None):
            result_list.clear_widgets()
            query = query_input.text.strip()
            for wiki_item in self._load_wiki_selector_results(query):
                btn = FridgeButton(
                    text=self._format_wiki_selector_option(wiki_item),
                    halign="left",
                    height=dp(56),
                    font_size=dp(get_font_size("body_medium")),
                    on_release=lambda _instance, item=wiki_item: _select_wiki(item),
                )
                result_list.add_widget(btn)

            if not result_list.children:
                result_list.add_widget(
                    self._create_hint_box(
                        "没有匹配的 Wiki。确认名称后可点击上方“新建 Wiki”。",
                        tone="secondary",
                    )
                )

        def _create_wiki(_btn=None):
            wiki_name = query_input.text.strip() or name_getter()
            wiki_item = self._create_wiki_from_selector(
                wiki_name=wiki_name,
                category=category_getter(),
                unit=unit_getter(),
            )
            if not wiki_item:
                self._show_error_dialog("新建 Wiki 失败，请检查名称后重试")
                return
            target_button.text = wiki_item["name"]
            dialog.dismiss()

        search_btn.bind(on_release=_render_results)
        create_btn.bind(on_release=_create_wiki)
        dialog.add_widget(root)
        _render_results()
        dialog.open()

    def _format_wiki_selector_context(
        self,
        target_button: FridgeButton,
        raw_name: str,
    ) -> str:
        selected_wiki = self._wiki_button_value(target_button)
        if selected_wiki:
            return f"当前归属：{selected_wiki}。清空搜索时显示全部 Wiki。"
        raw_name = (raw_name or "").strip()
        if raw_name:
            return f"当前识别：{raw_name}。清空搜索时显示全部 Wiki。"
        return "清空搜索时显示全部 Wiki。"

    def _load_wiki_selector_results(self, query: str) -> list[Dict[str, Any]]:
        keyword = (query or "").strip()
        if keyword:
            return wiki_service.search_wikis(keyword, limit=30)
        return wiki_service.get_all_wikis(limit=50, include_inventory_count=False)

    def _format_wiki_selector_option(self, wiki_item: Dict[str, Any]) -> str:
        parts = [wiki_item.get("name") or "未命名 Wiki"]
        category = wiki_item.get("category_name")
        unit = wiki_item.get("default_unit")
        expiry_days = wiki_item.get("suggested_expiry_days")
        details = [value for value in (category, unit) if value]
        if expiry_days:
            details.append(f"{expiry_days}天")
        if details:
            parts.append(" / ".join(details))
        return "  ·  ".join(parts)

    def _create_wiki_from_selector(
        self,
        wiki_name: str,
        category: str,
        unit: str,
    ) -> Optional[Dict[str, Any]]:
        wiki_name = (wiki_name or "").strip()
        if not wiki_name:
            return None

        existing = wiki_service.get_wiki_by_name(wiki_name)
        if existing:
            return existing

        return wiki_service.create_wiki(
            name=wiki_name,
            default_unit=(unit or "").strip() or None,
            category_id=self._category_id_for_name(category),
        )

    def _category_id_for_name(self, category_name: str) -> Optional[str]:
        category_name = (category_name or "").strip()
        if not category_name:
            return None
        for category in wiki_service.get_all_categories():
            if getattr(category, "name", None) == category_name:
                return getattr(category, "id", None)
        return None

    def _create_prefilled_text_input(self, value, **kwargs) -> FridgeTextInput:
        widget = FridgeTextInput(**kwargs)
        widget.text = "" if value is None else str(value)
        widget.cursor = (len(widget.text), 0)
        return widget

    def _create_edit_date_selector(self, value) -> tuple[BoxLayout, FridgeButton]:
        row = BoxLayout(size_hint_y=None, height=dp(50), spacing=dp(8))
        date_button = FridgeButton(
            text=self._format_edit_date_button_text(value),
            halign="left",
            size_hint_x=1,
        )
        date_button.bind(
            on_release=lambda _btn: self._open_edit_date_picker(date_button)
        )
        clear_button = FridgeButton(
            text="清空",
            size_hint_x=None,
            width=dp(70),
            on_release=lambda _btn: self._clear_edit_date_button(date_button),
        )
        row.add_widget(date_button)
        row.add_widget(clear_button)
        return row, date_button

    def _format_edit_date_button_text(self, value) -> str:
        selected_date = self._coerce_edit_date(value)
        if selected_date is not None:
            return selected_date.strftime("%Y-%m-%d")
        return DATE_BUTTON_PLACEHOLDER

    def _edit_date_button_value(self, button: FridgeButton) -> str:
        text = (button.text or "").strip()
        if text == DATE_BUTTON_PLACEHOLDER:
            return ""
        return text

    def _clear_edit_date_button(self, button: FridgeButton):
        button.text = DATE_BUTTON_PLACEHOLDER

    def _open_edit_date_picker(self, target_button: FridgeButton):
        initial_date = (
            self._coerce_edit_date(self._edit_date_button_value(target_button))
            or date.today()
        )
        picker = ChineseMDModalDatePicker(
            year=initial_date.year,
            month=initial_date.month,
            day=initial_date.day,
        )
        self._edit_date_picker = picker
        picker.bind(
            on_ok=lambda instance, *args, btn=target_button: self._on_edit_date_ok(
                instance,
                *args,
                target_button=btn,
            )
        )
        picker.bind(
            on_cancel=lambda instance, *_args: self._on_edit_date_cancel(instance)
        )
        picker.bind(on_dismiss=lambda *_args: self._clear_active_date_picker())
        self._schedule_edit_date_picker_refresh(picker)
        picker.open()

    def _on_edit_date_ok(
        self,
        picker_instance,
        *args,
        target_button: FridgeButton,
    ):
        selected_date = self._date_picker_selected_date(picker_instance, *args)
        target_button.text = selected_date.strftime("%Y-%m-%d")
        self._dismiss_edit_date_picker(picker_instance)

    def _on_edit_date_cancel(self, picker_instance):
        self._dismiss_edit_date_picker(picker_instance)

    def _dismiss_edit_date_picker(self, picker_instance):
        try:
            picker_instance.dismiss()
        except Exception:
            pass
        self._edit_date_picker = None

    def _date_picker_selected_date(self, picker_instance, *args) -> date:
        selected = args[0] if args else None
        if selected is None:
            for attr in ("date", "sel_date", "current_date"):
                if hasattr(picker_instance, attr):
                    selected = getattr(picker_instance, attr)
                    break
        if selected is None and all(
            hasattr(picker_instance, attr) for attr in ("sel_year", "sel_month", "sel_day")
        ):
            try:
                selected = date(
                    picker_instance.sel_year,
                    picker_instance.sel_month,
                    picker_instance.sel_day,
                )
            except (TypeError, ValueError):
                selected = None

        return self._coerce_edit_date(selected) or date.today()

    def _coerce_edit_date(self, value) -> Optional[date]:
        if value is None:
            return None
        if isinstance(value, datetime):
            return value.date()
        if isinstance(value, date):
            return value

        text = str(value).strip()
        if not text or text == DATE_BUTTON_PLACEHOLDER:
            return None
        for fmt in ("%Y-%m-%d", "%Y-%m-%d %H:%M"):
            try:
                return datetime.strptime(text, fmt).date()
            except ValueError:
                continue
        return None

    def _schedule_edit_date_picker_refresh(self, picker_instance):
        for delay in (0, 0.03, 0.08):
            Clock.schedule_once(
                lambda *_args, inst=picker_instance: self._configure_edit_date_picker(
                    inst
                ),
                delay,
            )

    def _configure_edit_date_picker(self, picker_instance):
        try:
            picker_instance.supporting_text = "选择日期"
            picker_instance.text_button_ok = "确定"
            picker_instance.text_button_cancel = "取消"
            if CHINESE_FONT:
                apply_font_to_widget(picker_instance, CHINESE_FONT)
        except Exception:
            pass

    def _clear_active_date_picker(self):
        self._edit_date_picker = None

    def _create_field_block(self, title: str, widget) -> BoxLayout:
        block = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        block.bind(minimum_height=block.setter("height"))
        label = Label(
            text=title,
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("label_large")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(label)
        if CHINESE_FONT:
            label.font_name = CHINESE_FONT
        block.add_widget(label)
        block.add_widget(widget)
        return block

    def _save_item_edits(self, dialog: ModalView, index: int, updates: Dict[str, Any]):
        default_purchase_date = self.draft.import_payload.get("purchase_date")
        normalized_item = order_import_service.normalize_review_item(
            updates,
            default_purchase_date=default_purchase_date,
        )
        self.draft.update_item(index, normalized_item)
        dialog.dismiss()
        self._render_current_state()

    def _commit_import(self, _instance):
        payload = self.draft.build_commit_payload()
        selected_count = self.draft.selected_importable_count()
        if selected_count <= 0:
            self._show_error_dialog("当前没有勾选可导入的条目")
            return

        result = order_import_service.commit_import(payload)
        self.draft.mark_created_rows(result.get("created_rows", []))
        self._render_current_state()
        self._show_success_dialog(result)

    def _show_error_dialog(self, message: str):
        dialog = ModalView(size_hint=(0.82, None), height=dp(212), auto_dismiss=True)

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(16),
            size_hint=(1, None),
            height=dp(212),
        )
        self._decorate_modal_panel(root)

        title_label = Label(
            text="导入失败",
            size_hint_y=None,
            height=dp(30),
            halign="left",
            valign="middle",
            color=COLORS["error_dark"],
            bold=True,
        )
        msg_label = Label(
            text=message,
            size_hint_y=1,
            halign="left",
            valign="top",
            color=COLORS["text_secondary"],
            font_size=dp(get_font_size("body_medium")),
        )
        _bind_label_text(title_label)
        msg_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
            msg_label.font_name = CHINESE_FONT

        root.add_widget(title_label)
        root.add_widget(msg_label)
        root.add_widget(
            FridgeButton(
                text="知道了",
                size_hint=(1, None),
                height=dp(44),
                on_release=lambda _btn: dialog.dismiss(),
            )
        )
        dialog.add_widget(root)
        dialog.open()

    def _show_success_dialog(self, result: Dict[str, Any]):
        failed_rows = result.get("failed_rows") or []
        failure_text = (
            "；".join(
                f"第{row['row']}条 {row.get('name', '')}: {row.get('reason', '')}"
                for row in failed_rows[:3]
            )
            if failed_rows
            else "无失败条目"
        )
        message = (
            f"成功导入 {result.get('created_count', 0)} 条，"
            f"跳过 {result.get('skipped_count', 0)} 条，"
            f"失败 {len(failed_rows)} 条。\n{failure_text}"
        )

        dialog = ModalView(size_hint=(0.84, None), height=dp(260), auto_dismiss=True)
        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(16),
            size_hint=(1, None),
            height=dp(260),
        )
        self._decorate_modal_panel(root)

        title_label = Label(
            text="导入完成",
            size_hint_y=None,
            height=dp(30),
            halign="left",
            valign="middle",
            color=COLORS["success_dark"],
            bold=True,
        )
        msg_label = Label(
            text=message,
            size_hint_y=1,
            halign="left",
            valign="top",
            color=COLORS["text_secondary"],
            font_size=dp(get_font_size("body_medium")),
        )
        _bind_label_text(title_label)
        msg_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
            msg_label.font_name = CHINESE_FONT

        root.add_widget(title_label)
        root.add_widget(msg_label)

        button_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        stay_btn = FridgeButton(
            text="留在此页",
            size_hint_x=0.4,
            on_release=lambda _btn: dialog.dismiss(),
        )
        items_btn = FridgeButton(
            text="去看库存",
            variant="primary",
            size_hint_x=0.6,
            on_release=lambda _btn: self._finish_after_success(dialog),
        )
        button_row.add_widget(stay_btn)
        button_row.add_widget(items_btn)
        root.add_widget(button_row)
        dialog.add_widget(root)
        dialog.open()

    def _finish_after_success(self, dialog: ModalView):
        dialog.dismiss()
        self.draft.reset()
        self._render_current_state()
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            app.screen_manager.current = "items"

    def _decorate_modal_panel(self, widget):
        with widget.canvas.before:
            Color(*COLORS["surface"])
            widget._modal_bg = RoundedRectangle(
                pos=widget.pos, size=widget.size, radius=[dp(20)]
            )
        with widget.canvas.after:
            Color(*COLORS["divider"])
            widget._modal_outline = Line(
                width=dp(1), rounded_rectangle=(0, 0, 0, 0, dp(20))
            )

        def _update_panel(instance, _value):
            instance._modal_bg.pos = instance.pos
            instance._modal_bg.size = instance.size
            instance._modal_outline.rounded_rectangle = (
                instance.x,
                instance.y,
                instance.width,
                instance.height,
                dp(20),
            )

        widget.bind(pos=_update_panel, size=_update_panel)
        _update_panel(widget, None)

    def _reset_to_pick(self, _instance):
        self.draft.reset()
        self._render_current_state()

    def _on_back_click(self, _instance):
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            app.screen_manager.current = "add_entry"

    def on_enter(self):
        if self.draft.view_state == "pick" and self._file_dialog is not None:
            try:
                self._file_dialog.dismiss()
            except Exception:
                pass
            self._file_dialog = None
        self._render_current_state()

    def on_leave(self):
        if self._file_dialog is not None:
            try:
                self._file_dialog.dismiss()
            except Exception:
                pass
            self._file_dialog = None
