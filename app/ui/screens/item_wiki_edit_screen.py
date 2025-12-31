# -*- coding: utf-8 -*-
"""
物品Wiki编辑页 - 现代化设计
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.textinput import TextInput
from kivy.uix.behaviors import ButtonBehavior
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Line, Ellipse
from kivy.clock import Clock
from kivy.properties import StringProperty, ObjectProperty, ListProperty
from kivymd.app import MDApp
from kivymd.uix.label import MDIcon

import logging
from app.services.wiki_service import wiki_service
from app.ui.theme.design_tokens import COLOR_PALETTE, DESIGN_TOKENS
from app.ui.widgets.icon_picker import IconPicker
from app.utils.font_helper import CHINESE_FONT_NAME as CHINESE_FONT

logger = logging.getLogger(__name__)

# 现代配色方案
MODERN_COLORS = {
    'primary': [0.42, 0.52, 1, 1],          # 蓝紫色
    'primary_light': [0.75, 0.78, 1, 1],     # 浅蓝紫色
    'success': [0.35, 0.82, 0.55, 1],        # 翠绿色
    'warning': [1, 0.58, 0.25, 1],           # 橙黄色
    'error': [0.95, 0.35, 0.38, 1],          # 玫红色
    'surface': [0.98, 0.98, 1, 1],           # 极浅蓝
    'card': [1, 1, 1, 1],                    # 纯白
    'input_bg': [0.94, 0.95, 1, 1],          # 输入框背景
    'input_border': [0.88, 0.89, 0.95, 1],   # 输入框边框
    'input_border_focused': [0.42, 0.52, 1, 0.6],  # 聚焦边框
    'text_primary': [0.12, 0.15, 0.22, 1],   # 深色文字
    'text_secondary': [0.55, 0.58, 0.65, 1], # 次要文字
    'text_hint': [0.65, 0.68, 0.75, 1],      # 提示文字
    'divider': [0.92, 0.93, 0.98, 1],        # 分隔线
    'shadow': [0, 0, 0, 0.04],               # 阴影
}


class CustomSpinnerOption(SpinnerOption):
    """自定义下拉选项 - 支持中文字体"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = MATERIAL_COLORS['card']
        self.color = MATERIAL_COLORS['text_primary']
        self.height = dp(48)
        self.font_size = dp(15)
        if CHINESE_FONT:
            self.font_name = CHINESE_FONT


# 解决循环引用
MATERIAL_COLORS = {
    'primary': [0.42, 0.52, 1, 1],
    'card': [1, 1, 1, 1],
    'text_primary': [0.12, 0.15, 0.22, 1],
}


