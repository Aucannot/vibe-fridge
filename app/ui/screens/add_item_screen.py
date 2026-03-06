# -*- coding: utf-8 -*-
"""
添加物品屏幕 - 新建物品表单
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.gridlayout import GridLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.metrics import dp
from kivy.properties import StringProperty, ObjectProperty
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.button import (
    MDButton, MDIconButton, MDButtonText
)
from kivymd.uix.dialog import MDDialog
from kivymd.uix.pickers import MDModalDatePicker
from kivymd.uix.selectioncontrol import MDCheckbox
from kivymd.uix.list import MDListItem, MDListItemHeadlineText
from kivy.properties import StringProperty
from datetime import date, datetime
import os

from app.services.item_service import item_service

from app.utils.logger import setup_logger
from app.utils.font_helper import apply_font_to_widget, CHINESE_FONT_NAME as CHINESE_FONT

logger = setup_logger(__name__)

# 获取中文字体名称
CHINESE_FONT = CHINESE_FONT


class OneLineListItem(MDListItem):
    """单行列表项 - 用于下拉菜单"""
    text = StringProperty()
    
    def __init__(self, text="", **kwargs):
        # 固定行高，避免在下拉菜单中被压扁
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(48))
        super().__init__(**kwargs)

        self.text = text

        # 使用自定义颜色，确保在浅色背景上可见
        headline = MDListItemHeadlineText(text=text)
        try:
            headline.color = (0, 0, 0, 1)
        except AttributeError:
            pass
        if CHINESE_FONT:
            headline.font_name = CHINESE_FONT
        self.add_widget(headline)


class AddItemScreen(Screen):
    """添加物品屏幕"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'add_item'
        self._build_ui()
        self._create_category_menu()

        # 表单数据
        self.form_data = {
            'name': '',
            'category': '食品',
            'description': '',
            'quantity': 1,
            'unit': '',
            'purchase_date': None,
            'expiry_date': None,
            'tags': [],
            'enable_reminder': True
        }

        # 日期选择器
        self.date_picker = None

        # 尝试为整个屏幕应用中文字体（再次获取，避免导入时 CHINESE_FONT 仍为 None）
        try:
            import app.main as main_module
            runtime_font = getattr(main_module, 'CHINESE_FONT_NAME', None)
        except Exception:
            runtime_font = None
        if runtime_font:
            apply_font_to_widget(self, runtime_font)

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

        # 表单区域（可滚动）
        form_scroll = self._create_form_scroll()
        main_layout.add_widget(form_scroll)

        # 底部按钮栏
        button_bar = self._create_button_bar()
        main_layout.add_widget(button_bar)

        self.add_widget(main_layout)

    def _create_header(self) -> BoxLayout:
        """创建头部栏"""
        header = BoxLayout(size_hint_y=None, height=dp(56))

        # 返回按钮
        back_btn = MDIconButton(
            icon="arrow-left",
            on_release=self._on_back_click,
            font_name="Roboto",
        )
        header.add_widget(back_btn)

        # 标题
        title_label = Label(
            text="添加物品",
            size_hint_x=0.8,
            font_size=dp(20),
            bold=True
        )
        header.add_widget(title_label)

        return header

    def _create_form_scroll(self) -> ScrollView:
        """创建表单滚动区域"""
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

        form_layout = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            padding=dp(16),
            spacing=dp(16)
        )
        form_layout.bind(minimum_height=form_layout.setter('height'))

        # 基本信息卡片
        basic_card = self._create_basic_info_card()
        form_layout.add_widget(basic_card)

        # 数量卡片
        quantity_card = self._create_quantity_card()
        form_layout.add_widget(quantity_card)

        # 日期卡片
        date_card = self._create_date_card()
        form_layout.add_widget(date_card)

        # 选项卡片
        options_card = self._create_options_card()
        form_layout.add_widget(options_card)

        scroll_view.add_widget(form_layout)
        return scroll_view

    def _create_basic_info_card(self) -> MDCard:
        """创建基本信息卡片"""
        card = MDCard(
            size_hint_y=None,
            height=dp(200),
            padding=dp(16),
            radius=[dp(8), dp(8), dp(8), dp(8)]
        )

        layout = BoxLayout(orientation='vertical', spacing=dp(8))

        # 物品名称
        name_layout = BoxLayout(size_hint_y=None, height=dp(40))
        name_layout.add_widget(Label(
            text="名称*:",
            size_hint_x=None,
            width=dp(60),
            color=(0.4, 0.4, 0.4, 1)
        ))
        self.name_input = TextInput(
            hint_text="输入物品名称",
            multiline=False,
            size_hint_x=1
        )
        if CHINESE_FONT:
            self.name_input.font_name = CHINESE_FONT
        name_layout.add_widget(self.name_input)
        layout.add_widget(name_layout)

        # 类别选择
        category_layout = BoxLayout(size_hint_y=None, height=dp(40))
        category_layout.add_widget(Label(
            text="类别*:",
            size_hint_x=None,
            width=dp(60),
            color=(0.4, 0.4, 0.4, 1)
        ))
        self.category_button = MDButton(
            size_hint_x=1,
            style="filled",
            on_release=self._show_category_menu,
        )
        category_text = MDButtonText(text="食品")
        if CHINESE_FONT:
            category_text.font_name = CHINESE_FONT
        # 保存引用以便后续更新/重置
        self.category_label = category_text
        self.category_button.add_widget(category_text)
        category_layout.add_widget(self.category_button)
        layout.add_widget(category_layout)

        # 描述
        desc_layout = BoxLayout(size_hint_y=None, height=dp(80))
        desc_layout.add_widget(Label(
            text="描述:",
            size_hint_x=None,
            width=dp(60),
            color=(0.4, 0.4, 0.4, 1)
        ))
        self.desc_input = TextInput(
            hint_text="可选的描述信息",
            multiline=True,
            size_hint_x=1
        )
        if CHINESE_FONT:
            self.desc_input.font_name = CHINESE_FONT
        desc_layout.add_widget(self.desc_input)
        layout.add_widget(desc_layout)

        card.add_widget(layout)
        return card

    def _create_quantity_card(self) -> MDCard:
        """创建数量卡片"""
        card = MDCard(
            size_hint_y=None,
            height=dp(120),
            padding=dp(16),
            radius=[dp(8), dp(8), dp(8), dp(8)]
        )

        layout = GridLayout(cols=2, rows=2, spacing=dp(8))

        # 数量
        layout.add_widget(Label(
            text="数量:",
            color=(0.4, 0.4, 0.4, 1)
        ))
        quantity_layout = BoxLayout(spacing=dp(8))
        self.quantity_input = TextInput(
            text="1",
            multiline=False,
            size_hint_x=0.5,
            input_filter='int'
        )
        if CHINESE_FONT:
            self.quantity_input.font_name = CHINESE_FONT
        quantity_layout.add_widget(self.quantity_input)

        # 单位
        layout.add_widget(Label(
            text="单位:",
            color=(0.4, 0.4, 0.4, 1)
        ))
        self.unit_input = TextInput(
            hint_text="个、盒、瓶...",
            multiline=False,
            size_hint_x=1
        )
        if CHINESE_FONT:
            self.unit_input.font_name = CHINESE_FONT
        layout.add_widget(self.unit_input)

        # 数量加减按钮
        button_layout = BoxLayout(spacing=dp(8))
        decrease_btn = MDIconButton(
            icon="minus",
            on_release=lambda x: self._change_quantity(-1)
        )
        button_layout.add_widget(decrease_btn)

        increase_btn = MDIconButton(
            icon="plus",
            on_release=lambda x: self._change_quantity(1),
            font_name="Roboto",
        )
        button_layout.add_widget(increase_btn)

        quantity_layout.add_widget(button_layout)
        layout.add_widget(quantity_layout)

        card.add_widget(layout)
        return card

    def _create_date_card(self) -> MDCard:
        """创建日期卡片"""
        card = MDCard(
            size_hint_y=None,
            height=dp(160),
            padding=dp(16),
            radius=[dp(8), dp(8), dp(8), dp(8)]
        )

        layout = GridLayout(cols=1, rows=3, spacing=dp(8))

        # 购买日期
        purchase_layout = BoxLayout(size_hint_y=None, height=dp(40))
        purchase_layout.add_widget(Label(
            text="购买日期:",
            size_hint_x=None,
            width=dp(80),
            color=(0.4, 0.4, 0.4, 1)
        ))
        self.purchase_date_button = MDButton(
            on_release=lambda x: self._show_date_picker('purchase')
        )
        # 创建按钮文本部件（新的KivyMD API需要这样）
        purchase_text = MDButtonText(text="点击选择日期")
        if CHINESE_FONT:
            purchase_text.font_name = CHINESE_FONT
        # 保存引用，后续更新文本
        self.purchase_date_label = purchase_text
        self.purchase_date_button.add_widget(purchase_text)
        purchase_layout.add_widget(self.purchase_date_button)
        layout.add_widget(purchase_layout)

        # 过期日期
        expiry_layout = BoxLayout(size_hint_y=None, height=dp(40))
        expiry_layout.add_widget(Label(
            text="过期日期:",
            size_hint_x=None,
            width=dp(80),
            color=(0.4, 0.4, 0.4, 1)
        ))
        self.expiry_date_button = MDButton(
            on_release=lambda x: self._show_date_picker('expiry')
        )
        # 创建按钮文本部件（新的KivyMD API需要这样）
        expiry_text = MDButtonText(text="点击选择日期")
        if CHINESE_FONT:
            expiry_text.font_name = CHINESE_FONT
        # 保存引用，后续更新文本
        self.expiry_date_label = expiry_text
        self.expiry_date_button.add_widget(expiry_text)
        expiry_layout.add_widget(self.expiry_date_button)
        layout.add_widget(expiry_layout)

        # 日期提示
        date_hint = Label(
            text="注：过期日期用于计算提醒时间",
            size_hint_y=None,
            height=dp(30),
            font_size=dp(12),
            color=(0.6, 0.6, 0.6, 1)
        )
        layout.add_widget(date_hint)

        card.add_widget(layout)
        return card

    def _create_options_card(self) -> MDCard:
        """创建选项卡片"""
        card = MDCard(
            size_hint_y=None,
            height=dp(120),
            padding=dp(16),
            radius=[dp(8), dp(8), dp(8), dp(8)]
        )

        layout = BoxLayout(orientation='vertical', spacing=dp(8))

        # 提醒开关
        reminder_layout = BoxLayout(size_hint_y=None, height=dp(40))
        reminder_checkbox = MDCheckbox(
            size_hint_x=None,
            width=dp(40),
            active=True,
            on_active=self._on_reminder_toggle
        )
        reminder_layout.add_widget(reminder_checkbox)
        reminder_layout.add_widget(Label(
            text="启用过期提醒",
            color=(0.4, 0.4, 0.4, 1)
        ))
        layout.add_widget(reminder_layout)

        # 标签输入
        tag_layout = BoxLayout(size_hint_y=None, height=dp(40))
        tag_layout.add_widget(Label(
            text="标签:",
            size_hint_x=None,
            width=dp(60),
            color=(0.4, 0.4, 0.4, 1)
        ))
        self.tag_input = TextInput(
            hint_text="用逗号分隔，如：生鲜, 早餐",
            multiline=False,
            size_hint_x=1
        )
        if CHINESE_FONT:
            self.tag_input.font_name = CHINESE_FONT
        tag_layout.add_widget(self.tag_input)
        layout.add_widget(tag_layout)

        card.add_widget(layout)
        return card

    def _create_button_bar(self) -> BoxLayout:
        """创建按钮栏"""
        button_bar = BoxLayout(
            size_hint_y=None,
            height=dp(56),
            padding=dp(8),
            spacing=dp(8)
        )

        # 取消按钮
        cancel_btn = MDButton(
            on_release=self._on_cancel_click
        )
        # 创建按钮文本部件（新的KivyMD API需要这样）
        cancel_text = MDButtonText(text="取消")
        if CHINESE_FONT:
            cancel_text.font_name = CHINESE_FONT
        cancel_btn.add_widget(cancel_text)
        button_bar.add_widget(cancel_btn)

        # 提交按钮
        submit_btn = MDButton(
            size_hint_x=0.6,
            style="filled",
            on_release=self._on_submit_click
        )
        # 创建按钮文本部件（新的KivyMD API需要这样）
        submit_text = MDButtonText(text="添加")
        if CHINESE_FONT:
            submit_text.font_name = CHINESE_FONT
        submit_btn.add_widget(submit_text)
        button_bar.add_widget(submit_btn)

        return button_bar

    def _create_category_menu(self):
        """预先准备类别数据（自定义弹窗使用）"""
        self._category_items = [
            ("食品", "食品"),
            ("日用品", "日用品"),
            ("药品", "药品"),
            ("化妆品", "化妆品"),
            ("其他", "其他"),
        ]

    def _show_category_menu(self, instance):
        """显示类别选择弹窗（自定义 ModalView，替代 MDDropdownMenu）"""
        from kivy.uix.modalview import ModalView
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label

        dialog = ModalView(
            size_hint=(0.8, None),
            height=dp(280),
            auto_dismiss=True,
        )

        root = BoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(12),
        )

        # 标题
        title_label = Label(
            text="选择类别",
            size_hint_y=None,
            height=dp(32),
            bold=True,
            color=(0.2, 0.2, 0.2, 1),
        )
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        root.add_widget(title_label)

        # 选项按钮
        for text, category in self._category_items:
            def _on_select(btn_instance, cat=category, label=text, dlg=dialog):
                self._select_category(cat)
                dlg.dismiss()

            btn = MDButton(
                style="text",
                size_hint_y=None,
                height=dp(40),
                on_release=_on_select,
            )
            btn_text = MDButtonText(text=text)
            if CHINESE_FONT:
                btn_text.font_name = CHINESE_FONT
            btn.add_widget(btn_text)
            root.add_widget(btn)

        dialog.add_widget(root)
        dialog.open()

    def _select_category(self, category: str):
        """选择类别"""
        # 更新按钮文本
        category_map = {
            "食品": "食品",
            "日用品": "日用品",
            "药品": "药品",
            "化妆品": "化妆品",
            "其他": "其他",
        }
        # 使用 MDButtonText 组件更新按钮文字，兼容 KivyMD 2.x API
        if hasattr(self, "category_label"):
            self.category_label.text = category_map.get(category, "食品")

        # 保存到表单数据
        self.form_data['category'] = category

    def _show_date_picker(self, date_type: str):
        """显示日期选择器"""
        from datetime import date
        today = date.today()
        self.date_picker = MDModalDatePicker(
            year=today.year,
            month=today.month,
            day=today.day,
        )

        self.date_picker.bind(
            # 点击 OK 时回调；使用 *args 兼容不同版本的事件参数
            on_ok=lambda instance, *args, dt=date_type: self._on_date_ok(
                instance, *args, date_type=dt
            ),
            # 打开后再应用字体，确保内部子控件已经创建
            on_open=lambda instance: self._apply_font_to_date_picker(instance),
        )
        self.date_picker.open()

    def _on_date_ok(self, picker_instance, *args, date_type: str | None = None):
        """MDModalDatePicker 确认按钮回调，兼容不同参数签名"""
        from datetime import date as _date

        # KivyMD 可能会把选中的日期作为 args[0] 传入
        selected = None
        if args:
            selected = args[0]
        # 兜底：从选择器属性中尝试获取日期
        if selected is None:
            # 不同实现可能有不同属性名，这里做一些容错
            for attr in ("date", "sel_date", "current_date"):
                if hasattr(picker_instance, attr):
                    selected = getattr(picker_instance, attr)
                    break
        if selected is None:
            selected = _date.today()

        if date_type:
            self._on_date_selected(selected, date_type)

    def _apply_font_to_date_picker(self, picker_instance):
        """在日期选择器真正打开后，递归应用中文字体，避免标题/星期/按钮显示为方块"""
        try:
            font_name = CHINESE_FONT
            if not font_name:
                import app.main as main_module
                font_name = getattr(main_module, "CHINESE_FONT_NAME", None)
            if font_name:
                apply_font_to_widget(picker_instance, font_name)
        except Exception:
            # 字体应用失败时静默忽略，不影响功能
            pass

    def _on_date_selected(self, selected_date, date_type: str):
        """日期选择回调"""
        date_str = selected_date.strftime('%Y-%m-%d')

        if date_type == 'purchase':
            if hasattr(self, 'purchase_date_label'):
                self.purchase_date_label.text = date_str
            self.form_data['purchase_date'] = selected_date
        else:  # expiry
            if hasattr(self, 'expiry_date_label'):
                self.expiry_date_label.text = date_str
            self.form_data['expiry_date'] = selected_date

    def _change_quantity(self, delta: int):
        """改变数量"""
        try:
            current = int(self.quantity_input.text)
            new_value = max(1, current + delta)
            self.quantity_input.text = str(new_value)
            self.form_data['quantity'] = new_value
        except ValueError:
            self.quantity_input.text = "1"
            self.form_data['quantity'] = 1

    def _on_reminder_toggle(self, checkbox, active):
        """提醒开关切换"""
        self.form_data['enable_reminder'] = active

    def _on_back_click(self, instance):
        """返回按钮点击"""
        self._navigate_back()

    def _on_cancel_click(self, instance):
        """取消按钮点击"""
        self._navigate_back()

    def _navigate_back(self):
        """导航返回主屏幕"""
        app = MDApp.get_running_app()
        if hasattr(app, 'screen_manager'):
            app.screen_manager.current = 'main'

    def _on_submit_click(self, instance):
        """提交按钮点击"""
        if self._validate_form():
            self._submit_form()

    def _validate_form(self) -> bool:
        """验证表单数据"""
        # 获取名称
        name = self.name_input.text.strip()
        if not name:
            self._show_error_dialog("错误", "物品名称不能为空")
            return False

        # 获取数量
        try:
            quantity = int(self.quantity_input.text)
            if quantity <= 0:
                self._show_error_dialog("错误", "数量必须大于0")
                return False
        except ValueError:
            self._show_error_dialog("错误", "数量必须是数字")
            return False

        # 检查过期日期是否早于购买日期
        if (self.form_data['purchase_date'] and self.form_data['expiry_date'] and
            self.form_data['expiry_date'] < self.form_data['purchase_date']):
            self._show_error_dialog("错误", "过期日期不能早于购买日期")
            return False

        # 更新表单数据
        self.form_data.update({
            'name': name,
            'description': self.desc_input.text.strip(),
            'quantity': quantity,
            'unit': self.unit_input.text.strip() or None,
        })

        # 处理标签
        tags_text = self.tag_input.text.strip()
        if tags_text:
            self.form_data['tags'] = [tag.strip() for tag in tags_text.split(',') if tag.strip()]
        else:
            self.form_data['tags'] = []

        return True

    def _submit_form(self):
        """提交表单"""
        try:
            # 创建物品
            item = item_service.create_item(
                name=self.form_data['name'],
                category=self.form_data['category'],
                quantity=self.form_data['quantity'],
                expiry_date=self.form_data['expiry_date'],
                purchase_date=self.form_data['purchase_date'],
                description=self.form_data['description'],
                unit=self.form_data['unit'],
                tags=self.form_data['tags'],
                is_reminder_enabled=self.form_data['enable_reminder']
            )

            if item:
                logger.info(f"物品添加成功: {item.name} (ID: {item.id})")
                self._show_success_dialog(item)
            else:
                logger.error("物品添加失败")
                self._show_error_dialog("错误", "添加物品失败，请重试")

        except Exception as e:
            logger.error(f"提交表单失败: {str(e)}")
            self._show_error_dialog("错误", f"添加物品失败: {str(e)}")

    def _show_error_dialog(self, title: str, message: str):
        """显示错误对话框（自定义 ModalView，兼容 KivyMD 2.0）"""
        from kivy.uix.modalview import ModalView
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label

        dialog = ModalView(size_hint=(0.8, None), height=dp(200), auto_dismiss=True)

        root = BoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(16),
        )

        title_label = Label(
            text=title,
            size_hint_y=None,
            height=dp(32),
            bold=True,
            color=(0.8, 0.2, 0.2, 1),
        )
        msg_label = Label(
            text=message,
            size_hint_y=1,
            halign="left",
            valign="top",
            color=(0.2, 0.2, 0.2, 1),
        )
        msg_label.bind(
            size=lambda inst, val: setattr(inst, "text_size", (val[0], None))
        )
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
            msg_label.font_name = CHINESE_FONT

        root.add_widget(title_label)
        root.add_widget(msg_label)

        # 按钮区域
        btn_bar = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            padding=(0, dp(8), 0, 0),
            spacing=dp(12),
        )
        btn_bar.add_widget(BoxLayout())  # 占位，让按钮靠右

        ok_btn = MDButton(style="text", on_release=lambda x: dialog.dismiss())
        ok_text = MDButtonText(text="确定")
        if CHINESE_FONT:
            ok_text.font_name = CHINESE_FONT
        ok_btn.add_widget(ok_text)
        btn_bar.add_widget(ok_btn)

        root.add_widget(btn_bar)
        dialog.add_widget(root)
        dialog.open()

    def _show_success_dialog(self, item):
        """显示成功对话框（自定义 ModalView，兼容 KivyMD 2.0）"""
        from kivy.uix.modalview import ModalView
        from kivy.uix.boxlayout import BoxLayout
        from kivy.uix.label import Label

        dialog = ModalView(size_hint=(0.8, None), height=dp(220), auto_dismiss=True)

        root = BoxLayout(
            orientation="vertical",
            padding=dp(16),
            spacing=dp(16),
        )

        title_label = Label(
            text="添加成功",
            size_hint_y=None,
            height=dp(32),
            bold=True,
            color=(0.2, 0.6, 0.2, 1),
        )
        msg_label = Label(
            text=f"物品 '{item.name}' 已成功添加",
            size_hint_y=1,
            halign="left",
            valign="top",
            color=(0.2, 0.2, 0.2, 1),
        )
        msg_label.bind(
            size=lambda inst, val: setattr(inst, "text_size", (val[0], None))
        )
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
            msg_label.font_name = CHINESE_FONT

        root.add_widget(title_label)
        root.add_widget(msg_label)

        # 按钮区域
        btn_bar = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            padding=(0, dp(8), 0, 0),
            spacing=dp(12),
        )

        def _on_continue(_instance):
            dialog.dismiss()
            self._reset_form()

        def _on_back(_instance):
            dialog.dismiss()
            self._navigate_after_success()

        continue_btn = MDButton(style="text", on_release=_on_continue)
        continue_text = MDButtonText(text="继续添加")
        if CHINESE_FONT:
            continue_text.font_name = CHINESE_FONT
        continue_btn.add_widget(continue_text)

        back_btn = MDButton(style="text", on_release=_on_back)
        back_text = MDButtonText(text="返回主页")
        if CHINESE_FONT:
            back_text.font_name = CHINESE_FONT
        back_btn.add_widget(back_text)

        btn_bar.add_widget(continue_btn)
        btn_bar.add_widget(back_btn)

        root.add_widget(btn_bar)
        dialog.add_widget(root)
        dialog.open()

    def _reset_form(self, instance=None):
        """重置表单"""
        # 重置输入字段
        self.name_input.text = ""
        self.desc_input.text = ""
        self.quantity_input.text = "1"
        self.unit_input.text = ""
        self.tag_input.text = ""

        # 重置按钮文本
        if hasattr(self, "purchase_date_label"):
            self.purchase_date_label.text = "点击选择日期"
        if hasattr(self, "expiry_date_label"):
            self.expiry_date_label.text = "点击选择日期"

        # 重置表单数据
        self.form_data = {
            'name': '',
            'category': "食品",
            'description': '',
            'quantity': 1,
            'unit': '',
            'purchase_date': None,
            'expiry_date': None,
            'tags': [],
            'enable_reminder': True
        }

        # 重置类别按钮
        if hasattr(self, "category_label"):
            self.category_label.text = "食品"

        # 聚焦到名称输入框
        self.name_input.focus = True

    def _navigate_after_success(self, instance=None):
        """成功后导航"""
        self._navigate_back()

    def on_enter(self):
        """进入屏幕时调用"""
        # 重置表单
        self._reset_form()
        # 聚焦到名称输入框
        self.name_input.focus = True

    def on_leave(self):
        """离开屏幕时调用"""
        # 关闭日期选择器
        if self.date_picker:
            self.date_picker.dismiss()


# 测试代码
if __name__ == '__main__':
    from kivy.app import App as KivyApp

    class TestApp(KivyApp):
        def build(self):
            return AddItemScreen()

    TestApp().run()