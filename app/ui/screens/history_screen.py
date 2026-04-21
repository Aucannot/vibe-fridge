# -*- coding: utf-8 -*-
"""
历史屏幕
"""

from datetime import date

from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivymd.uix.label import MDIcon

from app.services.item_service import item_service
from app.ui.theme.design_tokens import COLOR_PALETTE, get_card_style, get_font_size
from app.utils.font_helper import CHINESE_FONT_NAME as CHINESE_FONT
from app.utils.font_helper import apply_font_to_widget
from app.utils.logger import setup_logger

logger = setup_logger(__name__)

COLORS = COLOR_PALETTE
HERO_CARD = get_card_style("hero")
LIST_CARD = get_card_style("list")


def _bind_label_text(widget, horizontal_padding=0):
    widget.bind(
        size=lambda inst, val: setattr(
            inst, "text_size", (max(0, val[0] - horizontal_padding), None)
        )
    )


class RestoreButton(ButtonBehavior, BoxLayout):
    __events__ = ("on_release",)

    def __init__(self, text="恢复", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint = (None, None)
        self.size = (dp(72), dp(34))
        self.padding = (dp(12), dp(8))
        self._pressed = False
        label = Label(
            text=text,
            halign="center",
            valign="middle",
            font_size=dp(get_font_size("label_medium")),
            color=COLORS["on_primary_container"],
        )
        label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        if CHINESE_FONT:
            label.font_name = CHINESE_FONT
        self.add_widget(label)
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _redraw(self, *_args):
        bg_color = COLORS["surface_tint"] if self._pressed else COLORS["primary_container"]
        radius = dp(16)
        self.canvas.before.clear()
        self.canvas.after.clear()
        with self.canvas.before:
            Color(*bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        with self.canvas.after:
            Color(*COLORS["divider"])
            Line(
                width=dp(1),
                rounded_rectangle=(self.x, self.y, self.width, self.height, radius),
            )

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._pressed = True
            self._redraw()
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        should_dispatch = self._pressed and self.collide_point(*touch.pos)
        self._pressed = False
        self._redraw()
        if should_dispatch:
            self.dispatch("on_release")
            return True
        return super().on_touch_up(touch)

    def on_release(self, *_args):
        pass


class HistoryItemCard(BoxLayout):
    def __init__(self, item_data, on_restore, **kwargs):
        super().__init__(**kwargs)
        self.item_id = str(item_data.id)
        self.item_name = item_data.name
        self.category = (
            item_data.wiki.category.name
            if item_data.wiki and item_data.wiki.category
            else "其他"
        )
        self.expiry_date = (
            item_data.expiry_date.strftime("%Y-%m-%d") if item_data.expiry_date else "无"
        )
        self.quantity = item_data.quantity
        self.status = item_data.status.value
        self.consumed_at = (
            item_data.consumed_at.strftime("%Y-%m-%d %H:%M")
            if item_data.consumed_at
            else None
        )
        self.days_until_expiry = (
            (item_data.expiry_date - date.today()).days if item_data.expiry_date else 0
        )
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(108)
        self.padding = (dp(14), dp(14), dp(14), dp(14))
        self.spacing = dp(12)
        self._build_ui(on_restore)
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _build_ui(self, on_restore):
        icon_shell = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=dp(48),
            height=dp(48),
            padding=dp(10),
        )
        with icon_shell.canvas.before:
            Color(*self._status_bg_color())
            self._icon_bg = RoundedRectangle(
                pos=icon_shell.pos, size=icon_shell.size, radius=[dp(16)]
            )
        icon_shell.bind(
            pos=lambda inst, _val: setattr(self._icon_bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(self._icon_bg, "size", inst.size),
        )
        icon_shell.add_widget(
            MDIcon(
                icon=self._category_icon(),
                theme_text_color="Custom",
                text_color=self._status_text_color(),
                halign="center",
                valign="middle",
                font_size=dp(22),
            )
        )
        self.add_widget(icon_shell)

        text_box = BoxLayout(orientation="vertical", spacing=dp(4))

        name_label = Label(
            text=f"{self.item_name} ×{self.quantity}" if self.quantity > 1 else self.item_name,
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_small")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(name_label)
        if CHINESE_FONT:
            name_label.font_name = CHINESE_FONT
        text_box.add_widget(name_label)

        status_label = Label(
            text=f"{self.category} · {self._status_text()}",
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(status_label)
        if CHINESE_FONT:
            status_label.font_name = CHINESE_FONT
        text_box.add_widget(status_label)

        detail_label = Label(
            text=self._detail_text(),
            halign="left",
            valign="top",
            font_size=dp(get_font_size("body_small")),
            color=self._status_text_color(),
        )
        _bind_label_text(detail_label)
        if CHINESE_FONT:
            detail_label.font_name = CHINESE_FONT
        text_box.add_widget(detail_label)
        self.add_widget(text_box)

        action_box = BoxLayout(
            orientation="vertical",
            size_hint=(None, 1),
            width=dp(76),
            padding=(0, dp(10), 0, dp(10)),
        )
        restore_btn = RestoreButton()
        restore_btn.bind(on_release=lambda *_args: on_restore(self.item_id))
        action_box.add_widget(restore_btn)
        self.add_widget(action_box)

    def _status_bg_color(self):
        return (
            COLORS["success_container"]
            if self.status == "consumed"
            else COLORS["error_container"]
        )

    def _status_text_color(self):
        return COLORS["success"] if self.status == "consumed" else COLORS["error"]

    def _status_text(self):
        return "已食用" if self.status == "consumed" else "已过期"

    def _detail_text(self):
        if self.status == "consumed" and self.consumed_at:
            return f"食用时间：{self.consumed_at}"
        if self.expiry_date != "无":
            return f"过期日期：{self.expiry_date}"
        return "无日期信息"

    def _category_icon(self):
        return {
            "食品": "food-apple",
            "日用品": "home-outline",
            "药品": "medical-bag",
            "化妆品": "lipstick",
            "其他": "package-variant-closed",
        }.get(self.category, "package-variant-closed")

    def _redraw(self, *_args):
        radius = dp(LIST_CARD["radius"])
        self.canvas.before.clear()
        self.canvas.after.clear()
        with self.canvas.before:
            Color(*COLORS["surface"])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        with self.canvas.after:
            Color(*COLORS["divider"])
            Line(
                width=dp(1),
                rounded_rectangle=(self.x, self.y, self.width, self.height, radius),
            )


class HistoryScreen(Screen):
    """历史屏幕 - 显示已食用和已过期的物品"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "history"
        self.item_list_layout = None
        self._consumed_value = None
        self._expired_value = None
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical")
        with root.canvas.before:
            Color(*COLORS["background"])
            self._bg_rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(
            pos=lambda inst, _val: setattr(self._bg_rect, "pos", inst.pos),
            size=lambda inst, _val: setattr(self._bg_rect, "size", inst.size),
        )

        root.add_widget(self._create_header())

        scroll = ScrollView(
            do_scroll_x=False,
            bar_width=dp(3),
            bar_color=(*COLORS["primary"][:3], 0.25),
            bar_inactive_color=(*COLORS["primary"][:3], 0.1),
        )
        content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=(dp(16), dp(14), dp(16), dp(24)),
            spacing=dp(14),
        )
        content.bind(minimum_height=content.setter("height"))

        content.add_widget(self._create_overview_card())

        section_title = Label(
            text="历史记录",
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_medium")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(section_title)
        if CHINESE_FONT:
            section_title.font_name = CHINESE_FONT
        content.add_widget(section_title)

        self.item_list_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(10),
        )
        self.item_list_layout.bind(minimum_height=self.item_list_layout.setter("height"))
        content.add_widget(self.item_list_layout)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _create_header(self):
        header = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(92),
            padding=(dp(20), dp(18), dp(20), dp(12)),
            spacing=dp(2),
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

        title = Label(
            text="历史记录",
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("headline_small")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(title)
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        header.add_widget(title)

        subtitle = Label(
            text="收纳已食用和已过期物品，并提供清晰的恢复入口。",
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_medium")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(subtitle)
        if CHINESE_FONT:
            subtitle.font_name = CHINESE_FONT
        header.add_widget(subtitle)
        return header

    def _create_overview_card(self):
        card = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(146),
            padding=dp(HERO_CARD["padding"]),
            spacing=dp(12),
        )
        with card.canvas.before:
            Color(*COLORS["surface_elevated"])
            self._hero_bg = RoundedRectangle(
                pos=card.pos, size=card.size, radius=[dp(HERO_CARD["radius"])]
            )
        with card.canvas.after:
            Color(*COLORS["divider"])
            self._hero_outline = Line(
                rounded_rectangle=(0, 0, 0, 0, dp(HERO_CARD["radius"])),
                width=dp(1),
            )
        card.bind(pos=self._update_hero_card, size=self._update_hero_card)

        eyebrow = Label(
            text="回收区",
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("label_medium")),
            color=COLORS["secondary"],
        )
        _bind_label_text(eyebrow)
        if CHINESE_FONT:
            eyebrow.font_name = CHINESE_FONT
        card.add_widget(eyebrow)

        headline = Label(
            text="把“已食用”和“已过期”分开统计，并给每条记录显式恢复按钮，避免误触。",
            halign="left",
            valign="top",
            font_size=dp(get_font_size("title_medium")),
            color=COLORS["text_primary"],
            bold=True,
        )
        _bind_label_text(headline)
        if CHINESE_FONT:
            headline.font_name = CHINESE_FONT
        card.add_widget(headline)

        metrics = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(10))
        self._consumed_value = self._metric_chip("已食用 0")
        self._expired_value = self._metric_chip("已过期 0", warn=True)
        metrics.add_widget(self._consumed_value)
        metrics.add_widget(self._expired_value)
        metrics.add_widget(BoxLayout())
        card.add_widget(metrics)
        return card

    def _metric_chip(self, text, warn=False):
        chip = Label(
            text=text,
            size_hint=(None, None),
            width=dp(94),
            height=dp(34),
            halign="center",
            valign="middle",
            font_size=dp(get_font_size("label_medium")),
            color=COLORS["error"] if warn else COLORS["success"],
        )
        chip.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        if CHINESE_FONT:
            chip.font_name = CHINESE_FONT
        with chip.canvas.before:
            Color(*(COLORS["error_container"] if warn else COLORS["success_container"]))
            bg = RoundedRectangle(pos=chip.pos, size=chip.size, radius=[dp(17)])
        chip.bind(
            pos=lambda inst, _val: setattr(bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(bg, "size", inst.size),
        )
        return chip

    def _update_header_divider(self, instance, _value):
        self._header_divider.points = [instance.x, instance.y, instance.right, instance.y]

    def _update_hero_card(self, instance, _value):
        radius = dp(HERO_CARD["radius"])
        self._hero_bg.pos = instance.pos
        self._hero_bg.size = instance.size
        self._hero_outline.rounded_rectangle = (
            instance.x,
            instance.y,
            instance.width,
            instance.height,
            radius,
        )

    def _show_empty_state(self):
        empty_card = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(220),
            padding=(dp(20), dp(28), dp(20), dp(28)),
            spacing=dp(10),
        )
        with empty_card.canvas.before:
            Color(*COLORS["surface"])
            bg = RoundedRectangle(
                pos=empty_card.pos,
                size=empty_card.size,
                radius=[dp(HERO_CARD["radius"])],
            )
        with empty_card.canvas.after:
            Color(*COLORS["divider"])
            outline = Line(
                width=dp(1),
                rounded_rectangle=(0, 0, 0, 0, dp(HERO_CARD["radius"])),
            )
        empty_card.bind(
            pos=lambda inst, _val: setattr(bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(bg, "size", inst.size),
        )
        empty_card.bind(
            pos=lambda inst, _val: setattr(
                outline,
                "rounded_rectangle",
                (inst.x, inst.y, inst.width, inst.height, dp(HERO_CARD["radius"])),
            ),
            size=lambda inst, _val: setattr(
                outline,
                "rounded_rectangle",
                (inst.x, inst.y, inst.width, inst.height, dp(HERO_CARD["radius"])),
            ),
        )
        empty_card.add_widget(
            MDIcon(
                icon="history",
                theme_text_color="Custom",
                text_color=COLORS["text_hint"],
                halign="center",
                valign="middle",
                size_hint_y=None,
                height=dp(56),
                font_size=dp(42),
            )
        )

        title = Label(
            text="暂无历史记录",
            size_hint_y=None,
            height=dp(26),
            halign="center",
            valign="middle",
            font_size=dp(get_font_size("title_medium")),
            bold=True,
            color=COLORS["text_primary"],
        )
        title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        empty_card.add_widget(title)

        subtitle = Label(
            text="已食用或已过期的物品会显示在这里，恢复后会重新回到库存列表。",
            halign="center",
            valign="middle",
            font_size=dp(get_font_size("body_medium")),
            color=COLORS["text_secondary"],
        )
        subtitle.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            subtitle.font_name = CHINESE_FONT
        empty_card.add_widget(subtitle)
        self.item_list_layout.add_widget(empty_card)

    def _load_items(self):
        self.item_list_layout.clear_widgets()
        try:
            items = item_service.get_history_items()
            consumed_count = sum(1 for item in items if item.status.value == "consumed")
            expired_count = max(0, len(items) - consumed_count)
            self._consumed_value.text = f"已食用 {consumed_count}"
            self._expired_value.text = f"已过期 {expired_count}"

            if not items:
                self._show_empty_state()
                return

            for item in items:
                self.item_list_layout.add_widget(
                    HistoryItemCard(item, on_restore=self._on_restore_item)
                )
        except Exception as exc:
            logger.error(f"加载历史物品失败: {exc}")
            self._consumed_value.text = "已食用 0"
            self._expired_value.text = "已过期 0"
            self._show_empty_state()

    def _on_restore_item(self, item_id):
        if item_service.restore_item(str(item_id)):
            logger.info(f"物品已恢复: {item_id}")
            self._load_items()

    def on_enter(self):
        self._load_items()
        if CHINESE_FONT:
            apply_font_to_widget(self, CHINESE_FONT)
