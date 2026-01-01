# -*- coding: utf-8 -*-
"""
图标选择器组件 - 美化版
"""

from kivy.uix.modalview import ModalView
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line, Ellipse
from kivy.animation import Animation
from kivy.properties import ObjectProperty, StringProperty, BooleanProperty
from kivymd.uix.label import MDIcon

try:
    from app.utils.font_helper import CHINESE_FONT_NAME
except:
    CHINESE_FONT_NAME = None

from app.ui.theme.design_tokens import COLOR_PALETTE

COLORS = COLOR_PALETTE

# 鲜艳配色
BRIGHT_COLORS = {
    'primary': [0.39, 0.40, 0.95, 1],
    'success': [0.13, 0.77, 0.37, 1],
    'warning': [0.96, 0.35, 0.07, 1],
    'error': [0.94, 0.27, 0.27, 1],
    'surface': [1, 1, 1, 1],
    'surface_variant': [0.96, 0.96, 0.96, 1],
    'background': [0.98, 0.98, 0.99, 1],
    'text_primary': [0.15, 0.15, 0.15, 1],
    'text_secondary': [0.50, 0.50, 0.50, 1],
    'accent': [0.40, 0.20, 0.80, 1],
}

# 常用图标列表 - 使用 Material Design 确认存在的图标名称
ICON_NAMES = [
    # 食品
    "bottle-tonic", "coffee", "coffee-to-go", "egg", "fish",
    "food", "food-apple", "hamburger", "food-drumstick",
    "pizza", "tea", "water", "bottle-wine", "glass-wine",
    "cup", "beaker", "flask", "food-steak",
    # 个人护理
    "brush", "lipstick", "shower", "tooth",
    # 日用
    "home", "basket", "bag-personal", "bottle-soda",
    "pot", "shower-head",
    # 文具
    "pencil", "pen", "notebook", "book", "book-open",
    "clipboard", "file", "file-document",
    # 医药
    "medical-bag", "pill", "stethoscope", "bandage", "hospital-box",
    "medication", "needle", "thermometer", "heart-pulse",
    # 其他
    "package-variant", "archive", "gift", "star",
    "star-outline", "crown", "cube", "link",
    "help-circle", "information", "account", "cog",
]


class IconCard(ButtonBehavior, BoxLayout):
    """美观的图标卡片"""
    __events__ = ('on_release',)

    icon_name = StringProperty()
    is_selected = BooleanProperty(False)
    _hovered = False

    def __init__(self, icon_name, **kwargs):
        super().__init__(**kwargs)
        self.icon_name = icon_name
        self.orientation = "vertical"
        self.size_hint_x = 1  # 填充网格分配的水平空间
        self.size_hint_y = None
        self.height = dp(78)  # 增加高度以容纳图标名称
        self.padding = dp(0)
        self.spacing = dp(0)

        self._bg_rect = None
        self._bg_color = None
        self._icon_widget = None
        self._name_label = None
        self._touch_inside = False

        self._setup_ui()
        self._update_visual_state()
        self.bind(pos=self._update_background, size=self._update_background)

    def _setup_ui(self):
        # 使用 AnchorLayout 确保图标居中
        anchor_layout = AnchorLayout(
            size_hint=(1, 1),
            anchor_x="center",
            anchor_y="center"
        )
        self.add_widget(anchor_layout)

        # 图标
        self._icon_widget = MDIcon(
            icon=self.icon_name,
            size_hint=(None, None),
            width=dp(60),
            height=dp(60),
            halign="center",
            valign="middle",
            font_size=dp(48),
        )
        # 设置初始颜色
        self._icon_widget.color = self._get_icon_color()
        anchor_layout.add_widget(self._icon_widget)

        # 图标名称标签
        self._name_label = Label(
            text=self.icon_name,
            size_hint_y=None,
            height=dp(14),
            font_size=dp(9),
            color=self._get_text_color(),
            halign="center",
            valign="middle",
        )
        self.add_widget(self._name_label)

    def _get_bg_color(self):
        if self.is_selected:
            return [0.95, 0.88, 1, 1]  # 选中：淡紫色背景
        return [0.98, 0.98, 0.99, 1]  # 默认：浅灰背景

    def _get_border_color(self):
        if self.is_selected:
            return [0.60, 0.30, 0.95, 1]  # 选中：紫色边框
        return [0.90, 0.90, 0.95, 0.3]  # 默认：浅灰边框

    def _get_icon_color(self):
        if self.is_selected:
            return [0.60, 0.30, 0.95, 1]  # 选中：紫色图标
        return BRIGHT_COLORS['text_primary']  # 默认：深灰色图标

    def _get_text_color(self):
        if self.is_selected:
            return [0.60, 0.30, 0.95, 1]  # 选中：紫色文字
        return BRIGHT_COLORS['text_secondary']  # 默认：灰色文字

    def _update_background(self, instance=None, value=None):
        self.canvas.before.clear()
        bg_color = self._get_bg_color()
        border_color = self._get_border_color()
        radius = dp(12)

        with self.canvas.before:
            # 背景填充
            Color(*bg_color)
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])

            # 边框
            Color(*border_color)
            self._border_rect = Line(
                width=dp(2),
                rounded_rectangle=(self.x, self.y, self.width, self.height, radius)
            )

        # 更新图标颜色
        if self._icon_widget:
            self._icon_widget.color = self._get_icon_color()

        # 更新名称标签颜色
        if self._name_label:
            self._name_label.color = self._get_text_color()

    def _update_visual_state(self):
        self._update_background()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._touch_inside = True
            self._update_visual_state()
            # 立即返回 True 防止事件传播
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self._touch_inside and self.collide_point(*touch.pos):
            if not self._hovered:
                self._hovered = True
                self._update_visual_state()
        else:
            if self._hovered:
                self._hovered = False
                self._update_visual_state()

    def on_touch_up(self, touch):
        if self._touch_inside:
            self._touch_inside = False
            if self.collide_point(*touch.pos):
                # 在区域内释放，触发选择
                self.dispatch('on_release')
            # 清除悬停状态
            self._hovered = False
            self._update_visual_state()
            return True
        # 清除悬停状态
        self._hovered = False
        self._update_visual_state()

    def on_release(self, *args):
        pass


