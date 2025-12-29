# -*- coding: utf-8 -*-
"""
物品详情屏幕 - 显示物品详细信息和管理功能
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.modalview import ModalView
from kivy.metrics import dp
from kivy.properties import (
    StringProperty, NumericProperty, ObjectProperty, ListProperty
)
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.button import (
    MDButton, MDIconButton, MDButtonText
)
from kivymd.uix.dialog import MDDialog
from kivymd.uix.list import (
    MDList, MDListItem,
    MDListItemLeadingIcon,
    MDListItemHeadlineText
)
from datetime import date, datetime
import os

from app.services.item_service import item_service
from app.services.wiki_service import wiki_service
from app.models.item import ItemStatus
from app.utils.logger import setup_logger
from app.utils.font_helper import apply_font_to_widget, CHINESE_FONT_NAME as CHINESE_FONT

logger = setup_logger(__name__)


class ItemDetailScreen(Screen):
    """物品详情屏幕"""

    # 属性绑定
    item_id = StringProperty("")
    item_name = StringProperty("")
    item_category = StringProperty("")
    item_description = StringProperty("")
    item_quantity = NumericProperty(1)
    item_unit = StringProperty("")
    purchase_date = StringProperty("")
    expiry_date = StringProperty("")
    days_until_expiry = NumericProperty(0)
    reminder_date = StringProperty("")
    status = StringProperty("")
    predicted_expiry_date = StringProperty("")
    prediction_confidence = NumericProperty(0.0)
    source_info = StringProperty("")

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'item_detail'
        self.current_item = None
        self._build_ui()

        # 绑定属性变化
        self.bind(
            item_id=self._on_item_id_changed,
            item_name=self._on_item_data_changed
        )

    def _build_ui(self):
        """构建UI界面"""
        # 主布局 - 设置白色背景
        main_layout = BoxLayout(orientation='vertical')
        from kivy.graphics import Color, Rectangle
        with main_layout.canvas.before:
            Color(1, 1, 1, 1)  # 白色背景
            self.bg_rect = Rectangle(pos=main_layout.pos, size=main_layout.size)
        
        def update_bg_rect(instance, value):
            self.bg_rect.pos = instance.pos
            self.bg_rect.size = instance.size
        
        main_layout.bind(pos=update_bg_rect, size=update_bg_rect)

        # 头部栏
        header = self._create_header()
        main_layout.add_widget(header)

        # 内容区域（可滚动）
        content = self._create_content()
        main_layout.add_widget(content)

        # 底部操作栏
        action_bar = self._create_action_bar()
        main_layout.add_widget(action_bar)

        self.add_widget(main_layout)

    def _create_header(self) -> BoxLayout:
        """创建头部栏"""
        header = BoxLayout(size_hint_y=None, height=dp(56))

        # 返回按钮（显式设置图标颜色，避免与背景融在一起）
        back_btn = MDIconButton(
            icon="arrow-left",
            on_release=self._on_back_click,
        )
        try:
            # KivyMD 2.0 使用 icon_color，自定义为深色
            back_btn.icon_color = (0.2, 0.2, 0.2, 1)
        except Exception:
            pass
        header.add_widget(back_btn)

        # 标题
        self.title_label = Label(
            text="物品详情",
            size_hint_x=0.7,
            font_size=dp(20),
            bold=True
        )
        if CHINESE_FONT:
            self.title_label.font_name = CHINESE_FONT
        header.add_widget(self.title_label)

        # 编辑按钮
        edit_btn = MDIconButton(
            icon="pencil",
            on_release=self._on_edit_click,
            font_name="Roboto",
        )
        header.add_widget(edit_btn)

        return header

    def _create_content(self) -> ScrollView:
        """创建内容区域"""
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

        content_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            padding=dp(16),
            spacing=dp(16)
        )
        content_layout.bind(minimum_height=content_layout.setter('height'))

        # 基本信息卡片
        basic_info_card = self._create_basic_info_card()
        content_layout.add_widget(basic_info_card)

        # 数量信息卡片
        quantity_card = self._create_quantity_card()
        content_layout.add_widget(quantity_card)

        # 日期信息卡片
        date_card = self._create_date_card()
        content_layout.add_widget(date_card)

        # AI预测卡片（如果有数据）
        self.ai_card = self._create_ai_card()
        content_layout.add_widget(self.ai_card)

        # 来源信息卡片（如果有数据）
        self.source_card = self._create_source_card()
        content_layout.add_widget(self.source_card)

        # 标签卡片
        self.tag_card = self._create_tag_card()
        content_layout.add_widget(self.tag_card)

        scroll_view.add_widget(content_layout)
        return scroll_view

    def _create_basic_info_card(self) -> MDCard:
        """创建基本信息卡片"""
        card = MDCard(
            size_hint_y=None,
            height=dp(120),
            padding=dp(16),
            radius=[dp(8), dp(8), dp(8), dp(8)]
        )

        layout = GridLayout(cols=2, rows=3, spacing=dp(8))

        # 物品名称
        name_static_label = Label(
            text="名称:",
            size_hint_x=None,
            width=dp(60),
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            name_static_label.font_name = CHINESE_FONT
        layout.add_widget(name_static_label)
        self.name_label = Label(
            text=self.item_name,
            bold=True,
            color=(0, 0, 0, 1)
        )
        if CHINESE_FONT:
            self.name_label.font_name = CHINESE_FONT
        layout.add_widget(self.name_label)

        # 类别
        category_static_label = Label(
            text="类别:",
            size_hint_x=None,
            width=dp(60),
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            category_static_label.font_name = CHINESE_FONT
        layout.add_widget(category_static_label)
        self.category_label = Label(
            text=self.item_category,
            color=(0.2, 0.4, 0.6, 1)
        )
        if CHINESE_FONT:
            self.category_label.font_name = CHINESE_FONT
        layout.add_widget(self.category_label)

        # 描述
        desc_static_label = Label(
            text="描述:",
            size_hint_x=None,
            width=dp(60),
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            desc_static_label.font_name = CHINESE_FONT
        layout.add_widget(desc_static_label)
        self.description_label = Label(
            text=self.item_description or "无描述",
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            self.description_label.font_name = CHINESE_FONT
        layout.add_widget(self.description_label)

        card.add_widget(layout)
        return card

    def _create_quantity_card(self) -> MDCard:
        """创建数量信息卡片"""
        card = MDCard(
            size_hint_y=None,
            height=dp(80),
            padding=dp(16),
            radius=[dp(8), dp(8), dp(8), dp(8)]
        )

        layout = GridLayout(cols=4, rows=1, spacing=dp(8))

        # 数量标签
        quantity_static_label = Label(
            text="数量:",
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            quantity_static_label.font_name = CHINESE_FONT
        layout.add_widget(quantity_static_label)

        # 数量显示
        self.quantity_label = Label(
            text=str(self.item_quantity),
            bold=True,
            font_size=dp(20),
            color=(0.2, 0.6, 0.2, 1)
        )
        if CHINESE_FONT:
            self.quantity_label.font_name = CHINESE_FONT
        layout.add_widget(self.quantity_label)

        # 单位
        unit_static_label = Label(
            text="单位:",
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            unit_static_label.font_name = CHINESE_FONT
        layout.add_widget(unit_static_label)
        self.unit_label = Label(
            text=self.item_unit or "个",
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            self.unit_label.font_name = CHINESE_FONT
        layout.add_widget(self.unit_label)

        card.add_widget(layout)
        return card

    def _create_date_card(self) -> MDCard:
        """创建日期信息卡片"""
        card = MDCard(
            size_hint_y=None,
            height=dp(160),
            padding=dp(16),
            radius=[dp(8), dp(8), dp(8), dp(8)]
        )

        layout = GridLayout(cols=2, rows=4, spacing=dp(8))

        # 购买日期
        purchase_static_label = Label(
            text="购买日期:",
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            purchase_static_label.font_name = CHINESE_FONT
        layout.add_widget(purchase_static_label)
        self.purchase_date_label = Label(
            text=self.purchase_date or "未设置",
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            self.purchase_date_label.font_name = CHINESE_FONT
        layout.add_widget(self.purchase_date_label)

        # 过期日期
        expiry_static_label = Label(
            text="过期日期:",
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            expiry_static_label.font_name = CHINESE_FONT
        layout.add_widget(expiry_static_label)
        self.expiry_date_label = Label(
            text=self.expiry_date or "未设置",
            color=self._get_expiry_date_color(),
            bold=self.days_until_expiry <= 3
        )
        if CHINESE_FONT:
            self.expiry_date_label.font_name = CHINESE_FONT
        layout.add_widget(self.expiry_date_label)

        # 过期天数
        status_static_label = Label(
            text="过期状态:",
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            status_static_label.font_name = CHINESE_FONT
        layout.add_widget(status_static_label)
        self.expiry_status_label = Label(
            text=self._get_expiry_status_text(),
            color=self._get_expiry_status_color(),
            bold=True
        )
        if CHINESE_FONT:
            self.expiry_status_label.font_name = CHINESE_FONT
        layout.add_widget(self.expiry_status_label)

        # 提醒日期
        reminder_static_label = Label(
            text="提醒日期:",
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            reminder_static_label.font_name = CHINESE_FONT
        layout.add_widget(reminder_static_label)
        self.reminder_date_label = Label(
            text=self.reminder_date or "未设置",
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            self.reminder_date_label.font_name = CHINESE_FONT
        layout.add_widget(self.reminder_date_label)

        card.add_widget(layout)
        return card

    def _create_ai_card(self) -> MDCard:
        """创建AI预测卡片"""
        card = MDCard(
            size_hint_y=None,
            height=dp(0),
            padding=dp(16),
            radius=[dp(8), dp(8), dp(8), dp(8)]
        )

        self.ai_layout = BoxLayout(orientation='vertical')
        ai_title_label = Label(
            text="AI预测信息",
            bold=True,
            size_hint_y=None,
            height=dp(24),
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            ai_title_label.font_name = CHINESE_FONT
        self.ai_layout.add_widget(ai_title_label)

        self.ai_content_label = Label(
            text="",
            color=(0.4, 0.4, 0.4, 1),
            halign="left",
            valign="top"
        )
        self.ai_content_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1])))
        if CHINESE_FONT:
            self.ai_content_label.font_name = CHINESE_FONT
        self.ai_layout.add_widget(self.ai_content_label)

        card.add_widget(self.ai_layout)
        return card

    def _create_source_card(self) -> MDCard:
        """创建来源信息卡片"""
        card = MDCard(
            size_hint_y=None,
            height=dp(0),
            padding=dp(16),
            radius=[dp(8), dp(8), dp(8), dp(8)]
        )

        self.source_layout = BoxLayout(orientation='vertical')
        source_title_label = Label(
            text="来源信息",
            bold=True,
            size_hint_y=None,
            height=dp(24),
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            source_title_label.font_name = CHINESE_FONT
        self.source_layout.add_widget(source_title_label)

        self.source_content_label = Label(
            text="",
            color=(0.4, 0.4, 0.4, 1),
            halign="left",
            valign="top"
        )
        self.source_content_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1])))
        if CHINESE_FONT:
            self.source_content_label.font_name = CHINESE_FONT
        self.source_layout.add_widget(self.source_content_label)

        card.add_widget(self.source_layout)
        return card

    def _create_tag_card(self) -> MDCard:
        """创建标签卡片"""
        card = MDCard(
            size_hint_y=None,
            height=dp(80),
            padding=dp(16),
            radius=[dp(8), dp(8), dp(8), dp(8)]
        )

        self.tag_layout = GridLayout(cols=3, rows=1, spacing=dp(8))
        tag_static_label = Label(
            text="标签:",
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            tag_static_label.font_name = CHINESE_FONT
        self.tag_layout.add_widget(tag_static_label)

        self.tag_content_label = Label(
            text="无标签",
            color=(0.4, 0.4, 0.4, 1)
        )
        if CHINESE_FONT:
            self.tag_content_label.font_name = CHINESE_FONT
        self.tag_layout.add_widget(self.tag_content_label)

        card.add_widget(self.tag_layout)
        return card

    def _create_action_bar(self) -> BoxLayout:
        """创建底部操作栏"""
        action_bar = BoxLayout(
            size_hint_y=None,
            height=dp(56),
            padding=dp(8),
            spacing=dp(8)
        )

        # 删除按钮
        delete_btn = MDButton(
            style="outlined",
            on_release=self._on_delete_click
        )
        # 创建按钮文本部件（新的KivyMD API需要这样）
        delete_text = MDButtonText(
            text="删除",
            theme_text_color="Custom",
            text_color=(0.9, 0.3, 0.3, 1)
        )
        try:
            import app.main as main_module
            chinese_font = getattr(main_module, 'CHINESE_FONT_NAME', None)
            if chinese_font:
                delete_text.font_name = chinese_font
        except:
            pass
        delete_btn.add_widget(delete_text)
        action_bar.add_widget(delete_btn)

        # 增加数量按钮
        increase_btn = MDButton(
            style="filled",
            on_release=lambda x: self._change_quantity(1)
        )
        increase_text = MDButtonText(text="+1")
        try:
            import app.main as main_module
            chinese_font = getattr(main_module, 'CHINESE_FONT_NAME', None)
            if chinese_font:
                increase_text.font_name = chinese_font
        except:
            pass
        increase_btn.add_widget(increase_text)
        action_bar.add_widget(increase_btn)

        # 减少数量按钮
        decrease_btn = MDButton(
            style="filled",
            on_release=lambda x: self._change_quantity(-1)
        )
        decrease_text = MDButtonText(text="-1")
        try:
            import app.main as main_module
            chinese_font = getattr(main_module, 'CHINESE_FONT_NAME', None)
            if chinese_font:
                decrease_text.font_name = chinese_font
        except:
            pass
        decrease_btn.add_widget(decrease_text)
        action_bar.add_widget(decrease_btn)

        # 返回主界面按钮（符合安卓底部操作习惯）
        back_btn = MDButton(
            style="filled",
            on_release=self._on_back_click,
        )
        back_text = MDButtonText(text="返回")
        try:
            import app.main as main_module
            chinese_font = getattr(main_module, "CHINESE_FONT_NAME", None)
            if chinese_font:
                back_text.font_name = chinese_font
        except Exception:
            pass
        back_btn.add_widget(back_text)
        action_bar.add_widget(back_btn)

        return action_bar

    def _get_expiry_date_color(self):
        """获取过期日期颜色"""
        if not self.expiry_date:
            return (0.4, 0.4, 0.4, 1)
        elif self.days_until_expiry < 0:
            return (0.9, 0.3, 0.3, 1)  # 红色
        elif self.days_until_expiry <= 3:
            return (0.9, 0.6, 0.2, 1)  # 橙色
        else:
            return (0.2, 0.6, 0.2, 1)  # 绿色

    def _get_expiry_status_text(self):
        """获取过期状态文本"""
        if not self.expiry_date:
            return "无过期日期"
        elif self.days_until_expiry < 0:
            return f"已过期 {-self.days_until_expiry} 天"
        elif self.days_until_expiry == 0:
            return "今天过期"
        elif self.days_until_expiry <= 3:
            return f"即将过期 ({self.days_until_expiry}天)"
        else:
            return f"正常 ({self.days_until_expiry}天后)"

    def _get_expiry_status_color(self):
        """获取过期状态颜色"""
        if not self.expiry_date:
            return (0.4, 0.4, 0.4, 1)
        elif self.days_until_expiry < 0:
            return (0.9, 0.3, 0.3, 1)  # 红色
        elif self.days_until_expiry <= 3:
            return (0.9, 0.6, 0.2, 1)  # 橙色
        else:
            return (0.2, 0.6, 0.2, 1)  # 绿色

    def _on_item_id_changed(self, instance, value):
        """物品ID变化时调用"""
        if value:
            self._load_item(value)

    def _load_wiki_item(self, item_name: str):
        """加载物品wiki信息"""
        try:
            wiki_item = wiki_service.get_wiki_by_name(item_name)
            if not wiki_item:
                logger.error(f"物品wiki不存在: {item_name}")
                return

            self.item_name = wiki_item['name']
            self.item_category = wiki_item['category_name'] or "其他"
            self.item_description = wiki_item['description'] or ""
            inventory_items = item_service.get_inventory_by_name(item_name)
            total_quantity = sum(item.quantity for item in inventory_items)
            self.item_quantity = total_quantity
            self.item_unit = wiki_item['default_unit'] or "个"
            
            self.source_info = f"共{len(inventory_items)}条库存记录"

            self._update_wiki_ui()

        except Exception as e:
            logger.error(f"加载物品wiki信息失败: {str(e)}")

    def _update_wiki_ui(self):
        """更新wiki信息UI显示"""
        # 更新标题
        self.title_label.text = self.item_name
        if CHINESE_FONT:
            self.title_label.font_name = CHINESE_FONT

        # 更新基本信息
        self.name_label.text = self.item_name
        if CHINESE_FONT:
            self.name_label.font_name = CHINESE_FONT
        self.category_label.text = self.item_category
        if CHINESE_FONT:
            self.category_label.font_name = CHINESE_FONT
        self.description_label.text = self.item_description or "无描述"
        if CHINESE_FONT:
            self.description_label.font_name = CHINESE_FONT

        # 更新数量信息
        self.quantity_label.text = str(self.item_quantity)
        if CHINESE_FONT:
            self.quantity_label.font_name = CHINESE_FONT
        self.unit_label.text = self.item_unit or "个"
        if CHINESE_FONT:
            self.unit_label.font_name = CHINESE_FONT

        # 更新来源信息
        self._update_source_card()

    def _on_item_data_changed(self, instance, value):
        """物品数据变化时调用"""
        if self.current_item:
            self._update_ui()

    def _load_item(self, item_id: str):
        """加载物品数据"""
        try:
            self.current_item = item_service.get_item(item_id)
            if not self.current_item:
                logger.error(f"物品不存在: {item_id}")
                return

            # 更新属性
            self.item_name = self.current_item.name
            self.item_category = self._get_category_text(self.current_item)
            self.item_description = self.current_item.description or ""
            self.item_quantity = self.current_item.quantity
            self.item_unit = self.current_item.unit or ""
            self.purchase_date = self._format_date(self.current_item.purchase_date)
            self.expiry_date = self._format_date(self.current_item.expiry_date)
            self.days_until_expiry = self.current_item.days_until_expiry or 0
            self.reminder_date = self._format_date(self.current_item.reminder_date)
            self.status = self.current_item.status.value
            self.predicted_expiry_date = self._format_date(self.current_item.predicted_expiry_date)
            self.prediction_confidence = self.current_item.prediction_confidence or 0.0

            # 更新来源信息
            if self.current_item.source_app:
                self.source_info = f"{self.current_item.source_app} - {self.current_item.source_order_id or '无订单号'}"
            else:
                self.source_info = "手动添加"

            # 更新UI
            self._update_ui()

        except Exception as e:
            logger.error(f"加载物品详情失败: {str(e)}")

    def _update_ui(self):
        """更新UI显示"""
        # 更新标题
        self.title_label.text = self.item_name
        if CHINESE_FONT:
            self.title_label.font_name = CHINESE_FONT

        # 更新基本信息
        self.name_label.text = self.item_name
        if CHINESE_FONT:
            self.name_label.font_name = CHINESE_FONT
        self.category_label.text = self.item_category
        if CHINESE_FONT:
            self.category_label.font_name = CHINESE_FONT
        self.description_label.text = self.item_description or "无描述"
        if CHINESE_FONT:
            self.description_label.font_name = CHINESE_FONT

        # 更新数量信息
        self.quantity_label.text = str(self.item_quantity)
        if CHINESE_FONT:
            self.quantity_label.font_name = CHINESE_FONT
        self.unit_label.text = self.item_unit or "个"
        if CHINESE_FONT:
            self.unit_label.font_name = CHINESE_FONT

        # 更新日期信息
        self.purchase_date_label.text = self.purchase_date or "未设置"
        if CHINESE_FONT:
            self.purchase_date_label.font_name = CHINESE_FONT
        self.expiry_date_label.text = self.expiry_date or "未设置"
        if CHINESE_FONT:
            self.expiry_date_label.font_name = CHINESE_FONT
        self.expiry_date_label.color = self._get_expiry_date_color()
        self.expiry_date_label.bold = self.days_until_expiry <= 3

        self.expiry_status_label.text = self._get_expiry_status_text()
        if CHINESE_FONT:
            self.expiry_status_label.font_name = CHINESE_FONT
        self.expiry_status_label.color = self._get_expiry_status_color()

        self.reminder_date_label.text = self.reminder_date or "未设置"
        if CHINESE_FONT:
            self.reminder_date_label.font_name = CHINESE_FONT

        # 更新AI卡片
        self._update_ai_card()

        # 更新来源卡片
        self._update_source_card()

        # 更新标签卡片
        self._update_tag_card()

        # 底部返回按钮无需动态更新

    def _format_date(self, date_obj):
        """格式化日期"""
        if not date_obj:
            return ""
        if isinstance(date_obj, date):
            return date_obj.strftime('%Y-%m-%d')
        return str(date_obj)

    def _get_category_text(self, item):
        """获取类别文本"""
        try:
            if item.wiki and item.wiki.category:
                return item.wiki.category.name
        except Exception:
            pass
        return "其他"

    def _update_ai_card(self):
        """更新AI卡片"""
        if self.predicted_expiry_date:
            confidence_text = f"{self.prediction_confidence*100:.1f}%" if self.prediction_confidence else "未知"
            ai_text = f"预测过期日期: {self.predicted_expiry_date}\n置信度: {confidence_text}"
            self.ai_content_label.text = ai_text
            if CHINESE_FONT:
                self.ai_content_label.font_name = CHINESE_FONT
            self.ai_card.height = dp(80)
        else:
            self.ai_card.height = dp(0)

    def _update_source_card(self):
        """更新来源卡片"""
        if self.source_info and self.source_info != "手动添加":
            self.source_content_label.text = self.source_info
            if CHINESE_FONT:
                self.source_content_label.font_name = CHINESE_FONT
            self.source_card.height = dp(60)
        else:
            self.source_card.height = dp(0)

    def _update_tag_card(self):
        """更新标签卡片"""
        if self.current_item and self.current_item.tags:
            tag_names = [tag.name for tag in self.current_item.tags]
            self.tag_content_label.text = ", ".join(tag_names)
            if CHINESE_FONT:
                self.tag_content_label.font_name = CHINESE_FONT
            self.tag_card.height = dp(80)
        else:
            self.tag_content_label.text = "无标签"
            if CHINESE_FONT:
                self.tag_content_label.font_name = CHINESE_FONT
            self.tag_card.height = dp(80)

    def _on_back_click(self, instance):
        """返回按钮点击"""
        app = MDApp.get_running_app()
        if hasattr(app, 'screen_manager'):
            app.screen_manager.current = 'main'

    def _on_edit_click(self, instance):
        """编辑按钮点击"""
        # TODO: 实现编辑功能
        logger.info(f"编辑物品: {self.item_id}")

    def _on_delete_click(self, instance):
        """删除按钮点击"""
        self._show_delete_dialog()

    def _show_delete_dialog(self):
        """显示删除确认对话框（使用 ModalView 适配 KivyMD 2.0）"""
        # 延迟导入，避免循环依赖
        from kivy.uix.modalview import ModalView
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label
        from kivy.metrics import dp

        # 获取中文字体
        chinese_font = None
        try:
            import app.main as main_module
            chinese_font = getattr(main_module, "CHINESE_FONT_NAME", None)
        except Exception:
            pass

        dialog = ModalView(size_hint=(0.8, None), height=dp(180), auto_dismiss=False)

        root = BoxLayout(orientation="vertical", padding=dp(20), spacing=dp(16))

        # 标题
        title_label = Label(
            text="确认删除",
            size_hint_y=None,
            height=dp(32),
            bold=True,
            color=(0.2, 0.2, 0.2, 1),
        )
        if chinese_font:
            title_label.font_name = chinese_font
        root.add_widget(title_label)

        # 内容
        content_label = Label(
            text=f"确定要删除 '{self.item_name}' 吗？",
            size_hint_y=None,
            height=dp(60),
            color=(0.3, 0.3, 0.3, 1),
        )
        if chinese_font:
            content_label.font_name = chinese_font
        root.add_widget(content_label)

        # 按钮区域
        btn_bar = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(44), spacing=dp(16))

        # 取消按钮
        cancel_btn = MDButton(on_release=lambda x: dialog.dismiss())
        cancel_text = MDButtonText(text="取消")
        if chinese_font:
            cancel_text.font_name = chinese_font
        cancel_btn.add_widget(cancel_text)
        btn_bar.add_widget(cancel_btn)

        # 确认按钮
        def _on_confirm(instance):
            dialog.dismiss()
            self._confirm_delete(instance)

        confirm_btn = MDButton(on_release=_on_confirm)
        confirm_text = MDButtonText(text="确定")
        if chinese_font:
            confirm_text.font_name = chinese_font
        confirm_btn.add_widget(confirm_text)
        btn_bar.add_widget(confirm_btn)

        root.add_widget(btn_bar)

        dialog.add_widget(root)
        self.delete_dialog = dialog
        dialog.open()

    def _confirm_delete(self, instance):
        """确认删除"""
        try:
            if item_service.delete_item(self.item_id):
                logger.info(f"物品删除成功: {self.item_name}")
                self.delete_dialog.dismiss()
                # 返回主屏幕
                app = MDApp.get_running_app()
                if hasattr(app, 'screen_manager'):
                    app.screen_manager.current = 'main'
            else:
                logger.error(f"物品删除失败: {self.item_id}")
        except Exception as e:
            logger.error(f"删除物品失败: {str(e)}")
            self.delete_dialog.dismiss()

    def _change_quantity(self, delta: int):
        """改变数量"""
        try:
            if item_service.update_item_quantity(self.item_id, delta):
                # 重新加载物品数据
                self._load_item(self.item_id)
        except Exception as e:
            logger.error(f"更新物品数量失败: {str(e)}")

    def _toggle_reminder(self, instance):
        """切换提醒开关"""
        try:
            if self.current_item:
                new_value = not self.current_item.is_reminder_enabled
                if item_service.update_item(self.item_id, is_reminder_enabled=new_value):
                    # 重新加载物品数据
                    self._load_item(self.item_id)
        except Exception as e:
            logger.error(f"切换提醒开关失败: {str(e)}")

    def on_enter(self):
        """进入屏幕时调用"""
        # 如果有传递item_id，加载数据
        app = MDApp.get_running_app()
        if hasattr(app, 'current_item_id'):
            self.item_id = app.current_item_id
        # 每次进入详情页后，为整个详情页重新应用中文字体，避免从其他页面返回后字体被还原
        try:
            import app.main as main_module
            chinese_font = getattr(main_module, "CHINESE_FONT_NAME", None)
        except Exception:
            chinese_font = None
        if chinese_font:
            apply_font_to_widget(self, chinese_font)

    def on_leave(self):
        """离开屏幕时调用"""
        # 清理
        self.item_id = ""
        self.current_item = None


# 测试代码
if __name__ == '__main__':
    from kivy.app import App as KivyApp

    class TestApp(KivyApp):
        def build(self):
            screen = ItemDetailScreen()
            screen.item_id = "test_id"  # 设置测试ID
            return screen

    TestApp().run()