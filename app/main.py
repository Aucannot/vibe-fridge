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
from kivy.core.text import LabelBase

# 配置 Kivy 基本设置（必须在导入其他 Kivy 模块之前）
Config.set('graphics', 'width', '360')
Config.set('graphics', 'height', '780')
Config.set('kivy', 'window_icon', 'assets/icon.png')

# 现在可以导入其他模块
from kivymd.app import MDApp
from kivy.core.window import Window
from kivy.uix.screenmanager import ScreenManager
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.anchorlayout import AnchorLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.clock import Clock
from dotenv import load_dotenv

# 加载环境变量
load_dotenv()

# 导入字体辅助工具并注册中文字体
from app.utils.font_helper import register_chinese_font, apply_font_to_widget
from app.services.order_import_service import (
    LEGACY_SILICONFLOW_API_KEY_ENV,
    SILICONFLOW_API_KEY_ENV,
)

# 注册中文字体（必须在导入使用字体的模块之前）
chinese_font_name = register_chinese_font()

# 存储字体名称供其他模块使用（供各个 Screen 模块引用）
CHINESE_FONT_NAME = chinese_font_name


def ensure_kivymd_icon_font():
    """Register KivyMD icon font aliases used by old and new widgets."""
    try:
        from kivymd import fonts_path

        icon_font_path = os.path.join(fonts_path, "materialdesignicons-webfont.ttf")
        if not os.path.exists(icon_font_path):
            return

        # Newer KivyMD uses "Icons"; some local code still referenced the legacy alias.
        LabelBase.register(name="Icons", fn_regular=icon_font_path)
        LabelBase.register(name="MaterialIcons", fn_regular=icon_font_path)
    except Exception:
        return


ensure_kivymd_icon_font()

# 导入应用模块（注意：需在字体注册之后）
from app.ui.screens.main_screen import MainScreen
from app.ui.screens.items_screen import ItemsScreen
from app.ui.screens.item_detail_screen import ItemDetailScreen
from app.ui.screens.item_wiki_detail_screen import ItemWikiDetailScreen
from app.ui.screens.item_wiki_edit_screen import ItemWikiEditScreen
from app.ui.screens.add_item_screen import AddItemScreen
from app.ui.screens.add_entry_screen import AddEntryScreen
from app.ui.screens.order_import_screen import OrderImportScreen
from app.ui.screens.recipes_screen import RecipesScreen
from app.ui.screens.settings_screen import SettingsScreen
from app.ui.screens.history_screen import HistoryScreen
from app.services.database import init_database
from app.utils.logger import setup_logger
from app.services.item_service import seed_example_items
from app.ui.theme.design_tokens import COLOR_PALETTE


COLORS = COLOR_PALETTE