class ModernButton(ButtonBehavior, BoxLayout):
    """现代化按钮"""

    def __init__(self, text="", is_primary=True, icon=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.is_primary = is_primary
        self._bg_rect = None
        self._border_rect = None
        self._pressed = False

        self.size_hint_y = None
        self.height = dp(52)

        self._setup_ui(text, icon)
        self._update_colors()

    def _setup_ui(self, text, icon):
        # 背景
        self.bind(pos=self._update_canvas, size=self._update_canvas)

        if icon:
            icon_widget = MDIcon(
                icon=icon,
                size_hint_x=None,
                width=dp(20),
                font_size=dp(20),
                halign="center",
                valign="middle",
            )
            self.add_widget(icon_widget)

        label = Label(
            text=text,
            size_hint_x=1,
            halign="center",
            valign="middle",
            font_size=dp(15),
            bold=True,
            color=self._get_text_color(),
        )
        if CHINESE_FONT:
            label.font_name = CHINESE_FONT
        self.add_widget(label)

    def _get_bg_color(self):
        if self.is_primary:
            return MODERN_COLORS['primary']
        return MODERN_COLORS['card']

    def _get_text_color(self):
        if self.is_primary:
            return [1, 1, 1, 1]
        return MODERN_COLORS['text_primary']

    def _get_border_color(self):
        if self.is_primary:
            return [0, 0, 0, 0]
        return MODERN_COLORS['input_border']

    def _update_colors(self):
        # 更新文字颜色
        for child in self.children:
            if isinstance(child, Label):
                child.color = self._get_text_color() if self._pressed else (
                    MODERN_COLORS['primary'] if not self.is_primary else [1, 1, 1, 1]
                )

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        radius = dp(14)

        bg_color = self._get_bg_color()
        if self._pressed:
            bg_color = [c * 0.9 for c in bg_color[:3]] + [bg_color[3]]

        with self.canvas.before:
            if not self.is_primary:
                shadow = [0, 0, 0, 0.03]
                Color(*shadow)
                RoundedRectangle(
                    pos=(self.x + dp(1), self.y - dp(2)),
                    size=self.size,
                    radius=[radius]
                )

            Color(*bg_color)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])

            if not self._pressed and not self.is_primary:
                Color(*self._get_border_color())
                self._border_rect = Line(
                    width=dp(1.5),
                    rounded_rectangle=(self.x, self.y, self.width, self.height, radius)
                )

        self._update_colors()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._pressed = True
            self._update_canvas()
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._pressed:
            self._pressed = False
            self._update_canvas()
            if self.collide_point(*touch.pos):
                self.dispatch('on_release')
        return super().on_touch_up(touch)

    def on_release(self, *args):
        pass


class ModernTextInput(TextInput):
    """现代化输入框"""

    def __init__(self, hint_text="", is_multiline=False, **kwargs):
        super().__init__(**kwargs)
        self._bg_rect = None
        self._border_rect = None
        self._focused = False

        self.size_hint_y = None
        self.height = dp(52) if not is_multiline else dp(100)

        self.background_color = MODERN_COLORS['input_bg']
        self.foreground_color = MODERN_COLORS['text_primary']
        self.cursor_color = MODERN_COLORS['primary']
        self.multiline = is_multiline
        self.hint_text_color = MODERN_COLORS['text_hint']
        self.hint_text = hint_text
        self.padding = (dp(16), dp(10), dp(16), dp(10))
        self.font_size = dp(15)
        self.border = 0

        if CHINESE_FONT:
            self.font_name = CHINESE_FONT

        self._setup_canvas()

    def _setup_canvas(self):
        self.bind(pos=self._update_canvas, size=self._update_canvas,
                  focus=self._on_focus_change)
        self._update_canvas()

    def _on_focus_change(self, instance, value):
        self._focused = value
        self._update_canvas()

    def _update_canvas(self, *args):
        self.canvas.after.clear()
        radius = dp(12)

        border_color = MODERN_COLORS['input_border_focused'] if self._focused else MODERN_COLORS['input_border']
        border_width = dp(2) if self._focused else dp(1.5)

        with self.canvas.after:
            Color(*border_color)
            self._border_rect = Line(
                width=border_width,
                rounded_rectangle=(self.x, self.y, self.width, self.height, radius)
            )


