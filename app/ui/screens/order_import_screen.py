# -*- coding: utf-8 -*-
"""
订单截图批量导入屏幕
"""

import os
import threading
from typing import Any, Dict, Optional

from kivy.clock import Clock
from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.filechooser import FileChooserListLayout, FileChooserListView
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
from app.ui.screens.add_item_screen import FridgeButton, FridgeTextInput, _bind_label_text
from app.ui.theme.design_tokens import COLOR_PALETTE, get_card_style, get_font_size
from app.utils.font_helper import CHINESE_FONT_NAME as CHINESE_FONT
from app.utils.font_helper import apply_font_to_widget
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

COLORS = COLOR_PALETTE
SECTION_CARD = get_card_style("section")


def _kv_rgba(color_name: str) -> str:
    return ", ".join(str(component) for component in COLORS[color_name])


class FridgeFileChooserListLayout(FileChooserListLayout):
    """Lightweight list layout that matches the app's light modal design."""

    _ENTRY_TEMPLATE = "FridgeFileListEntry"


class FridgeFileChooserListView(FileChooserListView):
    """Styled file chooser used by the order import flow."""


Builder.load_string(
    f"""
<FridgeFileChooserListLayout>:
    on_entry_added: treeview.add_node(args[1])
    on_entries_cleared: treeview.root.nodes = []
    on_subentry_to_entry: not args[2].locked and treeview.add_node(args[1], args[2])
    on_remove_subentry: args[2].nodes = []
    canvas.before:
        Color:
            rgba: {_kv_rgba("surface_variant")}
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(18)]
    canvas.after:
        Color:
            rgba: {_kv_rgba("divider")}
        Line:
            width: dp(1)
            rounded_rectangle: self.x, self.y, self.width, self.height, dp(18)
    ScrollView:
        pos: root.pos
        size: root.size
        size_hint: None, None
        do_scroll_x: False
        bar_width: dp(3)
        Scatter:
            do_rotation: False
            do_scale: False
            do_translation: False
            size: treeview.size
            size_hint_y: None
            TreeView:
                id: treeview
                hide_root: True
                size_hint_y: None
                width: self.parent.parent.width
                height: self.minimum_height
                on_node_expand: root.controller.entry_subselect(args[1])
                on_node_collapse: root.controller.close_subselection(args[1])

<FridgeFileChooserListView>:
    layout: layout
    FridgeFileChooserListLayout:
        id: layout
        controller: root

[FridgeFileListEntry@FloatLayout+TreeViewNode]:
    locked: False
    entries: []
    path: ctx.path
    is_selected: self.path in ctx.controller().selection
    size_hint_y: None
    height: "44dp"
    is_leaf: not ctx.isdir or ctx.name.endswith(".." + ctx.sep) or self.locked
    on_touch_down: self.collide_point(*args[1].pos) and ctx.controller().entry_touched(self, args[1])
    on_touch_up: self.collide_point(*args[1].pos) and ctx.controller().entry_released(self, args[1])
    canvas.before:
        Color:
            rgba: ({_kv_rgba("primary_container")}) if self.is_selected else (0, 0, 0, 0)
        RoundedRectangle:
            pos: self.x + dp(6), self.y + dp(3)
            size: self.width - dp(12), self.height - dp(6)
            radius: [dp(14)]
    BoxLayout:
        pos: root.pos
        size: root.size
        padding: dp(12), 0, dp(12), 0
        spacing: dp(10)
        Image:
            source: "atlas://data/images/defaulttheme/filechooser_%s" % ("folder" if ctx.isdir else "file")
            size_hint_x: None
            width: dp(18)
        Label:
            text: ctx.name
            font_name: ctx.controller().font_name
            color: {_kv_rgba("text_primary")}
            text_size: self.size
            halign: "left"
            valign: "middle"
            shorten: True
        Label:
            text: "" if ctx.isdir else "{{}}".format(ctx.get_nice_size())
            font_name: ctx.controller().font_name
            color: {_kv_rgba("text_secondary")}
            size_hint_x: None
            width: dp(74)
            text_size: self.size
            halign: "right"
            valign: "middle"
"""
)