class VibeFridgeApp(MDApp):
    """主应用类"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.logger = setup_logger(__name__)
        # 设置主题
        self.theme_cls.theme_style = "Light"
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.material_style = "M3"
        
        # 底部导航按钮引用
        self.home_btn = None
        self.items_btn = None
        self.recipes_btn = None
        self.settings_btn = None
        
        # 设置中文字体（如果已注册）
        if chinese_font_name:
            try:
                # 确保 KivyMD 内部使用 font_style/role 的控件也切到中文字体。
                if hasattr(self.theme_cls, 'font_styles'):
                    font_styles = dict(self.theme_cls.font_styles)
                    for style_name, style_roles in font_styles.items():
                        if style_name in ('Icon', 'Icons'):
                            continue
                        if not isinstance(style_roles, dict):
                            continue
                        for role_name, role_values in style_roles.items():
                            if isinstance(role_values, dict):
                                role_values['font-name'] = chinese_font_name
                    self.theme_cls.font_styles = font_styles
                self.logger.debug(f"已为 KivyMD 设置中文字体: {chinese_font_name}")
            except Exception as e:
                self.logger.debug(f"设置 KivyMD 字体失败: {e}")
                import traceback
                traceback.print_exc()

            # 特别确保MDIcon类使用正确的字体
            try:
                from kivymd.uix.label import MDIcon
                if hasattr(MDIcon, 'font_name'):
                    MDIcon.font_name = 'Icons'
                    self.logger.debug("已为 MDIcon 设置图标字体为 Icons")

                # 确保MDCheckbox也使用正确的图标字体
                from kivymd.uix.selectioncontrol import MDCheckbox
                if hasattr(MDCheckbox, 'font_name'):
                    MDCheckbox.font_name = 'Icons'
                    self.logger.debug("已为 MDCheckbox 设置图标字体为 Icons")
            except Exception as e:
                self.logger.debug(f"设置 MDIcon/MDCheckbox 字体失败: {e}")
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
        self.screen_manager = ScreenManager(size_hint=(1, 1), size=(Window.size))

        # 加载并添加各个屏幕
        self.load_screens()

        # 全局应用中文字体到所有已有控件
        if chinese_font_name:
            apply_font_to_widget(self.screen_manager, chinese_font_name)

        # 设置默认屏幕
        self.screen_manager.current = "main"

        # 构建根布局：上方为 ScreenManager，下方为固定底部导航栏
        root = BoxLayout(orientation="vertical", size_hint=(1, 1))
        self.screen_manager.size_hint = (1, 1)
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

        # 物品Wiki详情屏幕
        item_wiki_detail_screen = ItemWikiDetailScreen(name='item_wiki_detail')
        self.screen_manager.add_widget(item_wiki_detail_screen)

        # 物品Wiki编辑屏幕
        item_wiki_edit_screen = ItemWikiEditScreen(name='item_wiki_edit')
        self.screen_manager.add_widget(item_wiki_edit_screen)

        # 选择添加方式屏幕
        add_entry_screen = AddEntryScreen(name="add_entry")
        self.screen_manager.add_widget(add_entry_screen)

        # 订单截图导入屏幕
        order_import_screen = OrderImportScreen(name="order_import")
        self.screen_manager.add_widget(order_import_screen)

        # 添加物品屏幕（手动添加）
        add_item_screen = AddItemScreen(name='add_item')
        self.screen_manager.add_widget(add_item_screen)

        # 食谱屏幕
        recipes_screen = RecipesScreen(name="recipes")
        self.screen_manager.add_widget(recipes_screen)

        # 设置屏幕
        settings_screen = SettingsScreen(name="settings")
        self.screen_manager.add_widget(settings_screen)

        # 历史屏幕
        history_screen = HistoryScreen(name="history")
        self.screen_manager.add_widget(history_screen)

    # ---------------- 底部导航栏相关 ----------------
    def _create_bottom_nav_bar(self):
        """创建应用底部的导航栏：首页 / 物品 / ➕ / 食谱 / 设置"""
        from kivy.graphics import Color, RoundedRectangle, Line
        
        nav = BoxLayout(
            size_hint_y=None,
            height=dp(74),
            padding=(dp(10), dp(8), dp(10), dp(10)),
            spacing=dp(4),
        )
        with nav.canvas.before:
            self._nav_bg_color = Color(*COLORS["surface"])
            self._nav_bg_rect = RoundedRectangle(
                pos=nav.pos,
                size=nav.size,
                radius=[dp(22), dp(22), 0, 0],
            )
        with nav.canvas.after:
            self._nav_divider_color = Color(*COLORS["divider"])
            self._nav_divider_line = Line(points=[])
        nav.bind(
            pos=lambda inst, _val: setattr(self._nav_bg_rect, "pos", inst.pos),
            size=lambda inst, _val: setattr(self._nav_bg_rect, "size", inst.size),
        )
        nav.bind(
            pos=lambda inst, _val: setattr(
                self._nav_divider_line,
                "points",
                [inst.x, inst.top, inst.right, inst.top],
            ),
            size=lambda inst, _val: setattr(
                self._nav_divider_line,
                "points",
                [inst.x, inst.top, inst.right, inst.top],
            ),
        )

        def make_btn(text, on_press, is_center=False):
            from kivy.animation import Animation
            from kivy.uix.behaviors import ButtonBehavior
            from kivy.properties import StringProperty, ColorProperty, NumericProperty, BooleanProperty
            from kivymd.uix.label import MDIcon

            class NavButton(ButtonBehavior, BoxLayout):
                text = StringProperty("")
                icon = StringProperty("")
                icon_color = ColorProperty(COLORS["text_hint"])
                text_color = ColorProperty(COLORS["text_hint"])
                bg_color = ColorProperty((0, 0, 0, 0))
                bg_highlight = ColorProperty(COLORS["surface_tint"])
                icon_highlight = ColorProperty(COLORS["primary"])
                text_highlight = ColorProperty(COLORS["primary"])
                is_center_btn = BooleanProperty(False)
                scale_x = NumericProperty(1.0)
                scale_y = NumericProperty(1.0)

                def __init__(self, **kwargs):
                    super().__init__(**kwargs)
                    self.orientation = "vertical"
                    self.spacing = dp(2)
                    self.size_hint_y = None
                    self.height = dp(52) if not self.is_center_btn else dp(56)
                    self.bind(on_press=self._on_press)
                    self.bind(scale_x=self._on_scale_change, scale_y=self._on_scale_change)
                    self.bind(center=self._on_center_change)
                    
                    if self.is_center_btn:
                        self.bg_color = COLORS["primary"]
                        self.icon_color = COLORS["on_primary"]
                    
                    self.bind(bg_color=self._update_bg_color)
                    self._build_content()
                    self._setup_background()

                def _setup_background(self):
                    if self.is_center_btn:
                        radius = [dp(22)]
                    else:
                        radius = [dp(18)]
                    with self.canvas.before:
                        self._bg_color = Color(*self.bg_color)
                        self._bg_rect = RoundedRectangle(size=self.size, pos=self.pos, radius=radius)
                    self.bind(size=lambda ins, val: setattr(self._bg_rect, 'size', val))
                    self.bind(pos=lambda ins, val: setattr(self._bg_rect, 'pos', val))
                
                def _update_bg_color(self, instance, value):
                    if hasattr(self, '_bg_color'):
                        self._bg_color.rgba = value

                def _on_center_change(self, instance, value):
                    if hasattr(self, '_scale_instruction'):
                        self._scale_instruction.origin = value

                def _on_scale_change(self, instance, value):
                    from kivy.graphics import PushMatrix, PopMatrix, Scale
                    if not hasattr(self, '_scale_instruction'):
                        with self.canvas.before:
                            self._push_matrix = PushMatrix()
                            self._scale_instruction = Scale(x=1, y=1, origin=self.center)
                            self._pop_matrix = PopMatrix()
                    self._scale_instruction.x = self.scale_x
                    self._scale_instruction.y = self.scale_y
                    self._scale_instruction.origin = self.center

                def _build_content(self):
                    self.clear_widgets()
                    icon_size = dp(28) if self.is_center_btn else dp(24)
                    icon_lbl = MDIcon(
                        icon=self.icon,
                        font_size=icon_size,
                        halign="center",
                        valign="middle",
                        theme_icon_color="Custom",
                        icon_color=self.icon_color,
                    )
                    icon_lbl.bind(
                        size=lambda ins, val: setattr(ins, 'text_size', val),
                        icon_color=lambda ins, val: setattr(self, 'icon_color', val)
                    )
                    if self.is_center_btn:
                        icon_lbl.size_hint = (None, None)
                        icon_lbl.size = (icon_size, icon_size)
                        icon_lbl.bind(size=lambda ins, val: setattr(ins, 'text_size', val))

                        icon_container = AnchorLayout(
                            anchor_x="center",
                            anchor_y="center",
                            size_hint=(1, 1),
                        )
                        icon_container.add_widget(icon_lbl)
                        self.add_widget(icon_container)
                    else:
                        # 确保普通导航图标在容器中水平居中
                        icon_lbl.size_hint_x = 1
                        icon_lbl.size_hint_y = None
                        icon_lbl.height = dp(24)

                        icon_container = BoxLayout(
                            orientation='horizontal',
                            size_hint_x=1,
                            size_hint_y=None,
                            height=dp(24),
                        )
                        icon_container.add_widget(icon_lbl)
                        self.add_widget(icon_container)

                    if not self.is_center_btn:
                        label = Label(
                            text=self.text,
                            font_size=dp(11),
                            halign="center",
                            valign="middle",
                            size_hint_x=1,
                            size_hint_y=None,
                            height=dp(16),
                            color=self.text_color,
                        )
                        if CHINESE_FONT_NAME:
                            label.font_name = CHINESE_FONT_NAME
                        label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1])))
                        self.add_widget(label)

                def _on_press(self, *args):
                    anim = Animation(
                        scale_x=0.92,
                        scale_y=0.92,
                        duration=0.1,
                        t="out_quad",
                    )
                    anim.bind(on_complete=lambda *_: Animation(
                        scale_x=1.0,
                        scale_y=1.0,
                        duration=0.15,
                        t="in_out_quad",
                    ).start(self))
                    anim.start(self)

                def set_highlight(self, highlighted):
                    if self.is_center_btn:
                        return
                    if highlighted:
                        self.bg_color = self.bg_highlight
                    else:
                        self.bg_color = (0, 0, 0, 0)
                    self._update_text_colors(highlighted)

                def _update_text_colors(self, highlighted):
                    new_icon_color = self.icon_highlight if highlighted else COLORS["text_hint"]
                    new_text_color = self.text_highlight if highlighted else COLORS["text_hint"]
                    for child in self.children:
                        if hasattr(child, 'icon_color'):
                            child.icon_color = new_icon_color
                        elif hasattr(child, 'color'):
                            child.color = new_text_color

            btn = NavButton(
                text=text,
                icon="add" if is_center else "",
                on_release=on_press,
                size_hint_x=None if is_center else 1,
                width=dp(72) if is_center else dp(0),
                is_center_btn=is_center,
            )
            if is_center:
                btn.icon = "plus"
                btn.bg_highlight = COLORS["primary"]
                btn.icon_highlight = COLORS["on_primary"]
            return btn

        home_btn = make_btn("首页", lambda *_: self.switch_to_screen("main"))
        home_btn.icon = "home-outline"
        home_btn._build_content()

        items_btn = make_btn("物品", lambda *_: self.switch_to_screen("items"))
        items_btn.icon = "fridge-outline"
        items_btn._build_content()

        plus_btn = make_btn("", lambda *_: self.switch_to_screen("add_entry"), is_center=True)
        plus_btn.icon = "plus"
        plus_btn._build_content()

        recipes_btn = make_btn("菜谱", lambda *_: self.switch_to_screen("recipes"))
        recipes_btn.icon = "silverware-fork-knife"
        recipes_btn._build_content()

        settings_btn = make_btn("设置", lambda *_: self.switch_to_screen("settings"))
        settings_btn.icon = "cog-outline"
        settings_btn._build_content()

        left_layout = BoxLayout(orientation='horizontal', size_hint_x=1)
        left_layout.add_widget(home_btn)
        left_layout.add_widget(items_btn)

        center_layout = BoxLayout(
            orientation='horizontal',
            size_hint=(None, 1),
            width=dp(84),
        )
        center_layout.padding = (0, dp(2), 0, 0)
        center_layout.add_widget(plus_btn)

        right_layout = BoxLayout(orientation='horizontal', size_hint_x=1)
        right_layout.add_widget(recipes_btn)
        right_layout.add_widget(settings_btn)

        nav.add_widget(left_layout)
        nav.add_widget(center_layout)
        nav.add_widget(right_layout)

        self.home_btn = home_btn
        self.items_btn = items_btn
        self.recipes_btn = recipes_btn
        self.settings_btn = settings_btn

        self._set_button_highlight(self.home_btn)

        return nav

    def switch_to_screen(self, name: str):
        """切换 ScreenManager 当前显示的屏幕"""
        if not hasattr(self, "screen_manager"):
            return
        if name in self.screen_manager.screen_names:
            self.screen_manager.current = name
            self._update_nav_buttons(name)

    def _update_nav_buttons(self, current_screen: str):
        """根据当前屏幕更新底部导航按钮的高亮状态"""
        self._set_button_normal(self.home_btn)
        self._set_button_normal(self.items_btn)
        self._set_button_normal(self.recipes_btn)
        self._set_button_normal(self.settings_btn)

        if current_screen == "main":
            self._set_button_highlight(self.home_btn)
        elif current_screen == "items":
            self._set_button_highlight(self.items_btn)
        elif current_screen == "recipes":
            self._set_button_highlight(self.recipes_btn)
        elif current_screen == "settings":
            self._set_button_highlight(self.settings_btn)
        # 其他屏幕（如 add_entry, add_item, item_detail）不设置任何按钮为高亮
        # 确保所有按钮都保持普通状态

    def _set_button_highlight(self, btn):
        """设置按钮为高亮状态"""
        if btn and hasattr(btn, 'set_highlight'):
            btn.set_highlight(True)

    def _set_button_normal(self, btn):
        """设置按钮为普通状态"""
        if btn and hasattr(btn, 'set_highlight'):
            btn.set_highlight(False)

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
        api_key = os.getenv(SILICONFLOW_API_KEY_ENV) or os.getenv(
            LEGACY_SILICONFLOW_API_KEY_ENV
        )
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