class HeaderBar(BoxLayout):
    """标题栏"""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(64)
        self.padding = (dp(20), dp(12), dp(20), dp(12))
        self.spacing = dp(12)

        # 左侧装饰
        deco = BoxLayout(size_hint_x=None, width=dp(4))
        with deco.canvas.before:
            Color(*[0.60, 0.30, 0.95, 1])
            self._deco_rect = Rectangle(pos=deco.pos, size=deco.size)
        deco.bind(pos=lambda i, v: self._update_deco_pos(v), size=lambda i, v: self._update_deco_size(v))
        self.add_widget(deco)

        # 标题文本
        title_box = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(2))
        title = Label(
            text="选择图标",
            font_size=dp(20),
            color=BRIGHT_COLORS['text_primary'],
            halign="left",
            valign="middle",
            bold=True,
        )
        if CHINESE_FONT_NAME:
            title.font_name = CHINESE_FONT_NAME
        title.size_hint_y = None
        title.height = dp(28)
        title.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        title_box.add_widget(title)

        subtitle = Label(
            text=f"共 {len(ICON_NAMES)} 个可选图标",
            font_size=dp(12),
            color=BRIGHT_COLORS['text_secondary'],
            halign="left",
            valign="middle",
        )
        if CHINESE_FONT_NAME:
            subtitle.font_name = CHINESE_FONT_NAME
        subtitle.size_hint_y = None
        subtitle.height = dp(16)
        subtitle.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        title_box.add_widget(subtitle)

        self.add_widget(title_box)

    def _update_deco_pos(self, pos):
        if hasattr(self, '_deco_rect'):
            self._deco_rect.pos = pos

    def _update_deco_size(self, size):
        if hasattr(self, '_deco_rect'):
            self._deco_rect.size = size


