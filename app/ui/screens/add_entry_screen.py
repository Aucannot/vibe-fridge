# -*- coding: utf-8 -*-
"""
选择添加方式屏幕
"""

from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.label import MDIcon

from app.ui.theme.design_tokens import COLOR_PALETTE, get_card_style, get_font_size
from app.utils.font_helper import CHINESE_FONT_NAME as CHINESE_FONT

COLORS = COLOR_PALETTE
LIST_CARD = get_card_style("list")


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


class EntryActionCard(ButtonBehavior, BoxLayout):
    """Single entry option card."""

    __events__ = ("on_release",)

    def __init__(self, title, subtitle, icon, cta_text, accent, enabled, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(156)
        self.padding = dp(LIST_CARD["padding"])
        self.spacing = dp(14)
        self.enabled = enabled
        self._accent = accent
        self._pressed = False
        self._icon_bg = None
        self._body = None
        self._status_box = None
        self._build_ui(title, subtitle, icon, cta_text)
        self.bind(minimum_height=self._update_height)
        self.bind(pos=self._redraw, size=self._redraw)
        self._update_height()
        self._redraw()

    def _build_ui(self, title, subtitle, icon, cta_text):
        icon_container = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint=(None, 1),
            width=dp(72),
        )
        icon_shell = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=dp(56),
            height=dp(56),
            padding=dp(12),
        )
        self._icon_bg = icon_shell
        with icon_shell.canvas.before:
            Color(
                *(COLORS["surface_tint"] if self.enabled else COLORS["surface_variant"])
            )
            self._icon_bg_rect = RoundedRectangle(
                pos=icon_shell.pos,
                size=icon_shell.size,
                radius=[dp(18)],
            )
        icon_shell.bind(
            pos=lambda inst, _val: setattr(self._icon_bg_rect, "pos", inst.pos),
            size=lambda inst, _val: setattr(self._icon_bg_rect, "size", inst.size),
        )
        icon_shell.add_widget(
            MDIcon(
                icon=icon,
                theme_text_color="Custom",
                text_color=self._accent if self.enabled else COLORS["text_hint"],
                halign="center",
                valign="middle",
                font_size=dp(26),
            )
        )
        icon_container.add_widget(icon_shell)
        self.add_widget(icon_container)

        body = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            spacing=dp(6),
            padding=(0, dp(2), 0, dp(2)),
        )
        body.bind(minimum_height=body.setter("height"))
        self._body = body

        title_label = Label(
            text=title,
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="top",
            font_size=dp(get_font_size("title_medium")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_auto_height(title_label, dp(28))
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        body.add_widget(title_label)

        subtitle_label = Label(
            text=subtitle,
            size_hint_y=None,
            height=dp(48),
            halign="left",
            valign="top",
            font_size=dp(get_font_size("body_medium")),
            color=COLORS["text_secondary"],
        )
        _bind_auto_height(subtitle_label, dp(48))
        if CHINESE_FONT:
            subtitle_label.font_name = CHINESE_FONT
        body.add_widget(subtitle_label)
        self.add_widget(body)

        status_container = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint=(None, 1),
            width=dp(108),
        )
        status_box = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(68),
            spacing=dp(8),
        )
        self._status_box = status_box

        self._status_chip = Label(
            text="已就绪" if self.enabled else "规划中",
            size_hint_y=None,
            height=dp(28),
            halign="center",
            valign="middle",
            font_size=dp(get_font_size("label_medium")),
            color=self._accent if self.enabled else COLORS["text_hint"],
        )
        self._status_chip.bind(
            size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1]))
        )
        if CHINESE_FONT:
            self._status_chip.font_name = CHINESE_FONT
        status_box.add_widget(self._status_chip)

        self._cta = Label(
            text=cta_text,
            size_hint_y=None,
            height=dp(24),
            halign="center",
            valign="middle",
            font_size=dp(get_font_size("label_large")),
            bold=self.enabled,
            color=self._accent if self.enabled else COLORS["text_hint"],
        )
        self._cta.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        if CHINESE_FONT:
            self._cta.font_name = CHINESE_FONT
        status_box.add_widget(self._cta)

        status_container.add_widget(status_box)
        self.add_widget(status_container)

    def _update_height(self, *_args):
        body_height = self._body.height if self._body else 0
        status_height = self._status_box.height if self._status_box else 0
        content_height = max(dp(56), body_height, status_height)
        vertical_padding = self.padding[1] + self.padding[3]
        self.height = max(dp(144), content_height + vertical_padding)

    def _redraw(self, *_args):
        radius = dp(LIST_CARD["radius"])
        bg_color = COLORS["surface_elevated"] if self.enabled else COLORS["surface"]
        if self._pressed and self.enabled:
            bg_color = COLORS["surface_tint"]

        self.canvas.before.clear()
        self.canvas.after.clear()
        with self.canvas.before:
            Color(*bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        with self.canvas.after:
            Color(*(self._accent if self.enabled else COLORS["divider"]))
            Line(
                width=dp(1),
                rounded_rectangle=(self.x, self.y, self.width, self.height, radius),
            )

        self._status_chip.canvas.before.clear()
        with self._status_chip.canvas.before:
            Color(
                *(
                    COLORS["primary_container"]
                    if self.enabled
                    else COLORS["surface_variant"]
                )
            )
            RoundedRectangle(
                pos=self._status_chip.pos,
                size=self._status_chip.size,
                radius=[dp(14)],
            )

    def on_touch_down(self, touch):
        if self.enabled and self.collide_point(*touch.pos):
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


class AddEntryScreen(Screen):
    """选择添加方式的入口屏幕"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "add_entry"
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
            padding=(dp(16), dp(12), dp(16), dp(20)),
            spacing=dp(14),
        )
        content.bind(minimum_height=content.setter("height"))
        preview_card = EntryActionCard(
            title="从订单截图自动批量导入",
            subtitle="上传买菜或外卖订单截图，系统将自动拆分出物品名称、数量和日期线索。",
            icon="image-multiple",
            cta_text="即将开放",
            accent=COLORS["secondary"],
            enabled=False,
        )
        content.add_widget(preview_card)

        capture_card = EntryActionCard(
            title="拍照识别日期后补充信息",
            subtitle="先识别包装上的生产日期，再补足分类、数量和库存信息，适合快速录入。",
            icon="camera-outline",
            cta_text="即将开放",
            accent=COLORS["accent"],
            enabled=False,
        )
        content.add_widget(capture_card)

        manual_card = EntryActionCard(
            title="手动添加物品",
            subtitle="使用完整表单录入名称、分类、日期、提醒和说明，当前已经可用。",
            icon="pencil-plus",
            cta_text="进入",
            accent=COLORS["primary"],
            enabled=True,
        )
        manual_card.bind(on_release=self._go_to_manual_add)
        content.add_widget(manual_card)

        content.add_widget(BoxLayout(size_hint_y=None, height=dp(4)))
        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _create_header(self):
        header = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(92),
            padding=(dp(16), dp(16), dp(16), dp(12)),
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

        top_row = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(12))

        back_shell = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=dp(40),
            height=dp(40),
            padding=dp(8),
        )
        with back_shell.canvas.before:
            Color(*COLORS["surface_tint"])
            self._back_bg = RoundedRectangle(
                pos=back_shell.pos,
                size=back_shell.size,
                radius=[dp(14)],
            )
        back_shell.bind(
            pos=lambda inst, _val: setattr(self._back_bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(self._back_bg, "size", inst.size),
            on_touch_up=lambda inst, touch: self._handle_back_touch(inst, touch),
        )
        back_shell.add_widget(
            MDIcon(
                icon="arrow-left",
                theme_text_color="Custom",
                text_color=COLORS["text_primary"],
                halign="center",
                valign="middle",
                font_size=dp(22),
            )
        )
        top_row.add_widget(back_shell)

        title_box = BoxLayout(orientation="vertical", spacing=dp(2))
        title = Label(
            text="选择添加方式",
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("headline_small")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(title)
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        title_box.add_widget(title)

        subtitle = Label(
            text="先选入口，再进入对应的录入流程。",
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
        title_box.add_widget(subtitle)

        top_row.add_widget(title_box)
        header.add_widget(top_row)
        return header

    def _update_header_divider(self, instance, _value):
        self._header_divider.points = [
            instance.x,
            instance.y,
            instance.right,
            instance.y,
        ]

    def _handle_back_touch(self, widget, touch):
        if widget.collide_point(*touch.pos):
            self._on_back_click(None)
            return True
        return False

    def _on_back_click(self, _instance):
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            app.screen_manager.current = "main"

    def _go_to_manual_add(self, _instance):
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            app.screen_manager.current = "add_item"
