# -*- coding: utf-8 -*-
"""
物品详情屏幕 - 显示物品详细信息和管理功能
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.modalview import ModalView
from kivy.uix.floatlayout import FloatLayout
from kivy.metrics import dp
from kivy.properties import (
    StringProperty, NumericProperty, ObjectProperty, ListProperty
)
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.label import MDIcon
from kivymd.uix.list import (
    MDList, MDListItem,
    MDListItemLeadingIcon,
    MDListItemHeadlineText
)
from datetime import date, datetime
import os

from app.services.item_service import item_service
from app.services.wiki_service import wiki_service
from app.models.item import ItemStatus
from app.utils.logger import setup_logger
from app.utils.font_helper import apply_font_to_widget, CHINESE_FONT_NAME as CHINESE_FONT
from app.ui.theme.design_tokens import COLOR_PALETTE, get_card_style, get_font_size

logger = setup_logger(__name__)
COLORS = COLOR_PALETTE
SECTION_CARD = get_card_style("section")


def _bind_label_text(widget, horizontal_padding=0):
    widget.bind(
        size=lambda inst, val: setattr(
            inst, "text_size", (max(0, val[0] - horizontal_padding), None)
        )
    )


def _bind_auto_height(widget, min_height, horizontal_padding=0):
    _bind_label_text(widget, horizontal_padding)
    widget.bind(
        texture_size=lambda inst, val: setattr(inst, "height", max(min_height, val[1]))
    )


class DetailButton(Button):
    """Rounded action button aligned with the refreshed design system."""

    def __init__(self, variant="secondary", radius=14, **kwargs):
        self.variant = variant
        self._pressed = False
        self._radius = dp(radius)
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(48))
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("font_size", dp(get_font_size("label_large")))
        super().__init__(**kwargs)
        self.valign = "middle"
        if CHINESE_FONT:
            self.font_name = CHINESE_FONT
        self.bind(pos=self._redraw, size=self._redraw)
        self.bind(size=self._update_text_size)
        self._update_text_size()
        self._redraw()

    def _palette(self):
        if self.variant == "primary":
            return COLORS["primary"], None, COLORS["on_primary"]
        if self.variant == "danger":
            return COLORS["error_container"], COLORS["error"], COLORS["error_dark"]
        if self.variant == "tonal":
            return COLORS["primary_container"], None, COLORS["on_primary_container"]
        return COLORS["surface_variant"], COLORS["divider"], COLORS["text_primary"]

    def _update_text_size(self, *_args):
        self.text_size = (max(0, self.width - dp(20)), self.height)

    def _redraw(self, *_args):
        fill, border, text_color = self._palette()
        current_fill = (
            (fill[0] * 0.95, fill[1] * 0.95, fill[2] * 0.95, fill[3]) if self._pressed else fill
        )
        self.color = text_color
        self.canvas.before.clear()
        self.canvas.after.clear()
        with self.canvas.before:
            Color(*current_fill)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])
        if border:
            with self.canvas.after:
                Color(*border)
                Line(
                    width=dp(1),
                    rounded_rectangle=(self.x, self.y, self.width, self.height, self._radius),
                )

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._pressed = True
            self._redraw()
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._pressed:
            self._pressed = False
            self._redraw()
        return super().on_touch_up(touch)


class ItemDetailScreen(Screen):
    """物品详情屏幕"""

    # 属性绑定
    item_id = StringProperty("")
    item_name = StringProperty("")
    item_category = StringProperty("")
    item_description = StringProperty("")
    item_quantity = NumericProperty(1)
    item_unit = StringProperty("")
    purchase_date = StringProperty("")
    expiry_date = StringProperty("")
    days_until_expiry = NumericProperty(0)
    reminder_date = StringProperty("")
    status = StringProperty("")
    predicted_expiry_date = StringProperty("")
    prediction_confidence = NumericProperty(0.0)
    source_info = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'item_detail'
        self.current_item = None
        self._build_ui()

        # 绑定属性变化
        self.bind(
            item_id=self._on_item_id_changed,
            item_name=self._on_item_data_changed
        )

    def _build_ui(self):
        """构建UI界面"""
        main_layout = BoxLayout(orientation='vertical')
        with main_layout.canvas.before:
            Color(*COLORS["background"])
            self.bg_rect = Rectangle(pos=main_layout.pos, size=main_layout.size)

        def update_bg_rect(instance, _value):
            self.bg_rect.pos = instance.pos
            self.bg_rect.size = instance.size

        main_layout.bind(pos=update_bg_rect, size=update_bg_rect)

        main_layout.add_widget(self._create_header())
        main_layout.add_widget(self._create_content())
        main_layout.add_widget(self._create_action_bar())

        self.add_widget(main_layout)

    def _create_header(self) -> BoxLayout:
        """创建头部栏"""
        header = BoxLayout(
            size_hint_y=None,
            height=dp(88),
            padding=(dp(12), dp(14), dp(16), dp(14)),
            spacing=dp(10),
        )
        with header.canvas.before:
            Color(*COLORS["surface"])
            self.header_bg_rect = Rectangle(pos=header.pos, size=header.size)
        with header.canvas.after:
            Color(*COLORS["divider"])
            self.header_divider = Line(points=[])
        header.bind(
            pos=lambda inst, _val: setattr(self.header_bg_rect, "pos", inst.pos),
            size=lambda inst, _val: setattr(self.header_bg_rect, "size", inst.size),
        )
        header.bind(pos=self._update_header_divider, size=self._update_header_divider)

        back_btn = MDIconButton(
            icon="arrow-left",
            on_release=self._on_back_click,
        )
        try:
            back_btn.icon_color = COLORS["text_primary"]
        except Exception:
            pass
        header.add_widget(back_btn)

        title_box = BoxLayout(orientation="vertical", spacing=dp(2))
        self.title_label = Label(
            text="物品详情",
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("headline_small")),
            color=COLORS["text_primary"],
            bold=True,
        )
        _bind_label_text(self.title_label)
        if CHINESE_FONT:
            self.title_label.font_name = CHINESE_FONT
        title_box.add_widget(self.title_label)

        self.header_subtitle = Label(
            text="查看库存记录、日期信息和状态提示",
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(self.header_subtitle)
        if CHINESE_FONT:
            self.header_subtitle.font_name = CHINESE_FONT
        title_box.add_widget(self.header_subtitle)
        header.add_widget(title_box)

        edit_btn = MDIconButton(
            icon="pencil",
            on_release=self._on_edit_click,
            font_name="Roboto",
        )
        try:
            edit_btn.icon_color = COLORS["primary"]
        except Exception:
            pass
        header.add_widget(edit_btn)

        return header

    def _create_content(self) -> ScrollView:
        """创建内容区域"""
        scroll_view = ScrollView(do_scroll_x=False, bar_width=0)
        with scroll_view.canvas.before:
            Color(*COLORS["background"])
            scroll_bg_rect = Rectangle(pos=scroll_view.pos, size=scroll_view.size)

        def update_scroll_bg(instance, _value):
            scroll_bg_rect.pos = instance.pos
            scroll_bg_rect.size = instance.size

        scroll_view.bind(pos=update_scroll_bg, size=update_scroll_bg)

        content_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            padding=dp(16),
            spacing=dp(14)
        )
        content_layout.bind(minimum_height=content_layout.setter('height'))

        content_layout.add_widget(self._create_basic_info_card())
        content_layout.add_widget(self._create_quantity_card())
        content_layout.add_widget(self._create_date_card())
        self.ai_card = self._create_ai_card()
        content_layout.add_widget(self.ai_card)
        self.source_card = self._create_source_card()
        content_layout.add_widget(self.source_card)
        self.tag_card = self._create_tag_card()
        content_layout.add_widget(self.tag_card)
        content_layout.add_widget(BoxLayout(size_hint_y=None, height=dp(8)))

        scroll_view.add_widget(content_layout)
        return scroll_view

    def _update_header_divider(self, instance, _value):
        self.header_divider.points = [instance.x, instance.y, instance.right, instance.y]

    def _create_section_card(self, title: str, icon: str, subtitle: str | None = None):
        card = MDCard(
            size_hint_y=None,
            padding=0,
            radius=[dp(SECTION_CARD["radius"])] * 4,
            style="elevated",
            md_bg_color=COLORS["surface"],
        )
        content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(SECTION_CARD["gap"]),
            padding=dp(SECTION_CARD["padding"]),
        )
        content.bind(minimum_height=content.setter("height"))
        content.bind(height=lambda inst, val: setattr(card, "height", val))

        header = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(12))
        icon_box = FloatLayout(size_hint=(None, None), width=dp(38), height=dp(38))
        with icon_box.canvas.before:
            Color(*COLORS["primary_container"])
            icon_box._bg = RoundedRectangle(pos=icon_box.pos, size=icon_box.size, radius=[dp(12)])
        icon_box.bind(
            pos=lambda inst, _val: setattr(inst._bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(inst._bg, "size", inst.size),
        )
        icon_widget = MDIcon(
            icon=icon,
            size_hint=(None, None),
            size=(dp(18), dp(18)),
            halign="center",
            valign="middle",
            font_size=dp(18),
        )
        icon_widget.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        icon_widget.color = COLORS["primary"]
        icon_box.add_widget(icon_widget)
        icon_box.bind(
            pos=lambda inst, _val: self._position_centered_icon(inst, icon_widget),
            size=lambda inst, _val: self._position_centered_icon(inst, icon_widget),
        )
        icon_widget.bind(size=lambda _inst, _val: self._position_centered_icon(icon_box, icon_widget))
        header.add_widget(icon_box)

        text_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(0))
        text_box.bind(minimum_height=text_box.setter("height"))
        text_box.bind(
            minimum_height=lambda inst, val: setattr(header, "height", max(dp(38), val))
        )
        title_label = Label(
            text=title,
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_medium")),
            color=COLORS["text_primary"],
            bold=True,
        )
        _bind_auto_height(title_label, dp(22))
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        text_box.add_widget(title_label)

        if subtitle:
            text_box.spacing = dp(2)
            subtitle_label = Label(
                text=subtitle,
                size_hint_y=None,
                height=dp(18),
                halign="left",
                valign="top",
                font_size=dp(get_font_size("body_small")),
                color=COLORS["text_secondary"],
            )
            _bind_auto_height(subtitle_label, dp(18))
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
        self._decorate_card(card, SECTION_CARD["radius"])
        return card, body

    def _decorate_card(self, widget, radius):
        with widget.canvas.after:
            Color(*COLORS["divider"])
            widget._outline = Line(width=dp(1), rounded_rectangle=(0, 0, 0, 0, dp(radius)))

        def _update_outline(instance, _value):
            widget._outline.rounded_rectangle = (
                instance.x, instance.y, instance.width, instance.height, dp(radius)
            )

        widget.bind(pos=_update_outline, size=_update_outline)
        _update_outline(widget, None)

    def _position_centered_icon(self, icon_box, icon_widget):
        icon_widget.text_size = icon_widget.size
        icon_widget.pos = (
            icon_box.x + (icon_box.width - icon_widget.width) / 2,
            icon_box.y + (icon_box.height - icon_widget.height) / 2 - dp(1),
        )

    def _create_caption(self, text: str):
        label = Label(
            text=text,
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("label_large")),
            color=COLORS["text_secondary"],
        )
        _bind_auto_height(label, dp(18))
        if CHINESE_FONT:
            label.font_name = CHINESE_FONT
        return label

    def _create_value_block(self, caption: str, value_label: Label):
        block = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        block.bind(minimum_height=block.setter("height"))
        block.add_widget(self._create_caption(caption))
        block.add_widget(value_label)
        return block

    def _create_basic_info_card(self) -> MDCard:
        """创建基本信息卡片"""
        card, body = self._create_section_card(
            "基本信息",
            "information-outline",
        )

        self.name_label = Label(
            text=self.item_name,
            size_hint_y=None,
            height=dp(26),
            halign="left",
            valign="middle",
            bold=True,
            font_size=dp(get_font_size("title_medium")),
            color=COLORS["text_primary"],
        )
        _bind_auto_height(self.name_label, dp(26))
        if CHINESE_FONT:
            self.name_label.font_name = CHINESE_FONT
        body.add_widget(self._create_value_block("名称", self.name_label))

        self.category_label = Label(
            text=self.item_category,
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
            color=COLORS["secondary_dark"],
            font_size=dp(get_font_size("body_medium")),
        )
        _bind_auto_height(self.category_label, dp(22))
        if CHINESE_FONT:
            self.category_label.font_name = CHINESE_FONT
        body.add_widget(self._create_value_block("类别", self.category_label))

        self.description_label = Label(
            text=self.item_description or "无描述",
            size_hint_y=None,
            halign="left",
            valign="top",
            color=COLORS["text_secondary"],
            font_size=dp(get_font_size("body_medium")),
        )
        _bind_label_text(self.description_label)
        self.description_label.bind(
            texture_size=lambda inst, val: setattr(inst, "height", max(dp(24), val[1]))
        )
        if CHINESE_FONT:
            self.description_label.font_name = CHINESE_FONT
        body.add_widget(self._create_value_block("描述", self.description_label))
        return card

    def _create_quantity_card(self) -> MDCard:
        """创建数量信息卡片"""
        card, body = self._create_section_card(
            "库存数量",
            "counter",
        )

        quantity_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
        self.quantity_label = Label(
            text=str(self.item_quantity),
            size_hint=(None, None),
            width=dp(72),
            height=dp(36),
            halign="left",
            valign="middle",
            bold=True,
            font_size=dp(get_font_size("headline_small")),
            color=COLORS["success_dark"],
        )
        _bind_label_text(self.quantity_label)
        if CHINESE_FONT:
            self.quantity_label.font_name = CHINESE_FONT
        quantity_row.add_widget(self.quantity_label)

        self.unit_label = Label(
            text=self.item_unit or "个",
            halign="left",
            valign="middle",
            color=COLORS["text_secondary"],
            font_size=dp(get_font_size("body_medium")),
        )
        _bind_label_text(self.unit_label)
        if CHINESE_FONT:
            self.unit_label.font_name = CHINESE_FONT
        quantity_row.add_widget(self.unit_label)
        body.add_widget(self._create_value_block("数量", quantity_row))
        return card

    def _create_date_card(self) -> MDCard:
        """创建日期信息卡片"""
        card, body = self._create_section_card(
            "日期与提醒",
            "calendar-clock",
        )

        self.purchase_date_label = Label(
            text=self.purchase_date or "未设置",
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
            color=COLORS["text_secondary"],
            font_size=dp(get_font_size("body_medium")),
        )
        _bind_auto_height(self.purchase_date_label, dp(22))
        if CHINESE_FONT:
            self.purchase_date_label.font_name = CHINESE_FONT
        body.add_widget(self._create_value_block("购买日期", self.purchase_date_label))

        self.expiry_date_label = Label(
            text=self.expiry_date or "未设置",
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
            color=self._get_expiry_date_color(),
            font_size=dp(get_font_size("body_medium")),
            bold=self.days_until_expiry <= 3,
        )
        _bind_auto_height(self.expiry_date_label, dp(22))
        if CHINESE_FONT:
            self.expiry_date_label.font_name = CHINESE_FONT
        body.add_widget(self._create_value_block("过期日期", self.expiry_date_label))

        self.expiry_status_label = Label(
            text=self._get_expiry_status_text(),
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
            color=self._get_expiry_status_color(),
            font_size=dp(get_font_size("body_medium")),
            bold=True,
        )
        _bind_auto_height(self.expiry_status_label, dp(22))
        if CHINESE_FONT:
            self.expiry_status_label.font_name = CHINESE_FONT
        body.add_widget(self._create_value_block("过期状态", self.expiry_status_label))

        self.reminder_date_label = Label(
            text=self.reminder_date or "未设置",
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
            color=COLORS["text_secondary"],
            font_size=dp(get_font_size("body_medium")),
        )
        _bind_auto_height(self.reminder_date_label, dp(22))
        if CHINESE_FONT:
            self.reminder_date_label.font_name = CHINESE_FONT
        body.add_widget(self._create_value_block("提醒日期", self.reminder_date_label))
        return card

    def _create_ai_card(self) -> MDCard:
        """创建AI预测卡片"""
        card, self.ai_layout = self._create_section_card(
            "AI 预测信息",
            "sparkles",
        )

        self.ai_content_label = Label(
            text="",
            color=COLORS["text_secondary"],
            halign="left",
            valign="top",
            size_hint_y=None,
            font_size=dp(get_font_size("body_medium")),
        )
        _bind_label_text(self.ai_content_label)
        self.ai_content_label.bind(
            texture_size=lambda inst, val: setattr(inst, "height", max(dp(40), val[1]))
        )
        if CHINESE_FONT:
            self.ai_content_label.font_name = CHINESE_FONT
        self.ai_layout.add_widget(self.ai_content_label)
        card.height = 0
        card.opacity = 0
        return card

    def _create_source_card(self) -> MDCard:
        """创建来源信息卡片"""
        card, self.source_layout = self._create_section_card(
            "来源信息",
            "source-branch",
        )

        self.source_content_label = Label(
            text="",
            color=COLORS["text_secondary"],
            halign="left",
            valign="top",
            size_hint_y=None,
            font_size=dp(get_font_size("body_medium")),
        )
        _bind_label_text(self.source_content_label)
        self.source_content_label.bind(
            texture_size=lambda inst, val: setattr(inst, "height", max(dp(28), val[1]))
        )
        if CHINESE_FONT:
            self.source_content_label.font_name = CHINESE_FONT
        self.source_layout.add_widget(self.source_content_label)
        card.height = 0
        card.opacity = 0
        return card

    def _create_tag_card(self) -> MDCard:
        """创建标签卡片"""
        card, self.tag_layout = self._create_section_card(
            "标签",
            "tag-outline",
        )

        self.tag_content_label = Label(
            text="无标签",
            color=COLORS["text_secondary"],
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(22),
            font_size=dp(get_font_size("body_medium")),
        )
        _bind_auto_height(self.tag_content_label, dp(22))
        if CHINESE_FONT:
            self.tag_content_label.font_name = CHINESE_FONT
        self.tag_layout.add_widget(self.tag_content_label)
        return card

    def _create_action_bar(self) -> BoxLayout:
        """创建底部操作栏"""
        action_bar = BoxLayout(
            size_hint_y=None,
            height=dp(84),
            padding=(dp(16), dp(12), dp(16), dp(16)),
            spacing=dp(10)
        )
        with action_bar.canvas.before:
            Color(*COLORS["surface"])
            action_bar._bg = Rectangle(pos=action_bar.pos, size=action_bar.size)
        with action_bar.canvas.after:
            Color(*COLORS["divider"])
            action_bar._line = Line(points=[])
        action_bar.bind(
            pos=lambda inst, _val: setattr(inst._bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(inst._bg, "size", inst.size),
        )
        action_bar.bind(pos=self._update_action_divider, size=self._update_action_divider)

        delete_btn = DetailButton(
            text="删除",
            variant="danger",
            size_hint_x=0.26,
            on_release=self._on_delete_click,
        )
        action_bar.add_widget(delete_btn)

        increase_btn = DetailButton(
            text="+1",
            variant="tonal",
            size_hint_x=0.18,
            on_release=lambda _x: self._change_quantity(1),
        )
        action_bar.add_widget(increase_btn)

        decrease_btn = DetailButton(
            text="-1",
            size_hint_x=0.18,
            on_release=lambda _x: self._change_quantity(-1),
        )
        action_bar.add_widget(decrease_btn)

        back_btn = DetailButton(
            text="返回",
            variant="primary",
            size_hint_x=0.32,
            on_release=self._on_back_click,
        )
        action_bar.add_widget(back_btn)

        return action_bar

    def _update_action_divider(self, instance, _value):
        instance._line.points = [instance.x, instance.top, instance.right, instance.top]

    def _get_expiry_date_color(self):
        """获取过期日期颜色"""
        if not self.expiry_date:
            return COLORS["text_secondary"]
        elif self.days_until_expiry < 0:
            return COLORS["error"]
        elif self.days_until_expiry <= 3:
            return COLORS["warning"]
        else:
            return COLORS["success"]

    def _get_expiry_status_text(self):
        """获取过期状态文本"""
        if not self.expiry_date:
            return "无过期日期"
        elif self.days_until_expiry < 0:
            return f"已过期 {-self.days_until_expiry} 天"
        elif self.days_until_expiry == 0:
            return "今天过期"
        elif self.days_until_expiry <= 3:
            return f"即将过期 ({self.days_until_expiry}天)"
        else:
            return f"正常 ({self.days_until_expiry}天后)"

    def _get_expiry_status_color(self):
        """获取过期状态颜色"""
        if not self.expiry_date:
            return COLORS["text_secondary"]
        elif self.days_until_expiry < 0:
            return COLORS["error"]
        elif self.days_until_expiry <= 3:
            return COLORS["warning"]
        else:
            return COLORS["success"]

    def _on_item_id_changed(self, instance, value):
        """物品ID变化时调用"""
        if value:
            self._load_item(value)

    def _load_wiki_item(self, item_name: str):
        """加载物品wiki信息"""
        try:
            wiki_item = wiki_service.get_wiki_by_name(item_name)
            if not wiki_item:
                logger.error(f"物品wiki不存在: {item_name}")
                return

            self.item_name = wiki_item['name']
            self.item_category = wiki_item['category_name'] or "其他"
            self.item_description = wiki_item['description'] or ""
            inventory_items = item_service.get_inventory_by_name(item_name)
            total_quantity = sum(item.quantity for item in inventory_items)
            self.item_quantity = total_quantity
            self.item_unit = wiki_item['default_unit'] or "个"
            
            self.source_info = f"共{len(inventory_items)}条库存记录"

            self._update_wiki_ui()

        except Exception as e:
            logger.error(f"加载物品wiki信息失败: {str(e)}")

    def _update_wiki_ui(self):
        """更新wiki信息UI显示"""
        # 更新标题
        self.title_label.text = self.item_name
        if CHINESE_FONT:
            self.title_label.font_name = CHINESE_FONT

        # 更新基本信息
        self.name_label.text = self.item_name
        if CHINESE_FONT:
            self.name_label.font_name = CHINESE_FONT
        self.category_label.text = self.item_category
        if CHINESE_FONT:
            self.category_label.font_name = CHINESE_FONT
        self.description_label.text = self.item_description or "无描述"
        if CHINESE_FONT:
            self.description_label.font_name = CHINESE_FONT

        # 更新数量信息
        self.quantity_label.text = str(self.item_quantity)
        if CHINESE_FONT:
            self.quantity_label.font_name = CHINESE_FONT
        self.unit_label.text = self.item_unit or "个"
        if CHINESE_FONT:
            self.unit_label.font_name = CHINESE_FONT

        # 更新来源信息
        self._update_source_card()

    def _on_item_data_changed(self, instance, value):
        """物品数据变化时调用"""
        if self.current_item:
            self._update_ui()

    def _load_item(self, item_id: str):
        """加载物品数据"""
        try:
            self.current_item = item_service.get_item(item_id)
            if not self.current_item:
                logger.error(f"物品不存在: {item_id}")
                return

            # 更新属性
            self.item_name = self.current_item.name
            self.item_category = self._get_category_text(self.current_item)
            self.item_description = self.current_item.description or ""
            self.item_quantity = self.current_item.quantity
            self.item_unit = self.current_item.unit or ""
            self.purchase_date = self._format_date(self.current_item.purchase_date)
            self.expiry_date = self._format_date(self.current_item.expiry_date)
            self.days_until_expiry = self.current_item.days_until_expiry or 0
            self.reminder_date = self._format_date(self.current_item.reminder_date)
            self.status = self.current_item.status.value
            self.predicted_expiry_date = self._format_date(self.current_item.predicted_expiry_date)
            self.prediction_confidence = self.current_item.prediction_confidence or 0.0

            # 更新来源信息
            if self.current_item.source_app:
                source_parts = [
                    self.current_item.source_app,
                    self.current_item.source_order_id or "无订单号",
                ]
                if self.current_item.source_order_time:
                    source_label = {
                        "model": "订单识别",
                        "image_file_mtime": "截图时间估算",
                        "model_time_image_date": "识别时间+截图日期估算",
                        "manual": "手动确认",
                    }.get(self.current_item.source_order_time_source)
                    time_text = self.current_item.source_order_time.strftime(
                        "%Y-%m-%d %H:%M"
                    )
                    if source_label:
                        time_text = f"{time_text}（{source_label}）"
                    source_parts.append(
                        time_text
                    )
                self.source_info = " - ".join(source_parts)
            else:
                self.source_info = "手动添加"

            # 更新UI
            self._update_ui()

        except Exception as e:
            logger.error(f"加载物品详情失败: {str(e)}")

    def _update_ui(self):
        """更新UI显示"""
        # 更新标题
        self.title_label.text = self.item_name
        if CHINESE_FONT:
            self.title_label.font_name = CHINESE_FONT

        # 更新基本信息
        self.name_label.text = self.item_name
        if CHINESE_FONT:
            self.name_label.font_name = CHINESE_FONT
        self.category_label.text = self.item_category
        if CHINESE_FONT:
            self.category_label.font_name = CHINESE_FONT
        self.description_label.text = self.item_description or "无描述"
        if CHINESE_FONT:
            self.description_label.font_name = CHINESE_FONT

        # 更新数量信息
        self.quantity_label.text = str(self.item_quantity)
        if CHINESE_FONT:
            self.quantity_label.font_name = CHINESE_FONT
        self.unit_label.text = self.item_unit or "个"
        if CHINESE_FONT:
            self.unit_label.font_name = CHINESE_FONT

        # 更新日期信息
        self.purchase_date_label.text = self.purchase_date or "未设置"
        if CHINESE_FONT:
            self.purchase_date_label.font_name = CHINESE_FONT
        self.expiry_date_label.text = self.expiry_date or "未设置"
        if CHINESE_FONT:
            self.expiry_date_label.font_name = CHINESE_FONT
        self.expiry_date_label.color = self._get_expiry_date_color()
        self.expiry_date_label.bold = self.days_until_expiry <= 3

        self.expiry_status_label.text = self._get_expiry_status_text()
        if CHINESE_FONT:
            self.expiry_status_label.font_name = CHINESE_FONT
        self.expiry_status_label.color = self._get_expiry_status_color()

        self.reminder_date_label.text = self.reminder_date or "未设置"
        if CHINESE_FONT:
            self.reminder_date_label.font_name = CHINESE_FONT

        # 更新AI卡片
        self._update_ai_card()

        # 更新来源卡片
        self._update_source_card()

        # 更新标签卡片
        self._update_tag_card()

        # 底部返回按钮无需动态更新

    def _format_date(self, date_obj):
        """格式化日期"""
        if not date_obj:
            return ""
        if isinstance(date_obj, date):
            return date_obj.strftime('%Y-%m-%d')
        return str(date_obj)

    def _get_category_text(self, item):
        """获取类别文本"""
        try:
            if item.wiki and item.wiki.category:
                return item.wiki.category.name
        except Exception:
            pass
        return "其他"

    def _update_ai_card(self):
        """更新AI卡片"""
        if self.predicted_expiry_date:
            confidence_text = f"{self.prediction_confidence*100:.1f}%" if self.prediction_confidence else "未知"
            ai_text = f"预测过期日期: {self.predicted_expiry_date}\n置信度: {confidence_text}"
            self.ai_content_label.text = ai_text
            if CHINESE_FONT:
                self.ai_content_label.font_name = CHINESE_FONT
            self.ai_card.opacity = 1
            Clock.schedule_once(lambda _dt: setattr(self.ai_card, "height", self.ai_card._content.height), 0)
        else:
            self.ai_card.height = dp(0)
            self.ai_card.opacity = 0

    def _update_source_card(self):
        """更新来源卡片"""
        if self.source_info and self.source_info != "手动添加":
            self.source_content_label.text = self.source_info
            if CHINESE_FONT:
                self.source_content_label.font_name = CHINESE_FONT
            self.source_card.opacity = 1
            Clock.schedule_once(lambda _dt: setattr(self.source_card, "height", self.source_card._content.height), 0)
        else:
            self.source_card.height = dp(0)
            self.source_card.opacity = 0

    def _update_tag_card(self):
        """更新标签卡片"""
        if self.current_item and self.current_item.tags:
            tag_names = [tag.name for tag in self.current_item.tags]
            self.tag_content_label.text = ", ".join(tag_names)
            if CHINESE_FONT:
                self.tag_content_label.font_name = CHINESE_FONT
            self.tag_card.height = dp(80)
        else:
            self.tag_content_label.text = "无标签"
            if CHINESE_FONT:
                self.tag_content_label.font_name = CHINESE_FONT
            self.tag_card.height = dp(80)

    def _on_back_click(self, instance):
        """返回按钮点击"""
        app = MDApp.get_running_app()
        if hasattr(app, 'screen_manager'):
            app.screen_manager.current = 'main'

    def _on_edit_click(self, instance):
        """编辑按钮点击"""
        # TODO: 实现编辑功能
        logger.info(f"编辑物品: {self.item_id}")

    def _on_delete_click(self, instance):
        """删除按钮点击"""
        self._show_delete_dialog()

    def _show_delete_dialog(self):
        """显示删除确认对话框（使用 ModalView 适配 KivyMD 2.0）"""
        dialog = ModalView(size_hint=(0.82, None), height=dp(208), auto_dismiss=False)

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(16),
            size_hint=(1, None),
            height=dp(208),
        )
        self._decorate_modal_panel(root)

        title_label = Label(
            text="确认删除",
            size_hint_y=None,
            height=dp(32),
            halign="left",
            valign="middle",
            bold=True,
            color=COLORS["error_dark"],
        )
        _bind_label_text(title_label)
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        root.add_widget(title_label)

        content_label = Label(
            text=f"确定要删除 '{self.item_name}' 吗？",
            size_hint_y=1,
            halign="left",
            valign="top",
            color=COLORS["text_secondary"],
            font_size=dp(get_font_size("body_medium")),
        )
        content_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            content_label.font_name = CHINESE_FONT
        root.add_widget(content_label)

        btn_bar = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(16))

        cancel_btn = DetailButton(text="取消", on_release=lambda _x: dialog.dismiss())
        btn_bar.add_widget(cancel_btn)

        def _on_confirm(instance):
            dialog.dismiss()
            self._confirm_delete(instance)

        confirm_btn = DetailButton(text="确定删除", variant="danger", on_release=_on_confirm)
        btn_bar.add_widget(confirm_btn)

        root.add_widget(btn_bar)

        dialog.add_widget(root)
        self.delete_dialog = dialog
        dialog.open()

    def _decorate_modal_panel(self, widget):
        with widget.canvas.before:
            Color(*COLORS["surface"])
            widget._modal_bg = RoundedRectangle(pos=widget.pos, size=widget.size, radius=[dp(20)])
        with widget.canvas.after:
            Color(*COLORS["divider"])
            widget._modal_outline = Line(width=dp(1), rounded_rectangle=(0, 0, 0, 0, dp(20)))

        def _update_panel(instance, _value):
            instance._modal_bg.pos = instance.pos
            instance._modal_bg.size = instance.size
            instance._modal_outline.rounded_rectangle = (
                instance.x, instance.y, instance.width, instance.height, dp(20)
            )

        widget.bind(pos=_update_panel, size=_update_panel)
        _update_panel(widget, None)

    def _confirm_delete(self, instance):
        """确认删除"""
        try:
            if item_service.delete_item(self.item_id):
                logger.info(f"物品删除成功: {self.item_name}")
                self.delete_dialog.dismiss()
                # 返回主屏幕
                app = MDApp.get_running_app()
                if hasattr(app, 'screen_manager'):
                    app.screen_manager.current = 'main'
            else:
                logger.error(f"物品删除失败: {self.item_id}")
        except Exception as e:
            logger.error(f"删除物品失败: {str(e)}")
            self.delete_dialog.dismiss()

    def _change_quantity(self, delta: int):
        """改变数量"""
        try:
            if item_service.update_item_quantity(self.item_id, delta):
                # 重新加载物品数据
                self._load_item(self.item_id)
        except Exception as e:
            logger.error(f"更新物品数量失败: {str(e)}")

    def _toggle_reminder(self, instance):
        """切换提醒开关"""
        try:
            if self.current_item:
                new_value = not self.current_item.is_reminder_enabled
                if item_service.update_item(self.item_id, is_reminder_enabled=new_value):
                    # 重新加载物品数据
                    self._load_item(self.item_id)
        except Exception as e:
            logger.error(f"切换提醒开关失败: {str(e)}")

    def on_enter(self):
        """进入屏幕时调用"""
        # 如果有传递item_id，加载数据
        app = MDApp.get_running_app()
        if hasattr(app, 'current_item_id'):
            self.item_id = app.current_item_id
        # 每次进入详情页后，为整个详情页重新应用中文字体，避免从其他页面返回后字体被还原
        try:
            import app.main as main_module
            chinese_font = getattr(main_module, "CHINESE_FONT_NAME", None)
        except Exception:
            chinese_font = None
        if chinese_font:
            apply_font_to_widget(self, chinese_font)

    def on_leave(self):
        """离开屏幕时调用"""
        # 清理
        self.item_id = ""
        self.current_item = None


# 测试代码
if __name__ == '__main__':
    from kivy.app import App as KivyApp

    class TestApp(KivyApp):
        def build(self):
            screen = ItemDetailScreen()
            screen.item_id = "test_id"  # 设置测试ID
            return screen

    TestApp().run()