class IconSelectCard(ButtonBehavior, BoxLayout):
    """图标选择卡片"""

    def __init__(self, icon_name="", **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self._bg_rect = None
        self._icon_circle = None
        self._pressed = False

        self.orientation = "horizontal"
        self.size_hint_y = None
        self.size_hint_x = 1
        self.height = dp(64)
        self.padding = dp(16)
        self.spacing = dp(14)

        self._setup_ui()
        self._update_canvas()
        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def _setup_ui(self):
        icon_display = self.icon_name if self.icon_name else "help-circle-outline"

        # 图标容器
        icon_container = BoxLayout(
            size_hint_x=None,
            width=dp(44),
            height=dp(44),
            padding=dp(10),
        )

        with icon_container.canvas.before:
            Color(*MODERN_COLORS['primary_light'])
            self._icon_circle = Ellipse(pos=icon_container.pos, size=icon_container.size)
        icon_container.bind(pos=self._update_icon_circle, size=self._update_icon_circle)

        icon = MDIcon(
            icon=icon_display,
            size_hint=(1, 1),
            halign="center",
            valign="middle",
            font_size=dp(24),
        )
        icon.color = MODERN_COLORS['primary']
        icon_container.add_widget(icon)
        self._icon_widget = icon
        self.add_widget(icon_container)

        # 文字区域
        text_box = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(4))

        title = Label(
            text="物品图标",
            halign="left",
            valign="middle",
            color=MODERN_COLORS['text_primary'],
            font_size=dp(15),
            bold=True,
        )
        title.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        text_box.add_widget(title)

        self._subtitle = Label(
            text=self.icon_name if self.icon_name else "点击选择图标",
            halign="left",
            valign="bottom",
            color=MODERN_COLORS['text_hint'],
            font_size=dp(13),
        )
        self._subtitle.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        if CHINESE_FONT:
            self._subtitle.font_name = CHINESE_FONT
        text_box.add_widget(self._subtitle)
        self.add_widget(text_box)

        # 箭头
        arrow = MDIcon(
            icon="chevron-right",
            size_hint_x=None,
            width=dp(20),
            font_size=dp(20),
            halign="center",
            valign="middle",
        )
        arrow.color = MODERN_COLORS['text_hint']
        self.add_widget(arrow)

    def _update_icon_circle(self, *args):
        if hasattr(self, 'children') and self.children:
            icon_container = self.children[-1].parent if hasattr(self.children[-1], 'parent') else None
            if icon_container and self._icon_circle:
                self._icon_circle.pos = icon_container.pos
                self._icon_circle.size = icon_container.size

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        radius = dp(14)

        bg_color = MODERN_COLORS['input_bg']
        if self._pressed:
            bg_color = [c * 0.98 for c in bg_color[:3]] + [bg_color[3]]

        with self.canvas.before:
            Color(*bg_color)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])

        # 更新图标圆圈
        for child in self.children:
            if hasattr(child, 'canvas'):
                for widget in child.children:
                    if hasattr(widget, 'canvas') and widget != self._icon_widget:
                        if widget.children:
                            for sub in widget.children:
                                if hasattr(sub, 'canvas'):
                                    sub.canvas.before.clear()
                                    Color(*MODERN_COLORS['primary_light'])
                                    if hasattr(self, '_icon_circle'):
                                        self._icon_circle.pos = widget.pos
                                        self._icon_circle.size = widget.size
                                        Ellipse(pos=widget.pos, size=widget.size)
                                        break

    def set_icon(self, icon_name: str):
        self.icon_name = icon_name
        icon_display = icon_name if icon_name else "help-circle-outline"
        self._icon_widget.icon = icon_display
        self._subtitle.text = icon_name if icon_name else "点击选择图标"

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._pressed = True
            self._update_canvas()
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._pressed:
            self._pressed = False
            self._update_canvas()
            if self.collide_point(*touch.pos):
                self.dispatch('on_release')
        return super().on_touch_up(touch)

    def on_release(self, *args):
        pass


