# -*- coding: utf-8 -*-
"""
物品Wiki编辑页 - iOS 风格设计
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.textinput import TextInput
from kivy.uix.behaviors import ButtonBehavior
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle, Line, Rectangle
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

# iOS 风格配色方案
IOS_COLORS = {
    'background': [0.95, 0.95, 0.97, 1],      # iOS 浅灰背景
    'card': [1, 1, 1, 1],                    # iOS 白色卡片
    'primary': [0, 0.48, 1, 1],              # iOS 蓝色
    'input_bg': [1, 1, 1, 1],               # iOS 输入框白色背景
    'input_border': [0.8, 0.8, 0.82, 1],     # iOS 输入框边框
    'input_border_focused': [0, 0.48, 1, 1],  # iOS 聚焦边框（蓝色）
    'text_primary': [0, 0, 0, 1],            # iOS 黑色文字
    'text_secondary': [0.4, 0.4, 0.42, 1],   # iOS 灰色次要文字
    'text_hint': [0.6, 0.6, 0.62, 1],        # iOS 提示文字
    'divider': [0.82, 0.82, 0.84, 1],        # iOS 分隔线
    'icon_bg': [0.95, 0.95, 0.97, 1],        # iOS 图标背景
}


class CustomSpinnerOption(SpinnerOption):
    """简约风格下拉选项"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = [1, 1, 1, 1]  # 纯白背景
        self.color = IOS_COLORS['text_primary']
        self.height = dp(50)  # 与输入框高度一致
        self.font_size = dp(16)
        if CHINESE_FONT:
            self.font_name = CHINESE_FONT


# 解决循环引用
MATERIAL_COLORS = IOS_COLORS


class IOSButton(ButtonBehavior, BoxLayout):
    """iOS 风格按钮"""

    def __init__(self, text="", is_primary=True, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.is_primary = is_primary
        self._bg_rect = None
        self._pressed = False

        self.size_hint_y = None
        self.height = dp(44)  # iOS 标准按钮高度

        self._setup_ui(text)
        self._update_colors()

    def _setup_ui(self, text):
        # 背景
        self.bind(pos=self._update_canvas, size=self._update_canvas)

        label = Label(
            text=text,
            size_hint=(1, 1),
            halign="center",
            valign="middle",
            font_size=dp(17),  # iOS 标准字体大小
            bold=True,
            color=self._get_text_color(),
        )
        if CHINESE_FONT:
            label.font_name = CHINESE_FONT
        self.add_widget(label)

    def _get_bg_color(self):
        if self.is_primary:
            return IOS_COLORS['primary']
        return [1, 1, 1, 1]

    def _get_text_color(self):
        if self.is_primary:
            return [1, 1, 1, 1]
        return IOS_COLORS['primary']

    def _update_colors(self):
        for child in self.children:
            if isinstance(child, Label):
                child.color = self._get_text_color()

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        radius = dp(8)  # iOS 圆角较小

        bg_color = self._get_bg_color()
        if self._pressed:
            bg_color = [c * 0.9 for c in bg_color[:3]] + [bg_color[3]]

        with self.canvas.before:
            # iOS 按钮没有阴影
            Color(*bg_color)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])

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


