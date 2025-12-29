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
from app.models.item import ItemCategory, ItemStatus
from app.utils.logger import setup_logger
from app.utils.font_helper import apply_font_to_widget, CHINESE_FONT_NAME as CHINESE_FONT
from app.ui.theme.design_tokens import COLOR_PALETTE, DESIGN_TOKENS

logger = setup_logger(__name__)

COLORS = COLOR_PALETTE

CATEGORY_MAP = {
    ItemCategory.FOOD.value: "食品",
    ItemCategory.DAILY_NECESSITIES.value: "日用品",
    ItemCategory.MEDICINE.value: "药品",
    ItemCategory.COSMETICS.value: "化妆品",
    ItemCategory.OTHERS.value: "其他",
}

CATEGORY_ICONS = {
    ItemCategory.FOOD.value: "food-apple",
    ItemCategory.DAILY_NECESSITIES.value: "home",
    ItemCategory.MEDICINE.value: "medical-bag",
    ItemCategory.COSMETICS.value: "face-woman",
    ItemCategory.OTHERS.value: "package-variant",
}

STATUS_COLORS = {
    'fresh': COLORS['success'],
    'expiring': COLORS['warning'],
    'expired': COLORS['error'],
}

ALL_CATEGORY = "all"


class CategoryChip(BoxLayout):
    """分类筛选标签 - 带动画效果"""
    __events__ = ('on_release',)

    category_key = StringProperty()
    category_name = StringProperty()
    icon = StringProperty()
    is_selected = BooleanProperty(False)
    count = NumericProperty(0)

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
        self.height = dp(38)
        self.padding = (dp(10), dp(4), dp(10), dp(4))
        spacing = dp(6)

        self._setup_ui()
        self._update_visual_state()

    def _setup_ui(self):
        icon = MDIcon(
            icon=self.icon,
            theme_text_color="Custom",
            text_color=self._get_icon_color(),
            size_hint_x=None,
            width=dp(22),
            size_hint_y=None,
            height=dp(30),
            halign="center",
            valign="middle",
            font_size=dp(16),
        )
        self.add_widget(icon)

        name_label = Label(
            text=self.category_name,
            size_hint_x=None,
            width=dp(50),
            size_hint_y=None,
            height=dp(30),
            halign="left",
            valign="middle",
            color=self._get_text_color(),
            font_size=dp(13),
            bold=self.is_selected,
        )
        name_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0] - dp(4), None)))
        if CHINESE_FONT:
            name_label.font_name = CHINESE_FONT
        self.add_widget(name_label)

        if self.count > 0:
            count_badge = BoxLayout(
                size_hint_x=None,
                width=dp(28),
                size_hint_y=None,
                height=dp(18),
                padding=(dp(4), 0, dp(4), 0),
            )
            count_label = Label(
                text=str(self.count),
                size_hint=(1, 1),
                halign="center",
                valign="middle",
                color=self._get_count_color(),
                font_size=dp(11),
                bold=True,
            )
            if CHINESE_FONT:
                count_label.font_name = CHINESE_FONT
            count_badge.add_widget(count_label)

            with count_badge.canvas.before:
                Color(*self._get_badge_color())
                Ellipse(pos=count_badge.pos, size=count_badge.size)
            count_badge.bind(pos=self._update_badge_ellipse, size=self._update_badge_ellipse)
            self.add_widget(count_badge)

    def _update_badge_ellipse(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._get_badge_color())
            Ellipse(pos=self.pos, size=self.size)

    def _get_icon_color(self):
        if self.is_selected:
            return COLORS['surface']
        return COLORS['text_secondary']

    def _get_text_color(self):
        if self.is_selected:
            return COLORS['surface']
        return COLORS['text_primary']

    def _get_count_color(self):
        if self.is_selected:
            return COLORS['surface']
        return COLORS['primary']

    def _get_badge_color(self):
        if self.is_selected:
            return COLORS['surface'], (1, 1, 1, 0.3)
        return COLORS['primary'], (1, 1, 1, 0.8)

    def _get_background_color(self):
        if self.is_selected:
            return COLORS['chip_selected']
        if self._hovered:
            return COLORS['chip_unselected']
        return COLORS['chip_unselected']

    def _update_visual_state(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*self._get_background_color())
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])

    def set_selected(self, selected: bool):
        if self.is_selected != selected:
            self.is_selected = selected
            self._animate_selection()
        else:
            self._update_visual_state()

    def _animate_selection(self):
        if self.is_selected:
            anim = Animation(height=dp(42), duration=0.1)
            anim.bind(on_complete=lambda *args: Animation(height=dp(38), duration=0.1).start(self))
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
        self.category_icon = CATEGORY_ICONS.get(self.category, "package-variant")
        self._hovered = False

        self.orientation = "horizontal"
        self.size_hint_y = None
        self.size_hint_x = 1
        self.height = dp(56)
        self.padding = (dp(12), dp(6), dp(12), dp(6))

        self._setup_ui()

    def _setup_ui(self):
        icon_bg = BoxLayout(
            size_hint_x=None,
            width=dp(40),
            size_hint_y=None,
            height=dp(44),
            padding=dp(4),
        )
        with icon_bg.canvas.before:
            Color(*COLORS['primary_container'])
            RoundedRectangle(pos=icon_bg.pos, size=icon_bg.size, radius=[dp(8)])

        icon = MDIcon(
            icon=self.category_icon,
            theme_text_color="Custom",
            text_color=COLORS['primary'],
            size_hint=(1, 1),
            halign="center",
            valign="middle",
            font_size=dp(20),
        )
        icon_bg.add_widget(icon)
        self.add_widget(icon_bg)

        text_box = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(2))

        name_label = Label(
            text=self.item_name,
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="bottom",
            color=COLORS['text_primary'],
            font_size=dp(15),
            bold=True,
        )
        name_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            name_label.font_name = CHINESE_FONT
        text_box.add_widget(name_label)

        category_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(16), spacing=dp(4))
        cat_label = Label(
            text=CATEGORY_MAP.get(self.category, self.category),
            size_hint_y=None,
            height=dp(16),
            halign="left",
            valign="top",
            color=COLORS['text_secondary'],
            font_size=dp(12),
        )
        cat_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            cat_label.font_name = CHINESE_FONT
        category_row.add_widget(cat_label)

        if self.has_inventory > 0:
            stock_indicator = Label(
                text="● 有库存",
                size_hint_y=None,
                height=dp(16),
                color=COLORS['success'],
                font_size=dp(11),
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
                width=dp(32),
                size_hint_y=None,
                height=dp(32),
                padding=(dp(4), dp(2)),
            )
            with badge.canvas.before:
                Color(*COLORS['primary'])
                RoundedRectangle(pos=badge.pos, size=badge.size, radius=[dp(12)])

            count_label = Label(
                text=str(self.has_inventory),
                size_hint=(1, 1),
                halign="center",
                valign="middle",
                color=COLORS['surface'],
                font_size=dp(14),
                bold=True,
            )
            if CHINESE_FONT:
                count_label.font_name = CHINESE_FONT
            badge.add_widget(count_label)
            self.add_widget(badge)

        self._update_background()

    def _update_background(self):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.is_selected:
                Color(*COLORS['primary_container'])
            elif self._hovered:
                Color(*COLORS['surface_variant'])
            else:
                Color(*COLORS['surface'])
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
        self.height = dp(64)
        self.padding = (dp(10), dp(6), dp(10), dp(6))

        self._setup_ui()

    def _setup_ui(self):
        status_color = STATUS_COLORS.get(self.status, STATUS_COLORS['fresh'])

        status_indicator = BoxLayout(
            size_hint_x=None,
            width=dp(6),
            size_hint_y=None,
            height=dp(52),
        )
        with status_indicator.canvas.before:
            Color(*status_color)
            RoundedRectangle(pos=status_indicator.pos, size=status_indicator.size, radius=[dp(3)])
        self.add_widget(status_indicator)

        icon_box = BoxLayout(
            size_hint_x=None,
            width=dp(40),
            size_hint_y=None,
            height=dp(52),
            padding=dp(4),
        )
        with icon_box.canvas.before:
            Color(*COLORS['background'])
            RoundedRectangle(pos=icon_box.pos, size=icon_box.size, radius=[dp(6)])

        icon = MDIcon(
            icon=self._get_status_icon(),
            theme_text_color="Custom",
            text_color=status_color,
            size_hint=(1, 1),
            halign="center",
            valign="middle",
            font_size=dp(18),
        )
        icon_box.add_widget(icon)
        self.add_widget(icon_box)

        text_box = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(3))

        name_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(22), spacing=dp(6))
        name_label = Label(
            text=self.item_name,
            size_hint_x=1,
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="bottom",
            color=COLORS['text_primary'],
            font_size=dp(14),
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
                width=dp(30),
                size_hint_y=None,
                height=dp(22),
                halign="right",
                valign="bottom",
                color=COLORS['primary'],
                font_size=dp(13),
                bold=True,
            )
            if CHINESE_FONT:
                qty_label.font_name = CHINESE_FONT
            name_row.add_widget(qty_label)

        text_box.add_widget(name_row)

        date_row = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(18), spacing=dp(4))
        date_icon = MDIcon(
            icon="calendar-clock",
            theme_text_color="Custom",
            text_color=COLORS['text_hint'],
            size_hint_x=None,
            width=dp(16),
            size_hint_y=None,
            height=dp(18),
            halign="center",
            valign="middle",
            font_size=dp(12),
        )
        date_row.add_widget(date_icon)

        date_label = Label(
            text=f"过期: {self.expiry_date}" if self.expiry_date != "无" else "无过期日期",
            size_hint_x=1,
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
            color=self._get_expiry_color(),
            font_size=dp(12),
        )
        date_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            date_label.font_name = CHINESE_FONT
        date_row.add_widget(date_label)

        text_box.add_widget(date_row)

        status_label = Label(
            text=self._get_status_text(),
            size_hint_y=None,
            height=dp(16),
            halign="left",
            valign="middle",
            color=status_color,
            font_size=dp(11),
            italic=True,
        )
        if CHINESE_FONT:
            status_label.font_name = CHINESE_FONT
        text_box.add_widget(status_label)

        self.add_widget(text_box)

        arrow = MDIcon(
            icon="chevron-right",
            theme_text_color="Custom",
            text_color=COLORS['text_hint'],
            size_hint_x=None,
            width=dp(20),
            size_hint_y=None,
            height=dp(52),
            halign="center",
            valign="middle",
            font_size=dp(20),
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
            'fresh': COLORS['text_secondary'],
            'expiring': COLORS['warning'],
            'expired': COLORS['error'],
        }
        return colors.get(self.status, COLORS['text_secondary'])

    def _update_background(self):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.is_selected:
                Color(*COLORS['primary_container'])
            elif self._hovered:
                Color(*COLORS['surface_variant'])
            else:
                Color(*COLORS['surface'])
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
            color=COLORS['text_primary'],
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
                color=COLORS['text_secondary'],
                font_size=dp(12),
            )
            subtitle_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
            if CHINESE_FONT:
                subtitle_label.font_name = CHINESE_FONT
            self.add_widget(subtitle_label)