class SectionCard(BoxLayout):
    """分组卡片"""

    def __init__(self, title="", icon=None, size_hint_y=None, **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.icon = icon

        self.orientation = "vertical"
        self.size_hint_y = size_hint_y or None
        self.spacing = dp(0)

        self._setup_ui()

    def _setup_ui(self):
        # 卡片背景
        with self.canvas.before:
            Color(*MODERN_COLORS['card'])
            self._shadow = None
            self._bg_rect = None
        self.bind(pos=self._update_canvas, size=self._update_canvas)

        # 标题栏
        if self.title:
            header = BoxLayout(
                orientation="horizontal",
                size_hint_y=None,
                height=dp(48),
                padding=(dp(20), dp(8), dp(20), dp(8)),
                spacing=dp(12),
            )

            if self.icon:
                header_icon = MDIcon(
                    icon=self.icon,
                    size_hint_x=None,
                    width=dp(24),
                    font_size=dp(20),
                    halign="center",
                    valign="middle",
                )
                header_icon.color = MODERN_COLORS['primary']
                header.add_widget(header_icon)

            header_title = Label(
                text=self.title,
                size_hint_x=1,
                halign="left",
                valign="middle",
                color=MODERN_COLORS['text_primary'],
                font_size=dp(16),
                bold=True,
            )
            header_title.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
            if CHINESE_FONT:
                header_title.font_name = CHINESE_FONT
            header.add_widget(header_title)

            self.add_widget(header)

            # 分隔线
            divider = BoxLayout(size_hint_y=None, height=dp(1))
            with divider.canvas.before:
                Color(*MODERN_COLORS['divider'])
                RoundedRectangle(pos=divider.pos, size=divider.size, radius=[0])
            divider.bind(pos=lambda i, v: self._update_divider(divider),
                        size=lambda i, v: self._update_divider(divider))
            self.add_widget(divider)

        # 内容容器
        self._content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(0),
        )
        self.add_widget(self._content)

    def add_field(self, widget):
        """添加字段到内容区"""
        field_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            size_hint_x=1,
        )

        # 字段容器
        field_container = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            size_hint_x=1,
            padding=(dp(20), dp(8), dp(20), dp(8)),
        )
        field_container.add_widget(widget)

        field_box.add_widget(field_container)

        # 分隔线（除最后一个）
        if len(self._content.children) > 0:
            divider = BoxLayout(size_hint_y=None, height=dp(1))
            with divider.canvas.before:
                Color(*MODERN_COLORS['divider'])
                rect = RoundedRectangle(pos=divider.pos, size=divider.size, radius=[0])
            divider.bind(pos=lambda i, v: setattr(rect, 'pos', v),
                        size=lambda i, v: setattr(rect, 'size', v))
            field_box.add_widget(divider)

        self._content.add_widget(field_box)
        self.height = dp(48 if self.title else 0) + dp(1 if self.title else 0) + \
                      len(self._content.children) * (widget.height + dp(16) + dp(1))

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        radius = dp(16)

        with self.canvas.before:
            # 阴影
            Color(*[0, 0, 0, 0.02])
            RoundedRectangle(
                pos=(self.x + dp(2), self.y - dp(2)),
                size=self.size,
                radius=[radius]
            )
            # 背景
            Color(*MODERN_COLORS['card'])
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])

    def _update_divider(self, divider):
        if divider.canvas.before.children:
            divider.canvas.before.children[0].pos = divider.pos
            divider.canvas.before.children[0].size = divider.size


class HeaderBar(BoxLayout):
    """页眉栏"""

    def __init__(self, title="", subtitle="", **kwargs):
        super().__init__(**kwargs)
        self.title_text = title
        self.subtitle_text = subtitle

        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(80)
        self.padding = (dp(20), dp(16), dp(20), dp(16))
        self.spacing = dp(16)

        self._bg_rect = None
        self._deco_line = None

        self._setup_ui()

    def _setup_ui(self):
        # 装饰背景
        self.bind(pos=self._update_canvas, size=self._update_canvas)

        # 返回按钮
        back_btn = BoxLayout(
            size_hint_x=None,
            width=dp(40),
            height=dp(40),
            padding=dp(8),
        )
        back_btn.bind(on_touch_down=lambda *args: self.dispatch('on_back'))

        with back_btn.canvas.before:
            Color(*[0, 0, 0, 0.04])
            RoundedRectangle(pos=back_btn.pos, size=back_btn.size, radius=[dp(12)])
        back_btn.bind(pos=lambda i, v: self._update_back_btn(back_btn),
                     size=lambda i, v: self._update_back_btn(back_btn))

        back_icon = MDIcon(
            icon="arrow-left",
            size_hint=(1, 1),
            halign="center",
            valign="middle",
            font_size=dp(20),
        )
        back_icon.color = MODERN_COLORS['text_primary']
        back_btn.add_widget(back_icon)
        self.add_widget(back_btn)

        # 标题区域
        title_box = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(4))

        title = Label(
            text=self.title_text,
            halign="left",
            valign="middle",
            color=MODERN_COLORS['text_primary'],
            font_size=dp(22),
            bold=True,
        )
        title.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        title_box.add_widget(title)

        if self.subtitle_text:
            subtitle = Label(
                text=self.subtitle_text,
                halign="left",
                valign="middle",
                color=MODERN_COLORS['text_secondary'],
                font_size=dp(13),
            )
            subtitle.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
            if CHINESE_FONT:
                subtitle.font_name = CHINESE_FONT
            title_box.add_widget(subtitle)

        self.add_widget(title_box)

    def _update_canvas(self, *args):
        # 装饰线
        pass

    def _update_back_btn(self, btn):
        btn.canvas.before.clear()
        with btn.canvas.before:
            Color(*[0, 0, 0, 0.04])
            RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(12)])

    __events__ = ('on_back',)

    def on_back(self):
        pass


