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
from kivymd.app import MDApp
from kivymd.uix.list import MDList, MDListItem, MDListItemLeadingIcon

from app.services.item_service import item_service
from app.models.item import ItemCategory
from app.utils.logger import setup_logger
from app.utils.font_helper import apply_font_to_widget

logger = setup_logger(__name__)


try:
    import app.main as main_module

    CHINESE_FONT = getattr(main_module, "CHINESE_FONT_NAME", None)
except Exception:
    CHINESE_FONT = None


class SimpleItemListItem(MDListItem):
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

        # 左侧图标
        self._setup_icon()
        # 文本区域
        self._setup_text()

    def _setup_icon(self):
        icon_map = {
            ItemCategory.FOOD.value: "food",
            ItemCategory.DAILY_NECESSITIES.value: "home",
            ItemCategory.MEDICINE.value: "pill",
            ItemCategory.COSMETICS.value: "lipstick",
            ItemCategory.OTHERS.value: "package-variant",
        }
        icon_name = icon_map.get(self.category, "package-variant")
        self.add_widget(MDListItemLeadingIcon(icon=icon_name))

    def _setup_text(self):
        # 这里只展示一行：名称 x数量
        text = f"{self.item_name} x{self.quantity}"
        label = Label(
            text=text,
            halign="left",
            valign="middle",
            color=(0, 0, 0, 1),
        )
        label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            label.font_name = CHINESE_FONT
        self.add_widget(label)


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
                height=dp(40),
                background_normal="",
                background_color=(0.96, 0.96, 0.96, 1),
                color=(0.15, 0.15, 0.15, 1),
                on_release=lambda *_: self._on_category_selected(category),
            )
            if CHINESE_FONT:
                btn.font_name = CHINESE_FONT
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
        self.item_list_layout = MDList()
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
                btn.background_color = (0.25, 0.55, 0.9, 1)
                btn.color = (1, 1, 1, 1)
            else:
                btn.background_color = (0.96, 0.96, 0.96, 1)
                btn.color = (0.15, 0.15, 0.15, 1)

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
                    color=(0.6, 0.6, 0.6, 1),
                )
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
                color=(0.9, 0.3, 0.3, 1),
            )
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


