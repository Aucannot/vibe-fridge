# -*- coding: utf-8 -*-
"""
图标选择器组件
"""

from kivy.animation import Animation
from kivy.graphics import Color, Line, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ObjectProperty, StringProperty
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.scrollview import ScrollView
from kivymd.uix.label import MDIcon

try:
    from app.utils.font_helper import CHINESE_FONT_NAME
except Exception:
    CHINESE_FONT_NAME = None

from app.ui.theme.design_tokens import COLOR_PALETTE, get_card_style, get_font_size

COLORS = COLOR_PALETTE
SECTION_CARD = get_card_style("section")
LIST_CARD = get_card_style("list")

# 常用图标列表
ICON_NAMES = [
    "bottle-tonic", "coffee", "coffee-to-go", "egg", "fish",
    "food", "food-apple", "hamburger", "food-drumstick",
    "pizza", "tea", "water", "bottle-wine", "glass-wine",
    "cup", "beaker", "flask", "food-steak",
    "brush", "lipstick", "shower", "tooth",
    "home", "basket", "bag-personal", "bottle-soda",
    "pot", "shower-head",
    "pencil", "pen", "notebook", "book", "book-open",
    "clipboard", "file", "file-document",
    "medical-bag", "pill", "stethoscope", "bandage", "hospital-box",
    "medication", "needle", "thermometer", "heart-pulse",
    "package-variant", "archive", "gift", "star",
    "star-outline", "crown", "cube", "link",
    "help-circle", "information", "account", "cog",
]


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


def _humanize_icon_name(icon_name: str) -> str:
    return icon_name.replace("-", " ")