class SelectedPreview(BoxLayout):
    """选中图标预览"""
    def __init__(self, icon_name="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(56)
        self.padding = (dp(20), dp(8), dp(20), dp(8))
        self.spacing = dp(16)

        # 背景卡片
        with self.canvas.before:
            Color(*[0.96, 0.96, 1, 1])
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=lambda i, v: self._update_bg_pos(v), size=lambda i, v: self._update_bg_size(v))

        # 图标显示
        self._icon_display = BoxLayout(
            size_hint_x=None, width=dp(40), height=dp(40),
            padding=dp(0)
        )
        with self._icon_display.canvas.before:
            Color(*[0.60, 0.30, 0.95, 0.12])
            self._icon_bg = Ellipse(pos=self._icon_display.pos, size=self._icon_display.size)
        self._icon_display.bind(pos=lambda i, v: self._update_icon_bg_pos(v), size=lambda i, v: self._update_icon_bg_size(v))
        self.add_widget(self._icon_display)

        # 文字显示
        text_box = BoxLayout(orientation="vertical", size_hint_x=1)
        self._icon_widget = MDIcon(
            icon=icon_name if icon_name else "help-circle-outline",
            font_size=dp(22),
            halign="center",
            valign="middle",
        )
        self._icon_widget.color = [0.60, 0.30, 0.95, 1]
        self._icon_display.add_widget(self._icon_widget)

        # 更新图标显示
        self._label_main = Label(
            text="已选择" if icon_name else "未选择",
            font_size=dp(14),
            color=BRIGHT_COLORS['text_primary'],
            halign="left",
            valign="middle",
            bold=True,
        )
        if CHINESE_FONT_NAME:
            self._label_main.font_name = CHINESE_FONT_NAME
        self._label_main.size_hint_y = None
        self._label_main.height = dp(20)
        self._label_main.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        text_box.add_widget(self._label_main)

        self._label_sub = Label(
            text=icon_name if icon_name else "点击下方图标进行选择",
            font_size=dp(12),
            color=BRIGHT_COLORS['text_secondary'],
            halign="left",
            valign="middle",
        )
        if CHINESE_FONT_NAME:
            self._label_sub.font_name = CHINESE_FONT_NAME
        self._label_sub.size_hint_y = None
        self._label_sub.height = dp(18)
        self._label_sub.bind(size=lambda i, v: setattr(i, "text_size", (v[0], None)))
        text_box.add_widget(self._label_sub)

        self.add_widget(text_box)

    def _update_bg_pos(self, pos):
        if hasattr(self, '_bg_rect'):
            self._bg_rect.pos = pos

    def _update_bg_size(self, size):
        if hasattr(self, '_bg_rect'):
            self._bg_rect.size = size

    def _update_icon_bg_pos(self, pos):
        if hasattr(self, '_icon_bg'):
            self._icon_bg.pos = pos

    def _update_icon_bg_size(self, size):
        if hasattr(self, '_icon_bg'):
            self._icon_bg.size = size

    def set_icon(self, icon_name):
        self._icon_widget.icon = icon_name if icon_name else "help-circle-outline"
        self._label_main.text = "已选择" if icon_name else "未选择"
        self._label_sub.text = icon_name if icon_name else "点击下方图标进行选择"


class IconPickerActionBar(BoxLayout):
    """底部操作栏"""
    def __init__(self, on_cancel=None, on_confirm=None, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(72)
        self.padding = (dp(20), dp(16), dp(20), dp(16))
        self.spacing = dp(12)
        self._on_cancel = on_cancel
        self._on_confirm = on_confirm

        # 取消按钮
        cancel = BoxLayout(
            size_hint_x=0.5, size_hint_y=None, height=dp(48),
            padding=dp(0)
        )
        cancel._bg_rect = None
        with cancel.canvas.before:
            Color(*[0.95, 0.95, 0.97, 1])
            cancel._bg_rect = RoundedRectangle(pos=cancel.pos, size=cancel.size, radius=[dp(12)])
            Color(*[0.50, 0.50, 0.55, 0.3])
            Line(width=dp(1.5), rounded_rectangle=(
                cancel.x, cancel.y, cancel.width, cancel.height, dp(12)
            ))
        cancel.bind(pos=lambda i, v: self._update_cancel_bg_pos(v),
                   size=lambda i, v: self._update_cancel_bg_size(v))

        cancel_label = Label(
            text="取消",
            font_size=dp(15),
            color=BRIGHT_COLORS['text_secondary'],
            halign="center",
            valign="middle",
        )
        if CHINESE_FONT_NAME:
            cancel_label.font_name = CHINESE_FONT_NAME
        cancel.add_widget(cancel_label)

        # 添加点击处理
        def on_cancel_touch_down(t):
            if cancel.collide_point(*t.pos):
                setattr(cancel_label, 'color', [0.30, 0.30, 0.35, 1])
                return True
            return False

        def on_cancel_touch_up(t):
            if cancel.collide_point(*t.pos):
                setattr(cancel_label, 'color', BRIGHT_COLORS['text_secondary'])
                if self._on_cancel:
                    self._on_cancel(cancel)
                return True
            return False

        cancel.on_touch_down = on_cancel_touch_down
        cancel.on_touch_up = on_cancel_touch_up

        self.add_widget(cancel)
        self._cancel_btn = cancel

        # 确定按钮
        confirm = BoxLayout(
            size_hint_x=0.5, size_hint_y=None, height=dp(48),
            padding=dp(0)
        )
        confirm._bg_rect = None
        with confirm.canvas.before:
            Color(*[0.60, 0.30, 0.95, 1])
            confirm._bg_rect = RoundedRectangle(pos=confirm.pos, size=confirm.size, radius=[dp(12)])
        confirm.bind(pos=lambda i, v: self._update_confirm_bg_pos(v),
                   size=lambda i, v: self._update_confirm_bg_size(v))

        confirm_label = Label(
            text="确定选择",
            font_size=dp(15),
            color=[1, 1, 1, 1],
            halign="center",
            valign="middle",
            bold=True,
        )
        if CHINESE_FONT_NAME:
            confirm_label.font_name = CHINESE_FONT_NAME
        confirm.add_widget(confirm_label)

        # 点击效果
        def on_confirm_touch_down(t):
            if confirm.collide_point(*t.pos):
                setattr(confirm_label, 'color', [0.90, 0.50, 0.90, 1])
                return True
            return False

        def on_confirm_touch_up(t):
            if confirm.collide_point(*t.pos):
                setattr(confirm_label, 'color', [1, 1, 1, 1])
                if self._on_confirm:
                    self._on_confirm(confirm)
                return True
            return False

        confirm.on_touch_down = on_confirm_touch_down
        confirm.on_touch_up = on_confirm_touch_up

        self.add_widget(confirm)
        self._confirm_btn = confirm

    def _update_cancel_bg_pos(self, pos):
        if hasattr(self, '_cancel_btn') and hasattr(self._cancel_btn, '_bg_rect'):
            self._update_cancel_bg()

    def _update_cancel_bg_size(self, size):
        if hasattr(self, '_cancel_btn') and hasattr(self._cancel_btn, '_bg_rect'):
            self._update_cancel_bg()

    def _update_cancel_bg(self):
        if hasattr(self, '_cancel_btn'):
            btn = self._cancel_btn
            btn.canvas.before.clear()
            with btn.canvas.before:
                Color(*[0.95, 0.95, 0.97, 1])
                RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(12)])
                Color(*[0.50, 0.50, 0.55, 0.3])
                Line(width=dp(1.5), rounded_rectangle=(
                    btn.x, btn.y, btn.width, btn.height, dp(12)
                ))

    def _update_confirm_bg_pos(self, pos):
        if hasattr(self, '_confirm_btn'):
            self._update_confirm_bg()

    def _update_confirm_bg_size(self, size):
        if hasattr(self, '_confirm_btn'):
            self._update_confirm_bg()

    def _update_confirm_bg(self):
        if hasattr(self, '_confirm_btn'):
            btn = self._confirm_btn
            btn.canvas.before.clear()
            with btn.canvas.before:
                Color(*[0.60, 0.30, 0.95, 1])
                RoundedRectangle(pos=btn.pos, size=btn.size, radius=[dp(12)])


