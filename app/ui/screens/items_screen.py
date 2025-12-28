# -*- coding: utf-8 -*-
"""
物品分页屏幕 - 左侧类别列表 + 右侧物品明细列表
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, ObjectProperty
from kivy.graphics import Color, Rectangle
from kivymd.app import MDApp
from kivymd.uix.list import MDList, MDListItem
from kivymd.uix.button import MDIconButton

from app.services.item_service import item_service
from app.models.item import ItemCategory
from app.utils.logger import setup_logger
from app.utils.font_helper import apply_font_to_widget

logger = setup_logger(__name__)


try:
    from app.main import CHINESE_FONT_NAME
    CHINESE_FONT = CHINESE_FONT_NAME
except Exception:
    CHINESE_FONT = None


class SimpleItemListItem(BoxLayout):
    """物品列表项（精简版，用于右侧列表）"""

    item_id = StringProperty()
    item_name = StringProperty()
    category = StringProperty()
    expiry_date = StringProperty()
    days_until_expiry = NumericProperty(0)
    quantity = NumericProperty(1)

    def __init__(self, item_data, **kwargs):
        super().__init__(**kwargs)
        self.item_id = item_data.get("id", "")
        self.item_name = item_data.get("name", "未命名")
        self.category = item_data.get("category", ItemCategory.OTHERS.value)
        self.expiry_date = item_data.get("expiry_date", "无")
        self.days_until_expiry = item_data.get("days_until_expiry", 0)
        self.quantity = item_data.get("quantity", 1)

        # 设置基本布局属性
        self.padding = (0, 0, 0, 0)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.size_hint_x = 1  # 确保占据完整宽度
        self.height = dp(80)
        
        # 直接添加图标到左侧 (固定宽度)
        icon = self._setup_icon()
        icon.size_hint_x = None
        icon.width = dp(48)
        self.add_widget(icon)
        
        # 添加文本内容到中间（占据剩余空间）
        text_box = self._setup_text()
        text_box.size_hint_x = 1  # 占据剩余空间
        text_box.size_hint_y = None
        text_box.height = dp(80)
        self.add_widget(text_box)
        
        # 添加复选框到右侧 (固定宽度)
        checkbox = self._setup_checkbox()
        checkbox.size_hint_x = None
        checkbox.width = dp(48)
        self.add_widget(checkbox)
        
        self._setup_background()
        
        # 添加点击事件支持 - 使用Kivy标准事件名，不需要手动绑定

    def _setup_icon(self):
        from kivymd.uix.label import MDIcon
        icon_map = {
            ItemCategory.FOOD.value: "food-apple",  # 使用KivyMD支持的食物图标
            ItemCategory.DAILY_NECESSITIES.value: "home",
            ItemCategory.MEDICINE.value: "medical-bag",  # 使用KivyMD支持的药品图标
            ItemCategory.COSMETICS.value: "face-woman",  # 使用KivyMD支持的化妆品图标
            ItemCategory.OTHERS.value: "package-variant",
        }
        icon_name = icon_map.get(self.category, "package-variant")
        icon = MDIcon(
            icon=icon_name,
            theme_text_color="Custom",
            text_color=(0.4, 0.4, 0.4, 1),
            size_hint_x=None,
            width=dp(48),
            size_hint_y=None,
            height=dp(80),
            halign="center",
            valign="middle",
            font_size=dp(28),  # 设置合适的图标大小
        )
        # KivyMD会自动处理图标字体，不需要手动设置font_name为Roboto
        return icon

    def _setup_text(self):
        text_box = BoxLayout(
            orientation="vertical",
            padding=(dp(8), dp(6)),
            spacing=dp(2),
            size_hint_y=None,
            size_hint_x=1,
        )
        text_box.bind(minimum_height=lambda inst, val: setattr(inst, "height", val))
        
        def _make_label(text, height, color, font_size=dp(14), bold=False):
            lbl = Label(
                text=text,
                size_hint_y=None,
                height=height,
                halign="left",
                valign="middle",
                color=color,
                font_size=font_size,
                bold=bold,
            )
            lbl.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
            if CHINESE_FONT:
                lbl.font_name = CHINESE_FONT
            return lbl
        
        headline_text = f"{self.item_name} x{self.quantity}"
        text_box.add_widget(_make_label(headline_text, dp(24), (0.15, 0.15, 0.15, 1), dp(16), True))

        category_map = {
            ItemCategory.FOOD.value: "食品",
            ItemCategory.DAILY_NECESSITIES.value: "日用品",
            ItemCategory.MEDICINE.value: "药品",
            ItemCategory.COSMETICS.value: "化妆品",
            ItemCategory.OTHERS.value: "其他",
        }
        category_text = category_map.get(self.category, "其他")

        if self.expiry_date == "无":
            status_text = "无过期日期"
            status_color = (0.5, 0.5, 0.5, 1)
        else:
            status_text = "正常"
            status_color = (0.3, 0.7, 0.3, 1)
            if self.days_until_expiry < 0:
                status_text = "已过期"
                status_color = (0.85, 0.25, 0.25, 1)
            elif self.days_until_expiry <= 3:
                status_text = "即将过期"
                status_color = (0.9, 0.6, 0.2, 1)

        supporting_text = f"{category_text}  |  {status_text}"
        text_box.add_widget(_make_label(supporting_text, dp(20), status_color, dp(13)))

        if self.expiry_date == "无":
            tertiary_text = "无过期日期"
            tertiary_color = (0.55, 0.55, 0.55, 1)
        else:
            days_text = f"剩余{self.days_until_expiry}天"
            if self.days_until_expiry < 0:
                days_text = f"过期{-self.days_until_expiry}天"
            elif self.days_until_expiry == 0:
                days_text = "今天过期"
            tertiary_text = f"{self.expiry_date}  |  {days_text}"
            if self.days_until_expiry < 0:
                tertiary_color = (0.8, 0.2, 0.2, 1)
            elif self.days_until_expiry <= 3:
                tertiary_color = (0.85, 0.55, 0.2, 1)
            else:
                tertiary_color = (0.45, 0.45, 0.45, 1)
        text_box.add_widget(_make_label(tertiary_text, dp(20), tertiary_color, dp(12)))

        return text_box

    def _setup_checkbox(self):
        from kivy.uix.checkbox import CheckBox
        checkbox = CheckBox(
            size_hint_x=None,
            width=dp(48),
        )
        return checkbox

    def _setup_background(self):
        if self.expiry_date == "无":
            self._set_background_color(1, 1, 1)
        elif self.days_until_expiry < 0:
            self._set_background_color(1, 0.9, 0.9)
        elif self.days_until_expiry <= 3:
            self._set_background_color(1, 1, 0.9)
        else:
            self._set_background_color(1, 1, 1)

    def _set_background_color(self, r, g, b):
        with self.canvas.before:
            Color(r, g, b, 1)
            Rectangle(pos=self.pos, size=self.size)
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.expiry_date == "无":
                Color(1, 1, 1, 1)
            elif self.days_until_expiry < 0:
                Color(1, 0.9, 0.9, 1)
            elif self.days_until_expiry <= 3:
                Color(1, 1, 0.9, 1)
            else:
                Color(1, 1, 1, 1)
            Rectangle(pos=self.pos, size=self.size)
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            # 触发点击事件
            self.dispatch('on_release')
        return super().on_touch_down(touch) if hasattr(super(), 'on_touch_down') else False
    
    def on_release(self, *args):
        # 默认实现，会被外部绑定覆盖
        pass


class ItemsScreen(Screen):
    """物品分页屏幕"""

    selected_category = ObjectProperty(allownone=True)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "items"
        self._category_buttons = {}
        self._build_ui()
        self._load_items()

    def _build_ui(self):
        root = BoxLayout(orientation="horizontal")

        # 左侧类别栏
        left = BoxLayout(
            orientation="vertical",
            size_hint_x=0.28,
            padding=(dp(4), dp(8)),
            spacing=dp(4),
        )

        # 标题
        title = Label(
            text="类别",
            size_hint_y=None,
            height=dp(28),
            color=(0.3, 0.3, 0.3, 1),
        )
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        left.add_widget(title)

        # 类别按钮区域（滚动）
        cat_scroll = ScrollView(size_hint=(1, 1))
        cat_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(4),
        )
        cat_box.bind(minimum_height=cat_box.setter("height"))

        def add_cat_btn(text, category):
            btn = Button(
                text=text,
                size_hint_y=None,
                height=dp(44),
                size_hint_x=1,
                width=dp(100),
                background_normal="",
                background_color=(0.96, 0.96, 0.96, 1),
                color=(0.3, 0.3, 0.3, 1),
                halign="center",
                font_size=dp(15),
                on_release=lambda *_: self._on_category_selected(category),
            )
            btn.text_size = btn.size
            btn.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1])))

            def on_press(instance):
                instance.background_color = (0.2, 0.6, 0.9, 1)
                instance.color = (1, 1, 1, 1)

            def on_release(instance):
                if self.selected_category == category:
                    instance.background_color = (0.25, 0.55, 0.9, 1)
                    instance.color = (1, 1, 1, 1)
                else:
                    instance.background_color = (0.96, 0.96, 0.96, 1)
                    instance.color = (0.3, 0.3, 0.3, 1)

            btn.bind(on_press=on_press)
            btn.bind(on_release=on_release)
            cat_box.add_widget(btn)
            self._category_buttons[category] = btn

        # “全部” 用 None 表示
        add_cat_btn("全部", None)
        add_cat_btn("食品", ItemCategory.FOOD)
        add_cat_btn("日用品", ItemCategory.DAILY_NECESSITIES)
        add_cat_btn("药品", ItemCategory.MEDICINE)
        add_cat_btn("化妆品", ItemCategory.COSMETICS)
        add_cat_btn("其他", ItemCategory.OTHERS)

        cat_scroll.add_widget(cat_box)
        left.add_widget(cat_scroll)

        # 右侧列表区域
        right = BoxLayout(orientation="vertical")

        header = Label(
            text="物品明细",
            size_hint_y=None,
            height=dp(32),
            color=(0.2, 0.4, 0.6, 1),
        )
        if CHINESE_FONT:
            header.font_name = CHINESE_FONT
        right.add_widget(header)

        list_scroll = ScrollView()
        self.item_list_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(2),
        )
        self.item_list_layout.bind(minimum_height=self.item_list_layout.setter("height"))
        list_scroll.add_widget(self.item_list_layout)
        right.add_widget(list_scroll)

        root.add_widget(left)
        root.add_widget(right)

        self.add_widget(root)

    def _on_category_selected(self, category: ItemCategory | None):
        """点击左侧类别按钮"""
        self.selected_category = category
        self._update_category_button_styles()
        self._load_items(category)

    def _update_category_button_styles(self):
        """高亮当前选中类别"""
        for cat, btn in self._category_buttons.items():
            if cat == self.selected_category:
                btn.background_color = (0.2, 0.6, 0.9, 1)
                btn.color = (1, 1, 1, 1)
            else:
                btn.background_color = (0.96, 0.96, 0.96, 1)
                btn.color = (0.3, 0.3, 0.3, 1)

    def _prepare_item_data(self, item) -> dict:
        from datetime import date as _date

        expiry_date_str = "无"
        if item.expiry_date:
            if isinstance(item.expiry_date, _date):
                expiry_date_str = item.expiry_date.strftime("%Y-%m-%d")
            else:
                expiry_date_str = str(item.expiry_date)

        return {
            "id": item.id,
            "name": item.name,
            "category": item.category.value,
            "expiry_date": expiry_date_str,
            "days_until_expiry": item.days_until_expiry or 0,
            "quantity": item.quantity,
        }

    def _load_items(self, category: ItemCategory | None = None):
        """根据当前类别加载物品"""
        try:
            self.item_list_layout.clear_widgets()
            items = item_service.get_items(category=category)

            if not items:
                empty = Label(
                    text="该类别下暂无物品",
                    size_hint_y=None,
                    height=dp(60),
                    halign="left",
                    valign="middle",
                    color=(0.6, 0.6, 0.6, 1),
                )
                empty.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1])))
                if CHINESE_FONT:
                    empty.font_name = CHINESE_FONT
                self.item_list_layout.add_widget(empty)
                return

            for item in items:
                data = self._prepare_item_data(item)
                row = SimpleItemListItem(data)
                row.bind(
                    on_release=lambda inst, item_id=item.id: self._on_item_click(item_id)
                )
                self.item_list_layout.add_widget(row)

        except Exception as e:
            logger.error(f"加载物品列表失败: {e}")
            error = Label(
                text="加载失败，请重试",
                size_hint_y=None,
                height=dp(60),
                halign="left",
                valign="middle",
                color=(0.9, 0.3, 0.3, 1),
            )
            error.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1])))
            if CHINESE_FONT:
                error.font_name = CHINESE_FONT
            self.item_list_layout.add_widget(error)

    def _on_item_click(self, item_id: str):
        """点击右侧物品，跳转到详情"""
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            app.screen_manager.current = "item_detail"
            detail = app.screen_manager.get_screen("item_detail")
            if detail:
                detail.item_id = item_id
                detail._load_item(item_id)

    def on_enter(self):
        """进入屏幕时刷新数据并应用字体"""
        self._load_items(self.selected_category)
        try:
            import app.main as main_module

            font = getattr(main_module, "CHINESE_FONT_NAME", None)
        except Exception:
            font = None
        if font:
            apply_font_to_widget(self, font)


