from kivy.lang import Builder
from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.image import AsyncImage
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.properties import StringProperty, NumericProperty, ListProperty
from kivy.graphics import Color, RoundedRectangle, Line
from kivy.clock import Clock
from kivymd.app import MDApp

import logging
from app.services.wiki_service import wiki_service
from app.services.item_service import item_service
from app.ui.theme.design_tokens import COLOR_PALETTE, DESIGN_TOKENS
from app.utils.font_helper import CHINESE_FONT_NAME as CHINESE_FONT

logger = logging.getLogger(__name__)

COLORS = COLOR_PALETTE
FONTS = DESIGN_TOKENS


class InventoryListItem(BoxLayout):
    """库存列表项"""
    inventory_id = StringProperty("")
    item_name = StringProperty("")
    quantity = NumericProperty(0)
    unit = StringProperty("")
    production_date = StringProperty("")
    expiry_date = StringProperty("")
    location = StringProperty("")
    status = StringProperty("")
    
    def __init__(self, inventory_item, **kwargs):
        super().__init__(**kwargs)
        self.inventory_id = inventory_item.id
        self.item_name = inventory_item.name
        self.quantity = inventory_item.quantity
        self.unit = inventory_item.unit or ""
        self.production_date = inventory_item.purchase_date.strftime("%Y-%m-%d") if inventory_item.purchase_date else ""
        self.expiry_date = inventory_item.expiry_date.strftime("%Y-%m-%d") if inventory_item.expiry_date else ""
        self.location = ""
        self.status = inventory_item.status.value if inventory_item.status else ""
        
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(60)
        self.padding = (dp(12), dp(8))
        self.spacing = dp(12)
        
        self._build_ui()

    def _build_ui(self):
        with self.canvas.before:
            Color(*COLORS['surface'])
            self.bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
            Color(*COLORS['divider'])
            self.border_rect = Line(rounded_rectangle=(self.x, self.y, self.width, self.height, dp(8)), width=1)

        self.bind(pos=self._update_canvas, size=self._update_canvas)

        info_layout = BoxLayout(orientation="vertical", size_hint_x=1, spacing=dp(2))
        
        name_label = Label(
            text=f"{self.item_name} x{self.quantity}{self.unit}",
            font_size=dp(14),
            color=COLORS['text_primary'],
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(20),
            text_size=(None, dp(20)),
        )
        if CHINESE_FONT:
            name_label.font_name = CHINESE_FONT
        info_layout.add_widget(name_label)
        
        detail_text = ""
        if self.production_date:
            detail_text += f"生产: {self.production_date}"
        if self.expiry_date:
            if detail_text:
                detail_text += " | "
            detail_text += f"过期: {self.expiry_date}"
        if self.location:
            if detail_text:
                detail_text += " | "
            detail_text += f"位置: {self.location}"
        
        detail_label = Label(
            text=detail_text,
            font_size=dp(12),
            color=COLORS['text_secondary'],
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(18),
            text_size=(None, dp(18)),
        )
        if CHINESE_FONT:
            detail_label.font_name = CHINESE_FONT
        info_layout.add_widget(detail_label)
        
        self.add_widget(info_layout)

        arrow_label = Label(
            text="›",
            font_size=dp(24),
            color=COLORS['primary'],
            size_hint_x=None,
            width=dp(30),
        )
        self.add_widget(arrow_label)

    def _update_canvas(self, instance, value):
        self.bg_rect.pos = self.pos
        self.bg_rect.size = self.size
        self.border_rect.rounded_rectangle = (self.x, self.y, self.width, self.height, dp(8))

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            app = MDApp.get_running_app()
            if hasattr(app, "screen_manager"):
                app.screen_manager.current = "item_detail"
                detail = app.screen_manager.get_screen("item_detail")
                if detail:
                    detail.item_id = self.inventory_id
                    detail._load_item(self.inventory_id)
            return True
        return super().on_touch_down(touch)


