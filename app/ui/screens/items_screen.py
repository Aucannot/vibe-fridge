# -*- coding: utf-8 -*-
"""
物品目录屏幕 - 左侧分类和物品目录 + 右侧库存记录
Modernized with Material Design 3 principles
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, ObjectProperty, BooleanProperty, ListProperty
from kivy.graphics import Color, RoundedRectangle, Ellipse
from kivy.animation import Animation
from kivymd.app import MDApp
from kivymd.uix.label import MDIcon

from app.services.item_service import item_service
from app.services.wiki_service import wiki_service
from app.models.item import ItemStatus
from app.models.item_wiki import ItemWikiCategory
from app.utils.logger import setup_logger
from app.utils.font_helper import apply_font_to_widget, CHINESE_FONT_NAME as CHINESE_FONT
from app.ui.theme.design_tokens import COLOR_PALETTE, DESIGN_TOKENS

logger = setup_logger(__name__)

COLORS = COLOR_PALETTE

# 自定义更鲜艳的颜色
BRIGHT_COLORS = {
    'primary': [0.39, 0.40, 0.95, 1],
    'primary_light': [0.51, 0.55, 0.97, 1],
    'success': [0.13, 0.77, 0.37, 1],
    'warning': [0.96, 0.35, 0.07, 1],
    'error': [0.94, 0.27, 0.27, 1],
    'surface': [1, 1, 1, 1],
    'surface_variant': [0.96, 0.96, 0.96, 1],
    'background': [0.98, 0.98, 0.99, 1],
    'text_primary': [0.15, 0.15, 0.15, 1],
    'text_secondary': [0.50, 0.50, 0.50, 1],
    'selected_bg': [0.39, 0.40, 0.95, 1],
    'selected_text': [1, 1, 1, 1],
    'hover_bg': [0.92, 0.92, 0.98, 1],
    'card_bg': [1, 1, 1, 1],
    'accent_orange': [1, 0.60, 0.20, 1],
    'accent_purple': [0.60, 0.40, 0.95, 1],
    'accent_green': [0.20, 0.78, 0.45, 1],
}

# 分类图标和颜色映射
CATEGORY_CONFIG = {
    "全部": {"icon": "view-grid", "color": BRIGHT_COLORS['primary']},
    "食品": {"icon": "food-apple", "color": [0.95, 0.35, 0.35, 1]},
    "日用品": {"icon": "home", "color": [0.25, 0.60, 0.95, 1]},
    "药品": {"icon": "medical-bag", "color": [0.20, 0.75, 0.50, 1]},
    "化妆品": {"icon": "face-woman", "color": [0.95, 0.45, 0.75, 1]},
    "其他": {"icon": "package-variant", "color": [0.60, 0.60, 0.70, 1]},
}

CATEGORY_ICON_MAP = {
    "食品": "food-apple",
    "日用品": "home",
    "药品": "medical-bag",
    "化妆品": "face-woman",
    "其他": "package-variant",
}

STATUS_COLORS = {
    'fresh': BRIGHT_COLORS['success'],
    'expiring': BRIGHT_COLORS['warning'],
    'expired': BRIGHT_COLORS['error'],
}


class CategoryChip(BoxLayout):
    """分类筛选标签 - 鲜艳配色选中状态高亮"""
    __events__ = ('on_release',)

    category_key = StringProperty()
    category_name = StringProperty()
    icon = StringProperty()
    is_selected = BooleanProperty(False)
    count = NumericProperty(0)
    _name_label = None
    _icon_widget = None

    def __init__(self, category_key, category_name, icon_name, count=0, **kwargs):
        super().__init__(**kwargs)
        self.category_key = category_key
        self.category_name = category_name
        self.icon = icon_name
        self.count = count
        self._hovered = False

        self.orientation = "horizontal"
        self.size_hint_y = None
        self.size_hint_x = 1
        self.height = dp(48)
        self.padding = (dp(14), dp(8), dp(14), dp(8))

        self._setup_ui()
        self._update_visual_state()

    def _setup_ui(self):
        self._icon_widget = MDIcon(
            icon=self.icon,
            theme_text_color="Custom",
            text_color=self._get_icon_color(),
            size_hint_x=None,
            width=dp(28),
            size_hint_y=None,
            height=dp(32),
            halign="center",
            valign="middle",
            font_size=dp(20),
        )
        self.add_widget(self._icon_widget)

        self._name_label = Label(
            text=self.category_name,
            size_hint_x=1,
            size_hint_y=None,
            height=dp(32),
            halign="left",
            valign="middle",
            color=self._get_text_color(),
            font_size=dp(15),
            bold=True,
        )
        self._name_label.bind(
            size=lambda inst, val: self._update_label_size(),
            width=lambda inst, val: self._update_label_size()
        )
        if CHINESE_FONT:
            self._name_label.font_name = CHINESE_FONT
        self.add_widget(self._name_label)

        if self.count > 0:
            count_badge = BoxLayout(
                size_hint_x=None,
                width=dp(32),
                size_hint_y=None,
                height=dp(22),
                padding=(dp(8), 0, dp(8), 0),
            )
            count_label = Label(
                text=str(self.count),
                size_hint=(1, 1),
                halign="center",
                valign="middle",
                color=self._get_count_color(),
                font_size=dp(13),
                bold=True,
            )
            if CHINESE_FONT:
                count_label.font_name = CHINESE_FONT
            count_badge.add_widget(count_label)

            with count_badge.canvas.before:
                Color(*self._get_badge_bg_color())
                RoundedRectangle(pos=count_badge.pos, size=count_badge.size, radius=[dp(11)])
            count_badge.bind(pos=self._update_badge_pos, size=self._update_badge_pos)
            self.add_widget(count_badge)

    def _update_label_size(self):
        if self._name_label:
            width = self._name_label.width if self._name_label.width > 0 else 100
            self._name_label.text_size = (width - dp(8), None)

    def _update_badge_pos(self, *args):
        pass

    def _get_icon_color(self):
        if self.is_selected:
            return BRIGHT_COLORS['selected_text']
        return BRIGHT_COLORS['primary']

    def _get_text_color(self):
        if self.is_selected:
            return BRIGHT_COLORS['selected_text']
        return BRIGHT_COLORS['text_primary']

    def _get_count_color(self):
        if self.is_selected:
            return BRIGHT_COLORS['primary']
        return BRIGHT_COLORS['selected_text']

    def _get_badge_bg_color(self):
        if self.is_selected:
            return [1, 1, 1, 0.25]
        return BRIGHT_COLORS['primary'][:3] + [0.1]

    def _get_background_color(self):
        if self.is_selected:
            return BRIGHT_COLORS['selected_bg']
        if self._hovered:
            return BRIGHT_COLORS['hover_bg']
        return BRIGHT_COLORS['surface']

    def _update_visual_state(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._get_background_color())
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(14)])

        if self._icon_widget:
            self._icon_widget.text_color = self._get_icon_color()
        if self._name_label:
            self._name_label.color = self._get_text_color()

    def set_selected(self, selected: bool):
        if self.is_selected != selected:
            self.is_selected = selected
            self._animate_selection()
        else:
            self._update_visual_state()

    def _animate_selection(self):
        if self.is_selected:
            anim = Animation(height=dp(50), duration=0.12)
            anim.bind(on_complete=lambda *args: Animation(height=dp(48), duration=0.12).start(self))
            anim.start(self)
        self._update_visual_state()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dispatch('on_release')
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            if not self._hovered:
                self._hovered = True
                self._update_visual_state()
        else:
            if self._hovered:
                self._hovered = False
                self._update_visual_state()
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._hovered and not self.collide_point(*touch.pos):
            self._hovered = False
            self._update_visual_state()
        return super().on_touch_up(touch)

    def on_release(self, *args):
        pass


class WikiItemCard(BoxLayout):
    """物品目录卡片 - 左侧物品列表项"""
    __events__ = ('on_release',)

    item_name = StringProperty()
    category = StringProperty()
    has_inventory = NumericProperty(0)
    is_selected = BooleanProperty(False)
    category_icon = StringProperty()

    def __init__(self, item_data, **kwargs):
        super().__init__(**kwargs)
        self.item_name = item_data.get('name', '未命名')
        self.category = item_data.get('category', '其他')
        self.has_inventory = item_data.get('total_count', 0)
        self.category_icon = CATEGORY_ICON_MAP.get(self.category, "package-variant")
        self._hovered = False

        self.orientation = "horizontal"
        self.size_hint_y = None
        self.size_hint_x = 1
        self.height = dp(60)
        self.padding = (dp(14), dp(8), dp(14), dp(8))

        self._setup_ui()

    def _setup_ui(self):
        cat_config = CATEGORY_CONFIG.get(self.category, CATEGORY_CONFIG["其他"])
        icon_color = cat_config["color"]

        icon_bg = BoxLayout(
            size_hint_x=None,
            width=dp(44),
            size_hint_y=None,
            height=dp(44),
            padding=dp(6),
        )
        with icon_bg.canvas.before:
            Color(*icon_color[:3] + [0.15])
            RoundedRectangle(pos=icon_bg.pos, size=icon_bg.size, radius=[dp(12)])

        icon = MDIcon(
            icon=self.category_icon,
            theme_text_color="Custom",
            text_color=icon_color,
            size_hint=(1, 1),
            halign="center",
            valign="middle",
            font_size=dp(22),
        )
        icon_bg.add_widget(icon)
        self.add_widget(icon_bg)

        text_box = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(3))

        name_label = Label(
            text=self.item_name,
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="bottom",
            color=BRIGHT_COLORS['text_primary'],
            font_size=dp(16),
            bold=True,
        )
        name_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            name_label.font_name = CHINESE_FONT
        text_box.add_widget(name_label)

        category_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(18), spacing=dp(6))
        cat_label = Label(
            text=self.category,
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="top",
            color=BRIGHT_COLORS['text_secondary'],
            font_size=dp(13),
        )
        cat_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            cat_label.font_name = CHINESE_FONT
        category_row.add_widget(cat_label)

        if self.has_inventory > 0:
            stock_indicator = Label(
                text="● 有库存",
                size_hint_y=None,
                height=dp(18),
                color=BRIGHT_COLORS['success'],
                font_size=dp(12),
            )
            if CHINESE_FONT:
                stock_indicator.font_name = CHINESE_FONT
            category_row.add_widget(stock_indicator)

        text_box.add_widget(category_row)
        self.add_widget(text_box)

        if self.has_inventory > 0:
            badge = BoxLayout(
                orientation="vertical",
                size_hint_x=None,
                width=dp(36),
                size_hint_y=None,
                height=dp(36),
                padding=(dp(6), dp(4)),
            )
            with badge.canvas.before:
                Color(*BRIGHT_COLORS['accent_green'])
                RoundedRectangle(pos=badge.pos, size=badge.size, radius=[dp(14)])

            count_label = Label(
                text=str(self.has_inventory),
                size_hint=(1, 1),
                halign="center",
                valign="middle",
                color=BRIGHT_COLORS['surface'],
                font_size=dp(15),
                bold=True,
            )
            if CHINESE_FONT:
                count_label.font_name = CHINESE_FONT
            badge.add_widget(count_label)
            self.add_widget(badge)

        self._update_background()

    def _get_background_color(self):
        if self.is_selected:
            return BRIGHT_COLORS['selected_bg']
        if self._hovered:
            return BRIGHT_COLORS['hover_bg']
        return BRIGHT_COLORS['surface']

    def _update_background(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._get_background_color())
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(10)])

    def set_selected(self, selected: bool):
        self.is_selected = selected
        self._update_background()

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dispatch('on_release')
            self._animate_press()
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            if not self._hovered:
                self._hovered = True
                self._update_background()
        else:
            if self._hovered:
                self._hovered = False
                self._update_background()
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._hovered and not self.collide_point(*touch.pos):
            self._hovered = False
            self._update_background()
        return super().on_touch_up(touch)

    def _animate_press(self):
        orig_height = dp(56)
        anim = Animation(height=orig_height - dp(4), duration=0.05)
        anim.bind(on_complete=lambda *args: Animation(height=orig_height, duration=0.1).start(self))
        anim.start(self)

    def on_release(self, *args):
        pass


class InventoryRecordCard(BoxLayout):
    """库存记录卡片 - 右侧库存列表项"""
    __events__ = ('on_release',)

    item_id = StringProperty()
    item_name = StringProperty()
    expiry_date = StringProperty()
    quantity = NumericProperty(0)
    status = StringProperty('fresh')
    is_selected = BooleanProperty(False)

    def __init__(self, item_data, **kwargs):
        super().__init__(**kwargs)
        self.item_id = item_data.get("id", "")
        self.item_name = item_data.get("name", "未命名")
        self.expiry_date = item_data.get("expiry_date", "无")
        self.quantity = item_data.get("quantity", 0)
        self.status = item_data.get("status", "fresh")
        self._hovered = False

        self.orientation = "horizontal"
        self.size_hint_y = None
        self.size_hint_x = 1
        self.height = dp(68)
        self.padding = (dp(12), dp(8), dp(12), dp(8))

        self._setup_ui()

    def _setup_ui(self):
        status_color = STATUS_COLORS.get(self.status, STATUS_COLORS['fresh'])

        status_indicator = BoxLayout(
            size_hint_x=None,
            width=dp(8),
            size_hint_y=None,
            height=dp(52),
        )
        with status_indicator.canvas.before:
            Color(*status_color)
            RoundedRectangle(pos=status_indicator.pos, size=status_indicator.size, radius=[dp(4)])
        self.add_widget(status_indicator)

        icon_box = BoxLayout(
            size_hint_x=None,
            width=dp(44),
            size_hint_y=None,
            height=dp(52),
            padding=dp(6),
        )
        with icon_box.canvas.before:
            Color(*BRIGHT_COLORS['background'])
            RoundedRectangle(pos=icon_box.pos, size=icon_box.size, radius=[dp(10)])

        icon = MDIcon(
            icon=self._get_status_icon(),
            theme_text_color="Custom",
            text_color=status_color,
            size_hint=(1, 1),
            halign="center",
            valign="middle",
            font_size=dp(20),
        )
        icon_box.add_widget(icon)
        self.add_widget(icon_box)

        text_box = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(4))

        name_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(24), spacing=dp(8))
        name_label = Label(
            text=self.item_name,
            size_hint_x=1,
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="bottom",
            color=BRIGHT_COLORS['text_primary'],
            font_size=dp(15),
            bold=True,
        )
        name_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            name_label.font_name = CHINESE_FONT
        name_row.add_widget(name_label)

        if self.quantity > 0:
            qty_label = Label(
                text=f"x{self.quantity}",
                size_hint_x=None,
                width=dp(36),
                size_hint_y=None,
                height=dp(24),
                halign="right",
                valign="bottom",
                color=BRIGHT_COLORS['accent_orange'],
                font_size=dp(14),
                bold=True,
            )
            if CHINESE_FONT:
                qty_label.font_name = CHINESE_FONT
            name_row.add_widget(qty_label)

        text_box.add_widget(name_row)

        date_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(20), spacing=dp(6))
        date_icon = MDIcon(
            icon="calendar-clock",
            theme_text_color="Custom",
            text_color=BRIGHT_COLORS['text_secondary'],
            size_hint_x=None,
            width=dp(18),
            size_hint_y=None,
            height=dp(20),
            halign="center",
            valign="middle",
            font_size=dp(14),
        )
        date_row.add_widget(date_icon)

        date_label = Label(
            text=f"过期: {self.expiry_date}" if self.expiry_date != "无" else "无过期日期",
            size_hint_x=1,
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
            color=self._get_expiry_color(),
            font_size=dp(13),
        )
        date_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            date_label.font_name = CHINESE_FONT
        date_row.add_widget(date_label)

        text_box.add_widget(date_row)

        status_label = Label(
            text=self._get_status_text(),
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
            color=status_color,
            font_size=dp(12),
            italic=True,
        )
        if CHINESE_FONT:
            status_label.font_name = CHINESE_FONT
        text_box.add_widget(status_label)

        self.add_widget(text_box)

        arrow = MDIcon(
            icon="chevron-right",
            theme_text_color="Custom",
            text_color=BRIGHT_COLORS['text_secondary'],
            size_hint_x=None,
            width=dp(24),
            size_hint_y=None,
            height=dp(52),
            halign="center",
            valign="middle",
            font_size=dp(22),
        )
        self.add_widget(arrow)

        self._update_background()

    def _get_status_icon(self):
        icons = {
            'fresh': 'check-circle',
            'expiring': 'clock-alert',
            'expired': 'alert-circle',
        }
        return icons.get(self.status, 'help-circle')

    def _get_status_text(self):
        texts = {
            'fresh': '状态正常',
            'expiring': '即将过期',
            'expired': '已过期',
        }
        return texts.get(self.status, '未知状态')

    def _get_expiry_color(self):
        colors = {
            'fresh': BRIGHT_COLORS['text_secondary'],
            'expiring': BRIGHT_COLORS['warning'],
            'expired': BRIGHT_COLORS['error'],
        }
        return colors.get(self.status, BRIGHT_COLORS['text_secondary'])

    def _get_background_color(self):
        if self.is_selected:
            return BRIGHT_COLORS['selected_bg']
        if self._hovered:
            return BRIGHT_COLORS['hover_bg']
        return BRIGHT_COLORS['surface']

    def _update_background(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._get_background_color())
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dispatch('on_release')
            return True
        return super().on_touch_down(touch)

    def on_touch_move(self, touch):
        if self.collide_point(*touch.pos):
            if not self._hovered:
                self._hovered = True
                self._update_background()
        else:
            if self._hovered:
                self._hovered = False
                self._update_background()
        return super().on_touch_move(touch)

    def on_touch_up(self, touch):
        if self._hovered and not self.collide_point(*touch.pos):
            self._hovered = False
            self._update_background()
        return super().on_touch_up(touch)

    def on_release(self, *args):
        pass


class SectionHeader(BoxLayout):
    """分区标题栏"""
    title = StringProperty()
    subtitle = StringProperty(defaultvalue="")

    def __init__(self, title, subtitle="", **kwargs):
        super().__init__(**kwargs)
        self.title = title
        self.subtitle = subtitle
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(44)
        self.padding = (dp(4), dp(4), dp(4), dp(4))

        title_label = Label(
            text=self.title,
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="middle",
            color=BRIGHT_COLORS['text_primary'],
            font_size=dp(16),
            bold=True,
        )
        title_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        self.add_widget(title_label)

        if self.subtitle:
            subtitle_label = Label(
                text=self.subtitle,
                size_hint_y=None,
                height=dp(16),
                halign="left",
                valign="middle",
                color=BRIGHT_COLORS['text_secondary'],
                font_size=dp(12),
            )
            subtitle_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
            if CHINESE_FONT:
                subtitle_label.font_name = CHINESE_FONT
            self.add_widget(subtitle_label)


class ItemsScreen(Screen):
    """物品目录屏幕 - 左侧分类 + 右侧物品列表和库存记录"""

    selected_item_name = ObjectProperty(allownone=True)
    selected_category = StringProperty("全部")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "items"
        self._category_buttons = {}
        self._item_cards = {}
        self._categories = []
        self._build_ui()
        self._load_categories()
        self._load_wiki_items()

    def _build_ui(self):
        root = BoxLayout(orientation="horizontal", size_hint=(1, 1), spacing=dp(0), padding=dp(0))

        left_panel = BoxLayout(
            orientation="vertical",
            size_hint_x=0.3,
            padding=(dp(8), dp(8), dp(4), dp(8)),
            spacing=dp(6),
        )

        category_scroll = ScrollView(
            size_hint_y=1,
            do_scroll_x=False,
            bar_width=dp(3),
            bar_color=BRIGHT_COLORS['primary'],
            bar_inactive_color=BRIGHT_COLORS['surface_variant'],
        )
        self._category_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            size_hint_x=1,
            spacing=dp(4),
        )
        self._category_box.bind(minimum_height=self._category_box.setter("height"))
        category_scroll.add_widget(self._category_box)
        left_panel.add_widget(category_scroll)

        root.add_widget(left_panel)

        divider_v = BoxLayout(size_hint_x=None, width=dp(1), size_hint_y=1)
        with divider_v.canvas.before:
            Color(*BRIGHT_COLORS['surface_variant'][:3] + [0.5])
            RoundedRectangle(pos=divider_v.pos, size=divider_v.size, radius=[dp(0.5)])
        root.add_widget(divider_v)

        right_panel = BoxLayout(orientation="vertical", size_hint_x=0.7, padding=(dp(8), dp(8), dp(8), dp(8)), spacing=dp(6))

        item_scroll = ScrollView(
            size_hint_y=1,
            do_scroll_x=False,
            bar_width=dp(3),
            bar_color=BRIGHT_COLORS['primary'],
            bar_inactive_color=BRIGHT_COLORS['surface_variant'],
        )
        self._item_list_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            size_hint_x=1,
            spacing=dp(6),
        )
        self._item_list_box.bind(minimum_height=self._item_list_box.setter("height"))
        item_scroll.add_widget(self._item_list_box)
        right_panel.add_widget(item_scroll)

        root.add_widget(right_panel)

        self.add_widget(root)

    def _load_categories(self):
        """从数据库加载物品分类信息"""
        try:
            categories = wiki_service.get_all_categories()
            self._categories = categories
            
            # 定义默认分类
            default_categories = [
                {"name": "食品", "icon": "food-apple", "sort_order": 1},
                {"name": "日用品", "icon": "home", "sort_order": 2},
                {"name": "化妆品", "icon": "palette", "sort_order": 3},
                {"name": "药品", "icon": "medical-bag", "sort_order": 4},
                {"name": "其他", "icon": "package-variant", "sort_order": 5},
            ]
            
            # 获取现有分类名称
            existing_names = {cat.name for cat in categories}
            
            # 创建缺失的默认分类
            for cat_data in default_categories:
                if cat_data["name"] not in existing_names:
                    category = wiki_service.create_category(**cat_data)
                    if category:
                        self._categories.append(category)
                        existing_names.add(cat_data["name"])
            
            # 重新加载分类列表（确保包含新创建的分类）
            self._categories = wiki_service.get_all_categories()
            
            # 设置分类按钮
            self._setup_category_buttons()
                
        except Exception as e:
            logger.error(f"加载分类失败: {e}")

    def _setup_category_buttons(self):
        """设置分类按钮"""
        self._category_box.clear_widgets()
        self._category_buttons.clear()

        # 添加"全部"按钮
        all_btn = CategoryChip(
            category_key="全部",
            category_name="全部物品",
            icon_name="format-list-bulleted",
            count=0,
        )
        all_btn.bind(on_release=lambda inst: self._on_category_selected("全部"))
        self._category_box.add_widget(all_btn)
        self._category_buttons["全部"] = all_btn

        # 添加各个分类按钮
        for category in self._categories:
            btn = CategoryChip(
                category_key=category.name,
                category_name=category.name,
                icon_name=category.icon or "folder",
                count=0,
            )
            btn.bind(on_release=lambda inst, key=category.name: self._on_category_selected(key))
            self._category_box.add_widget(btn)
            self._category_buttons[category.name] = btn

        # 默认选中"全部"
        self._on_category_selected("全部")

    def _on_category_selected(self, category_key: str):
        self.selected_category = category_key

        for key, btn in self._category_buttons.items():
            btn.set_selected(key == category_key)

        self._load_wiki_items()

    def _load_wiki_items(self):
        self._item_list_box.clear_widgets()
        self._item_cards.clear()

        try:
            all_items = item_service.get_registered_items()

            # 根据选中的分类筛选物品
            if self.selected_category != "全部":
                items = [item for item in all_items if item.get('category') == self.selected_category]
            else:
                items = all_items

            if not items:
                empty_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(80), spacing=dp(4))
                empty_icon = MDIcon(
                    icon="package-variant-remove",
                    theme_text_color="Custom",
                    text_color=COLORS['text_hint'],
                    size_hint_y=None,
                    height=dp(32),
                    halign="center",
                    valign="middle",
                    font_size=dp(28),
                )
                empty_box.add_widget(empty_icon)

                empty = Label(
                    text="该分类下暂无物品",
                    size_hint_y=None,
                    height=dp(24),
                    halign="center",
                    valign="middle",
                    color=COLORS['text_hint'],
                    font_size=dp(14),
                )
                empty.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
                if CHINESE_FONT:
                    empty.font_name = CHINESE_FONT
                empty_box.add_widget(empty)

                hint = Label(
                    text="请选择其他分类或添加新物品",
                    size_hint_y=None,
                    height=dp(20),
                    halign="center",
                    valign="middle",
                    color=COLORS['text_hint'],
                    font_size=dp(12),
                )
                hint.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
                if CHINESE_FONT:
                    hint.font_name = CHINESE_FONT
                empty_box.add_widget(hint)
                self._item_list_box.add_widget(empty_box)
                return

            for item_data in items:
                card = WikiItemCard(item_data)
                card.bind(on_release=lambda inst, data=item_data: self._on_item_selected(data))
                self._item_list_box.add_widget(card)
                self._item_cards[item_data['name']] = card

        except Exception as e:
            logger.error(f"加载物品目录失败: {e}")
            error_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(60))
            error_icon = MDIcon(
                icon="alert-circle",
                theme_text_color="Custom",
                text_color=COLORS['error'],
                size_hint_y=None,
                height=dp(28),
                halign="center",
                valign="middle",
                font_size=dp(24),
            )
            error_box.add_widget(error_icon)

            error = Label(
                text="加载失败，请重试",
                size_hint_y=None,
                height=dp(24),
                halign="center",
                valign="middle",
                color=COLORS['error'],
                font_size=dp(14),
            )
            error.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
            if CHINESE_FONT:
                error.font_name = CHINESE_FONT
            error_box.add_widget(error)
            self._item_list_box.add_widget(error_box)

    def _on_item_selected(self, item_data):
        item_name = item_data['name']
        category = item_data.get('category', '其他')
        self.selected_item_name = item_name
        self.selected_category = category
        self._update_item_card_styles()
        
        # 跳转到物品Wiki详情页
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            app.screen_manager.current = "item_wiki_detail"
            detail = app.screen_manager.get_screen("item_wiki_detail")
            if detail:
                detail.load_wiki_item(item_name)

    def _update_item_card_styles(self):
        for name, card in self._item_cards.items():
            card.set_selected(name == self.selected_item_name)

    def on_enter(self):
        self._load_categories()
        self._load_wiki_items()
        try:
            import app.main as main_module
            font = getattr(main_module, "CHINESE_FONT_NAME", None)
        except Exception:
            font = None
        if font:
            apply_font_to_widget(self, font)

    def refresh_data(self):
        self._load_categories()
        self._load_wiki_items()
