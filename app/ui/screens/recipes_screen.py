# -*- coding: utf-8 -*-
"""
食谱屏幕 - 占位页，后续可扩展为推荐食谱、根据冰箱物品生成菜谱等
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp

from app.utils.font_helper import apply_font_to_widget


class RecipesScreen(Screen):
    """食谱屏幕（占位实现）"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "recipes"
        self._build_ui()

    def _build_ui(self):
        """构建简单的占位 UI"""
        layout = BoxLayout(orientation="vertical", padding=dp(16))

        title = Label(
            text="食谱（开发中）",
            font_size=dp(22),
            bold=True,
            color=(0.2, 0.4, 0.6, 1),
            size_hint_y=None,
            height=dp(60),
        )
        layout.add_widget(title)

        hint = Label(
            text="未来这里会根据冰箱里的物品推荐菜谱～",
            font_size=dp(16),
            color=(0.4, 0.4, 0.4, 1),
        )
        layout.add_widget(hint)

        self.add_widget(layout)

    def on_enter(self):
        """进入屏幕时为整个屏幕应用中文字体"""
        try:
            import app.main as main_module

            chinese_font = getattr(main_module, "CHINESE_FONT_NAME", None)
        except Exception:
            chinese_font = None
        if chinese_font:
            apply_font_to_widget(self, chinese_font)


