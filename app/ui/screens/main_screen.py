# -*- coding: utf-8 -*-
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
from kivy.uix.modalview import ModalView
from kivy.graphics import Color, Rectangle
from kivy.metrics import dp
from kivy.properties import (
    StringProperty, ListProperty, ObjectProperty, NumericProperty
)
from kivy.clock import Clock
from kivymd.app import MDApp
from kivymd.uix.list import (
    MDList, MDListItem,
    MDListItemHeadlineText,
    MDListItemSupportingText,
    MDListItemTertiaryText,
)
from kivymd.uix.button import MDFabButton, MDButton, MDIconButton, MDButtonText
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from datetime import date, timedelta
import os

from app.services.item_service import item_service, statistics_service
from app.models.item import ItemCategory, ItemStatus
from app.utils.logger import setup_logger
from app.utils.font_helper import apply_font_to_widget, CHINESE_FONT_NAME as CHINESE_FONT

print(f"main_screen.py: CHINESE_FONT = {CHINESE_FONT}")


class OneLineListItem(MDListItem):
    """单行列表项 - 用于下拉菜单"""
    text = StringProperty()

    def __init__(self, text="", **kwargs):
        super().__init__(**kwargs)
        self.theme_text_color = "Custom"
        self.text_color = (0, 0, 0, 1)
        self._txt = text

        from kivy.uix.label import Label
        from kivy.metrics import dp

        label = Label(
            text=text,
            size_hint_y=None,
            height=dp(48),
            halign="left",
            valign="middle",
            color=(0, 0, 0, 1),
            font_size=dp(16),
        )
        label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1])))
        if CHINESE_FONT:
            label.font_name = CHINESE_FONT
        self.add_widget(label)