class OrderImportScreen(Screen):
    """从订单截图导入库存。"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "order_import"
        self.draft = OrderImportDraft()
        self._file_dialog: Optional[ModalView] = None
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
            self.subtitle_label.text = "选择一张订单截图，再进入自动识别。"
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
            subtitle="支持 png、jpg、jpeg、webp、bmp。",
        )
        body.add_widget(
            self._create_hint_box(
                "建议选择订单列表页或结算页截图，商品名、数量和订单日期越清晰，识别结果越稳定。",
                tone="secondary",
            )
        )

        select_btn = FridgeButton(
            text="选择截图文件",
            variant="tonal",
            on_release=self._open_file_dialog,
        )
        body.add_widget(select_btn)

        if self.draft.image_path:
            body.add_widget(self._create_preview_card(self.draft.image_path))

        self.content_layout.add_widget(hero_card)

    def _render_parsing_state(self):
        card, body = self._create_section_card(
            title="正在解析",
            icon="progress-clock",
            subtitle="这一步会读取截图、调用视觉模型并规范化商品条目。",
        )

        icon_shell = BoxLayout(size_hint_y=None, height=dp(88), padding=(0, dp(18), 0, dp(6)))
        icon_shell.add_widget(
            MDIcon(
                icon="text-box-search-outline",
                theme_text_color="Custom",
                text_color=COLORS["secondary"],
                halign="center",
                valign="middle",
                font_size=dp(40),
            )
        )
        body.add_widget(icon_shell)

        progress_text = Label(
            text="正在识别商品名称、数量、订单日期和可推导的保质期线索。",
            size_hint_y=None,
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_medium")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(progress_text)
        progress_text.bind(
            texture_size=lambda inst, val: setattr(inst, "height", max(dp(28), val[1]))
        )
        if CHINESE_FONT:
            progress_text.font_name = CHINESE_FONT
        body.add_widget(progress_text)

        if self.draft.image_path:
            body.add_widget(self._create_preview_card(self.draft.image_path, compact=True))

        self.content_layout.add_widget(card)

    def _render_review_state(self):
        items = self.draft.import_payload.get("items") or []
        selected_count = sum(1 for item in items if item.get("selected"))
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
            size_hint_x=0.38,
            on_release=self._on_back_click,
        )
        parse_btn = FridgeButton(
            text="开始识别",
            variant="primary",
            size_hint_x=0.6,
            on_release=self._on_parse_click,
        )
        self.footer_bar.add_widget(back_btn)
        self.footer_bar.add_widget(parse_btn)

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
        selected_count = sum(
            1 for item in self.draft.import_payload.get("items", []) if item.get("selected")
        )
        commit_btn = FridgeButton(
            text=f"批量导入 ({selected_count})",
            variant="primary",
            size_hint_x=0.6,
            on_release=self._commit_import,
        )
        self.footer_bar.add_widget(reset_btn)
        self.footer_bar.add_widget(commit_btn)

    def _create_review_item_card(self, index: int, item: Dict[str, Any]) -> MDCard:
        title = item.get("name") or f"条目 {index + 1}"
        card, body = self._create_section_card(
            title=title,
            icon="basket-outline",
            subtitle="已忽略" if not item.get("selected") else "待导入",
        )

        detail_text = (
            f"数量：{item.get('quantity', 1)} {item.get('unit') or ''}\n"
            f"类别：{item.get('category') or '未设置'}\n"
            f"购买日期：{item.get('purchase_date') or '未识别'}\n"
            f"过期日期：{item.get('expiry_date') or '未识别'}\n"
            f"置信度：{(item.get('confidence') or 0) * 100:.0f}%"
        )
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
            texture_size=lambda inst, val: setattr(inst, "height", max(dp(92), val[1]))
        )
        if CHINESE_FONT:
            detail_label.font_name = CHINESE_FONT
        body.add_widget(detail_label)

        warnings = item.get("warnings") or []
        if warnings:
            body.add_widget(
                self._create_hint_box("；".join(warnings), tone="warning")
            )

        action_row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))

        checkbox_shell = BoxLayout(
            orientation="horizontal",
            size_hint_x=0.48,
            spacing=dp(6),
            padding=(0, 0, 0, 0),
        )
        checkbox = MDCheckbox(active=item.get("selected", True), size_hint=(None, None))
        checkbox.bind(
            active=lambda _checkbox, active, row=index: self._toggle_item_selected(
                row, active
            )
        )
        checkbox_shell.add_widget(checkbox)

        checkbox_label = Label(
            text="导入此条" if item.get("can_import") else "名称缺失",
            halign="left",
            valign="middle",
            color=COLORS["text_primary"] if item.get("can_import") else COLORS["error_dark"],
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
        action_row.add_widget(edit_btn)
        body.add_widget(action_row)
        return card

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

    def _create_section_card(self, title: str, icon: str, subtitle: str | None = None):
        card = MDCard(
            size_hint_y=None,
            padding=0,
            radius=[dp(SECTION_CARD["radius"])] * 4,
            style="elevated",
            md_bg_color=COLORS[SECTION_CARD["background"]],
        )
        content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(SECTION_CARD["gap"]),
            padding=dp(SECTION_CARD["padding"]),
        )
        content.bind(minimum_height=content.setter("height"))
        content.bind(height=lambda inst, val: setattr(card, "height", val))

        header = BoxLayout(size_hint_y=None, height=dp(42), spacing=dp(12))
        icon_box = BoxLayout(size_hint=(None, None), width=dp(38), height=dp(38))
        with icon_box.canvas.before:
            Color(*COLORS["primary_container"])
            icon_box._bg = RoundedRectangle(
                pos=icon_box.pos, size=icon_box.size, radius=[dp(12)]
            )
        icon_box.bind(
            pos=lambda inst, _val: setattr(inst._bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(inst._bg, "size", inst.size),
        )
        icon_widget = MDIcon(
            icon=icon,
            halign="center",
            valign="middle",
            font_size=dp(18),
            theme_text_color="Custom",
            text_color=COLORS["primary"],
        )
        icon_box.add_widget(icon_widget)
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

        chooser = FridgeFileChooserListView(
            path=self._default_file_picker_path(),
            filters=[f"*{ext}" for ext in sorted(SUPPORTED_IMAGE_EXTENSIONS)],
            multiselect=False,
            show_hidden=False,
            font_name=CHINESE_FONT or "Roboto",
        )
        chooser.bind(
            path=lambda _chooser, value: setattr(path_label, "text", f"当前目录：{value}")
        )
        path_label.text = f"当前目录：{chooser.path}"
        root.add_widget(chooser)

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
            os.path.expanduser("~/Pictures"),
            os.path.expanduser("~"),
        ):
            if os.path.isdir(candidate):
                return candidate
        return "."

    def _confirm_file_selection(self, dialog: ModalView, selection):
        if not selection:
            self._show_error_dialog("请选择一个图片文件")
            return

        self.draft.select_image(selection[0])
        dialog.dismiss()
        self._file_dialog = None
        self._render_current_state()

    def _on_parse_click(self, _instance):
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
        dialog = ModalView(size_hint=(0.88, None), height=dp(520), auto_dismiss=False)

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
            size_hint=(1, None),
            height=dp(520),
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

        fields = BoxLayout(orientation="vertical", spacing=dp(10))
        name_input = FridgeTextInput(text=item.get("name") or "", hint_text="物品名称")
        quantity_input = FridgeTextInput(
            text=str(item.get("quantity") or 1), hint_text="数量", input_filter="int"
        )
        unit_input = FridgeTextInput(text=item.get("unit") or "", hint_text="单位")
        category_input = FridgeTextInput(
            text=item.get("category") or "", hint_text="类别，例如：食品"
        )
        purchase_input = FridgeTextInput(
            text=item.get("purchase_date") or "", hint_text="购买日期 YYYY-MM-DD"
        )
        expiry_input = FridgeTextInput(
            text=item.get("expiry_date") or "", hint_text="过期日期 YYYY-MM-DD"
        )

        for label_text, widget in (
            ("物品名称", name_input),
            ("数量", quantity_input),
            ("单位", unit_input),
            ("类别", category_input),
            ("购买日期", purchase_input),
            ("过期日期", expiry_input),
        ):
            fields.add_widget(self._create_field_block(label_text, widget))
        root.add_widget(fields)

        root.add_widget(
            self._create_hint_box(
                "日期支持 YYYY-MM-DD；留空则按服务层规则重新回退。",
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
            text="保存修改",
            variant="primary",
            size_hint_x=0.64,
            on_release=lambda _btn: self._save_item_edits(
                dialog,
                index,
                {
                    "name": name_input.text.strip(),
                    "quantity": quantity_input.text.strip() or "1",
                    "unit": unit_input.text.strip(),
                    "category": category_input.text.strip(),
                    "purchase_date": purchase_input.text.strip(),
                    "expiry_date": expiry_input.text.strip(),
                    "selected": item.get("selected", True),
                    "warnings": [],
                },
            ),
        )
        button_row.add_widget(cancel_btn)
        button_row.add_widget(save_btn)
        root.add_widget(button_row)

        dialog.add_widget(root)
        dialog.open()

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
        selected_count = sum(1 for item in payload.get("items", []) if item.get("selected"))
        if selected_count <= 0:
            self._show_error_dialog("当前没有勾选可导入的条目")
            return

        result = order_import_service.commit_import(payload)
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