class ItemWikiEditScreen(Screen):
    """物品Wiki编辑页 - 现代化设计"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "item_wiki_edit"
        self.wiki_id = None
        self.wiki_name = ""
        self.wiki_icon = ""
        self._icon_picker = None

        self._build_ui()

    def _build_ui(self):
        main_layout = BoxLayout(orientation="vertical")

        # 背景色
        with main_layout.canvas.before:
            Color(*MODERN_COLORS['surface'])

        # 页眉
        self._header = HeaderBar(
            title="编辑物品信息",
            subtitle="完善物品的基本信息和属性"
        )
        self._header.bind(on_back=self._on_cancel)
        main_layout.add_widget(self._header)

        # 滚动区域
        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=dp(0),
        )

        content_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(16),
        )
        content_box.bind(minimum_height=content_box.setter("height"))

        content_box.add_widget(BoxLayout(size_hint_y=None, height=dp(8)))

        # 图标选择卡片
        self._icon_card = IconSelectCard()
        self._icon_card.bind(on_release=self._on_icon_select)
        content_box.add_widget(self._icon_card)

        # 基本信息分组
        basic_card = SectionCard(title="基本信息", icon="information-outline")

        # 物品名称
        name_box = BoxLayout(orientation="vertical", spacing=dp(6))
        name_label = Label(
            text="物品名称",
            halign="left",
            valign="middle",
            color=MODERN_COLORS['text_secondary'],
            font_size=dp(13),
        )
        name_label.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        if CHINESE_FONT:
            name_label.font_name = CHINESE_FONT
        name_box.add_widget(name_label)

        self._name_input = ModernTextInput(
            hint_text="请输入物品名称",
        )
        name_box.add_widget(self._name_input)

        name_wrapper = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(70))
        name_wrapper.add_widget(name_box)
        basic_card.add_field(name_wrapper)

        # 分类
        category_box = BoxLayout(orientation="vertical", spacing=dp(6))
        category_label = Label(
            text="物品分类",
            halign="left",
            valign="middle",
            color=MODERN_COLORS['text_secondary'],
            font_size=dp(13),
        )
        category_label.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        if CHINESE_FONT:
            category_label.font_name = CHINESE_FONT
        category_box.add_widget(category_label)

        self._category_spinner = Spinner(
            size_hint_y=None,
            height=dp(52),
            font_size=dp(15),
            background_color=MODERN_COLORS['input_bg'],
            text="选择分类",
            values=[],
            option_cls='CustomSpinnerOption',
        )
        if CHINESE_FONT:
            self._category_spinner.font_name = CHINESE_FONT
        category_box.add_widget(self._category_spinner)

        cat_wrapper = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(70))
        cat_wrapper.add_widget(category_box)
        basic_card.add_field(cat_wrapper)

        content_box.add_widget(basic_card)

        # 规格参数分组
        spec_card = SectionCard(title="规格参数", icon="tune-variant")

        # 默认单位
        unit_box = BoxLayout(orientation="vertical", spacing=dp(6))
        unit_label = Label(
            text="默认单位",
            halign="left",
            valign="middle",
            color=MODERN_COLORS['text_secondary'],
            font_size=dp(13),
        )
        unit_label.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        if CHINESE_FONT:
            unit_label.font_name = CHINESE_FONT
        unit_box.add_widget(unit_label)

        self._unit_input = ModernTextInput(
            hint_text="例如：个、盒、瓶、袋",
        )
        unit_box.add_widget(self._unit_input)

        unit_wrapper = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(70))
        unit_wrapper.add_widget(unit_box)
        spec_card.add_field(unit_wrapper)

        # 建议保质期
        expiry_box = BoxLayout(orientation="vertical", spacing=dp(6))
        expiry_label = Label(
            text="建议保质期（天）",
            halign="left",
            valign="middle",
            color=MODERN_COLORS['text_secondary'],
            font_size=dp(13),
        )
        expiry_label.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        if CHINESE_FONT:
            expiry_label.font_name = CHINESE_FONT
        expiry_box.add_widget(expiry_label)

        self._expiry_input = ModernTextInput(
            hint_text="例如：7、30、365",
            input_filter="int",
        )
        expiry_box.add_widget(self._expiry_input)

        expiry_wrapper = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(70))
        expiry_wrapper.add_widget(expiry_box)
        spec_card.add_field(expiry_wrapper)

        # 存放位置
        location_box = BoxLayout(orientation="vertical", spacing=dp(6))
        location_label = Label(
            text="存放位置",
            halign="left",
            valign="middle",
            color=MODERN_COLORS['text_secondary'],
            font_size=dp(13),
        )
        location_label.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        if CHINESE_FONT:
            location_label.font_name = CHINESE_FONT
        location_box.add_widget(location_label)

        self._location_input = ModernTextInput(
            hint_text="例如：冷藏、常温、冷冻",
        )
        location_box.add_widget(self._location_input)

        loc_wrapper = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(70))
        loc_wrapper.add_widget(location_box)
        spec_card.add_field(loc_wrapper)

        content_box.add_widget(spec_card)

        # 描述信息分组
        desc_card = SectionCard(title="描述信息", icon="text-long")

        # 描述
        desc_box = BoxLayout(orientation="vertical", spacing=dp(6))
        desc_label = Label(
            text="物品描述",
            halign="left",
            valign="middle",
            color=MODERN_COLORS['text_secondary'],
            font_size=dp(13),
        )
        desc_label.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        if CHINESE_FONT:
            desc_label.font_name = CHINESE_FONT
        desc_box.add_widget(desc_label)

        self._description_input = ModernTextInput(
            hint_text="输入物品的详细描述...",
            is_multiline=True,
        )
        desc_box.add_widget(self._description_input)

        content_box.add_widget(desc_box)

        # 底部按钮区
        button_container = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=(dp(20), dp(8), dp(20), dp(8)),
            spacing=dp(12),
        )

        self._cancel_btn = ModernButton(
            text="取消",
            is_primary=False,
        )
        self._cancel_btn.bind(on_release=self._on_cancel)
        button_container.add_widget(self._cancel_btn)

        self._save_btn = ModernButton(
            text="保存修改",
            is_primary=True,
        )
        self._save_btn.bind(on_release=self._on_save)
        button_container.add_widget(self._save_btn)

        content_box.add_widget(button_container)
        content_box.add_widget(BoxLayout(size_hint_y=None, height=dp(20)))

        scroll.add_widget(content_box)
        main_layout.add_widget(scroll)
        self.add_widget(main_layout)

    def load_wiki(self, wiki_name: str):
        """加载要编辑的物品Wiki"""
        try:
            self.wiki_name = wiki_name
            wiki_item = wiki_service.get_wiki_by_name(wiki_name)

            if wiki_item:
                self.wiki_id = wiki_item['id']
                self.wiki_icon = wiki_item.get('icon', '')

                # 填充表单
                self._name_input.text = wiki_item['name']
                self._icon_card.set_icon(self.wiki_icon)
                self._description_input.text = wiki_item.get('description') or ""
                self._unit_input.text = wiki_item.get('default_unit') or ""
                self._expiry_input.text = str(wiki_item.get('suggested_expiry_days', '')) if wiki_item.get('suggested_expiry_days') else ""
                self._location_input.text = wiki_item.get('storage_location') or ""

                if wiki_item.get('category_name'):
                    self._category_spinner.text = wiki_item['category_name']
            else:
                logger.warning(f"物品Wiki不存在: {wiki_name}")
                self._name_input.text = wiki_name

            self._load_categories()

        except Exception as e:
            logger.error(f"加载物品Wiki失败: {str(e)}")

    def _load_categories(self):
        """加载分类列表"""
        try:
            categories = wiki_service.get_all_categories()
            category_names = [cat.name for cat in categories]
            self._category_spinner.values = category_names

            if not category_names:
                self._category_spinner.text = "暂无分类"

        except Exception as e:
            logger.error(f"加载分类列表失败: {str(e)}")

    def _on_icon_select(self, instance):
        """打开图标选择器"""
        if self._icon_picker is None:
            self._icon_picker = IconPicker(current_icon=self.wiki_icon)
            self._icon_picker.on_icon_selected = self._icon_selected
        else:
            self._icon_picker.current_icon = self.wiki_icon
            self._icon_picker.selected_icon = self.wiki_icon

        self._icon_picker.show()

    def _icon_selected(self, icon_name: str):
        """图标选择回调"""
        self.wiki_icon = icon_name
        self._icon_card.set_icon(icon_name)

    def _on_cancel(self, instance):
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            app.screen_manager.current = "item_wiki_detail"

    def _on_save(self, instance):
        try:
            name = self._name_input.text.strip()
            if not name:
                logger.warning("物品名称不能为空")
                return

            category_name = self._category_spinner.text
            category_id = None
            if category_name and category_name != "选择分类" and category_name != "暂无分类":
                categories = wiki_service.get_all_categories()
                for cat in categories:
                    if cat.name == category_name:
                        category_id = cat.id
                        break

            description = self._description_input.text.strip() or None
            default_unit = self._unit_input.text.strip() or None
            suggested_expiry_days = None
            if self._expiry_input.text.strip():
                try:
                    suggested_expiry_days = int(self._expiry_input.text.strip())
                except ValueError:
                    pass
            storage_location = self._location_input.text.strip() or None

            logger.info(f"准备保存Wiki: name={name}, icon={self.wiki_icon}, category_id={category_id}")

            updates = {
                'name': name,
                'icon': self.wiki_icon or None,
                'description': description,
                'default_unit': default_unit,
                'suggested_expiry_days': suggested_expiry_days,
                'storage_location': storage_location,
            }
            if category_id:
                updates['category_id'] = category_id

            if self.wiki_id:
                success = wiki_service.update_wiki(self.wiki_id, **updates)
                if success:
                    logger.info(f"物品Wiki更新成功: {name}")
                    self._navigate_back()
                else:
                    logger.error("物品Wiki更新失败")
            else:
                new_wiki = wiki_service.create_wiki(**updates)
                if new_wiki:
                    logger.info(f"物品Wiki创建成功: {name}")
                    self.wiki_id = new_wiki['id']
                    self.wiki_name = name
                    self._navigate_back()
                else:
                    logger.error("物品Wiki创建失败")

        except Exception as e:
            logger.error(f"保存物品Wiki失败: {str(e)}")

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

    def on_enter(self):
        pass

    def on_leave(self):
        pass