class ItemListItem(BoxLayout):
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
        self.status = item_data.get('status', 'active')

        # 添加交互状态属性
        self.is_hovering = False
        self.is_pressed = False
        self.original_bg_color = None
        
        # 添加复选框相关属性
        self.item_name_label = None
        self.is_consumed = self.status == 'consumed'
        self._delete_timer = None
        self.checkbox_widget = None
        self.strikethrough_line = None

        # 设置基本布局属性
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.size_hint_x = 1
        self.height = dp(85)
        self.pos_hint = {'x': 0, 'y': 0}

        # 左侧图标
        icon = self._setup_icon()
        icon.size_hint_x = None
        icon.width = dp(48)
        self.add_widget(icon)

        # 中间文本内容
        text_box = self._setup_text(item_data)
        text_box.size_hint_x = 1
        self.add_widget(text_box)

        # 为文本内容应用中文字体
        if CHINESE_FONT:
            apply_font_to_widget(text_box, CHINESE_FONT)

        # 右侧复选框
        checkbox = self._setup_checkbox()
        checkbox.size_hint_x = None
        checkbox.width = dp(48)
        self.add_widget(checkbox)

        # 设置背景色（根据过期状态）
        self._setup_background()
        
        # 如果物品已消耗，显示消耗状态
        if self.is_consumed:
            self._show_consumed_state()
        
        # 为所有子控件应用中文字体
        if CHINESE_FONT:
            apply_font_to_widget(self, CHINESE_FONT)
        
        # 添加点击事件支持 - 使用Kivy标准事件名，不需要手动绑定
        self.register_event_type('on_release')
        
        # 绑定鼠标事件
        self.bind(on_touch_move=self.on_touch_move)

    def _setup_icon(self):
        """设置图标（测试MDIcon显示）"""
        from kivymd.uix.label import MDIcon
        
        # 创建MDIcon - 完全模仿items_screen.py的配置
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
            font_size=dp(28),
        )
        
        return icon
    
    def _setup_checkbox(self):
        """设置右侧复选框"""
        from kivymd.uix.selectioncontrol import MDCheckbox
        
        checkbox = MDCheckbox(
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={'center_y': 0.5},
            active=False,
        )
        checkbox.bind(on_active=self._on_checkbox_active)
        self.checkbox_widget = checkbox
        return checkbox
    
    def _setup_text(self, item_data):
        """设置文本内容，使用自定义容器避免 MDListItem 的子控件布局问题"""
        from kivy.uix.label import Label
        from kivy.uix.boxlayout import BoxLayout

        print(f"ItemListItem._setup_text: 开始设置文本, CHINESE_FONT = {CHINESE_FONT}")

        text_box = BoxLayout(
            orientation="vertical",
            padding=(dp(8), dp(6)),
            spacing=(dp(2)),
            size_hint_y=None,
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
                print(f"ItemListItem._make_label: 为Label '{text}' 设置字体 {CHINESE_FONT}")
            return lbl

        headline_text = f"{self.item_name} x{self.quantity}"
        self.item_name_label = _make_label(headline_text, dp(28), (0.1, 0.1, 0.1, 1), dp(18), True)
        text_box.add_widget(self.item_name_label)

        category_map = {
            ItemCategory.FOOD.value: "食品",
            ItemCategory.DAILY_NECESSITIES.value: "日用品",
            ItemCategory.MEDICINE.value: "药品",
            ItemCategory.COSMETICS.value: "化妆品",
            ItemCategory.OTHERS.value: "其他",
        }
        category_text = category_map.get(self.category, "其他")

        has_expiry = self.expiry_date != "无"
        if not has_expiry:
            status_text = "无过期日期"
            status_color = (0.5, 0.5, 0.5, 1)
        else:
            status_text = "正常"
            status_color = (0.2, 0.6, 0.2, 1)
            if self.days_until_expiry < 0:
                status_text = "已过期"
                status_color = (0.8, 0.2, 0.2, 1)
            elif self.days_until_expiry <= 3:
                status_text = "即将过期"
                status_color = (0.85, 0.5, 0.1, 1)

        supporting_text = f"{category_text}  |  {status_text}"
        text_box.add_widget(_make_label(supporting_text, dp(22), status_color, dp(14)))

        if self.expiry_date == "无":
            tertiary_text = "无过期日期"
            tertiary_color = (0.5, 0.5, 0.5, 1)
        else:
            days_text = f"剩余{self.days_until_expiry}天"
            if self.days_until_expiry < 0:
                days_text = f"过期{-self.days_until_expiry}天"
            elif self.days_until_expiry == 0:
                days_text = "今天过期"
            tertiary_text = f"{self.expiry_date}  |  {days_text}"
            if self.days_until_expiry < 0:
                tertiary_color = (0.75, 0.2, 0.2, 1)
            elif self.days_until_expiry <= 3:
                tertiary_color = (0.8, 0.5, 0.1, 1)
            else:
                tertiary_color = (0.4, 0.4, 0.4, 1)
        text_box.add_widget(_make_label(tertiary_text, dp(22), tertiary_color, dp(13)))

        return text_box

    def _setup_background(self):
        """根据过期状态设置背景色和圆角"""
        # 设置布局属性
        self.padding = (dp(8), dp(8), dp(8), dp(8))
        self.spacing = dp(12)
        
        # 没有过期日期的物品统一按“正常”处理，不高亮为即将过期/已过期
        if self.expiry_date == "无":
            self._set_background_color(1, 1, 1)
        elif self.days_until_expiry < 0:
            # 已过期 - 浅红色
            self._set_background_color(1, 0.95, 0.95)
        elif self.days_until_expiry <= 3:
            # 即将过期 - 浅黄色
            self._set_background_color(1, 1, 0.95)
        else:
            # 正常 - 白色
            self._set_background_color(1, 1, 1)

    def _set_background_color(self, r, g, b):
        """设置背景颜色和圆角"""
        from kivy.graphics import RoundedRectangle
        with self.canvas.before:
            Color(r, g, b, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12), dp(12), dp(12), dp(12)])

        # 绑定大小变化
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _update_rect(self, *args):
        """更新背景位置和大小"""
        from kivy.graphics import RoundedRectangle
        self.canvas.before.clear()
        with self.canvas.before:
            if self.expiry_date == "无":
                Color(1, 1, 1, 1)
            elif self.days_until_expiry < 0:
                Color(1, 0.95, 0.95, 1)
            elif self.days_until_expiry <= 3:
                Color(1, 1, 0.95, 1)
            else:
                Color(1, 1, 1, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12), dp(12), dp(12), dp(12)])
    
    def on_touch_move(self, instance, touch):
        """处理鼠标移动事件，实现悬停效果"""
        is_hovering = self.collide_point(*touch.pos)
        if is_hovering != self.is_hovering:
            self.is_hovering = is_hovering
            self._update_background_with_hover()
        return False

    def on_touch_down(self, touch):
        """处理触摸事件，添加按下效果"""
        if self.collide_point(*touch.pos):
            # 如果点击的是复选框，不触发物品项的点击事件
            if self.checkbox_widget and self.checkbox_widget.collide_point(*touch.pos):
                return self.checkbox_widget.on_touch_down(touch)
            self.is_pressed = True
            self._update_background_with_press()
            return True
        return super().on_touch_down(touch) if hasattr(super(), 'on_touch_down') else False

    def on_touch_up(self, touch):
        """处理触摸抬起事件"""
        if self.is_pressed and self.collide_point(*touch.pos):
            self.dispatch('on_release')
        self.is_pressed = False
        self._update_background_with_hover()
        return super().on_touch_up(touch) if hasattr(super(), 'on_touch_up') else False
    
    def on_release(self, *args):
        """释放事件（供外部绑定）"""
        pass
    
    def _on_checkbox_active(self, checkbox, value):
        """复选框状态变化处理"""
        if value and not self.is_consumed:
            self.is_consumed = True
            self._mark_as_consumed()
    
    def _mark_as_consumed(self):
        """标记物品为已消耗：灰色显示、删除线"""
        # 调用服务层标记物品为已消耗
        item_service.mark_as_consumed(self.item_id)
        
        # 显示消耗状态
        self._show_consumed_state()
    
    def _show_consumed_state(self):
        """显示物品消耗状态：灰色背景、删除线"""
        # 设置背景为灰色
        self.canvas.before.clear()
        from kivy.graphics import Color, RoundedRectangle, Line
        with self.canvas.before:
            Color(0.9, 0.9, 0.9, 1)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12), dp(12), dp(12), dp(12)])
        
        # 为物品名称添加删除线（使用Canvas画线）
        if self.item_name_label:
            self.item_name_label.color = (0.5, 0.5, 0.5, 1)
            # 绑定位置变化事件来更新删除线位置
            self.item_name_label.bind(pos=self._update_strikethrough_line, size=self._update_strikethrough_line)
            self._update_strikethrough_line()
    
    def _update_strikethrough_line(self, *args):
        """更新删除线位置"""
        if not self.item_name_label:
            return
        
        # 清除旧的删除线
        if self.strikethrough_line:
            self.canvas.after.remove(self.strikethrough_line)
        
        # 计算删除线位置（在文本中间）
        from kivy.graphics import Color, Line
        x = self.item_name_label.x
        y = self.item_name_label.y + self.item_name_label.height / 2
        width = self.item_name_label.width
        
        # 绘制删除线
        with self.canvas.after:
            Color(0.5, 0.5, 0.5, 1)
            self.strikethrough_line = Line(points=[x, y, x + width, y], width=1.5)

    def _update_background_with_hover(self):
        """更新背景色，添加悬停效果"""
        if self.expiry_date == "无":
            bg_color = (0.98, 0.98, 1, 1) if self.is_hovering else (1, 1, 1, 1)
        elif self.days_until_expiry < 0:
            bg_color = (1, 0.92, 0.92, 1) if self.is_hovering else (1, 0.95, 0.95, 1)
        elif self.days_until_expiry <= 3:
            bg_color = (1, 0.98, 0.92, 1) if self.is_hovering else (1, 1, 0.95, 1)
        else:
            bg_color = (0.98, 0.98, 1, 1) if self.is_hovering else (1, 1, 1, 1)
        
        self.canvas.before.clear()
        from kivy.graphics import Color, RoundedRectangle
        with self.canvas.before:
            Color(*bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12), dp(12), dp(12), dp(12)])

    def _update_background_with_press(self):
        """更新背景色，添加按下效果"""
        if self.expiry_date == "无":
            bg_color = (0.95, 0.95, 0.98, 1)
        elif self.days_until_expiry < 0:
            bg_color = (0.98, 0.88, 0.88, 1)
        elif self.days_until_expiry <= 3:
            bg_color = (0.98, 0.95, 0.88, 1)
        else:
            bg_color = (0.95, 0.95, 0.98, 1)
        
        self.canvas.before.clear()
        from kivy.graphics import Color, RoundedRectangle
        with self.canvas.before:
            Color(*bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12), dp(12), dp(12), dp(12)])


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
        
        # 设置定时清理已消耗物品
        Clock.schedule_interval(self._cleanup_consumed_items, 3600)  # 每小时清理一次

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
        header = BoxLayout(size_hint_y=None, height=dp(68), padding=dp(20))
        # 设置标题栏背景色
        from kivy.graphics import Color, Rectangle
        with header.canvas.before:
            Color(0.2, 0.6, 0.9, 1)  # 使用主题色作为标题栏背景
            header_bg_rect = Rectangle(pos=header.pos, size=header.size)
        
        def update_header_bg(instance, value):
            header_bg_rect.pos = instance.pos
            header_bg_rect.size = instance.size
        
        header.bind(pos=update_header_bg, size=update_header_bg)
        
        title_label = Label(
            text="vibe-fridge",
            font_size=dp(30),
            bold=True,
            color=(1, 1, 1, 1),  # 白色文字
            pos_hint={'center_y': 0.5}
        )
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        header.add_widget(title_label)

        return header

    def _create_filter_bar(self) -> BoxLayout:
        """创建筛选栏"""
        from kivymd.uix.textfield import MDTextField
        from kivymd.uix.button import MDIconButton
        
        filter_bar = BoxLayout(
            size_hint_y=None,
            height=dp(72),  # 增加高度，提供更舒适的点击区域
            padding=dp(16),
            spacing=dp(16)  # 增大间距，提升呼吸感
        )
        # 设置筛选栏背景色
        from kivy.graphics import Color, Rectangle
        with filter_bar.canvas.before:
            Color(0.98, 0.98, 1.0, 1)  # 浅蓝色背景，更柔和
            filter_bg_rect = Rectangle(pos=filter_bar.pos, size=filter_bar.size)
        
        def update_filter_bg(instance, value):
            filter_bg_rect.pos = instance.pos
            filter_bg_rect.size = instance.size
        
        filter_bar.bind(pos=update_filter_bg, size=update_filter_bg)

        # 类别筛选按钮（放在左边）
        self.category_button = MDButton(
            style="filled",
            md_bg_color=(0.2, 0.6, 0.9, 1),  # 主题色
            size_hint_x=0.38,  # 调整宽度比例，使布局更平衡
            radius=[dp(16), dp(16), dp(16), dp(16)],  # 增大圆角，更现代
            on_release=self._show_category_menu
        )
        category_text = MDButtonText(
            text="所有类别",
            font_size=dp(16),
            theme_font_name="Custom"
        )
        if CHINESE_FONT:
            category_text.font_name = CHINESE_FONT
        self.category_button.add_widget(category_text)
        filter_bar.add_widget(self.category_button)

        # 搜索相关组件容器
        search_container = BoxLayout(
            size_hint_x=0.62,  # 调整宽度比例，与类别按钮形成更好的平衡
            spacing=dp(12),  # 增大间距，提升呼吸感
            pos_hint={'center_y': 0.5}
        )
        
        # 搜索输入框（默认隐藏，点击搜索图标后显示）
        self.search_input = MDTextField(
            hint_text="搜索物品...",
            size_hint_x=1,
            mode="outlined",
            line_color_normal=(0.2, 0.6, 0.9, 0.5),
            line_color_focus=(0.2, 0.6, 0.9, 1),
            font_size=dp(15),
            radius=[dp(16), dp(16), dp(16), dp(16)],  # 增大圆角，更现代
            pos_hint={'center_y': 0.5},
            opacity=0,  # 默认隐藏
            disabled=True  # 默认禁用
        )
        search_container.add_widget(self.search_input)
        
        # 搜索图标按钮（放大镜样式，放在右边）
        self.search_icon_button = MDIconButton(
            icon="magnify",
            size_hint=(None, None),
            size=(dp(48), dp(48)),  # 增大点击区域
            theme_icon_color="Custom",
            icon_color=(0.2, 0.6, 0.9, 1),
            pos_hint={'center_y': 0.5},
            on_release=self._toggle_search_input
        )
        search_container.add_widget(self.search_icon_button)
        
        filter_bar.add_widget(search_container)

        return filter_bar
        
    def _toggle_search_input(self, *args):
        """切换搜索输入框的显示/隐藏状态"""
        from kivy.animation import Animation
        
        if self.search_input.opacity == 0:
            # 显示搜索框 - 使用更流畅的动画
            anim = Animation(opacity=1, duration=0.4, t='out_cubic')
            anim.start(self.search_input)
            self.search_input.disabled = False
            # 聚焦到搜索框
            def focus_search(dt):
                self.search_input.focus = True
            Clock.schedule_once(focus_search, 0.4)
        else:
            # 隐藏搜索框 - 使用更流畅的动画
            anim = Animation(opacity=0, duration=0.4, t='out_cubic')
            anim.bind(on_complete=lambda *args: self._on_search_hidden())
            anim.start(self.search_input)
    
    def _on_search_hidden(self):
        """搜索框隐藏完成后的回调"""
        self.search_input.disabled = True
        self.search_input.text = ""  # 清空搜索内容
        self._load_items()  # 重新加载物品列表

    def _create_stats_cards(self) -> BoxLayout:
        """创建统计卡片"""
        stats_layout = BoxLayout(
            size_hint_y=None,
            height=dp(128),
            padding=dp(20),
            spacing=dp(18)
        )

        self.total_card = self._create_stat_card("总物品", "0", (0.2, 0.55, 0.85, 1), (0.95, 0.98, 1.0, 1))
        stats_layout.add_widget(self.total_card)

        self.expiring_card = self._create_stat_card("即将过期", "0", (0.85, 0.55, 0.15, 1), (1.0, 0.98, 0.92, 1))
        stats_layout.add_widget(self.expiring_card)

        self.expired_card = self._create_stat_card("已过期", "0", (0.85, 0.25, 0.25, 1), (1.0, 0.94, 0.94, 1))
        stats_layout.add_widget(self.expired_card)

        return stats_layout

    def _create_stat_card(self, title: str, value: str, color, bg_color) -> MDCard:
        """创建统计卡片"""
        card = MDCard(
            size_hint=(1, 1),
            padding=dp(20),  # 增加内边距，提升空间感
            radius=[dp(16), dp(16), dp(16), dp(16)],  # 统一圆角大小
            md_bg_color=bg_color,
            elevation=3,  # 增强阴影效果，提升层次感
        )

        layout = BoxLayout(orientation='vertical')

        title_label = Label(
            text=title,
            font_size=dp(14),
            color=(0.45, 0.45, 0.45, 1),
            size_hint_y=None,
            height=dp(24),
        )
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        layout.add_widget(title_label)

        value_label = Label(
            text=value,
            font_size=dp(36),
            color=color,
            bold=True,
            size_hint_y=None,
            height=dp(52),
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
        """创建类别筛选菜单（使用自定义弹窗）"""
        from kivy.graphics import RoundedRectangle
        
        self.category_menu = ModalView(
            size_hint=(0.88, None),  # 增大宽度，更好的视觉效果
            auto_dismiss=True, 
            background_color=(0, 0, 0, 0.25)  # 调整背景透明度
        )
        self.category_menu.size_hint_y = None
        self.category_menu.height = dp(500)  # 增加高度，更舒适的空间

        main_box = BoxLayout(orientation="vertical", padding=dp(0), spacing=dp(0), size_hint_y=None)
        main_box.bind(minimum_height=main_box.setter('height'))

        content_box = BoxLayout(
            orientation="vertical",
            padding=dp(28),  # 增大内边距，提升空间感
            spacing=dp(18),  # 增大按钮间距，提升呼吸感
            size_hint_y=None,
            height=dp(500),
        )
        content_box.bind(height=self._update_content_height)

        with content_box.canvas.before:
            Color(1, 1, 1, 1)
            # 使用更大的圆角
            RoundedRectangle(size=content_box.size, pos=content_box.pos, radius=[dp(24), dp(24), dp(24), dp(24)])
        content_box.bind(pos=self._update_rect, size=self._update_rect)

        title_label = Label(
            text="选择类别",
            size_hint_y=None,
            height=dp(60),
            font_size=dp(24),
            bold=True,
            color=(0.2, 0.2, 0.2, 1),
            halign="center",
            valign="middle"
        )
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        content_box.add_widget(title_label)

        categories = [
            ("所有类别", None),
            ("食品", ItemCategory.FOOD),
            ("日用品", ItemCategory.DAILY_NECESSITIES),
            ("药品", ItemCategory.MEDICINE),
            ("化妆品", ItemCategory.COSMETICS),
            ("其他", ItemCategory.OTHERS),
        ]

        # 增加类别按钮容器，添加适当的间距
        button_container = BoxLayout(orientation="vertical", spacing=dp(14), size_hint_y=None)
        button_container.bind(minimum_height=button_container.setter('height'))
        
        for i, (cat_text, cat_value) in enumerate(categories):
            btn = self._create_category_button(cat_text, cat_value)
            button_container.add_widget(btn)
        
        content_box.add_widget(button_container)

        # 美化取消按钮
        close_btn = MDButton(
            style="outlined",
            size_hint_y=None,
            height=dp(56),
            radius=[dp(12), dp(12), dp(12), dp(12)],  # 增大圆角
            line_color=(0.2, 0.6, 0.9, 1),
            on_release=lambda x: self.category_menu.dismiss()
        )
        close_text = MDButtonText(
            text="取消",
            font_size=dp(16),
            theme_text_color="Custom",
            text_color=(0.2, 0.6, 0.9, 1),
            theme_font_name="Custom"
        )
        if CHINESE_FONT:
            close_text.font_name = CHINESE_FONT
        close_btn.add_widget(close_text)
        content_box.add_widget(close_btn)

        main_box.add_widget(content_box)
        self.category_menu.add_widget(main_box)

    def _create_category_button(self, text, category_value):
        """创建带悬停效果的类别按钮"""
        # 检查是否是当前选中的类别
        is_selected = False
        if hasattr(self, 'selected_category'):
            if category_value is None and self.selected_category is None:
                is_selected = True
            elif category_value is not None and self.selected_category == category_value:
                is_selected = True
        
        btn = MDButton(
            style="filled" if is_selected else "outlined",  # 使用outlined样式替代text，更现代
            md_bg_color=(0.2, 0.6, 0.9, 1) if is_selected else (0.96, 0.96, 0.96, 1),
            size_hint_y=None,
            height=dp(56),
            radius=[dp(12), dp(12), dp(12), dp(12)],  # 增大圆角，更现代
            line_color=(0.2, 0.6, 0.9, 1) if not is_selected else (0, 0, 0, 0),  # 未选中时显示边框
        )
        btn_text = MDButtonText(
            text=text,
            font_size=dp(16),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1) if is_selected else (0.3, 0.3, 0.3, 1),
            theme_font_name="Custom"
        )
        if CHINESE_FONT:
            btn_text.font_name = CHINESE_FONT

        btn.add_widget(btn_text)
        btn.bind(
            on_release=lambda instance, v=category_value, t=text: [
                self._select_category(v),
                self.category_menu.dismiss()
            ]
        )
        
        # 添加悬停效果
        def on_hover(instance, touch):
            if not is_selected and instance.collide_point(*touch.pos):
                instance.md_bg_color = (0.92, 0.95, 1.0, 1)
            elif not is_selected:
                instance.md_bg_color = (0.96, 0.96, 0.96, 1)
            return False
        
        btn.bind(on_touch_move=on_hover)
        
        return btn

    def _update_rect(self, instance, value):
        from kivy.graphics import RoundedRectangle
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(1, 1, 1, 1)
            RoundedRectangle(size=instance.size, pos=instance.pos, radius=[dp(24), dp(24), dp(24), dp(24)])

    def _update_content_height(self, instance, height):
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
                print(f"_load_items: 创建空状态标签, CHINESE_FONT = {CHINESE_FONT}")
                empty_label = Label(
                    text="暂无物品，点击右下角+添加",
                    size_hint_y=None,
                    height=dp(100),
                    halign="left",
                    valign="middle",
                    color=(0.6, 0.6, 0.6, 1),
                )
                empty_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1])))
                if CHINESE_FONT:
                    empty_label.font_name = CHINESE_FONT
                    print(f"_load_items: 空标签字体设置为 {empty_label.font_name}")
                else:
                    print(f"_load_items: CHINESE_FONT为None，无法设置空标签字体")
                self.item_list_layout.add_widget(empty_label)
                
                # 为类别按钮重新应用中文字体（确保切换类别后字体正确）
                print(f"_load_items: 为类别按钮重新应用字体, CHINESE_FONT = {CHINESE_FONT}")
                if CHINESE_FONT:
                    for child in self.category_button.children:
                        if isinstance(child, MDButtonText):
                            child.font_name = CHINESE_FONT
                            print(f"_load_items: 类别按钮字体设置为 {child.font_name}")
                            break
                else:
                    print(f"_load_items: CHINESE_FONT为None，无法设置类别按钮字体")
                
                return

            # 添加物品项
            print(f"_load_items: 开始添加物品项, 物品数量 = {len(items)}, CHINESE_FONT = {CHINESE_FONT}")
            for item in items:
                item_data = self._prepare_item_data(item)
                list_item = ItemListItem(item_data)
                list_item.bind(on_release=lambda instance, item_id=item.id:
                              self._on_item_click(item_id))
                self.item_list_layout.add_widget(list_item)
                # 为每个物品项立即应用中文字体
                if CHINESE_FONT:
                    apply_font_to_widget(list_item, CHINESE_FONT)
                    print(f"_load_items: 为物品项 {item.name} 应用字体")

            # 为类别按钮重新应用中文字体（确保切换类别后字体正确）
            print(f"_load_items: 为类别按钮重新应用字体, CHINESE_FONT = {CHINESE_FONT}")
            if CHINESE_FONT:
                for child in self.category_button.children:
                    if isinstance(child, MDButtonText):
                        child.font_name = CHINESE_FONT
                        print(f"_load_items: 类别按钮字体设置为 {child.font_name}")
                        break
            else:
                print(f"_load_items: CHINESE_FONT为None，无法设置类别按钮字体")

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
            'quantity': item.quantity,
            'status': item.status.value if item.status else 'active'
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
        print(f"_show_category_menu 被调用, CHINESE_FONT = {CHINESE_FONT}")
        
        # 重新创建类别菜单以更新选中状态
        self.category_menu.clear_widgets()
        self._create_category_menu()
        
        self.category_menu.open()
        
        # 延迟应用字体，确保所有控件都已经创建完成
        def apply_font_delayed(dt):
            if CHINESE_FONT:
                apply_font_to_widget(self.category_menu, CHINESE_FONT)
        
        Clock.schedule_once(apply_font_delayed, 0.3)

    def _select_category(self, category: ItemCategory):
        """选择类别"""
        self.category_menu.dismiss()
        
        # 保存当前选中的类别
        self.selected_category = category

        if category:
            category_text = {
                ItemCategory.FOOD: "食品",
                ItemCategory.DAILY_NECESSITIES: "日用品",
                ItemCategory.MEDICINE: "药品",
                ItemCategory.COSMETICS: "化妆品",
                ItemCategory.OTHERS: "其他"
            }.get(category, "所有类别")
        else:
            category_text = "所有类别"

        # 更新类别按钮的文本（需要更新MDButtonText控件）
        print(f"_select_category: 开始更新类别按钮文本, category_text = {category_text}")
        print(f"_select_category: CHINESE_FONT = {CHINESE_FONT}")
        for child in self.category_button.children:
            if isinstance(child, MDButtonText):
                print(f"_select_category: 找到MDButtonText, 当前text = {child.text}")
                child.text = category_text
                child.theme_font_name = "Custom"
                if CHINESE_FONT:
                    child.font_name = CHINESE_FONT
                    print(f"_select_category: 设置字体为 {child.font_name}")
                else:
                    print(f"_select_category: CHINESE_FONT为None，无法设置字体")
                break
        else:
            print(f"_select_category: 未找到MDButtonText控件")
        
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
        
        # 为类别按钮重新应用中文字体
        if CHINESE_FONT:
            for child in self.category_button.children:
                if isinstance(child, MDButtonText):
                    child.font_name = CHINESE_FONT
                    break

    def on_leave(self):
        """离开屏幕时调用"""
        # 清理资源
        if hasattr(self, 'category_menu'):
            self.category_menu.dismiss()
    
    def _cleanup_consumed_items(self, dt):
        """定时清理超过3天的已消耗物品"""
        try:
            count = item_service.cleanup_consumed_items(days=3)
            if count > 0:
                logger.info(f"定时清理了 {count} 个已消耗物品")
                # 刷新列表
                self._load_items(self.selected_category)
        except Exception as e:
            logger.error(f"定时清理已消耗物品失败: {e}")


# 测试代码
if __name__ == '__main__':
    from kivy.app import App as KivyApp

    class TestApp(KivyApp):
        def build(self):
            return MainScreen()

    TestApp().run()