class ItemsScreen(Screen):
    """物品目录屏幕 - 左侧分类和物品目录 + 右侧库存记录"""

    selected_item_name = ObjectProperty(allownone=True)
    selected_item_category = StringProperty()
    selected_filter_category = StringProperty(defaultvalue=ALL_CATEGORY)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "items"
        self._item_cards = {}
        self._category_buttons = {}
        self._category_counts = {}
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="horizontal", size_hint=(1, 1), spacing=dp(0), padding=dp(0))

        left_panel = BoxLayout(
            orientation="vertical",
            size_hint_x=0.42,
            padding=(dp(8), dp(8), dp(4), dp(8)),
            spacing=dp(6),
        )

        header_section = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(44))
        main_title = Label(
            text="物品目录",
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            color=COLORS['text_primary'],
            font_size=dp(18),
            bold=True,
        )
        main_title.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            main_title.font_name = CHINESE_FONT
        header_section.add_widget(main_title)

        sub_title = Label(
            text="选择分类和物品查看库存",
            size_hint_y=None,
            height=dp(16),
            halign="left",
            valign="middle",
            color=COLORS['text_secondary'],
            font_size=dp(12),
        )
        sub_title.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            sub_title.font_name = CHINESE_FONT
        header_section.add_widget(sub_title)
        left_panel.add_widget(header_section)

        category_scroll = ScrollView(
            size_hint_y=None,
            height=dp(140),
            do_scroll_x=False,
            bar_width=dp(3),
            bar_color=COLORS['primary'],
            bar_inactive_color=COLORS['divider'],
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

        divider = BoxLayout(size_hint_y=None, height=dp(1), size_hint_x=1)
        with divider.canvas.before:
            Color(*COLORS['divider'])
            RoundedRectangle(pos=divider.pos, size=divider.size, radius=[dp(0.5)])
        left_panel.add_widget(divider)

        item_list_label = Label(
            text="物品列表",
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="middle",
            color=COLORS['text_secondary'],
            font_size=dp(13),
            bold=True,
        )
        item_list_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            item_list_label.font_name = CHINESE_FONT
        left_panel.add_widget(item_list_label)

        item_scroll = ScrollView(
            size_hint_y=1,
            do_scroll_x=False,
            bar_width=dp(3),
            bar_color=COLORS['primary'],
            bar_inactive_color=COLORS['divider'],
        )
        self._item_list_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            size_hint_x=1,
            spacing=dp(6),
        )
        self._item_list_box.bind(minimum_height=self._item_list_box.setter("height"))
        item_scroll.add_widget(self._item_list_box)
        left_panel.add_widget(item_scroll)

        root.add_widget(left_panel)

        divider_v = BoxLayout(size_hint_x=None, width=dp(1), size_hint_y=1)
        with divider_v.canvas.before:
            Color(*COLORS['divider'])
            RoundedRectangle(pos=divider_v.pos, size=divider_v.size, radius=[dp(0.5)])
        root.add_widget(divider_v)

        right_panel = BoxLayout(orientation="vertical", size_hint_x=0.58, padding=(dp(8), dp(8), dp(8), dp(8)), spacing=dp(4))

        self.header_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(48))
        self.header = Label(
            text="库存记录",
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            color=COLORS['text_primary'],
            font_size=dp(17),
            bold=True,
        )
        self.header.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            self.header.font_name = CHINESE_FONT
        self.header_box.add_widget(self.header)

        self.sub_header = Label(
            text="",
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
            color=COLORS['text_secondary'],
            font_size=dp(12),
        )
        self.sub_header.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            self.sub_header.font_name = CHINESE_FONT
        self.header_box.add_widget(self.sub_header)
        right_panel.add_widget(self.header_box)

        record_list_label = Label(
            text="库存记录列表",
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="middle",
            color=COLORS['text_secondary'],
            font_size=dp(13),
            bold=True,
        )
        record_list_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            record_list_label.font_name = CHINESE_FONT
        right_panel.add_widget(record_list_label)

        list_scroll = ScrollView(
            size_hint_y=1,
            do_scroll_x=False,
            bar_width=dp(3),
            bar_color=COLORS['primary'],
            bar_inactive_color=COLORS['divider'],
        )
        self.item_list_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            size_hint_x=1,
            spacing=dp(6),
            padding=(dp(2), dp(4), dp(2), dp(4)),
        )
        self.item_list_layout.bind(minimum_height=self.item_list_layout.setter("height"))
        list_scroll.add_widget(self.item_list_layout)
        right_panel.add_widget(list_scroll)

        root.add_widget(right_panel)

        self.add_widget(root)

    def _load_category_buttons(self):
        self._category_box.clear_widgets()
        self._category_buttons.clear()
        self._category_counts.clear()

        all_count = 0
        category_items = {}

        try:
            all_items = item_service.get_registered_items()
            for item in all_items:
                cat = item.get('category', '其他')
                if cat not in category_items:
                    category_items[cat] = []
                category_items[cat].append(item)
                all_count += 1

            self._category_counts = {cat: len(items) for cat, items in category_items.items()}
            self._category_counts[ALL_CATEGORY] = all_count

        except Exception as e:
            logger.error(f"加载分类统计失败: {e}")

        all_btn = CategoryChip(
            category_key=ALL_CATEGORY,
            category_name="全部",
            icon_name="format-list-bulleted",
            count=all_count,
        )
        all_btn.bind(on_release=lambda inst: self._on_category_selected(ALL_CATEGORY))
        self._category_box.add_widget(all_btn)
        self._category_buttons[ALL_CATEGORY] = all_btn

        for cat_key, cat_name in CATEGORY_MAP.items():
            count = self._category_counts.get(cat_key, 0)
            icon_name = CATEGORY_ICONS.get(cat_key, "folder")
            btn = CategoryChip(
                category_key=cat_key,
                category_name=cat_name,
                icon_name=icon_name,
                count=count,
            )
            btn.bind(on_release=lambda inst, key=cat_key: self._on_category_selected(key))
            self._category_box.add_widget(btn)
            self._category_buttons[cat_key] = btn

        self._on_category_selected(self.selected_filter_category)

    def _on_category_selected(self, category_key: str):
        self.selected_filter_category = category_key

        for key, btn in self._category_buttons.items():
            btn.set_selected(key == category_key)

        self._load_wiki_items()

    def _load_wiki_items(self):
        self._item_list_box.clear_widgets()
        self._item_cards.clear()

        filter_cat = self.selected_filter_category

        try:
            all_items = item_service.get_registered_items()

            if filter_cat != ALL_CATEGORY:
                items = [item for item in all_items if item.get('category') == filter_cat]
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
                    text="试试其他分类或添加新物品",
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
                text_color=COLORS['danger'],
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
                color=COLORS['danger'],
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
        self.selected_item_category = category
        self._update_item_card_styles()
        self._load_inventory(item_name)

    def _update_item_card_styles(self):
        for name, card in self._item_cards.items():
            card.set_selected(name == self.selected_item_name)

    def _prepare_item_data(self, item) -> dict:
        from datetime import date as _date

        expiry_date_str = "无"
        if item.expiry_date:
            if isinstance(item.expiry_date, _date):
                expiry_date_str = item.expiry_date.strftime("%Y-%m-%d")
            else:
                expiry_date_str = str(item.expiry_date)

        status = 'fresh'
        if hasattr(item, 'status'):
            status_value = item.status.value if hasattr(item.status, 'value') else str(item.status)
            if status_value == 'expiring':
                status = 'expiring'
            elif status_value == 'expired':
                status = 'expired'

        return {
            "id": item.id,
            "name": item.name,
            "expiry_date": expiry_date_str,
            "quantity": item.quantity,
            "status": status,
        }

    def _load_inventory(self, item_name: str):
        self.item_list_layout.clear_widgets()

        category_text = CATEGORY_MAP.get(self.selected_item_category, self.selected_item_category)
        self.header.text = item_name
        self.sub_header.text = f"分类: {category_text}  ·  点击查看详情"

        try:
            items = item_service.get_inventory_by_name(item_name)

            if not items:
                empty_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(100), spacing=dp(6))
                empty_icon = MDIcon(
                    icon="package-variant",
                    theme_text_color="Custom",
                    text_color=COLORS['text_hint'],
                    size_hint_y=None,
                    height=dp(36),
                    halign="center",
                    valign="middle",
                    font_size=dp(32),
                )
                empty_box.add_widget(empty_icon)

                empty = Label(
                    text=f"暂无{item_name}的库存记录",
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
                    text="点击右上角按钮添加库存",
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
                self.item_list_layout.add_widget(empty_box)
                return

            for item in items:
                data = self._prepare_item_data(item)
                card = InventoryRecordCard(data)
                card.bind(
                    on_release=lambda inst, item_id=item.id: self._on_item_click(item_id)
                )
                self.item_list_layout.add_widget(card)

        except Exception as e:
            logger.error(f"加载库存记录失败: {e}")
            error_box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(60))
            error_icon = MDIcon(
                icon="wifi-off",
                theme_text_color="Custom",
                text_color=COLORS['danger'],
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
                color=COLORS['danger'],
                font_size=dp(14),
            )
            error.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
            if CHINESE_FONT:
                error.font_name = CHINESE_FONT
            error_box.add_widget(error)
            self.item_list_layout.add_widget(error_box)

    def _on_item_click(self, item_id: str):
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            app.screen_manager.current = "item_detail"
            detail = app.screen_manager.get_screen("item_detail")
            if detail:
                detail.item_id = item_id
                detail._load_item(item_id)

    def on_enter(self):
        self._load_category_buttons()
        self._load_wiki_items()
        if self.selected_item_name:
            self._load_inventory(self.selected_item_name)
        try:
            import app.main as main_module
            font = getattr(main_module, "CHINESE_FONT_NAME", None)
        except Exception:
            font = None
        if font:
            apply_font_to_widget(self, font)

    def refresh_data(self):
        self._load_category_buttons()
        self._load_wiki_items()
        if self.selected_item_name:
            self._load_inventory(self.selected_item_name)
