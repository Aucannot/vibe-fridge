# -*- coding: utf-8 -*-
"""
选择添加方式屏幕 - 展示三种添加物品的入口（仅展示，不实现逻辑）
1. 从订单截图自动批量导入
2. 拍照识别生产日期 + 手动选择物品类别
3. 手动添加
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.metrics import dp
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDButton, MDIconButton, MDButtonText

from app.utils.font_helper import apply_font_to_widget


try:
    import app.main as main_module

    CHINESE_FONT = getattr(main_module, "CHINESE_FONT_NAME", None)
except Exception:
    CHINESE_FONT = None


class AddEntryScreen(Screen):
    """选择添加方式的入口屏幕"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "add_entry"
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(16))

        # 头部
        header = BoxLayout(size_hint_y=None, height=dp(56), spacing=dp(8))

        back_btn = MDIconButton(
            icon="arrow-left",
            on_release=self._on_back_click,
            font_name="Roboto",
        )
        header.add_widget(back_btn)

        title = Label(
            text="选择添加方式",
            font_size=dp(20),
            bold=True,
            color=(0.2, 0.4, 0.6, 1),
        )
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        header.add_widget(title)

        root.add_widget(header)

        # 说明文字
        hint = Label(
            text="未来将支持更智能的添加方式，现在先作为功能预览展示：",
            size_hint_y=None,
            height=dp(40),
            color=(0.4, 0.4, 0.4, 1),
        )
        if CHINESE_FONT:
            hint.font_name = CHINESE_FONT
        root.add_widget(hint)

        # 三个卡片
        cards_box = BoxLayout(orientation="vertical", spacing=dp(12))

        cards_box.add_widget(self._create_card(
            title="从订单截图自动批量导入",
            subtitle="上传买菜 / 外卖订单截图，自动识别物品名称和数量。",
            icon="image-multiple",
            developed=False,
        ))

        cards_box.add_widget(self._create_card(
            title="拍照识别生产日期 + 选择类别",
            subtitle="对准包装上的生产日期拍照，自动识别日期，再手动选类别。",
            icon="camera-outline",
            developed=False,
        ))

        cards_box.add_widget(self._create_card(
            title="手动添加",
            subtitle="填写名称、数量、日期等详细信息（当前已实现）。",
            icon="pencil-plus",
            developed=True,
        ))

        root.add_widget(cards_box)

        self.add_widget(root)

    def _create_card(self, title: str, subtitle: str, icon: str, developed: bool) -> MDCard:
        """创建单个添加方式卡片"""
        card = MDCard(
            size_hint_y=None,
            height=dp(120),
            padding=dp(12),
            radius=[dp(10), dp(10), dp(10), dp(10)],
        )

        layout = BoxLayout(orientation="horizontal", spacing=dp(12))

        # 左侧图标
        icon_btn = MDIconButton(
            icon=icon,
            disabled=True,
            font_name="Roboto",
        )
        layout.add_widget(icon_btn)

        # 中间标题 + 描述
        text_box = BoxLayout(orientation="vertical", spacing=dp(4))

        title_label = Label(
            text=title,
            size_hint_y=None,
            height=dp(26),
            bold=True,
            color=(0.1, 0.1, 0.1, 1),
        )
        subtitle_label = Label(
            text=subtitle,
            color=(0.4, 0.4, 0.4, 1),
            halign="left",
            valign="top",
        )
        subtitle_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))

        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
            subtitle_label.font_name = CHINESE_FONT

        text_box.add_widget(title_label)
        text_box.add_widget(subtitle_label)
        layout.add_widget(text_box)

        # 右侧按钮
        if developed:
            btn = MDButton(
                style="filled",
                on_release=self._go_to_manual_add,
                size_hint_x=None,
                width=dp(80),
            )
            btn_text = MDButtonText(text="进入")
        else:
            btn = MDButton(
                style="outlined",
                disabled=True,
                size_hint_x=None,
                width=dp(80),
            )
            btn_text = MDButtonText(text="敬请期待")

        if CHINESE_FONT:
            btn_text.font_name = CHINESE_FONT
        btn.add_widget(btn_text)
        layout.add_widget(btn)

        card.add_widget(layout)
        return card

    def _on_back_click(self, instance):
        """返回主页"""
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            app.screen_manager.current = "main"

    def _go_to_manual_add(self, instance):
        """跳转到已经实现的手动添加表单"""
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            app.screen_manager.current = "add_item"

    def on_enter(self):
        """进入时为整个屏幕应用中文字体"""
        try:
            import app.main as main_module

            font = getattr(main_module, "CHINESE_FONT_NAME", None)
        except Exception:
            font = None
        if font:
            apply_font_to_widget(self, font)