class ItemWikiDetailScreen(Screen):
    """物品Wiki详情页"""
    item_name = StringProperty("")
    item_category = StringProperty("")
    item_description = StringProperty("")
    item_image = StringProperty("")
    item_unit = StringProperty("")
    total_quantity = NumericProperty(0)
    inventory_count = NumericProperty(0)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "item_wiki_detail"
        self._inventory_items = []
        self._build_ui()

    def _build_ui(self):
        main_layout = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(12))
        
        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=dp(3),
            bar_color=COLORS['primary'],
            bar_inactive_color=COLORS['divider'],
        )
        
        content_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(16))
        content_box.bind(minimum_height=content_box.setter("height"))
        
        self._image_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(200),
            size_hint_x=1,
        )
        with self._image_box.canvas.before:
            Color(*COLORS['surface'])
            RoundedRectangle(pos=self._image_box.pos, size=self._image_box.size, radius=[dp(12)])
        self._image_box.bind(pos=self._update_image_canvas, size=self._update_image_canvas)
        
        self._item_image = AsyncImage(
            source="",
            size_hint=(1, 1),
        )
        self._image_box.add_widget(self._item_image)
        content_box.add_widget(self._image_box)
        
        info_box = BoxLayout(orientation="vertical", size_hint_y=None, size_hint_x=1, padding=dp(16), spacing=dp(8))
        with info_box.canvas.before:
            Color(*COLORS['surface'])
            info_rect = RoundedRectangle(pos=info_box.pos, size=info_box.size, radius=[dp(12)])
        info_box.bind(pos=lambda i, v: setattr(info_rect, 'pos', v), size=lambda i, v: setattr(info_rect, 'size', v))
        
        header_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(28), spacing=dp(8))
        
        self._name_label = Label(
            text="",
            font_size=dp(20),
            color=COLORS['text_primary'],
            halign="left",
            valign="middle",
            size_hint_x=1,
            text_size=(None, dp(28)),
            bold=True,
        )
        if CHINESE_FONT:
            self._name_label.font_name = CHINESE_FONT
        header_box.add_widget(self._name_label)
        
        self._edit_button = Button(
            text="编辑",
            size_hint_x=None,
            width=dp(60),
            height=dp(28),
            font_size=dp(12),
            background_color=COLORS['primary'],
            color=(1, 1, 1, 1),
        )
        if CHINESE_FONT:
            self._edit_button.font_name = CHINESE_FONT
        self._edit_button.bind(on_release=self._on_edit)
        header_box.add_widget(self._edit_button)
        
        info_box.add_widget(header_box)
        
        self._category_label = Label(
            text="",
            font_size=dp(14),
            color=COLORS['text_secondary'],
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(20),
            text_size=(None, dp(20)),
        )
        if CHINESE_FONT:
            self._category_label.font_name = CHINESE_FONT
        info_box.add_widget(self._category_label)
        
        self._quantity_label = Label(
            text="",
            font_size=dp(16),
            color=COLORS['primary'],
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(24),
            text_size=(None, dp(24)),
        )
        if CHINESE_FONT:
            self._quantity_label.font_name = CHINESE_FONT
        info_box.add_widget(self._quantity_label)
        
        info_box.height = dp(28) + dp(20) + dp(24) + dp(8) * 2 + dp(16) * 2
        content_box.add_widget(info_box)
        
        self._description_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            size_hint_x=1,
            padding=dp(16),
        )
        with self._description_box.canvas.before:
            Color(*COLORS['surface'])
            desc_rect = RoundedRectangle(pos=self._description_box.pos, size=self._description_box.size, radius=[dp(12)])
        self._description_box.bind(pos=lambda i, v: setattr(desc_rect, 'pos', v), size=lambda i, v: setattr(desc_rect, 'size', v))
        
        desc_title = Label(
            text="物品描述",
            font_size=dp(16),
            color=COLORS['text_primary'],
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(24),
            text_size=(None, dp(24)),
            bold=True,
        )
        if CHINESE_FONT:
            desc_title.font_name = CHINESE_FONT
        self._description_box.add_widget(desc_title)
        
        self._description_label = Label(
            text="",
            font_size=dp(14),
            color=COLORS['text_secondary'],
            halign="left",
            valign="top",
            size_hint_y=None,
            text_size=(None, None),
        )
        if CHINESE_FONT:
            self._description_label.font_name = CHINESE_FONT
        self._description_box.add_widget(self._description_label)
        content_box.add_widget(self._description_box)
        
        inventory_title_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(32))
        inventory_title = Label(
            text="库存记录",
            font_size=dp(16),
            color=COLORS['text_primary'],
            halign="left",
            valign="middle",
            size_hint_x=1,
            text_size=(None, dp(32)),
            bold=True,
        )
        if CHINESE_FONT:
            inventory_title.font_name = CHINESE_FONT
        inventory_title_box.add_widget(inventory_title)
        
        self._inventory_count_label = Label(
            text="",
            font_size=dp(14),
            color=COLORS['text_secondary'],
            halign="right",
            valign="middle",
            size_hint_x=None,
            width=dp(100),
            text_size=(dp(100), dp(32)),
        )
        if CHINESE_FONT:
            self._inventory_count_label.font_name = CHINESE_FONT
        inventory_title_box.add_widget(self._inventory_count_label)
        content_box.add_widget(inventory_title_box)
        
        self._inventory_list_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            size_hint_x=1,
            spacing=dp(8),
        )
        content_box.add_widget(self._inventory_list_box)
        
        scroll.add_widget(content_box)
        main_layout.add_widget(scroll)
        
        back_button = Button(
            text="返回",
            size_hint_y=None,
            height=dp(48),
            font_size=dp(16),
            background_color=COLORS['surface'],
            color=COLORS['text_primary'],
        )
        if CHINESE_FONT:
            back_button.font_name = CHINESE_FONT
        back_button.bind(on_release=self._on_back)
        main_layout.add_widget(back_button)
        
        self.add_widget(main_layout)

    def _update_image_canvas(self, instance, value):
        for child in instance.canvas.before.children:
            if hasattr(child, 'pos'):
                child.pos = instance.pos
            if hasattr(child, 'size'):
                child.size = instance.size

    def load_wiki_item(self, item_name: str):
        """加载物品wiki信息"""
        try:
            wiki_item = wiki_service.get_wiki_by_name(item_name)

            if not wiki_item:
                logger.warning(f"物品wiki不存在: {item_name}，使用默认信息")
                self.item_name = item_name
                self.item_category = "其他"
                self.item_description = ""
                self.item_image = ""
                self.item_icon = ""  # 图标
                self.item_unit = "个"
            else:
                self.item_name = wiki_item['name']
                self.item_category = wiki_item['category_name'] or "其他"
                self.item_description = wiki_item['description'] or ""
                self.item_image = wiki_item.get('image_path') or ""
                self.item_icon = wiki_item.get('icon') or ""  # 获取自定义图标
                self.item_unit = wiki_item.get('default_unit') or "个"

            inventory_items = item_service.get_inventory_by_name(item_name)
            self._inventory_items = inventory_items
            self.total_quantity = sum(item.quantity for item in inventory_items)
            self.inventory_count = len(inventory_items)

            self._update_ui()

        except Exception as e:
            logger.error(f"加载物品wiki信息失败: {str(e)}")

    def _update_ui(self):
        self._name_label.text = self.item_name
        self._category_label.text = f"分类: {self.item_category}"
        self._quantity_label.text = f"当前库存: {self.total_quantity}{self.item_unit}"

        # 处理图片 - 如果有图片就显示，没有就清除
        if self.item_image:
            if not self.item_image.startswith(('http://', 'https://', '/')):
                import os
                self._item_image.source = os.path.abspath(self.item_image)
            else:
                self._item_image.source = self.item_image
        else:
            self._item_image.source = ""

        # 处理描述
        if self.item_description:
            self._description_label.text = self.item_description
            self._description_label.height = self._description_label.texture_size[1]
        else:
            self._description_label.text = "暂无描述"
            self._description_label.height = dp(20)

        self._description_box.height = dp(24) + dp(16) + self._description_label.height + dp(16)

        self._inventory_count_label.text = f"共{self.inventory_count}条"

        self._inventory_list_box.clear_widgets()
        self._inventory_list_box.height = dp(0)

        for inventory_item in self._inventory_items:
            list_item = InventoryListItem(inventory_item)
            self._inventory_list_box.add_widget(list_item)
            self._inventory_list_box.height += list_item.height + dp(8)

    def _on_back(self, instance):
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            app.screen_manager.current = "items"

    def _on_edit(self, instance):
        logger.info(f"编辑按钮点击: item_name={self.item_name}")
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            edit_screen = app.screen_manager.get_screen("item_wiki_edit")
            if edit_screen:
                edit_screen.load_wiki(self.item_name)
            app.screen_manager.current = "item_wiki_edit"

    def on_enter(self):
        pass

    def on_leave(self):
        pass