class IOSTextInput(TextInput):
    """简约圆角边框输入框"""

    def __init__(self, hint_text="", is_multiline=False, **kwargs):
        super().__init__(**kwargs)
        self._bg_rect = None
        self._border_rect = None
        self._border_color = None
        self._focused = False

        # 确保 TextInput 填充宽度并设置固定高度
        self.size_hint = (1, None)
        self.height = dp(50) if not is_multiline else dp(88)

        # 使用白色背景
        self.background_color = [1, 1, 1, 1]
        self.background_normal = ''
        # 使用 explicit 的黑色文字颜色，而不是从 IOS_COLORS 获取
        self.foreground_color = [0, 0, 0, 1]
        self.cursor_color = [0, 0.48, 1, 1]
        self.multiline = is_multiline
        self.hint_text_color = [0.7, 0.7, 0.7, 1]
        self.hint_text = hint_text
        self.padding = (dp(14), dp(10), dp(14), dp(10))
        self.font_size = dp(16)
        self.border = [0, 0, 0, 0]
        self.write_tab = False  # 防止 Tab 键被当作输入

        if CHINESE_FONT:
            self.font_name = CHINESE_FONT
            logger.info(f"IOSTextInput 使用中文字体: {CHINESE_FONT}")
        else:
            logger.info(f"IOSTextInput 未设置中文字体")

        logger.info(f"IOSTextInput 初始化: readonly={self.readonly}, disabled={self.disabled}")
        logger.info(f"  foreground_color={self.foreground_color}, hint_text_color={self.hint_text_color}")
        logger.info(f"  font_size={self.font_size}, font_name={self.font_name}")
        logger.info(f"  size_hint={self.size_hint}, height={self.height}")

        self.bind(focus=self._on_focus_change)
        self.bind(on_text_validate=self._on_text_validate)

    def _on_focus_change(self, instance, value):
        logger.info(f"IOSTextInput 焦点变化: {value}, readonly={self.readonly}, disabled={self.disabled}")
        self._focused = value

    def _on_text_validate(self, instance):
        logger.info(f"IOSTextInput 文本确认: {instance.text}")

    def keyboard_on_key_down(self, window, keycode, text, modifiers):
        logger.info(f"键盘按下: keycode={keycode}, text={text}")
        result = super().keyboard_on_key_down(window, keycode, text, modifiers)
        logger.info(f"键盘处理后: text='{self.text}', result={result}")
        return result

    def insert_text(self, substring, from_undo=False):
        logger.info(f"插入文本: '{substring}', 当前文本: '{self.text}'")
        super().insert_text(substring, from_undo=from_undo)
        logger.info(f"插入后文本: '{self.text}'")

    def on_text(self, instance, value):
        logger.info(f"文本变化: '{value}'")


