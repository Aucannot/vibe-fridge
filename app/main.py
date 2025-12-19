#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
vibe-fridge 主应用入口
"""

import os
import sys
from pathlib import Path

# 设置 UTF-8 编码
if sys.platform != 'win32':
    import locale
    locale.setlocale(locale.LC_ALL, 'zh_CN.UTF-8')

# 添加项目根目录到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

# 必须在导入任何 Kivy 模块之前设置 Config
from kivy.config import Config

# 配置 Kivy 基本设置（必须在导入其他 Kivy 模块之前）
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '640')
Config.set('kivy', 'window_icon', 'assets/icon.png')

# 现在可以导入其他模块
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入字体辅助工具并注册中文字体
from app.utils.font_helper import register_chinese_font, apply_font_to_widget

# 注册中文字体（必须在导入使用字体的模块之前）
chinese_font_name = register_chinese_font()

# 存储字体名称供其他模块使用（供各个 Screen 模块引用）
CHINESE_FONT_NAME = chinese_font_name

# 导入应用模块（注意：需在字体注册之后）
from app.ui.screens.main_screen import MainScreen
from app.ui.screens.items_screen import ItemsScreen
from app.ui.screens.item_detail_screen import ItemDetailScreen
from app.ui.screens.add_item_screen import AddItemScreen
from app.ui.screens.add_entry_screen import AddEntryScreen
from app.ui.screens.recipes_screen import RecipesScreen
from app.ui.screens.settings_screen import SettingsScreen
from app.services.database import init_database
from app.utils.logger import setup_logger
from app.services.item_service import seed_example_items


class VibeFridgeApp(MDApp):
    """主应用类"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        # 设置主题
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Blue"
        self.theme_cls.material_style = "M3"
        
        # 设置中文字体（如果已注册）
        if chinese_font_name:
            try:
                # 确保字体应用到所有文本组件：遍历 KivyMD 的字体样式并替换为中文字体
                if hasattr(self.theme_cls, 'font_styles'):
                    # 为所有字体样式设置中文字体
                    for style_name in self.theme_cls.font_styles:
                        if hasattr(self.theme_cls.font_styles[style_name], 'font_name'):
                            self.theme_cls.font_styles[style_name].font_name = chinese_font_name
                print(f"已为 KivyMD 设置中文字体: {chinese_font_name}")
            except Exception as e:
                print(f"设置 KivyMD 字体失败: {e}")
                import traceback
                traceback.print_exc()

    def build(self):
        """构建应用界面"""
        # 设置应用标题
        self.title = os.getenv('APP_NAME', 'vibe-fridge')

        # 设置窗口背景色为白色
        Window.clearcolor = (1, 1, 1, 1)

        # 初始化数据库
        init_database()

        # 创建屏幕管理器
        self.screen_manager = ScreenManager()

        # 加载并添加各个屏幕
        self.load_screens()

        # 全局应用中文字体到所有已有控件
        if chinese_font_name:
            apply_font_to_widget(self.screen_manager, chinese_font_name)

        # 设置默认屏幕
        self.screen_manager.current = "main"

        # 构建根布局：上方为 ScreenManager，下方为固定底部导航栏
        root = BoxLayout(orientation="vertical")
        root.add_widget(self.screen_manager)

        bottom_nav = self._create_bottom_nav_bar()
        root.add_widget(bottom_nav)

        return root

    def load_screens(self):
        """加载所有屏幕"""
        # 主屏幕 / 首页
        main_screen = MainScreen(name='main')
        self.screen_manager.add_widget(main_screen)

        # 物品屏幕：左侧类别 + 右侧明细
        items_screen = ItemsScreen(name="items")
        self.screen_manager.add_widget(items_screen)

        # 物品详情屏幕
        item_detail_screen = ItemDetailScreen(name='item_detail')
        self.screen_manager.add_widget(item_detail_screen)

        # 选择添加方式屏幕
        add_entry_screen = AddEntryScreen(name="add_entry")
        self.screen_manager.add_widget(add_entry_screen)

        # 添加物品屏幕（手动添加）
        add_item_screen = AddItemScreen(name='add_item')
        self.screen_manager.add_widget(add_item_screen)

        # 食谱屏幕
        recipes_screen = RecipesScreen(name="recipes")
        self.screen_manager.add_widget(recipes_screen)

        # 设置屏幕
        settings_screen = SettingsScreen(name="settings")
        self.screen_manager.add_widget(settings_screen)

    # ---------------- 底部导航栏相关 ----------------
    def _create_bottom_nav_bar(self):
        """创建应用底部的导航栏：首页 / 物品 / ➕ / 食谱 / 设置"""
        nav = BoxLayout(
            size_hint_y=None,
            height=dp(60),
            padding=(dp(4), dp(4), dp(4), dp(6)),
            spacing=dp(4),
        )

        def make_btn(text, on_press, is_center=False):
            btn = Button(
                text=text,
                on_release=on_press,
                background_normal="",
                background_color=(0.95, 0.95, 0.95, 1),
                color=(0.1, 0.1, 0.1, 1),
                size_hint_x=1,
            )
            if is_center:
                # 中间的大 + 号
                btn.font_size = dp(28)
                btn.bold = True
                btn.background_color = (0.25, 0.55, 0.9, 1)
                btn.color = (1, 1, 1, 1)
            else:
                btn.font_size = dp(14)
            if CHINESE_FONT_NAME:
                try:
                    btn.font_name = CHINESE_FONT_NAME
                except Exception:
                    pass
            return btn

        # 首页：当前的主列表界面
        home_btn = make_btn("首页", lambda *_: self.switch_to_screen("main"))
        # 物品：独立的“左侧分类 + 右侧明细”视图
        items_btn = make_btn("物品", lambda *_: self.switch_to_screen("items"))
        # 中间的大 + 号：先进入“选择添加方式”页
        plus_btn = make_btn("＋", lambda *_: self.switch_to_screen("add_entry"), is_center=True)
        # 食谱
        recipes_btn = make_btn("食谱", lambda *_: self.switch_to_screen("recipes"))
        # 设置
        settings_btn = make_btn("设置", lambda *_: self.switch_to_screen("settings"))

        nav.add_widget(home_btn)
        nav.add_widget(items_btn)
        nav.add_widget(plus_btn)
        nav.add_widget(recipes_btn)
        nav.add_widget(settings_btn)

        return nav

    def switch_to_screen(self, name: str):
        """切换 ScreenManager 当前显示的屏幕"""
        if not hasattr(self, "screen_manager"):
            return
        if name in self.screen_manager.screen_names:
            self.screen_manager.current = name

    def on_start(self):
        """应用启动时调用"""
        logger = setup_logger()
        logger.info("vibe-fridge 应用启动")

        # 如果数据库为空，插入一些示例物品，方便首次体验
        try:
            seed_example_items()
        except Exception as e:
            logger.error(f"插入示例物品失败: {e}")

        # 检查环境变量配置
        api_key = os.getenv('SILICON_FLOW_API_KEY')
        if not api_key or api_key == 'your_api_key_here':
            logger.warning("硅基流动 API 密钥未配置或使用默认值")

    def on_stop(self):
        """应用停止时调用"""
        logger = setup_logger()
        logger.info("vibe-fridge 应用停止")


def main():
    """应用主函数"""
    app = VibeFridgeApp()
    app.run()


if __name__ == '__main__':
    main()