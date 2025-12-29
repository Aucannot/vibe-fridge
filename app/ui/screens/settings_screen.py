# -*- coding: utf-8 -*-
"""
设置屏幕 - 占位页，后续可扩展为主题、通知等配置
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp

from app.utils.font_helper import apply_font_to_widget, CHINESE_FONT_NAME as CHINESE_FONT


class SettingsScreen(Screen):
    """设置屏幕（占位实现）"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "settings"
        self._build_ui()

    def _build_ui(self):
        """构建简单的占位 UI"""
        layout = BoxLayout(orientation="vertical", padding=dp(16))

        title = Label(
            text="设置（开发中）",
            font_size=dp(22),
            bold=True,
            color=(0.2, 0.4, 0.6, 1),
            size_hint_y=None,
            height=dp(60),
        )
        layout.add_widget(title)

        hint = Label(
            text="未来这里可以配置主题、提醒方式等选项。",
            font_size=dp(16),
            color=(0.4, 0.4, 0.4, 1),
        )
        layout.add_widget(hint)

        self.add_widget(layout)

    def on_enter(self):
        """进入屏幕时为整个屏幕应用中文字体"""
        if CHINESE_FONT:
            apply_font_to_widget(self, CHINESE_FONT)


