# -*- coding: utf-8 -*-
"""
物品 Wiki 编辑页
"""

import logging

from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty, ListProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivymd.app import MDApp
from kivymd.uix.label import MDIcon

from app.services.wiki_service import wiki_service
from app.ui.theme.design_tokens import COLOR_PALETTE, get_card_style, get_font_size
from app.ui.widgets.icon_picker import IconPicker
from app.utils.font_helper import CHINESE_FONT_NAME as CHINESE_FONT

logger = logging.getLogger(__name__)

COLORS = COLOR_PALETTE
SECTION_CARD = get_card_style("section")


def _bind_label_text(widget, horizontal_padding=0):
    widget.bind(
        size=lambda inst, val: setattr(
            inst, "text_size", (max(0, val[0] - horizontal_padding), None)
        )
    )


def _bind_auto_height(widget, min_height):
    widget.size_hint_y = None
    widget.height = min_height
    widget.bind(
        texture_size=lambda inst, val: setattr(
            inst, "height", max(min_height, val[1] or min_height)
        )
    )


class SurfaceButton(ButtonBehavior, BoxLayout):
    __events__ = ("on_release",)

    def __init__(self, text="", icon=None, variant="secondary", compact=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint = (None, None)
        self.height = dp(42 if compact else 48)
        self.width = dp(42 if compact and not text else 124)
        self.padding = (dp(12), dp(12))
        self.spacing = dp(6)
        self._variant = variant
        self._pressed = False

        if icon:
            self.add_widget(
                MDIcon(
                    icon=icon,
                    theme_text_color="Custom",
                    text_color=self._text_color(),
                    size_hint=(None, None),
                    size=(dp(18), dp(18)),
                    font_size=dp(18),
                )
            )

        if text:
            label = Label(
                text=text,
                halign="center",
                valign="middle",
                font_size=dp(get_font_size("label_large")),
                color=self._text_color(),
            )
            label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
            if CHINESE_FONT:
                label.font_name = CHINESE_FONT
            self.add_widget(label)

        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _fill_color(self):
        if self._variant == "primary":
            return COLORS["primary_dark"] if self._pressed else COLORS["primary"]
        if self._variant == "tonal":
            return COLORS["surface_tint"] if self._pressed else COLORS["primary_container"]
        return COLORS["surface_tint"] if self._pressed else COLORS["surface"]

    def _border_color(self):
        return None if self._variant == "primary" else COLORS["divider"]

    def _text_color(self):
        if self._variant == "primary":
            return COLORS["on_primary"]
        if self._variant == "tonal":
            return COLORS["on_primary_container"]
        return COLORS["text_primary"]

    def _redraw(self, *_args):
        radius = dp(16)
        text_color = self._text_color()
        for child in self.children:
            if isinstance(child, Label):
                child.color = text_color
            elif isinstance(child, MDIcon):
                child.text_color = text_color
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


class ThemedTextInput(TextInput):
    def __init__(self, hint_text="", multiline=False, **kwargs):
        super().__init__(**kwargs)
        self.multiline = multiline
        self.size_hint = (1, None)
        self.height = dp(52) if not multiline else dp(116)
        self.hint_text = hint_text
        self.background_normal = ""
        self.background_active = ""
        self.background_color = (0, 0, 0, 0)
        self.foreground_color = COLORS["text_primary"]
        self.cursor_color = COLORS["primary"]
        self.hint_text_color = COLORS["text_hint"]
        self.padding = (dp(14), dp(15), dp(14), dp(15))
        self.font_size = dp(get_font_size("body_large"))
        self.border = [0, 0, 0, 0]
        self.write_tab = False
        if CHINESE_FONT:
            self.font_name = CHINESE_FONT
        self.bind(pos=self._redraw, size=self._redraw, focus=self._redraw)
        self._redraw()

    def _redraw(self, *_args):
        radius = dp(14)
        fill = COLORS["surface"] if self.focus else COLORS["surface_variant"]
        outline = COLORS["primary"] if self.focus else COLORS["divider"]
        self.canvas.before.clear()
        self.canvas.after.clear()
        with self.canvas.before:
            Color(*fill)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        with self.canvas.after:
            Color(*outline)
            Line(
                width=dp(1),
                rounded_rectangle=(self.x, self.y, self.width, self.height, radius),
            )


class ThemedSpinnerOption(ButtonBehavior, BoxLayout):
    __events__ = ("on_release",)

    text = StringProperty("")
    selected = BooleanProperty(False)

    def __init__(self, text="", selected=False, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.selected = selected
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(48)
        self.padding = (dp(14), dp(12), dp(14), dp(12))
        self.spacing = dp(10)
        self._pressed = False
        self._label = None
        self._check_icon = None
        self._build_ui()
        self.bind(pos=self._redraw, size=self._redraw, selected=self._redraw)
        self._redraw()

    def _build_ui(self):
        self._label = Label(
            text=self.text,
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_large")),
            color=COLORS["text_primary"],
        )
        _bind_label_text(self._label)
        if CHINESE_FONT:
            self._label.font_name = CHINESE_FONT
        self.add_widget(self._label)

        self._check_icon = MDIcon(
            icon="check",
            theme_text_color="Custom",
            text_color=COLORS["primary"],
            size_hint=(None, None),
            size=(dp(18), dp(18)),
            font_size=dp(18),
            opacity=1 if self.selected else 0,
        )
        self.add_widget(self._check_icon)

    def _redraw(self, *_args):
        radius = dp(14)
        fill = COLORS["primary_container"] if self.selected else COLORS["surface_variant"]
        if self._pressed and not self.selected:
            fill = COLORS["surface_tint"]
        text_color = COLORS["on_primary_container"] if self.selected else COLORS["text_primary"]
        outline = COLORS["primary"] if self.selected else COLORS["divider"]
        self._label.color = text_color
        self._check_icon.opacity = 1 if self.selected else 0
        self.canvas.before.clear()
        self.canvas.after.clear()
        with self.canvas.before:
            Color(*fill)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        with self.canvas.after:
            Color(*outline)
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


class ThemedSpinner(ButtonBehavior, BoxLayout):
    __events__ = ("on_release",)

    text = StringProperty("")
    placeholder = StringProperty("")
    values = ListProperty()

    def __init__(self, placeholder="", values=None, **kwargs):
        super().__init__(**kwargs)
        self.placeholder = placeholder
        self.values = list(values or kwargs.pop("values", []))
        self.size_hint = (1, None)
        self.height = dp(52)
        self.orientation = "horizontal"
        self.padding = (dp(14), dp(14), dp(14), dp(14))
        self.spacing = dp(8)
        self._pressed = False
        self._dialog = None
        self._label = None
        self._chevron = None
        self.text = placeholder
        self._build_ui()
        self.bind(pos=self._redraw, size=self._redraw, text=self._sync_display)
        self._sync_display()
        self._redraw()

    def _build_ui(self):
        self._label = Label(
            text="",
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_large")),
            color=COLORS["text_primary"],
        )
        _bind_label_text(self._label)
        if CHINESE_FONT:
            self._label.font_name = CHINESE_FONT
        self.add_widget(self._label)

        self._chevron = MDIcon(
            icon="chevron-down",
            theme_text_color="Custom",
            text_color=COLORS["text_hint"],
            size_hint=(None, None),
            size=(dp(18), dp(18)),
            font_size=dp(18),
        )
        self.add_widget(self._chevron)

    def _has_value(self):
        return bool(self.text) and self.text != self.placeholder

    def _sync_display(self, *_args):
        has_value = self._has_value()
        self._label.text = self.text if has_value else self.placeholder
        self._label.color = COLORS["text_primary"] if has_value else COLORS["text_hint"]

    def _redraw(self, *_args):
        radius = dp(14)
        fill = COLORS["surface"] if self._pressed else COLORS["surface_variant"]
        outline = COLORS["primary"] if self._pressed else COLORS["divider"]
        self.canvas.before.clear()
        self.canvas.after.clear()
        with self.canvas.before:
            Color(*fill)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        with self.canvas.after:
            Color(*outline)
            Line(
                width=dp(1),
                rounded_rectangle=(self.x, self.y, self.width, self.height, radius),
            )

    def _decorate_modal_panel(self, panel):
        radius = dp(SECTION_CARD["radius"])
        with panel.canvas.before:
            Color(*COLORS["surface"])
            panel._panel_bg = RoundedRectangle(pos=panel.pos, size=panel.size, radius=[radius])
        with panel.canvas.after:
            Color(*COLORS["divider"])
            panel._panel_outline = Line(
                width=dp(1),
                rounded_rectangle=(panel.x, panel.y, panel.width, panel.height, radius),
            )

        def _update_panel(instance, _value):
            panel._panel_bg.pos = instance.pos
            panel._panel_bg.size = instance.size
            panel._panel_outline.rounded_rectangle = (
                instance.x,
                instance.y,
                instance.width,
                instance.height,
                radius,
            )

        panel.bind(pos=_update_panel, size=_update_panel)
        _update_panel(panel, None)

    def _open_dialog(self):
        if not self.values:
            return

        dialog_height = min(dp(460), dp(132) + len(self.values) * dp(56))
        dialog = ModalView(size_hint=(0.82, None), height=dialog_height, auto_dismiss=True)

        root = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dialog_height,
            padding=dp(18),
            spacing=dp(12),
        )
        self._decorate_modal_panel(root)

        title = Label(
            text=self.placeholder or "选择选项",
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_medium")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(title)
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        root.add_widget(title)

        scroll = ScrollView(do_scroll_x=False, size_hint=(1, 1), bar_width=dp(3))
        option_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8),
        )
        option_box.bind(minimum_height=option_box.setter("height"))

        for value in self.values:
            option = ThemedSpinnerOption(text=value, selected=(value == self.text))

            def _on_select(_instance, selected_value=value):
                self.text = selected_value
                dialog.dismiss()

            option.bind(on_release=_on_select)
            option_box.add_widget(option)

        scroll.add_widget(option_box)
        root.add_widget(scroll)

        action_row = BoxLayout(size_hint_y=None, height=dp(48))
        action_row.add_widget(BoxLayout())
        cancel_btn = SurfaceButton(text="取消", variant="secondary")
        cancel_btn.bind(on_release=lambda *_args: dialog.dismiss())
        action_row.add_widget(cancel_btn)
        root.add_widget(action_row)

        dialog.add_widget(root)
        self._dialog = dialog
        dialog.open()

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
        self._open_dialog()