class IconPicker(ModalView):
    """图标选择器对话框 - 美化版"""
    selected_icon = StringProperty("")
    on_icon_selected = ObjectProperty(None)

    def __init__(self, current_icon=None, **kwargs):
        super().__init__(**kwargs)
        self.current_icon = current_icon
        self.selected_icon = current_icon or ""
        self._selected_buttons = {}
        self._build_ui()

    def _build_ui(self):
        self.size_hint = (0.85, 0.75)
        self.pos_hint = {'center_x': 0.5, 'center_y': 0.5}
        self.background_color = [1, 1, 1, 1]
        self.auto_dismiss = False

        # 主容器
        main_layout = BoxLayout(
            orientation="vertical",
            padding=dp(8),
            spacing=dp(8),
        )

        # 标题栏
        header = HeaderBar()
        main_layout.add_widget(header)

        # 图标网格区域
        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=dp(0),
        )

        self._grid = GridLayout(
            cols=3,
            spacing=dp(8),
            padding=dp(6),
            size_hint_y=None
        )
        self._grid.bind(minimum_height=self._grid.setter('height'))
        scroll.add_widget(self._grid)

        main_layout.add_widget(scroll)

        # 创建图标卡片
        for icon_name in ICON_NAMES:
            card = IconCard(icon_name)
            # 使用闭包捕获正确的 icon_name
            def make_handler(name):
                return lambda x, _=None: self._select_icon(name)
            card.bind(on_release=make_handler(icon_name))
            self._selected_buttons[icon_name] = card
            self._grid.add_widget(card)

        # 底部操作栏
        action_bar = IconPickerActionBar(
            on_cancel=self._on_cancel,
            on_confirm=lambda x: self._on_confirm(x)
        )
        main_layout.add_widget(action_bar)

        self.add_widget(main_layout)

        # 更新选中样式
        if self.selected_icon and self.selected_icon in self._selected_buttons:
            self._select_icon(self.selected_icon)

    def _select_icon(self, icon_name: str):
        """选择图标"""
        self.selected_icon = icon_name

        # 更新选中样式 - 强制重置所有
        for name, btn in self._selected_buttons.items():
            if btn.is_selected != False:
                btn.is_selected = False
                btn._update_visual_state()  # 强制更新UI
        if icon_name in self._selected_buttons:
            btn = self._selected_buttons[icon_name]
            if btn.is_selected != True:
                btn.is_selected = True
                btn._update_visual_state()  # 强制更新UI

    def _on_cancel(self, instance):
        self.dismiss()

    def _on_confirm(self, instance):
        if self.on_icon_selected:
            self.on_icon_selected(self.selected_icon)
        self.dismiss()

    def show(self):
        # 显示动画
        self.opacity = 0
        super().open()
        anim = Animation(opacity=1, duration=0.25)
        anim.start(self)