class PickerButton(ButtonBehavior, BoxLayout):
    __events__ = ("on_release",)

    def __init__(self, text="", variant="secondary", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint = (1, None)
        self.height = dp(46)
        self.padding = (dp(14), dp(12), dp(14), dp(12))
        self._variant = variant
        self._pressed = False

        label = Label(
            text=text,
            halign="center",
            valign="middle",
            font_size=dp(get_font_size("label_large")),
            color=self._text_color(),
            bold=(variant == "primary"),
        )
        _bind_label_text(label)
        if CHINESE_FONT_NAME:
            label.font_name = CHINESE_FONT_NAME
        self._label = label
        self.add_widget(label)

        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _fill_color(self):
        if self._variant == "primary":
            return COLORS["primary_dark"] if self._pressed else COLORS["primary"]
        return COLORS["surface_tint"] if self._pressed else COLORS["surface_variant"]

    def _border_color(self):
        return None if self._variant == "primary" else COLORS["divider"]

    def _text_color(self):
        return COLORS["on_primary"] if self._variant == "primary" else COLORS["text_primary"]

    def _redraw(self, *_args):
        radius = dp(16)
        self._label.color = self._text_color()
        self.canvas.before.clear()
        self.canvas.after.clear()
        with self.canvas.before:
            Color(*self._fill_color())
            RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        border = self._border_color()
        if border:
            with self.canvas.after:
                Color(*border)
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


class IconCard(ButtonBehavior, BoxLayout):
    __events__ = ("on_release",)

    icon_name = StringProperty()
    is_selected = BooleanProperty(False)

    def __init__(self, icon_name, **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self.orientation = "vertical"
        self.size_hint = (1, None)
        self.height = dp(96)
        self.padding = (dp(8), dp(10), dp(8), dp(8))
        self.spacing = dp(8)
        self._pressed = False
        self._icon_widget = None
        self._icon_shell = None
        self._icon_bg = None
        self._label = None
        self._build_ui()
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _build_ui(self):
        self._icon_shell = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint=(None, None),
            size=(dp(44), dp(44)),
        )
        with self._icon_shell.canvas.before:
            Color(*COLORS["surface_tint"])
            self._icon_bg = RoundedRectangle(
                pos=self._icon_shell.pos,
                size=self._icon_shell.size,
                radius=[dp(16)],
            )
        self._icon_shell.bind(
            pos=lambda inst, _val: setattr(self._icon_bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(self._icon_bg, "size", inst.size),
        )

        self._icon_widget = MDIcon(
            icon=self.icon_name,
            theme_text_color="Custom",
            text_color=COLORS["text_primary"],
            size_hint=(None, None),
            size=(dp(22), dp(22)),
            halign="center",
            valign="middle",
            font_size=dp(22),
        )
        self._icon_widget.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        self._icon_shell.add_widget(self._icon_widget)
        self.add_widget(self._icon_shell)

        self._label = Label(
            text=_humanize_icon_name(self.icon_name),
            size_hint_y=None,
            height=dp(22),
            halign="center",
            valign="top",
            font_size=dp(10),
            color=COLORS["text_secondary"],
        )
        _bind_auto_height(self._label, dp(22), horizontal_padding=dp(4))
        if CHINESE_FONT_NAME:
            self._label.font_name = CHINESE_FONT_NAME
        self.add_widget(self._label)

    def _panel_fill(self):
        if self.is_selected:
            return COLORS["primary_container"]
        if self._pressed:
            return COLORS["surface_tint"]
        return COLORS["surface"]

    def _panel_border(self):
        return COLORS["primary"] if self.is_selected else COLORS["divider"]

    def _icon_fill(self):
        if self.is_selected:
            return COLORS["surface"]
        return COLORS["surface_tint"]

    def _icon_color(self):
        return COLORS["primary"] if self.is_selected else COLORS["text_primary"]

    def _text_color(self):
        return COLORS["on_primary_container"] if self.is_selected else COLORS["text_secondary"]

    def _redraw(self, *_args):
        radius = dp(LIST_CARD["radius"])
        self.canvas.before.clear()
        self.canvas.after.clear()
        with self.canvas.before:
            Color(*self._panel_fill())
            RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        with self.canvas.after:
            Color(*self._panel_border())
            Line(
                width=dp(2 if self.is_selected else 1),
                rounded_rectangle=(self.x, self.y, self.width, self.height, radius),
            )
        self._icon_widget.text_color = self._icon_color()
        self._label.color = self._text_color()
        self._icon_shell.canvas.before.clear()
        with self._icon_shell.canvas.before:
            Color(*self._icon_fill())
            self._icon_bg = RoundedRectangle(
                pos=self._icon_shell.pos,
                size=self._icon_shell.size,
                radius=[dp(16)],
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


class HeaderBar(BoxLayout):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(42)
        self.spacing = dp(0)

        title = Label(
            text="选择图标",
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("headline_small")),
            color=COLORS["text_primary"],
            bold=True,
        )
        _bind_label_text(title)
        if CHINESE_FONT_NAME:
            title.font_name = CHINESE_FONT_NAME
        self.add_widget(title)

        subtitle = Label(
            text=f"共 {len(ICON_NAMES)} 个图标",
            size_hint_y=None,
            height=dp(16),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("label_medium")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(subtitle)
        if CHINESE_FONT_NAME:
            subtitle.font_name = CHINESE_FONT_NAME
        self.add_widget(subtitle)


class SelectedPreview(BoxLayout):
    def __init__(self, icon_name="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(52)
        self.padding = (dp(10), dp(8), dp(10), dp(8))
        self.spacing = dp(10)

        with self.canvas.before:
            Color(*COLORS["surface_variant"])
            self._bg = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])
        with self.canvas.after:
            Color(*COLORS["divider"])
            self._outline = Line(
                width=dp(1),
                rounded_rectangle=(self.x, self.y, self.width, self.height, dp(16)),
            )
        self.bind(pos=self._redraw_panel, size=self._redraw_panel)

        icon_shell = AnchorLayout(
            anchor_x="center",
            anchor_y="center",
            size_hint=(None, None),
            size=(dp(36), dp(36)),
        )
        with icon_shell.canvas.before:
            Color(*COLORS["primary_container"])
            self._icon_bg = RoundedRectangle(
                pos=icon_shell.pos,
                size=icon_shell.size,
                radius=[dp(12)],
            )
        icon_shell.bind(
            pos=lambda inst, _val: setattr(self._icon_bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(self._icon_bg, "size", inst.size),
        )
        self._icon = MDIcon(
            icon=icon_name if icon_name else "help-circle-outline",
            theme_text_color="Custom",
            text_color=COLORS["primary"],
            size_hint=(None, None),
            size=(dp(18), dp(18)),
            halign="center",
            valign="middle",
            font_size=dp(18),
        )
        self._icon.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        icon_shell.add_widget(self._icon)
        self.add_widget(icon_shell)

        text_box = BoxLayout(orientation="vertical", spacing=dp(2))
        self._title = Label(
            text="当前选择",
            size_hint_y=None,
            height=dp(16),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("label_medium")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(self._title)
        if CHINESE_FONT_NAME:
            self._title.font_name = CHINESE_FONT_NAME
        text_box.add_widget(self._title)

        self._value = Label(
            text="未选择图标",
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_medium")),
            color=COLORS["text_primary"],
            bold=True,
        )
        _bind_label_text(self._value)
        if CHINESE_FONT_NAME:
            self._value.font_name = CHINESE_FONT_NAME
        text_box.add_widget(self._value)
        self.add_widget(text_box)

        self.set_icon(icon_name)

    def _redraw_panel(self, *_args):
        radius = dp(16)
        self._bg.pos = self.pos
        self._bg.size = self.size
        self._outline.rounded_rectangle = (
            self.x, self.y, self.width, self.height, radius
        )

    def set_icon(self, icon_name):
        self._icon.icon = icon_name if icon_name else "help-circle-outline"
        self._value.text = _humanize_icon_name(icon_name) if icon_name else "未选择图标"


class IconPickerActionBar(BoxLayout):
    def __init__(self, on_cancel=None, on_confirm=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(46)
        self.spacing = dp(10)

        cancel_btn = PickerButton(text="取消", variant="secondary")
        cancel_btn.bind(on_release=on_cancel if on_cancel else lambda *_args: None)
        self.add_widget(cancel_btn)

        confirm_btn = PickerButton(text="确定选择", variant="primary")
        confirm_btn.bind(on_release=on_confirm if on_confirm else lambda *_args: None)
        self.add_widget(confirm_btn)


class IconPicker(ModalView):
    """图标选择器对话框"""

    selected_icon = StringProperty("")
    on_icon_selected = ObjectProperty(None)

    def __init__(self, current_icon=None, **kwargs):
        super().__init__(**kwargs)
        self.current_icon = current_icon
        self.selected_icon = current_icon or ""
        self._selected_buttons = {}
        self._preview = None
        self._build_ui()

    def _build_ui(self):
        self.size_hint = (0.82, 0.76)
        self.pos_hint = {"center_x": 0.5, "center_y": 0.5}
        self.auto_dismiss = False
        self.background = ""
        self.background_color = (0, 0, 0, 0)

        panel = BoxLayout(
            orientation="vertical",
            padding=(dp(16), dp(16), dp(16), dp(14)),
            spacing=dp(12),
        )
        self._decorate_panel(panel)

        panel.add_widget(HeaderBar())

        self._preview = SelectedPreview(self.selected_icon)
        panel.add_widget(self._preview)

        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=dp(3),
            bar_color=(*COLORS["primary"][:3], 0.25),
            bar_inactive_color=(*COLORS["primary"][:3], 0.1),
        )

        self._grid = GridLayout(
            cols=3,
            spacing=dp(8),
            padding=(dp(2), dp(2), dp(2), dp(2)),
            size_hint_y=None,
        )
        self._grid.bind(minimum_height=self._grid.setter("height"))
        scroll.add_widget(self._grid)
        panel.add_widget(scroll)

        for icon_name in ICON_NAMES:
            card = IconCard(icon_name)
            card.bind(on_release=lambda _inst, selected_name=icon_name: self._select_icon(selected_name))
            self._selected_buttons[icon_name] = card
            self._grid.add_widget(card)

        action_bar = IconPickerActionBar(
            on_cancel=self._on_cancel,
            on_confirm=self._on_confirm,
        )
        panel.add_widget(action_bar)

        self.add_widget(panel)

        if self.selected_icon and self.selected_icon in self._selected_buttons:
            self._select_icon(self.selected_icon)

    def _decorate_panel(self, panel):
        radius = dp(20)
        with panel.canvas.before:
            Color(*COLORS["surface"])
            panel._bg = RoundedRectangle(pos=panel.pos, size=panel.size, radius=[radius])
        with panel.canvas.after:
            Color(*COLORS["divider"])
            panel._outline = Line(
                width=dp(1),
                rounded_rectangle=(panel.x, panel.y, panel.width, panel.height, radius),
            )

        def _update_panel(instance, _value):
            panel._bg.pos = instance.pos
            panel._bg.size = instance.size
            panel._outline.rounded_rectangle = (
                instance.x, instance.y, instance.width, instance.height, radius
            )

        panel.bind(pos=_update_panel, size=_update_panel)
        _update_panel(panel, None)

    def _select_icon(self, icon_name: str):
        self.selected_icon = icon_name
        if self._preview:
            self._preview.set_icon(icon_name)

        for name, btn in self._selected_buttons.items():
            should_select = name == icon_name
            if btn.is_selected != should_select:
                btn.is_selected = should_select
                btn._redraw()

    def _on_cancel(self, *_args):
        self.dismiss()

    def _on_confirm(self, *_args):
        if self.on_icon_selected:
            self.on_icon_selected(self.selected_icon)
        self.dismiss()

    def show(self):
        self.opacity = 0
        super().open()
        Animation(opacity=1, duration=0.2, t="out_cubic").start(self)
