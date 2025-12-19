"""
主屏幕 - 显示物品清单和主要功能
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.properties import (
    StringProperty, ListProperty, ObjectProperty, NumericProperty
)
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.list import (
    MDList, MDListItem,
    MDListItemLeadingIcon,
    MDListItemHeadlineText,
    MDListItemSupportingText,
    MDListItemTertiaryText,
)
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDFabButton, MDButton
from kivymd.uix.dialog import MDDialog
from kivymd.uix.menu import MDDropdownMenu
from datetime import date, timedelta
import os

from app.services.item_service import item_service, statistics_service
from app.models.item import ItemCategory, ItemStatus
from app.utils.logger import setup_logger
from app.utils.font_helper import apply_font_to_widget

logger = setup_logger(__name__)

# 获取中文字体名称
try:
    import app.main as main_module
    CHINESE_FONT = getattr(main_module, 'CHINESE_FONT_NAME', None)
except:
    CHINESE_FONT = None


class OneLineListItem(MDListItem):
    """单行列表项 - 用于下拉菜单"""
    text = StringProperty()
    
    def __init__(self, text="", **kwargs):
        super().__init__(**kwargs)
        self.text = text
        headline = MDListItemHeadlineText(text=text)
        if CHINESE_FONT:
            headline.font_name = CHINESE_FONT
        self.add_widget(headline)


class ItemListItem(MDListItem):
    """物品列表项"""
    item_id = StringProperty()
    item_name = StringProperty()
    category = StringProperty()
    expiry_date = StringProperty()
    days_until_expiry = NumericProperty(0)
    quantity = NumericProperty(1)

    def __init__(self, item_data, **kwargs):
        super().__init__(**kwargs)
        self.item_id = item_data.get('id', '')
        self.item_name = item_data.get('name', '未命名')
        self.category = item_data.get('category', ItemCategory.OTHERS.value)
        self.expiry_date = item_data.get('expiry_date', '无')
        self.days_until_expiry = item_data.get('days_until_expiry', 0)
        self.quantity = item_data.get('quantity', 1)

        # 设置图标
        self._setup_icon()

        # 设置文本
        self._setup_text(item_data)

        # 设置背景色（根据过期状态）
        self._setup_background()

    def _setup_icon(self):
        """设置图标"""
        icon_name = self._get_category_icon()
        self.add_widget(MDListItemLeadingIcon(
            icon=icon_name
        ))

    def _get_category_icon(self) -> str:
        """根据类别获取图标名称"""
        icon_map = {
            ItemCategory.FOOD.value: "food",
            ItemCategory.DAILY_NECESSITIES.value: "home",
            ItemCategory.MEDICINE.value: "pill",
            ItemCategory.COSMETICS.value: "lipstick",
            ItemCategory.OTHERS.value: "package-variant"
        }
        return icon_map.get(self.category, "package-variant")

    def _setup_text(self, item_data):
        """设置文本内容，使用自定义容器避免 MDListItem 的子控件布局问题"""
        from kivy.uix.label import Label
        from kivy.uix.boxlayout import BoxLayout

        text_box = BoxLayout(
            orientation="vertical",
            padding=(dp(8), dp(6)),
            spacing=dp(2),
            size_hint_y=None,
        )
        text_box.bind(minimum_height=lambda inst, val: setattr(inst, "height", val))

        def _make_label(text, height, color):
            lbl = Label(
                text=text,
                size_hint_y=None,
                height=height,
                halign="left",
                valign="middle",
                color=color,
            )
            # 让文本按容器宽度换行/居左
            lbl.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
            if CHINESE_FONT:
                lbl.font_name = CHINESE_FONT
            return lbl

        # 第一行：物品名称和数量
        headline_text = f"{self.item_name} x{self.quantity}"
        text_box.add_widget(_make_label(headline_text, dp(22), (0, 0, 0, 1)))

        # 第二行：类别和状态
        category_map = {
            ItemCategory.FOOD.value: "食品",
            ItemCategory.DAILY_NECESSITIES.value: "日用品",
            ItemCategory.MEDICINE.value: "药品",
            ItemCategory.COSMETICS.value: "化妆品",
            ItemCategory.OTHERS.value: "其他",
        }
        category_text = category_map.get(self.category, "其他")

        # 根据是否有过期日期来决定状态文案
        has_expiry = self.expiry_date != "无"
        if not has_expiry:
            # 未设置过期日期，不再错误显示为“即将过期”
            status_text = "无过期日期"
        else:
            status_text = "正常"
            if self.days_until_expiry < 0:
                status_text = "已过期"
            elif self.days_until_expiry <= 3:
                status_text = "即将过期"

        supporting_text = f"{category_text} | {status_text}"
        text_box.add_widget(_make_label(supporting_text, dp(18), (0.35, 0.35, 0.35, 1)))

        # 第三行：过期信息
        if self.expiry_date == "无":
            tertiary_text = "无过期日期"
        else:
            days_text = f"剩余{self.days_until_expiry}天"
            if self.days_until_expiry < 0:
                days_text = f"过期{-self.days_until_expiry}天"
            elif self.days_until_expiry == 0:
                days_text = "今天过期"
            tertiary_text = f"{self.expiry_date} | {days_text}"
        text_box.add_widget(_make_label(tertiary_text, dp(16), (0.5, 0.5, 0.5, 1)))

        self.add_widget(text_box)

    def _setup_background(self):
        """根据过期状态设置背景色"""
        # 没有过期日期的物品统一按“正常”处理，不高亮为即将过期/已过期
        if self.expiry_date == "无":
            self._set_background_color(1, 1, 1)
        elif self.days_until_expiry < 0:
            # 已过期 - 浅红色
            self._set_background_color(1, 0.9, 0.9)
        elif self.days_until_expiry <= 3:
            # 即将过期 - 浅黄色
            self._set_background_color(1, 1, 0.9)
        else:
            # 正常 - 白色
            self._set_background_color(1, 1, 1)

    def _set_background_color(self, r, g, b):
        """设置背景颜色"""
        with self.canvas.before:
            Color(r, g, b, 1)
            Rectangle(pos=self.pos, size=self.size)

        # 绑定大小变化
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        """更新矩形位置和大小"""
        self.canvas.before.clear()
        with self.canvas.before:
            Color(1, 1, 1, 1 if self.days_until_expiry > 3 else
                  0.9 if self.days_until_expiry >= 0 else 0.9)
            Rectangle(pos=self.pos, size=self.size)


class MainScreen(Screen):
    """主屏幕"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'main'
        self._build_ui()
        self._load_items()

        # 创建类别筛选菜单
        self._create_category_menu()

        # 设置定时刷新
        Clock.schedule_interval(self._refresh_items, 60)  # 每分钟刷新一次

    def _build_ui(self):
        """构建UI界面"""
        # 主内容布局（竖直 BoxLayout），后面会放在一个 FloatLayout 里，让悬浮按钮不占垂直空间
        main_layout = BoxLayout(orientation='vertical', size_hint=(1, 1))
        # 设置背景色
        from kivy.graphics import Color, Rectangle
        with main_layout.canvas.before:
            Color(1, 1, 1, 1)  # 白色背景
            self.bg_rect = Rectangle(pos=main_layout.pos, size=main_layout.size)
        
        def update_bg_rect(instance, value):
            self.bg_rect.pos = instance.pos
            self.bg_rect.size = instance.size
        
        main_layout.bind(pos=update_bg_rect, size=update_bg_rect)

        # 标题栏
        header = self._create_header()
        main_layout.add_widget(header)

        # 筛选栏
        filter_bar = self._create_filter_bar()
        main_layout.add_widget(filter_bar)

        # 统计卡片
        stats_cards = self._create_stats_cards()
        main_layout.add_widget(stats_cards)

        # 物品列表
        item_list = self._create_item_list()
        main_layout.add_widget(item_list)

        # 这里不再放置悬浮 + 按钮，改由应用底部统一的导航栏中间的大 + 负责新增物品
        self.add_widget(main_layout)

    def _create_header(self) -> BoxLayout:
        """创建标题栏"""
        header = BoxLayout(size_hint_y=None, height=dp(56))
        # 设置标题栏背景色
        from kivy.graphics import Color, Rectangle
        with header.canvas.before:
            Color(1, 1, 1, 1)  # 白色背景
            header_bg_rect = Rectangle(pos=header.pos, size=header.size)
        
        def update_header_bg(instance, value):
            header_bg_rect.pos = instance.pos
            header_bg_rect.size = instance.size
        
        header.bind(pos=update_header_bg, size=update_header_bg)
        
        title_label = Label(
            text="vibe-fridge",
            font_size=dp(24),
            bold=True,
            color=(0.2, 0.4, 0.6, 1)
        )
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        header.add_widget(title_label)

        return header

    def _create_filter_bar(self) -> BoxLayout:
        """创建筛选栏"""
        filter_bar = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            padding=dp(8),
            spacing=dp(8)
        )
        # 设置筛选栏背景色
        from kivy.graphics import Color, Rectangle
        with filter_bar.canvas.before:
            Color(0.95, 0.95, 0.95, 1)  # 浅灰色背景
            filter_bg_rect = Rectangle(pos=filter_bar.pos, size=filter_bar.size)
        
        def update_filter_bg(instance, value):
            filter_bg_rect.pos = instance.pos
            filter_bg_rect.size = instance.size
        
        filter_bar.bind(pos=update_filter_bg, size=update_filter_bg)

        # 搜索框（简化版）
        self.search_input = Label(
            text="点击筛选...",
            size_hint_x=0.6,
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            self.search_input.font_name = CHINESE_FONT
        filter_bar.add_widget(self.search_input)

        # 类别筛选按钮
        self.category_button = Button(
            text="所有类别",
            size_hint_x=0.4,
            background_color=(0.9, 0.9, 0.9, 1),
            color=(0, 0, 0, 1),
            on_release=self._show_category_menu
        )
        if CHINESE_FONT:
            self.category_button.font_name = CHINESE_FONT
        filter_bar.add_widget(self.category_button)

        return filter_bar

    def _create_stats_cards(self) -> BoxLayout:
        """创建统计卡片"""
        stats_layout = BoxLayout(
            size_hint_y=None,
            height=dp(100),
            padding=dp(8),
            spacing=dp(8)
        )

        # 总物品数卡片
        self.total_card = self._create_stat_card("总物品", "0", (0.2, 0.6, 0.8, 1))
        stats_layout.add_widget(self.total_card)

        # 即将过期卡片
        self.expiring_card = self._create_stat_card("即将过期", "0", (0.9, 0.6, 0.2, 1))
        stats_layout.add_widget(self.expiring_card)

        # 已过期卡片
        self.expired_card = self._create_stat_card("已过期", "0", (0.9, 0.3, 0.3, 1))
        stats_layout.add_widget(self.expired_card)

        return stats_layout

    def _create_stat_card(self, title: str, value: str, color) -> MDCard:
        """创建统计卡片"""
        card = MDCard(
            size_hint=(0.33, 1),
            padding=dp(8),
            radius=[dp(8), dp(8), dp(8), dp(8)]
        )

        layout = BoxLayout(orientation='vertical')

        # 标题
        title_label = Label(
            text=title,
            font_size=dp(12),
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        layout.add_widget(title_label)

        # 数值
        value_label = Label(
            text=value,
            font_size=dp(24),
            bold=True,
            color=color
        )
        if CHINESE_FONT:
            value_label.font_name = CHINESE_FONT
        layout.add_widget(value_label)

        card.add_widget(layout)
        return card

    def _create_item_list(self) -> ScrollView:
        """创建物品列表"""
        scroll_view = ScrollView()
        # 设置滚动视图背景色
        from kivy.graphics import Color, Rectangle
        with scroll_view.canvas.before:
            Color(1, 1, 1, 1)  # 白色背景
            scroll_bg_rect = Rectangle(pos=scroll_view.pos, size=scroll_view.size)
        
        def update_scroll_bg(instance, value):
            scroll_bg_rect.pos = instance.pos
            scroll_bg_rect.size = instance.size
        
        scroll_view.bind(pos=update_scroll_bg, size=update_scroll_bg)

        self.item_list_layout = MDList()
        scroll_view.add_widget(self.item_list_layout)

        return scroll_view

    def _create_category_menu(self):
        """创建类别筛选菜单"""
        category_items = [
            {
                "viewclass": "OneLineListItem",
                "text": "所有类别",
                "on_release": lambda x="所有类别": self._select_category(None),
            },
            {
                "viewclass": "OneLineListItem",
                "text": "食品",
                "on_release": lambda x="食品": self._select_category(ItemCategory.FOOD),
            },
            {
                "viewclass": "OneLineListItem",
                "text": "日用品",
                "on_release": lambda x="日用品": self._select_category(ItemCategory.DAILY_NECESSITIES),
            },
            {
                "viewclass": "OneLineListItem",
                "text": "药品",
                "on_release": lambda x="药品": self._select_category(ItemCategory.MEDICINE),
            },
            {
                "viewclass": "OneLineListItem",
                "text": "化妆品",
                "on_release": lambda x="化妆品": self._select_category(ItemCategory.COSMETICS),
            },
            {
                "viewclass": "OneLineListItem",
                "text": "其他",
                "on_release": lambda x="其他": self._select_category(ItemCategory.OTHERS),
            }
        ]

        self.category_menu = MDDropdownMenu(
            caller=self.category_button,
            items=category_items,
            width_mult=4,
            # 下拉菜单整体背景色，避免纯白色块太突兀
            background_color=(0.97, 0.97, 0.99, 1),
        )

        # 稍微加一点圆角和阴影，让下拉菜单更像悬浮卡片
        try:
            self.category_menu.radius = [dp(10), dp(10), dp(10), dp(10)]
            self.category_menu.shadow_color = (0, 0, 0, 0.18)
        except Exception:
            # 某些 KivyMD 版本可能没有这些属性，忽略即可
            pass

    def _load_items(self, category: ItemCategory = None):
        """加载物品列表"""
        try:
            # 清空当前列表
            self.item_list_layout.clear_widgets()

            # 获取物品
            items = item_service.get_items(category=category)

            # 添加无物品提示
            if not items:
                empty_label = Label(
                    text="暂无物品，点击右下角+添加",
                    size_hint_y=None,
                    height=dp(100),
                    color=(0.6, 0.6, 0.6, 1),
                    valign='middle'
                )
                if CHINESE_FONT:
                    empty_label.font_name = CHINESE_FONT
                self.item_list_layout.add_widget(empty_label)
                return

            # 添加物品项
            for item in items:
                item_data = self._prepare_item_data(item)
                list_item = ItemListItem(item_data)
                list_item.bind(on_release=lambda instance, item_id=item.id:
                              self._on_item_click(item_id))
                self.item_list_layout.add_widget(list_item)

            # 更新统计信息
            self._update_stats()

        except Exception as e:
            logger.error(f"加载物品列表失败: {str(e)}")
            error_label = Label(
                text="加载失败，请重试",
                size_hint_y=None,
                height=dp(50),
                color=(0.9, 0.3, 0.3, 1)
            )
            if CHINESE_FONT:
                error_label.font_name = CHINESE_FONT
            self.item_list_layout.add_widget(error_label)

    def _prepare_item_data(self, item) -> dict:
        """准备物品数据"""
        expiry_date_str = "无"
        if item.expiry_date:
            expiry_date_str = item.expiry_date.strftime('%Y-%m-%d')

        return {
            'id': item.id,
            'name': item.name,
            'category': item.category.value,
            'expiry_date': expiry_date_str,
            'days_until_expiry': item.days_until_expiry or 0,
            'quantity': item.quantity
        }

    def _update_stats(self):
        """更新统计信息"""
        try:
            # 总物品数
            total_items = len(item_service.get_items())
            self.total_card.children[0].children[0].text = str(total_items)

            # 即将过期物品（7天内）
            expiring_items = len(item_service.get_expiring_items(days=7))
            self.expiring_card.children[0].children[0].text = str(expiring_items)

            # 已过期物品
            expired_items = 0
            for item in item_service.get_items():
                if item.is_expired and item.status != ItemStatus.CONSUMED:
                    expired_items += 1
            self.expired_card.children[0].children[0].text = str(expired_items)

        except Exception as e:
            logger.error(f"更新统计信息失败: {str(e)}")

    def _refresh_items(self, dt):
        """定时刷新物品列表"""
        self._load_items()

    def _show_category_menu(self, instance):
        """显示类别筛选菜单"""
        self.category_menu.open()

    def _select_category(self, category: ItemCategory):
        """选择类别"""
        self.category_menu.dismiss()

        if category:
            category_text = {
                ItemCategory.FOOD: "食品",
                ItemCategory.DAILY_NECESSITIES: "日用品",
                ItemCategory.MEDICINE: "药品",
                ItemCategory.COSMETICS: "化妆品",
                ItemCategory.OTHERS: "其他"
            }.get(category, "所有类别")
            self.category_button.text = category_text
        else:
            self.category_button.text = "所有类别"

        self._load_items(category)

    def _on_item_click(self, item_id: str):
        """物品点击事件"""
        app = MDApp.get_running_app()
        if hasattr(app, 'screen_manager'):
            # 切换到物品详情屏幕
            app.screen_manager.current = 'item_detail'
            # 传递物品ID到详情屏幕
            item_detail_screen = app.screen_manager.get_screen('item_detail')
            if item_detail_screen:
                item_detail_screen.item_id = item_id
                item_detail_screen._load_item(item_id)

    def _on_add_item(self, instance):
        """添加物品按钮点击事件"""
        app = MDApp.get_running_app()
        if hasattr(app, 'screen_manager'):
            # 切换到添加物品屏幕
            app.screen_manager.current = 'add_item'

    def on_enter(self):
        """进入屏幕时调用"""
        self._load_items()

        # 每次进入主界面、并完成列表重建后，再为整个屏幕应用中文字体，
        # 避免返回时新创建的控件仍使用系统默认字体导致中文变成方块
        try:
            import app.main as main_module
            runtime_font = getattr(main_module, 'CHINESE_FONT_NAME', None)
        except Exception:
            runtime_font = None
        if runtime_font:
            apply_font_to_widget(self, runtime_font)

    def on_leave(self):
        """离开屏幕时调用"""
        # 清理资源
        if hasattr(self, 'category_menu'):
            self.category_menu.dismiss()


# 测试代码
if __name__ == '__main__':
    from kivy.app import App as KivyApp

    class TestApp(KivyApp):
        def build(self):
            return MainScreen()

    TestApp().run()