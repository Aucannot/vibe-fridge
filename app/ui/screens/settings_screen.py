# -*- coding: utf-8 -*-
"""
设置屏幕
"""

from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivymd.uix.label import MDIcon

from app.ui.theme.design_tokens import COLOR_PALETTE, get_card_style, get_font_size
from app.utils.font_helper import CHINESE_FONT_NAME as CHINESE_FONT
from app.utils.font_helper import apply_font_to_widget

COLORS = COLOR_PALETTE
SECTION_CARD = get_card_style("section")
LIST_CARD = get_card_style("list")


def _bind_label_text(widget, horizontal_padding=0):
    widget.bind(
        size=lambda inst, val: setattr(
            inst, "text_size", (max(0, val[0] - horizontal_padding), None)
        )
    )


class SettingsSectionHeader(Label):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.size_hint_y = None
        self.height = dp(26)
        self.halign = "left"
        self.valign = "middle"
        self.font_size = dp(get_font_size("label_large"))
        self.color = COLORS["primary"]
        _bind_label_text(self)
        if CHINESE_FONT:
            self.font_name = CHINESE_FONT


class ThemedSwitch(ButtonBehavior, BoxLayout):
    active = BooleanProperty(False)

    def __init__(self, active=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint = (None, None)
        self.size = (dp(56), dp(32))
        self.active = active
        self.bind(pos=self._redraw, size=self._redraw, active=self._redraw)
        self._redraw()

    def _redraw(self, *_args):
        radius = self.height / 2
        inset = dp(3)
        knob_size = self.height - inset * 2
        knob_x = self.right - inset - knob_size if self.active else self.x + inset
        track_color = COLORS["primary"] if self.active else COLORS["surface_variant"]
        border_color = None if self.active else COLORS["divider"]

        self.canvas.before.clear()
        self.canvas.after.clear()
        with self.canvas.before:
            Color(*track_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        with self.canvas.after:
            if border_color:
                Color(*border_color)
                Line(
                    width=dp(1),
                    rounded_rectangle=(self.x, self.y, self.width, self.height, radius),
                )
            Color(*COLORS["surface"])
            RoundedRectangle(
                pos=(knob_x, self.y + inset),
                size=(knob_size, knob_size),
                radius=[knob_size / 2],
            )

    def on_release(self, *_args):
        self.active = not self.active


class SettingsRow(BoxLayout):
    def __init__(self, icon, title, subtitle="", show_switch=False, danger=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(82)
        self.padding = (dp(14), dp(12), dp(14), dp(12))
        self.spacing = dp(12)
        self._danger = danger
        self._build_ui(icon, title, subtitle, show_switch)
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _build_ui(self, icon, title, subtitle, show_switch):
        icon_shell = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=dp(42),
            height=dp(42),
            padding=dp(9),
        )
        with icon_shell.canvas.before:
            Color(
                *(
                    COLORS["error_container"]
                    if self._danger
                    else COLORS["surface_tint"]
                )
            )
            self._icon_bg = RoundedRectangle(
                pos=icon_shell.pos, size=icon_shell.size, radius=[dp(14)]
            )
        icon_shell.bind(
            pos=lambda inst, _val: setattr(self._icon_bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(self._icon_bg, "size", inst.size),
        )
        icon_shell.add_widget(
            MDIcon(
                icon=icon,
                theme_text_color="Custom",
                text_color=COLORS["error"] if self._danger else COLORS["primary"],
                halign="center",
                valign="middle",
                font_size=dp(22),
            )
        )
        self.add_widget(icon_shell)

        text_box = BoxLayout(orientation="vertical", spacing=dp(2))

        title_label = Label(
            text=title,
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_small")),
            bold=True,
            color=COLORS["error"] if self._danger else COLORS["text_primary"],
        )
        _bind_label_text(title_label)
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        text_box.add_widget(title_label)

        if subtitle:
            subtitle_label = Label(
                text=subtitle,
                halign="left",
                valign="top",
                font_size=dp(get_font_size("body_small")),
                color=COLORS["text_secondary"],
            )
            _bind_label_text(subtitle_label)
            if CHINESE_FONT:
                subtitle_label.font_name = CHINESE_FONT
            text_box.add_widget(subtitle_label)

        self.add_widget(text_box)

        if show_switch:
            switch = ThemedSwitch(active=False)
            self.add_widget(switch)
        else:
            chevron = MDIcon(
                icon="chevron-right",
                theme_text_color="Custom",
                text_color=COLORS["text_hint"],
                size_hint=(None, None),
                size=(dp(18), dp(18)),
                font_size=dp(18),
            )
            self.add_widget(chevron)

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


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "settings"
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
            spacing=dp(12),
        )
        content.bind(minimum_height=content.setter("height"))

        self._add_section(
            content,
            "通知与提醒",
            [
                ("bell-ring-outline", "过期提醒", "提前推送即将过期物品", True, False),
                ("cart-outline", "购物提醒", "库存不足时提醒补货", True, False),
            ],
        )
        self._add_section(
            content,
            "显示与阅读",
            [
                ("palette-outline", "主题颜色", "当前主题：fresh utility", False, False),
                ("format-size", "字体大小", "当前使用默认字号", False, False),
            ],
        )
        self._add_section(
            content,
            "数据管理",
            [
                ("cloud-sync-outline", "数据同步", "当前仅保存在本机", False, False),
                ("database-export-outline", "数据备份", "导出本地备份文件", False, False),
                ("restore", "恢复数据", "从备份文件恢复库存和 Wiki", False, False),
            ],
        )
        self._add_section(
            content,
            "关于与支持",
            [
                ("information-outline", "关于 vibe-fridge", "版本 1.0.0", False, False),
                ("lifebuoy", "帮助与反馈", "查看常见问题和支持入口", False, False),
            ],
        )

        danger_header = SettingsSectionHeader("危险操作")
        content.add_widget(danger_header)
        content.add_widget(
            SettingsRow(
                icon="delete-outline",
                title="清除所有数据",
                subtitle="仅保留在显式确认后执行",
                danger=True,
            )
        )

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
            text="设置",
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
            text="管理提醒、显示方式和数据入口。",
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

    def _add_section(self, parent, title, rows):
        parent.add_widget(SettingsSectionHeader(title))
        for icon, row_title, subtitle, show_switch, danger in rows:
            parent.add_widget(
                SettingsRow(
                    icon=icon,
                    title=row_title,
                    subtitle=subtitle,
                    show_switch=show_switch,
                    danger=danger,
                )
            )

    def _update_header_divider(self, instance, _value):
        self._header_divider.points = [instance.x, instance.y, instance.right, instance.y]

    def on_enter(self):
        if CHINESE_FONT:
            apply_font_to_widget(self, CHINESE_FONT)