class IconSelectCard(ButtonBehavior, BoxLayout):
    """图标选择卡片"""

    def __init__(self, icon_name="", **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self._bg_rect = None
        self._pressed = False

        self.orientation = "horizontal"
        self.size_hint_y = None
        self.size_hint_x = 1
        self.height = dp(60)
        self.padding = dp(16)
        self.spacing = dp(14)

        self._setup_ui()
        self._update_canvas()
        self.bind(pos=self._update_canvas, size=self._update_canvas)

    def _setup_ui(self):
        icon_display = self.icon_name if self.icon_name else "help-circle-outline"

        # 图标容器 - 使用 AnchorLayout 让图标绝对居中
        icon_anchor = AnchorLayout(
            size_hint_x=None,
            width=dp(44),
            height=dp(44),
        )

        # 圆圈背景
        with icon_anchor.canvas.before:
            Color(0.94, 0.95, 1, 1)  # 浅灰色背景
            self._icon_circle = RoundedRectangle(
                pos=(icon_anchor.x, icon_anchor.y),
                size=icon_anchor.size,
                radius=[dp(22)]
            )
        icon_anchor.bind(pos=self._update_icon_circle, size=self._update_icon_circle)

        # 图标
        icon = MDIcon(
            icon=icon_display,
            size_hint=(None, None),
            width=dp(24),
            height=dp(24),
            font_size=dp(24),
        )
        icon.color = IOS_COLORS['primary']
        icon_anchor.add_widget(icon)
        self._icon_widget = icon
        self.add_widget(icon_anchor)

        # 文字区域
        text_box = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(2))

        title = Label(
            text="物品图标",
            halign="left",
            valign="middle",
            color=IOS_COLORS['text_primary'],
            font_size=dp(15),
            bold=True,
        )
        title.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        title.height = dp(20)
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        text_box.add_widget(title)

        self._subtitle = Label(
            text=self.icon_name if self.icon_name else "点击选择图标",
            halign="left",
            valign="bottom",
            color=IOS_COLORS['text_hint'],
            font_size=dp(13),
        )
        self._subtitle.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        self._subtitle.height = dp(18)
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
        arrow.color = IOS_COLORS['text_hint']
        self.add_widget(arrow)

    def _update_icon_circle(self, *args):
        if hasattr(self, '_icon_circle'):
            # 找到 icon_anchor
            for child in self.children:
                if isinstance(child, AnchorLayout):
                    self._icon_circle.pos = child.pos
                    self._icon_circle.size = child.size
                    break

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        radius = dp(14)

        bg_color = IOS_COLORS['input_bg']
        if self._pressed:
            bg_color = [c * 0.98 for c in bg_color[:3]] + [bg_color[3]]

        with self.canvas.before:
            # 阴影
            Color(*[0, 0, 0, 0.02])
            RoundedRectangle(
                pos=(self.x + dp(1), self.y - dp(1)),
                size=self.size,
                radius=[radius]
            )
            # 背景
            Color(*bg_color)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
            # 边框
            Color(*IOS_COLORS['input_border'])
            Line(
                width=dp(1),
                rounded_rectangle=(self.x, self.y, self.width, self.height, radius)
            )

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
        self._shadow_rect = None  # 保存阴影引用
        self._bg_rect = None  # 保存背景引用
        self._border_color = None  # 保存边框颜色引用
        self._border_line = None  # 保存边框线条引用

        self.orientation = "vertical"
        self.size_hint_y = size_hint_y or None
        self.spacing = dp(0)

        self._setup_ui()

    def _setup_ui(self):
        # 绑定位置和大小变化
        self.bind(pos=self._update_canvas, size=self._update_canvas)

        # 标题栏
        if self.title:
            header = BoxLayout(
                orientation="horizontal",
                size_hint=(1, None),
                height=dp(44),
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
                header_icon.color = IOS_COLORS['primary']
                header.add_widget(header_icon)

            header_title = Label(
                text=self.title,
                size_hint=(1, 1),
                halign="left",
                valign="middle",
                color=IOS_COLORS['text_primary'],
                font_size=dp(16),
                bold=True,
            )
            if CHINESE_FONT:
                header_title.font_name = CHINESE_FONT
            header.add_widget(header_title)

            self.add_widget(header)

            # 分隔线
            divider = BoxLayout(
                size_hint=(1, None),
                height=dp(1),
            )
            with divider.canvas.before:
                Color(*IOS_COLORS['divider'])
                divider.rect = RoundedRectangle(pos=divider.pos, size=divider.size, radius=[0])
            divider.bind(pos=lambda i, v: self._update_divider(divider),
                        size=lambda i, v: self._update_divider(divider))
            self.add_widget(divider)

        # 内容容器 - 使用 auto layout 自动计算高度
        self._content = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            spacing=dp(0),
        )
        self._content.bind(minimum_height=self._content.setter('height'))
        self.add_widget(self._content)

        # 卡片高度由标题和内容自动决定
        header_height = dp(44) + dp(1) if self.title else 0
        self._content.bind(minimum_height=lambda inst, val: setattr(self, 'height', header_height + val))

    def add_field(self, label_text, widget):
        """添加字段到内容区"""
        # 检测是否为多行输入框
        is_multiline = hasattr(widget, 'multiline') and widget.multiline

        if is_multiline:
            # 多行输入框使用垂直布局（标签在上，输入框在下）
            field_container = BoxLayout(
                orientation="vertical",
                size_hint=(1, None),
                padding=(dp(20), dp(6), dp(20), dp(6)),
                spacing=dp(4),
            )

            # 标签
            label = Label(
                text=label_text,
                size_hint=(1, None),
                height=dp(22),
                halign="left",
                valign="bottom",
                color=IOS_COLORS['text_secondary'],
                font_size=dp(14),
            )
            if CHINESE_FONT:
                label.font_name = CHINESE_FONT
            field_container.add_widget(label)

            # 输入框容器，高度由widget决定
            widget_container = BoxLayout(
                orientation="vertical",
                size_hint=(1, None),
                height=widget.height,
            )
            widget_container.add_widget(widget)
            field_container.add_widget(widget_container)

            field_container.bind(minimum_height=field_container.setter('height'))

        else:
            # 单行输入框使用水平布局（标签在左，输入框在右）
            field_container = BoxLayout(
                orientation="horizontal",
                size_hint=(1, None),
                padding=(dp(20), dp(8), dp(20), dp(8)),
            )

            # 左侧标签 - 使用相对宽度适应不同屏幕
            label_box = BoxLayout(
                orientation="vertical",
                size_hint_x=0.28,  # 占28%宽度，适应不同屏幕
                size_hint_y=1,
            )
            label = Label(
                text=label_text,
                halign="left",
                valign="middle",
                color=IOS_COLORS['text_secondary'],
                font_size=dp(14),
            )
            if CHINESE_FONT:
                label.font_name = CHINESE_FONT
            label_box.add_widget(label)
            field_container.add_widget(label_box)

            # 间距 - 也使用相对宽度
            spacing = BoxLayout(size_hint_x=0.03)  # 占3%宽度
            field_container.add_widget(spacing)

            # 右侧输入框容器 - 宽度自适应，高度由widget决定
            widget_container = BoxLayout(
                orientation="vertical",
                size_hint_x=1,  # 剩余约69%宽度
                size_hint_y=None,  # 不自适应高度
                height=widget.height,  # 固定高度为widget的高度
            )
            widget_container.add_widget(widget)
            field_container.add_widget(widget_container)

            field_container.bind(minimum_height=field_container.setter('height'))

        # 分隔线（除最后一个）
        if len(self._content.children) > 0:
            divider = BoxLayout(
                size_hint=(1, None),
                height=dp(1),
            )
            with divider.canvas.before:
                Color(*IOS_COLORS['divider'])
                rect = RoundedRectangle(pos=divider.pos, size=divider.size, radius=[0])
            divider.bind(pos=lambda i, v: setattr(rect, 'pos', v),
                        size=lambda i, v: setattr(rect, 'size', v))
            self._content.add_widget(divider)

        self._content.add_widget(field_container)

    def _update_canvas(self, *args):
        # 使用 canvas.before 来绘制背景和阴影，canvas.after 会覆盖子组件的渲染
        radius = dp(16)

        # 只在首次创建时绘制背景和阴影
        if self._bg_rect is None:
            with self.canvas.before:
                # 阴影
                Color(*[0, 0, 0, 0.08], group='card_bg')
                self._shadow_rect = RoundedRectangle(
                    pos=(self.x + dp(2), self.y - dp(2)),
                    size=self.size,
                    radius=[radius],
                    group='card_bg'
                )
                # 背景 - 稍微浅一点的白色，与背景有区分
                Color(*[0.98, 0.98, 0.99, 1], group='card_bg')
                self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius], group='card_bg')

        # 边框 - 使用 Line 绘制轮廓（不填充），避免遮挡子组件
        # 清除旧的边框指令
        try:
            if self._border_color and self._border_color in self.canvas.before.children:
                self.canvas.before.remove(self._border_color)
        except:
            pass
        try:
            if self._border_line and self._border_line in self.canvas.before.children:
                self.canvas.before.remove(self._border_line)
        except:
            pass

        # 重新绘制边框（使用 Line，只画轮廓）
        with self.canvas.before:
            self._border_color = Color(*[0.85, 0.85, 0.87, 1])
            self._border_line = Line(
                width=dp(1),
                rounded_rectangle=(self.x, self.y, self.width, self.height, radius)
            )

        # 更新阴影和背景的位置大小
        if self._shadow_rect:
            self._shadow_rect.pos = (self.x + dp(2), self.y - dp(2))
            self._shadow_rect.size = self.size
        if self._bg_rect:
            self._bg_rect.pos = self.pos
            self._bg_rect.size = self.size

    def _update_divider(self, divider):
        if hasattr(divider, 'rect'):
            divider.rect.pos = divider.pos
            divider.rect.size = divider.size

    def on_touch_down(self, touch):
        # 将触摸事件传递给子 widget，确保 TextInput 可以接收点击
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        # 传递移动事件
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        # 传递抬起事件
        return super().on_touch_up(touch)


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
        back_icon.color = IOS_COLORS['text_primary']
        back_btn.add_widget(back_icon)
        self.add_widget(back_btn)

        # 标题区域
        title_box = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(4))

        title = Label(
            text=self.title_text,
            halign="left",
            valign="middle",
            color=IOS_COLORS['text_primary'],
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
                color=IOS_COLORS['text_secondary'],
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
            Color(*IOS_COLORS['background'])

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
            size_hint=(1, None),
            spacing=dp(4),
        )
        content_box.bind(minimum_height=content_box.setter("height"))

        # 顶部间距
        content_box.add_widget(BoxLayout(size_hint=(1, None), height=dp(6)))

        # 图标选择卡片
        self._icon_card = IconSelectCard()
        self._icon_card.bind(on_release=self._on_icon_select)
        content_box.add_widget(self._icon_card)

        # 基本信息分组
        basic_card = SectionCard(title="基本信息", icon="information-outline")

        # 物品名称
        self._name_input = IOSTextInput(
            hint_text="请输入物品名称",
        )
        basic_card.add_field("物品名称", self._name_input)

        # 分类
        self._category_spinner = Spinner(
            size_hint_y=None,
            height=dp(50),  # 与输入框高度一致
            font_size=dp(16),
            background_color=[1, 1, 1, 1],  # 纯白背景
            text="选择分类",
            values=[],
            option_cls='CustomSpinnerOption',
        )
        if CHINESE_FONT:
            self._category_spinner.font_name = CHINESE_FONT
        basic_card.add_field("物品分类", self._category_spinner)

        content_box.add_widget(basic_card)

        # 规格参数分组
        spec_card = SectionCard(title="规格参数", icon="tune-variant")

        # 默认单位 - 下拉选择
        self._unit_spinner = Spinner(
            size_hint_y=None,
            height=dp(50),
            font_size=dp(16),
            background_color=[1, 1, 1, 1],
            text="选择单位",
            values=["个", "盒", "瓶", "袋", "包", "罐", "斤", "公斤", "条", "片", "支", "其他"],
            option_cls='CustomSpinnerOption',
        )
        if CHINESE_FONT:
            self._unit_spinner.font_name = CHINESE_FONT
        spec_card.add_field("默认单位", self._unit_spinner)

        # 建议保质期
        self._expiry_input = IOSTextInput(
            hint_text="例如：7、30、365",
            input_filter="int",
        )
        spec_card.add_field("建议保质期（天）", self._expiry_input)

        # 存放位置 - 下拉选择
        self._location_spinner = Spinner(
            size_hint_y=None,
            height=dp(50),
            font_size=dp(16),
            background_color=[1, 1, 1, 1],
            text="选择位置",
            values=["常温", "冷藏", "冷冻", "阴凉", "其他"],
            option_cls='CustomSpinnerOption',
        )
        if CHINESE_FONT:
            self._location_spinner.font_name = CHINESE_FONT
        spec_card.add_field("存放位置", self._location_spinner)

        content_box.add_widget(spec_card)

        # 描述信息分组
        desc_card = SectionCard(title="描述信息", icon="text-long")

        self._description_input = IOSTextInput(
            hint_text="输入物品的详细描述...",
            is_multiline=True,
        )
        desc_card.add_field("物品描述", self._description_input)
        content_box.add_widget(desc_card)

        # 底部按钮区
        button_container = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(56),
            padding=(dp(20), dp(8), dp(20), dp(8)),
            spacing=dp(12),
        )

        self._cancel_btn = IOSButton(
            text="取消",
            is_primary=False,
        )
        self._cancel_btn.bind(on_release=self._on_cancel)
        button_container.add_widget(self._cancel_btn)

        self._save_btn = IOSButton(
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
            logger.info(f"开始加载Wiki: wiki_name={wiki_name}")

            wiki_item = wiki_service.get_wiki_by_name(wiki_name)
            logger.info(f"获取到的Wiki数据: {wiki_item}")

            # 先加载分类列表（必须先加载才能正确设置分类）
            self._load_categories()

            if wiki_item:
                self.wiki_id = wiki_item['id']
                self.wiki_icon = wiki_item.get('icon', '')

                # 填充表单
                logger.info(f"设置物品名称: {wiki_item['name']}")
                self._name_input.text = wiki_item['name']
                self._icon_card.set_icon(self.wiki_icon)
                self._description_input.text = wiki_item.get('description') or ""

                # 单位 - 如果数据库中的值不在选项列表中，使用"其他"
                unit_value = wiki_item.get('default_unit') or ""
                if unit_value in self._unit_spinner.values:
                    self._unit_spinner.text = unit_value
                else:
                    self._unit_spinner.text = "其他"

                self._expiry_input.text = str(wiki_item.get('suggested_expiry_days', '')) if wiki_item.get('suggested_expiry_days') else ""

                # 存放位置 - 如果数据库中的值不在选项列表中，使用"其他"
                location_value = wiki_item.get('storage_location') or ""
                if location_value in self._location_spinner.values:
                    self._location_spinner.text = location_value
                else:
                    self._location_spinner.text = "其他"

                if wiki_item.get('category_name'):
                    self._category_spinner.text = wiki_item['category_name']
            else:
                logger.warning(f"物品Wiki不存在: {wiki_name}")
                self._name_input.text = wiki_name

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
        # 确保 wiki_icon 不是 None，使用默认值
        current_icon = self.wiki_icon if self.wiki_icon else "help-circle-outline"

        if self._icon_picker is None:
            self._icon_picker = IconPicker(current_icon=current_icon)
            self._icon_picker.on_icon_selected = self._icon_selected
        else:
            self._icon_picker.current_icon = current_icon
            self._icon_picker.selected_icon = current_icon

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
            default_unit = self._unit_spinner.text if self._unit_spinner.text != "选择单位" else None
            suggested_expiry_days = None
            if self._expiry_input.text.strip():
                try:
                    suggested_expiry_days = int(self._expiry_input.text.strip())
                except ValueError:
                    pass
            storage_location = self._location_spinner.text if self._location_spinner.text != "选择位置" else None

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
