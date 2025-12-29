# -*- coding: utf-8 -*-
"""
设置屏幕 - 应用配置和个性化设置
Modernized with Material Design 3 principles
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.switch import Switch
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.properties import ColorProperty, BooleanProperty, StringProperty
from kivy.clock import Clock
from kivy.graphics import Color, Rectangle, RoundedRectangle

from app.utils.font_helper import apply_font_to_widget, CHINESE_FONT_NAME as CHINESE_FONT
from app.ui.theme.design_tokens import COLOR_PALETTE, DESIGN_TOKENS

COLORS = COLOR_PALETTE


class AnimatedCard(BoxLayout):
    bg_color = ColorProperty((1, 1, 1, 1))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(16)
        self.spacing = dp(12)
        self.size_hint_y = None
        self.height = dp(100)
        self.bg_color = COLORS["surface"]
        self.bind(size=self._update_canvas, pos=self._update_canvas)

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(
                size=self.size,
                pos=self.pos,
                radius=[dp(16)]
            )

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            anim = Animation(scale_x=0.97, scale_y=0.97, duration=0.08, t="out_quad")
            anim.bind(on_complete=lambda *_: Animation(
                scale_x=1.0, scale_y=1.0, duration=0.12, t="in_out_quad"
            ).start(self))
            anim.start(self)
        return super().on_touch_down(touch)


class SettingsSection(BoxLayout):
    def __init__(self, title="", **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.padding = (dp(16), dp(8), dp(16), dp(8))
        self.spacing = dp(8)

        section_title = Label(
            text=title,
            font_size=dp(14),
            bold=True,
            color=COLORS["text_secondary"],
            size_hint_y=None,
            height=dp(20),
        )
        self.add_widget(section_title)


class SettingsItem(BoxLayout):
    def __init__(self, icon="", title="", subtitle="", show_switch=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(56)
        self.padding = dp(12)
        self.spacing = dp(12)

        with self.canvas.before:
            Color(*COLORS["surface"])
            bg_rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[dp(12)])
        self.bind(size=lambda ins, val: setattr(bg_rect, 'size', val))
        self.bind(pos=lambda ins, val: setattr(bg_rect, 'pos', val))

        if icon:
            from kivymd.uix.label import MDIcon
            icon_lbl = MDIcon(
                icon=icon,
                font_size=dp(22),
                theme_icon_color="Custom",
                icon_color=COLORS["primary"],
                size_hint_x=None,
                width=dp(32),
            )
            self.add_widget(icon_lbl)

        text_layout = BoxLayout(orientation="vertical", size_hint_x=1)
        title_lbl = Label(
            text=title,
            font_size=dp(15),
            color=COLORS["text_primary"],
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
        )
        title_lbl.bind(size=lambda ins, val: setattr(ins, 'text_size', val))

        if subtitle:
            subtitle_lbl = Label(
                text=subtitle,
                font_size=dp(12),
                color=COLORS["text_hint"],
                size_hint_y=None,
                height=dp(16),
                halign="left",
                valign="top",
            )
            subtitle_lbl.bind(size=lambda ins, val: setattr(ins, 'text_size', val))
            text_layout.add_widget(title_lbl)
            text_layout.add_widget(subtitle_lbl)
        else:
            text_layout.add_widget(title_lbl)

        self.add_widget(text_layout)

        if show_switch:
            switch = Switch(active=False, size_hint_x=None, width=dp(44))
            switch.bind(active=self._on_switch)
            self.add_widget(switch)

    def _on_switch(self, instance, value):
        anim = Animation(
            scale_x=0.9 if value else 1.0,
            scale_y=0.9 if value else 1.0,
            duration=0.1,
        )
        anim.start(instance)


class SettingsActionButton(BoxLayout):
    def __init__(self, text="", icon="", danger=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(52)
        self.padding = dp(16)
        self.spacing = dp(12)

        with self.canvas.before:
            Color(*COLORS["error"] if danger else COLORS["surface"])
            rect = RoundedRectangle(size=self.size, pos=self.pos, radius=[dp(12)])
        self.bind(size=lambda ins, val: setattr(rect, 'size', val))
        self.bind(pos=lambda ins, val: setattr(rect, 'pos', val))

        if icon:
            from kivymd.uix.label import MDIcon
            icon_lbl = MDIcon(
                icon=icon,
                font_size=dp(22),
                theme_icon_color="Custom",
                icon_color=COLORS["error"] if danger else COLORS["text_primary"],
                size_hint_x=None,
                width=dp(28),
            )
            self.add_widget(icon_lbl)

        text_lbl = Label(
            text=text,
            font_size=dp(15),
            color=COLORS["error"] if danger else COLORS["text_primary"],
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
        )
        text_lbl.bind(size=lambda ins, val: setattr(ins, 'text_size', val))
        self.add_widget(text_lbl)


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "settings"
        self._build_ui()
        Clock.schedule_once(lambda *_: self._animate_entrance(), 0.1)

    def _build_ui(self):
        from kivymd.uix.label import MDIcon
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.gridlayout import GridLayout
        from kivy.core.window import Window

        root = FloatLayout()
        bg_label = Label(
            size_hint_y=None,
            height=Window.size[1] if hasattr(Window, 'size') else dp(640),
            pos_hint={'x': 0, 'y': 0},
            color=(0, 0, 0, 0),
        )
        with bg_label.canvas.before:
            Color(*COLORS["background"])
            bg_rect = Rectangle(size=bg_label.size, pos=bg_label.pos)
        bg_label.bind(size=lambda ins, val: setattr(bg_rect, 'size', val))
        bg_label.bind(pos=lambda ins, val: setattr(bg_rect, 'pos', val))
        root.add_widget(bg_label)

        header = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(100),
            padding=(dp(20), dp(16), dp(20), dp(8)),
            pos_hint={'top': 1},
        )
        header.add_widget(Label(
            text="设置",
            font_size=dp(26),
            bold=True,
            color=COLORS["text_primary"],
            size_hint_y=None,
            height=dp(36),
        ))
        header.add_widget(Label(
            text="个性化配置和偏好设置",
            font_size=dp(14),
            color=COLORS["text_secondary"],
            size_hint_y=None,
            height=dp(20),
        ))
        root.add_widget(header)

        scroll = ScrollView(
            size_hint=(1, 0.85),
            pos_hint={'y': 0.05},
            bar_width=dp(4),
            scroll_type=['content'],
        )

        content = GridLayout(
            cols=1,
            size_hint_y=None,
            height=dp(800),
            spacing=dp(4),
        )

        content.add_widget(SettingsSection(title="账户"))
        content.add_widget(SettingsItem(
            icon="account",
            title="个人资料",
            subtitle="管理您的账户信息",
        ))
        content.add_widget(SettingsItem(
            icon="sync",
            title="数据同步",
            subtitle="跨设备同步冰箱数据",
            show_switch=True,
        ))

        content.add_widget(SettingsSection(title="通知"))
        content.add_widget(SettingsItem(
            icon="bell",
            title="过期提醒",
            subtitle="物品即将过期时通知我",
            show_switch=True,
        ))
        content.add_widget(SettingsItem(
            icon="cart",
            title="购物提醒",
            subtitle="库存不足时提醒购买",
            show_switch=True,
        ))

        content.add_widget(SettingsSection(title="外观"))
        content.add_widget(SettingsItem(
            icon="palette",
            title="主题颜色",
            subtitle="选择应用主题色",
        ))
        content.add_widget(SettingsItem(
            icon="format-size",
            title="字体大小",
            subtitle="调整界面文字大小",
        ))

        content.add_widget(SettingsSection(title="数据"))
        content.add_widget(SettingsItem(
            icon="database",
            title="数据备份",
            subtitle="备份到本地存储",
        ))
        content.add_widget(SettingsItem(
            icon="restore",
            title="恢复数据",
            subtitle="从备份恢复",
        ))

        content.add_widget(SettingsSection(title="关于"))
        content.add_widget(SettingsItem(
            icon="information",
            title="关于我们",
            subtitle="vibe-fridge v1.0.0",
        ))
        content.add_widget(SettingsItem(
            icon="help-circle",
            title="帮助与反馈",
            subtitle="常见问题和技术支持",
        ))

        danger_zone = SettingsSection(title="危险操作")
        content.add_widget(danger_zone)
        content.add_widget(SettingsActionButton(
            text="清除所有数据",
            icon="delete",
            danger=True,
        ))

        scroll.add_widget(content)
        root.add_widget(scroll)

        self.add_widget(root)

    def _animate_entrance(self):
        for i, child in enumerate(self.children):
            if isinstance(child, FloatLayout):
                for j, subchild in enumerate(child.children):
                    anim = Animation(
                        opacity=1,
                        y=subchild.y + dp(20) if hasattr(subchild, 'y') else 0,
                        duration=0.3,
                        t="out_quad"
                    )
                    anim.start(subchild)

    def on_enter(self):
        if CHINESE_FONT:
            apply_font_to_widget(self, CHINESE_FONT)