class SectionCard(BoxLayout):
    def __init__(self, title, subtitle="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.padding = dp(SECTION_CARD["padding"])
        self.spacing = dp(12)
        self.bind(minimum_height=self.setter("height"))
        self._build_header(title, subtitle)
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _build_header(self, title, subtitle):
        title_label = Label(
            text=title,
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_medium")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(title_label)
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        self.add_widget(title_label)

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
            self.add_widget(subtitle_label)

    def _redraw(self, *_args):
        radius = dp(SECTION_CARD["radius"])
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


class IconField(ButtonBehavior, BoxLayout):
    __events__ = ("on_release",)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(84)
        self.padding = (dp(16), dp(16), dp(16), dp(16))
        self.spacing = dp(12)
        self._pressed = False
        self._icon_widget = None
        self._subtitle = None
        self._build_ui()
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _build_ui(self):
        icon_shell = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=dp(44),
            height=dp(44),
            padding=dp(10),
        )
        with icon_shell.canvas.before:
            Color(*COLORS["primary_container"])
            self._icon_bg = RoundedRectangle(
                pos=icon_shell.pos, size=icon_shell.size, radius=[dp(14)]
            )
        icon_shell.bind(
            pos=lambda inst, _val: setattr(self._icon_bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(self._icon_bg, "size", inst.size),
        )
        self._icon_widget = MDIcon(
            icon="help-circle-outline",
            theme_text_color="Custom",
            text_color=COLORS["primary"],
            halign="center",
            valign="middle",
            font_size=dp(22),
        )
        icon_shell.add_widget(self._icon_widget)
        self.add_widget(icon_shell)

        text_box = BoxLayout(orientation="vertical", spacing=dp(2))
        title = Label(
            text="物品图标",
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_small")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(title)
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        text_box.add_widget(title)

        self._subtitle = Label(
            text="点击选择图标",
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(self._subtitle)
        if CHINESE_FONT:
            self._subtitle.font_name = CHINESE_FONT
        text_box.add_widget(self._subtitle)
        self.add_widget(text_box)

        self.add_widget(
            MDIcon(
                icon="chevron-right",
                theme_text_color="Custom",
                text_color=COLORS["text_hint"],
                size_hint=(None, None),
                size=(dp(18), dp(18)),
                font_size=dp(18),
            )
        )

    def set_icon(self, icon_name: str):
        display = icon_name or "help-circle-outline"
        self._icon_widget.icon = display
        self._subtitle.text = icon_name if icon_name else "点击选择图标"

    def _redraw(self, *_args):
        radius = dp(16)
        bg_color = COLORS["surface_tint"] if self._pressed else COLORS["surface"]
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


class ItemWikiEditScreen(Screen):
    """物品Wiki编辑页"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "item_wiki_edit"
        self.wiki_id = None
        self.wiki_name = ""
        self.wiki_icon = ""
        self._icon_picker = None
        self._name_input = None
        self._category_spinner = None
        self._unit_spinner = None
        self._expiry_input = None
        self._location_spinner = None
        self._description_input = None
        self._icon_card = None
        self._header_subtitle = None
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

        self._icon_card = IconField()
        self._icon_card.bind(on_release=self._on_icon_select)
        content.add_widget(self._icon_card)

        basic_card = SectionCard("基本信息", "先定义名称和分类，保证 Wiki 条目容易识别。")
        self._name_input = ThemedTextInput(hint_text="请输入物品名称")
        self._category_spinner = ThemedSpinner(placeholder="选择分类", values=[])
        basic_card.add_widget(self._field_stack("物品名称", self._name_input))
        basic_card.add_widget(self._field_stack("物品分类", self._category_spinner))
        content.add_widget(basic_card)

        spec_card = SectionCard("规格参数", "补充默认单位、保质期和存放位置，方便库存实例复用。")
        self._unit_spinner = ThemedSpinner(
            placeholder="选择单位",
            values=["个", "盒", "瓶", "袋", "包", "罐", "斤", "公斤", "条", "片", "支", "其他"],
        )
        self._expiry_input = ThemedTextInput(
            hint_text="例如：7、30、365",
            multiline=False,
            input_filter="int",
        )
        self._location_spinner = ThemedSpinner(
            placeholder="选择位置",
            values=["常温", "冷藏", "冷冻", "阴凉", "其他"],
        )
        spec_card.add_widget(self._field_stack("默认单位", self._unit_spinner))
        spec_card.add_widget(self._field_stack("建议保质期（天）", self._expiry_input))
        spec_card.add_widget(self._field_stack("存放位置", self._location_spinner))
        content.add_widget(spec_card)

        desc_card = SectionCard("描述信息", "可填写口味、采购建议或储存备注。")
        self._description_input = ThemedTextInput(
            hint_text="输入物品的详细描述...",
            multiline=True,
        )
        desc_card.add_widget(self._field_stack("物品描述", self._description_input))
        content.add_widget(desc_card)

        action_row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(12))
        cancel_btn = SurfaceButton(text="取消", variant="secondary")
        cancel_btn.bind(on_release=self._on_cancel)
        save_btn = SurfaceButton(text="保存修改", icon="check", variant="primary")
        save_btn.bind(on_release=self._on_save)
        action_row.add_widget(cancel_btn)
        action_row.add_widget(save_btn)
        content.add_widget(action_row)

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _create_header(self):
        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(100),
            padding=(dp(16), dp(18), dp(16), dp(12)),
            spacing=dp(10),
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

        back_btn = SurfaceButton(icon="arrow-left", variant="secondary", compact=True)
        back_btn.bind(on_release=self._on_cancel)
        header.add_widget(back_btn)

        title_box = BoxLayout(orientation="vertical", spacing=dp(2), size_hint_y=None)
        title_box.bind(minimum_height=title_box.setter("height"))
        title = Label(
            text="编辑物品信息",
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

        self._header_subtitle = Label(
            text="维护默认信息，库存会自动复用。",
            halign="left",
            valign="top",
            font_size=dp(get_font_size("body_medium")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(self._header_subtitle)
        _bind_auto_height(self._header_subtitle, dp(18))
        if CHINESE_FONT:
            self._header_subtitle.font_name = CHINESE_FONT
        title_box.add_widget(self._header_subtitle)
        header.add_widget(title_box)
        return header

    def _field_stack(self, label_text, widget):
        container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(6),
        )
        container.bind(minimum_height=container.setter("height"))

        label = Label(
            text=label_text,
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("label_large")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(label)
        if CHINESE_FONT:
            label.font_name = CHINESE_FONT
        container.add_widget(label)
        container.add_widget(widget)
        return container

    def _update_header_divider(self, instance, _value):
        self._header_divider.points = [instance.x, instance.y, instance.right, instance.y]

    def load_wiki(self, wiki_name: str):
        """加载要编辑的物品Wiki"""
        try:
            self.wiki_name = wiki_name
            wiki_item = wiki_service.get_wiki_by_name(wiki_name)
            self._load_categories()

            if wiki_item:
                self.wiki_id = wiki_item["id"]
                self.wiki_icon = wiki_item.get("icon", "")
                self._name_input.text = wiki_item["name"]
                self._icon_card.set_icon(self.wiki_icon)
                self._description_input.text = wiki_item.get("description") or ""

                unit_value = wiki_item.get("default_unit") or ""
                self._unit_spinner.text = (
                    unit_value if unit_value in self._unit_spinner.values else "其他"
                )

                self._expiry_input.text = (
                    str(wiki_item.get("suggested_expiry_days", ""))
                    if wiki_item.get("suggested_expiry_days")
                    else ""
                )

                location_value = wiki_item.get("storage_location") or ""
                self._location_spinner.text = (
                    location_value
                    if location_value in self._location_spinner.values
                    else "其他"
                )

                if wiki_item.get("category_name"):
                    self._category_spinner.text = wiki_item["category_name"]
            else:
                logger.warning(f"物品Wiki不存在: {wiki_name}")
                self._name_input.text = wiki_name
                self._description_input.text = ""
                self._icon_card.set_icon("")
        except Exception as exc:
            logger.error(f"加载物品Wiki失败: {exc}")

    def _load_categories(self):
        try:
            categories = wiki_service.get_all_categories()
            category_names = [cat.name for cat in categories]
            self._category_spinner.values = category_names
            if not category_names:
                self._category_spinner.text = "暂无分类"
        except Exception as exc:
            logger.error(f"加载分类列表失败: {exc}")

    def _on_icon_select(self, _instance):
        current_icon = self.wiki_icon if self.wiki_icon else "help-circle-outline"
        if self._icon_picker is None:
            self._icon_picker = IconPicker(current_icon=current_icon)
            self._icon_picker.on_icon_selected = self._icon_selected
        else:
            self._icon_picker.current_icon = current_icon
            self._icon_picker.selected_icon = current_icon
        self._icon_picker.show()

    def _icon_selected(self, icon_name: str):
        self.wiki_icon = icon_name
        self._icon_card.set_icon(icon_name)

    def _on_cancel(self, _instance):
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            app.screen_manager.current = "item_wiki_detail"

    def _on_save(self, _instance):
        try:
            name = self._name_input.text.strip()
            if not name:
                logger.warning("物品名称不能为空")
                return

            category_name = self._category_spinner.text
            category_id = None
            if category_name and category_name not in {"选择分类", "暂无分类"}:
                categories = wiki_service.get_all_categories()
                for category in categories:
                    if category.name == category_name:
                        category_id = category.id
                        break

            description = self._description_input.text.strip() or None
            default_unit = (
                self._unit_spinner.text
                if self._unit_spinner.text != "选择单位"
                else None
            )
            suggested_expiry_days = None
            if self._expiry_input.text.strip():
                try:
                    suggested_expiry_days = int(self._expiry_input.text.strip())
                except ValueError:
                    suggested_expiry_days = None
            storage_location = (
                self._location_spinner.text
                if self._location_spinner.text != "选择位置"
                else None
            )

            updates = {
                "name": name,
                "icon": self.wiki_icon or None,
                "description": description,
                "default_unit": default_unit,
                "suggested_expiry_days": suggested_expiry_days,
                "storage_location": storage_location,
            }
            if category_id:
                updates["category_id"] = category_id

            if self.wiki_id:
                success = wiki_service.update_wiki(self.wiki_id, **updates)
                if success:
                    self._navigate_back()
                else:
                    logger.error("物品Wiki更新失败")
            else:
                new_wiki = wiki_service.create_wiki(**updates)
                if new_wiki:
                    self.wiki_id = new_wiki["id"]
                    self.wiki_name = name
                    self._navigate_back()
                else:
                    logger.error("物品Wiki创建失败")
        except Exception as exc:
            logger.error(f"保存物品Wiki失败: {exc}")

    def _navigate_back(self):
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            items_screen = app.screen_manager.get_screen("items")
            if items_screen:
                items_screen.refresh_data()

            detail_screen = app.screen_manager.get_screen("item_wiki_detail")
            if detail_screen:
                detail_screen.load_wiki_item(self._name_input.text)
            app.screen_manager.current = "item_wiki_detail"
