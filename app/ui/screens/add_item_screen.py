# -*- coding: utf-8 -*-
"""
添加物品屏幕 - 新建物品表单
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.scrollview import ScrollView
from kivy.uix.button import Button
from kivy.clock import Clock
from kivy.metrics import dp
from kivy.graphics import Color, Rectangle, RoundedRectangle, Line
from kivymd.app import MDApp
from kivymd.uix.card import MDCard
from kivymd.uix.button import MDIconButton
from kivymd.uix.label import MDIcon
from kivymd.uix.pickers import MDModalDatePicker
from kivymd.uix.pickers.datepicker.datepicker import (
    MDDatePickerDaySelectableItem,
    MDDatePickerWeekdayLabel,
)
from kivymd.uix.selectioncontrol import MDCheckbox
from datetime import date

from app.services.item_service import item_service
from app.ui.theme.design_tokens import COLOR_PALETTE, get_card_style, get_font_size

from app.utils.logger import setup_logger
from app.utils.font_helper import apply_font_to_widget, CHINESE_FONT_NAME as CHINESE_FONT

logger = setup_logger(__name__)

# 获取中文字体名称
CHINESE_FONT = CHINESE_FONT
COLORS = COLOR_PALETTE
SECTION_CARD = get_card_style("section")


def _bind_label_text(widget, horizontal_padding=0):
    widget.bind(
        size=lambda inst, val: setattr(
            inst, "text_size", (max(0, val[0] - horizontal_padding), None)
        )
    )


class ChineseMDModalDatePicker(MDModalDatePicker):
    """Localized modal date picker with stable Chinese weekday labels."""

    WEEKDAY_SHORT_NAMES = {
        0: "一",
        1: "二",
        2: "三",
        3: "四",
        4: "五",
        5: "六",
        6: "日",
    }
    WEEKDAY_FULL_NAMES = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]

    def __init__(self, **kwargs):
        kwargs.setdefault("supporting_text", "选择日期")
        kwargs.setdefault("text_button_ok", "确定")
        kwargs.setdefault("text_button_cancel", "取消")
        super().__init__(**kwargs)

    def generate_list_widgets_days(self) -> None:
        calendar_list = []

        for day_index in self.calendar.iterweekdays():
            weekday_label = MDDatePickerWeekdayLabel(
                text=self.WEEKDAY_SHORT_NAMES.get(day_index, ""),
                date_picker=self,
            )
            if CHINESE_FONT:
                weekday_label.font_name = CHINESE_FONT
            self.calendar_layout.add_widget(weekday_label)

        for index in range(6 * 7):
            day_item = MDDatePickerDaySelectableItem(
                is_week_end=index % 7 == 6,
                date_picker=self,
            )
            if CHINESE_FONT:
                day_item.font_name = CHINESE_FONT
            calendar_list.append(day_item)
            self.calendar_layout.add_widget(day_item)

        self._calendar_list = calendar_list

    def set_text_full_date(self) -> str:
        if self.mode != "picker":
            return super().set_text_full_date()

        selected_date = date(self.sel_year, self.sel_month, self.sel_day)
        return (
            f"{self.WEEKDAY_FULL_NAMES[selected_date.weekday()]}，"
            f"{selected_date.month}月{selected_date.day}日"
        )

    def _update_date_label_text(self):
        self._current_month_name = self.set_text_full_date()
        self._current_full_month_name = f"{self.year}年{self.month}月"

    def on_open(self) -> None:
        super().on_open()
        if CHINESE_FONT:
            Clock.schedule_once(lambda *_: apply_font_to_widget(self, CHINESE_FONT), 0)


class FridgeTextInput(TextInput):
    """Rounded text input matching the fresh utility form style."""

    def __init__(self, hint_text="", is_multiline=False, **kwargs):
        super().__init__(**kwargs)
        self.multiline = is_multiline
        self.size_hint = (1, None)
        self.height = dp(52) if not is_multiline else dp(104)
        self.hint_text = hint_text
        self.background_normal = ""
        self.background_active = ""
        self.background_color = (0, 0, 0, 0)
        self.foreground_color = COLORS["text_primary"]
        self.cursor_color = COLORS["primary"]
        self.hint_text_color = COLORS["text_hint"]
        self.padding = (dp(14), dp(15), dp(14), dp(15))
        self.font_size = dp(get_font_size("body_large"))
        self.border = [0, 0, 0, 0]
        self.write_tab = False
        if CHINESE_FONT:
            self.font_name = CHINESE_FONT
        self.bind(pos=self._redraw, size=self._redraw, focus=self._redraw)

    def _redraw(self, *_args):
        radius = dp(14)
        fill = COLORS["surface"] if self.focus else COLORS["surface_variant"]
        outline = COLORS["primary"] if self.focus else COLORS["divider"]
        self.canvas.before.clear()
        self.canvas.after.clear()
        with self.canvas.before:
            Color(*fill)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        with self.canvas.after:
            Color(*outline)
            Line(
                width=dp(1),
                rounded_rectangle=(self.x, self.y, self.width, self.height, radius),
            )


class FridgeButton(Button):
    """Rounded button for selectors and bottom actions."""

    def __init__(self, variant="secondary", radius=14, **kwargs):
        self.variant = variant
        self._pressed = False
        self._radius = dp(radius)
        kwargs.setdefault("size_hint_y", None)
        kwargs.setdefault("height", dp(50))
        kwargs.setdefault("background_normal", "")
        kwargs.setdefault("background_down", "")
        kwargs.setdefault("background_color", (0, 0, 0, 0))
        kwargs.setdefault("font_size", dp(get_font_size("label_large")))
        super().__init__(**kwargs)
        self.valign = "middle"
        if CHINESE_FONT:
            self.font_name = CHINESE_FONT
        self.bind(pos=self._redraw, size=self._redraw)
        self.bind(size=self._update_text_size)
        self._update_text_size()
        self._redraw()

    def _palette(self):
        if self.variant == "primary":
            return (
                COLORS["primary_dark"] if self._pressed else COLORS["primary"],
                None,
                COLORS["on_primary"],
            )
        if self.variant == "tonal":
            return (
                COLORS["surface_tint"] if self._pressed else COLORS["primary_container"],
                COLORS["primary_container"],
                COLORS["on_primary_container"],
            )
        return (
            COLORS["surface_tint"] if self._pressed else COLORS["surface_variant"],
            COLORS["divider"],
            COLORS["text_primary"],
        )

    def _update_text_size(self, *_args):
        padding = dp(32) if self.halign == "left" else dp(20)
        self.text_size = (max(0, self.width - padding), self.height)

    def _redraw(self, *_args):
        fill, border, text_color = self._palette()
        self.color = text_color
        self.canvas.before.clear()
        self.canvas.after.clear()
        with self.canvas.before:
            Color(*fill)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[self._radius])
        if border:
            with self.canvas.after:
                Color(*border)
                Line(
                    width=dp(1),
                    rounded_rectangle=(
                        self.x,
                        self.y,
                        self.width,
                        self.height,
                        self._radius,
                    ),
                )

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._pressed = True
            self._redraw()
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._pressed:
            self._pressed = False
            self._redraw()
        return super().on_touch_up(touch)


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
        main_layout = BoxLayout(orientation='vertical')
        with main_layout.canvas.before:
            Color(*COLORS["background"])
            self.bg_rect = Rectangle(pos=main_layout.pos, size=main_layout.size)

        def update_bg_rect(instance, _value):
            self.bg_rect.pos = instance.pos
            self.bg_rect.size = instance.size

        main_layout.bind(pos=update_bg_rect, size=update_bg_rect)

        main_layout.add_widget(self._create_header())
        main_layout.add_widget(self._create_form_scroll())
        main_layout.add_widget(self._create_button_bar())

        self.add_widget(main_layout)

    def _create_header(self) -> BoxLayout:
        """创建头部栏"""
        header = BoxLayout(
            size_hint_y=None,
            height=dp(88),
            padding=(dp(12), dp(14), dp(16), dp(14)),
            spacing=dp(8),
        )
        with header.canvas.before:
            Color(*COLORS['surface'])
            self.header_bg_rect = Rectangle(pos=header.pos, size=header.size)
        with header.canvas.after:
            Color(*COLORS["divider"])
            self.header_divider = Line(points=[])
        header.bind(
            pos=lambda inst, val: setattr(self.header_bg_rect, 'pos', inst.pos),
            size=lambda inst, val: setattr(self.header_bg_rect, 'size', inst.size),
        )
        header.bind(pos=self._update_header_divider, size=self._update_header_divider)

        back_btn = MDIconButton(
            icon="arrow-left",
            on_release=self._on_back_click,
            font_name="Roboto",
        )
        header.add_widget(back_btn)

        title_box = BoxLayout(orientation="vertical", spacing=dp(2))
        title_label = Label(
            text="添加物品",
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("headline_small")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(title_label)
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        title_box.add_widget(title_label)

        subtitle_label = Label(
            text="快速记录库存、日期和提醒设置",
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(subtitle_label)
        if CHINESE_FONT:
            subtitle_label.font_name = CHINESE_FONT
        title_box.add_widget(subtitle_label)

        header.add_widget(title_box)

        return header

    def _create_form_scroll(self) -> ScrollView:
        """创建表单滚动区域"""
        scroll_view = ScrollView(do_scroll_x=False, bar_width=0)
        with scroll_view.canvas.before:
            Color(*COLORS["background"])
            scroll_bg_rect = Rectangle(pos=scroll_view.pos, size=scroll_view.size)

        def update_scroll_bg(instance, _value):
            scroll_bg_rect.pos = instance.pos
            scroll_bg_rect.size = instance.size

        scroll_view.bind(pos=update_scroll_bg, size=update_scroll_bg)

        form_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=dp(16),
            spacing=dp(14),
        )
        form_layout.bind(minimum_height=form_layout.setter("height"))

        form_layout.add_widget(self._create_basic_info_card())
        form_layout.add_widget(self._create_quantity_card())
        form_layout.add_widget(self._create_date_card())
        form_layout.add_widget(self._create_options_card())
        form_layout.add_widget(BoxLayout(size_hint_y=None, height=dp(8)))

        scroll_view.add_widget(form_layout)
        return scroll_view

    def _update_header_divider(self, instance, _value):
        self.header_divider.points = [instance.x, instance.y, instance.right, instance.y]

    def _create_section_card(self, title: str, icon: str, subtitle: str | None = None):
        card = MDCard(
            size_hint_y=None,
            padding=0,
            radius=[dp(SECTION_CARD["radius"])] * 4,
            style="elevated",
            md_bg_color=COLORS[SECTION_CARD["background"]],
        )
        content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(SECTION_CARD["gap"]),
            padding=dp(SECTION_CARD["padding"]),
        )
        content.bind(minimum_height=content.setter("height"))
        content.bind(height=lambda inst, val: setattr(card, "height", val))

        header = BoxLayout(size_hint_y=None, height=dp(40), spacing=dp(12))
        icon_box = BoxLayout(size_hint=(None, None), width=dp(36), height=dp(36))
        with icon_box.canvas.before:
            Color(*COLORS["primary_container"])
            icon_box._bg = RoundedRectangle(
                pos=icon_box.pos, size=icon_box.size, radius=[dp(12)]
            )
        icon_box.bind(
            pos=lambda inst, _val: setattr(inst._bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(inst._bg, "size", inst.size),
        )
        icon_widget = MDIcon(
            icon=icon,
            halign="center",
            valign="middle",
            font_size=dp(18),
        )
        icon_widget.color = COLORS["primary"]
        icon_box.add_widget(icon_widget)
        header.add_widget(icon_box)

        text_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(0))
        text_box.bind(minimum_height=text_box.setter("height"))
        text_box.bind(
            minimum_height=lambda inst, val: setattr(header, "height", max(dp(38), val))
        )
        title_label = Label(
            text=title,
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_medium")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(title_label)
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        text_box.add_widget(title_label)

        if subtitle:
            text_box.spacing = dp(2)
            subtitle_label = Label(
                text=subtitle,
                size_hint_y=None,
                height=dp(18),
                halign="left",
                valign="middle",
                font_size=dp(get_font_size("body_small")),
                color=COLORS["text_secondary"],
            )
            _bind_label_text(subtitle_label)
            if CHINESE_FONT:
                subtitle_label.font_name = CHINESE_FONT
            text_box.add_widget(subtitle_label)

        header.add_widget(text_box)
        content.add_widget(header)

        body = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(12))
        body.bind(minimum_height=body.setter("height"))
        content.add_widget(body)
        card.add_widget(content)
        self._apply_card_outline(card, SECTION_CARD["radius"])
        return card, body

    def _apply_card_outline(self, widget, radius):
        with widget.canvas.after:
            Color(*COLORS["divider"])
            widget._outline = Line(width=dp(1), rounded_rectangle=(0, 0, 0, 0, dp(radius)))

        def _update_outline(instance, _value):
            widget._outline.rounded_rectangle = (
                instance.x,
                instance.y,
                instance.width,
                instance.height,
                dp(radius),
            )

        widget.bind(pos=_update_outline, size=_update_outline)
        _update_outline(widget, None)

    def _create_field_label(self, text: str, required: bool = False) -> Label:
        label = Label(
            text=f"{text} *" if required else text,
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("label_large")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(label)
        if CHINESE_FONT:
            label.font_name = CHINESE_FONT
        return label

    def _create_field_block(self, title: str, widget, required: bool = False):
        block = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        block.bind(minimum_height=block.setter("height"))
        block.add_widget(self._create_field_label(title, required=required))
        block.add_widget(widget)
        return block

    def _create_hint_container(self, text: str, tone: str = "secondary") -> BoxLayout:
        container = BoxLayout(size_hint_y=None, height=dp(44), padding=(dp(12), 0))
        fill = COLORS["info_container"] if tone == "secondary" else COLORS["warning_container"]
        text_color = COLORS["secondary_dark"] if tone == "secondary" else COLORS["warning_dark"]
        with container.canvas.before:
            Color(*fill)
            container._bg = RoundedRectangle(
                pos=container.pos, size=container.size, radius=[dp(14)]
            )
        container.bind(
            pos=lambda inst, _val: setattr(inst._bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(inst._bg, "size", inst.size),
        )
        hint = Label(
            text=text,
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=text_color,
        )
        _bind_label_text(hint, horizontal_padding=dp(8))
        if CHINESE_FONT:
            hint.font_name = CHINESE_FONT
        container.add_widget(hint)
        return container

    def _create_basic_info_card(self) -> MDCard:
        """创建基本信息卡片"""
        card, body = self._create_section_card(
            "基本信息",
            "information-outline",
        )

        self.name_input = FridgeTextInput(hint_text="例如：鲜牛奶")
        body.add_widget(self._create_field_block("物品名称", self.name_input, required=True))

        self.category_button = FridgeButton(
            text="食品",
            variant="tonal",
            halign="left",
            on_release=self._show_category_menu,
        )
        body.add_widget(self._create_field_block("物品类别", self.category_button, required=True))

        self.desc_input = FridgeTextInput(
            hint_text="可选。例如：低温鲜奶、适合早餐。",
            is_multiline=True,
        )
        body.add_widget(self._create_field_block("补充说明", self.desc_input))
        return card

    def _create_quantity_card(self) -> MDCard:
        """创建数量卡片"""
        card, body = self._create_section_card(
            "数量与单位",
            "scale-balance",
        )

        quantity_block = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        quantity_block.bind(minimum_height=quantity_block.setter("height"))
        quantity_block.add_widget(self._create_field_label("库存数量"))

        quantity_row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(10))
        self.quantity_input = FridgeTextInput(text="1", input_filter="int")
        quantity_row.add_widget(self.quantity_input)

        decrease_btn = FridgeButton(
            text="-",
            size_hint=(None, None),
            width=dp(48),
            height=dp(48),
            font_size=dp(20),
            on_release=lambda _x: self._change_quantity(-1),
        )
        quantity_row.add_widget(decrease_btn)

        increase_btn = FridgeButton(
            text="+",
            size_hint=(None, None),
            width=dp(48),
            height=dp(48),
            font_size=dp(20),
            on_release=lambda _x: self._change_quantity(1),
        )
        quantity_row.add_widget(increase_btn)
        quantity_block.add_widget(quantity_row)
        body.add_widget(quantity_block)

        self.unit_input = FridgeTextInput(hint_text="例如：个、盒、瓶")
        body.add_widget(self._create_field_block("单位", self.unit_input))
        return card

    def _create_date_card(self) -> MDCard:
        """创建日期卡片"""
        card, body = self._create_section_card(
            "日期信息",
            "calendar-month-outline",
        )

        self.purchase_date_button = FridgeButton(
            text="点击选择日期",
            halign="left",
            on_release=lambda _x: self._show_date_picker("purchase"),
        )
        body.add_widget(self._create_field_block("购买日期", self.purchase_date_button))

        self.expiry_date_button = FridgeButton(
            text="点击选择日期",
            halign="left",
            on_release=lambda _x: self._show_date_picker("expiry"),
        )
        body.add_widget(self._create_field_block("过期日期", self.expiry_date_button))
        body.add_widget(self._create_hint_container("填写过期日期后，可用于首页筛选和过期提醒。", tone="warning"))
        return card

    def _create_options_card(self) -> MDCard:
        """创建选项卡片"""
        card, body = self._create_section_card(
            "附加选项",
            "tune-variant",
        )

        reminder_row = BoxLayout(size_hint_y=None, height=dp(52), spacing=dp(12))
        reminder_text = BoxLayout(orientation="vertical", spacing=dp(2))
        reminder_title = Label(
            text="启用过期提醒",
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_medium")),
            color=COLORS["text_primary"],
        )
        _bind_label_text(reminder_title)
        if CHINESE_FONT:
            reminder_title.font_name = CHINESE_FONT
        reminder_text.add_widget(reminder_title)

        reminder_hint = Label(
            text="需要结合过期日期一起使用。",
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(reminder_hint)
        if CHINESE_FONT:
            reminder_hint.font_name = CHINESE_FONT
        reminder_text.add_widget(reminder_hint)
        reminder_row.add_widget(reminder_text)

        self.reminder_checkbox = MDCheckbox(
            size_hint=(None, None),
            width=dp(40),
            height=dp(40),
            active=True,
            on_active=self._on_reminder_toggle,
        )
        reminder_row.add_widget(self.reminder_checkbox)
        body.add_widget(reminder_row)

        self.tag_input = FridgeTextInput(hint_text="用逗号分隔，例如：生鲜, 早餐")
        body.add_widget(self._create_field_block("标签", self.tag_input))
        return card

    def _create_button_bar(self) -> BoxLayout:
        """创建按钮栏"""
        button_bar = BoxLayout(
            size_hint_y=None,
            height=dp(84),
            padding=(dp(16), dp(12), dp(16), dp(16)),
            spacing=dp(10),
        )
        with button_bar.canvas.before:
            Color(*COLORS["surface"])
            button_bar._bg = Rectangle(pos=button_bar.pos, size=button_bar.size)
        with button_bar.canvas.after:
            Color(*COLORS["divider"])
            button_bar._line = Line(points=[])
        button_bar.bind(
            pos=lambda inst, _val: setattr(inst._bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(inst._bg, "size", inst.size),
        )
        button_bar.bind(pos=self._update_footer_divider, size=self._update_footer_divider)

        cancel_btn = FridgeButton(
            text="取消",
            size_hint_x=0.38,
            on_release=self._on_cancel_click,
        )
        button_bar.add_widget(cancel_btn)

        submit_btn = FridgeButton(
            text="添加到库存",
            variant="primary",
            size_hint_x=0.6,
            on_release=self._on_submit_click,
        )
        button_bar.add_widget(submit_btn)

        return button_bar

    def _update_footer_divider(self, instance, _value):
        instance._line.points = [instance.x, instance.top, instance.right, instance.top]

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

        dialog = ModalView(
            size_hint=(0.8, None),
            height=dp(332),
            auto_dismiss=True,
        )

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(12),
            size_hint=(1, None),
            height=dp(332),
        )
        self._decorate_modal_panel(root)

        title_label = Label(
            text="选择类别",
            size_hint_y=None,
            height=dp(32),
            halign="left",
            valign="middle",
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(title_label)
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        root.add_widget(title_label)

        for text, category in self._category_items:
            def _on_select(_btn_instance, cat=category, dlg=dialog):
                self._select_category(cat)
                dlg.dismiss()

            btn = FridgeButton(
                text=text,
                halign="left",
                variant="secondary",
                height=dp(46),
                on_release=_on_select,
            )
            root.add_widget(btn)

        dialog.add_widget(root)
        dialog.open()

    def _select_category(self, category: str):
        """选择类别"""
        category_map = {
            "食品": "食品",
            "日用品": "日用品",
            "药品": "药品",
            "化妆品": "化妆品",
            "其他": "其他",
        }
        if hasattr(self, "category_button"):
            self.category_button.text = category_map.get(category, "食品")
        self.form_data['category'] = category

    def _show_date_picker(self, date_type: str):
        """显示日期选择器"""
        from datetime import date
        today = date.today()
        self.date_picker = ChineseMDModalDatePicker(
            year=today.year,
            month=today.month,
            day=today.day,
        )

        self.date_picker.bind(
            # 点击 OK 时回调；使用 *args 兼容不同版本的事件参数
            on_ok=lambda instance, *args, dt=date_type: self._on_date_ok(
                instance, *args, date_type=dt
            ),
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
                self._apply_font_to_date_picker_ids(picker_instance, font_name)
        except Exception:
            # 字体应用失败时静默忽略，不影响功能
            pass

    def _configure_date_picker(self, picker_instance):
        """Apply localization and fonts after picker widgets exist."""
        self._localize_date_picker(picker_instance)
        self._apply_font_to_date_picker(picker_instance)

    def _schedule_date_picker_refresh(self, picker_instance):
        """Refresh the picker after KivyMD finishes its internal open-time updates."""
        delays = (0, 0.03, 0.08, 0.16)
        for delay in delays:
            Clock.schedule_once(
                lambda *_args, inst=picker_instance: self._configure_date_picker(inst),
                delay,
            )

    def _apply_font_to_date_picker_ids(self, picker_instance, font_name):
        """Set font on key KivyMD date picker labels that rely on theme styles."""
        ids = getattr(picker_instance, "ids", None)
        if not ids:
            return

        for key in ("supporting_label", "current_month_name"):
            widget = ids.get(key)
            if widget is not None and hasattr(widget, "font_name"):
                widget.font_name = font_name

        year_selection_items = ids.get("year_selection_items")
        if year_selection_items is not None:
            year_label = year_selection_items.ids.get("label")
            if year_label is not None and hasattr(year_label, "font_name"):
                year_label.font_name = font_name

    def _localize_date_picker(self, picker_instance):
        """Replace unstable locale defaults with readable Chinese text."""
        if picker_instance is None:
            return

        picker_instance.supporting_text = "选择日期"
        picker_instance.text_button_ok = "确定"
        picker_instance.text_button_cancel = "取消"
        picker_instance._current_month_name = self._format_date_picker_title(
            picker_instance
        )
        picker_instance._current_full_month_name = (
            f"{picker_instance.year}年{picker_instance.month}月"
        )
        self._localize_date_picker_weekdays(picker_instance)

    def _format_date_picker_title(self, picker_instance) -> str:
        selected = date(
            picker_instance.sel_year,
            picker_instance.sel_month,
            picker_instance.sel_day,
        )
        weekday_names = ["周一", "周二", "周三", "周四", "周五", "周六", "周日"]
        return f"{weekday_names[selected.weekday()]}，{selected.month}月{selected.day}日"

    def _localize_date_picker_weekdays(self, picker_instance):
        weekday_labels = [
            widget
            for widget in picker_instance.calendar_layout.children
            if type(widget).__name__ == "MDDatePickerWeekdayLabel"
        ]
        if not weekday_labels:
            return

        weekday_short_names = {
            0: "一",
            1: "二",
            2: "三",
            3: "四",
            4: "五",
            5: "六",
            6: "日",
        }
        ordered_days = list(picker_instance.calendar.iterweekdays())
        for widget, day_index in zip(reversed(weekday_labels), ordered_days):
            widget.text = weekday_short_names.get(day_index, "")

    def _on_date_selected(self, selected_date, date_type: str):
        """日期选择回调"""
        date_str = selected_date.strftime('%Y-%m-%d')

        if date_type == 'purchase':
            if hasattr(self, 'purchase_date_button'):
                self.purchase_date_button.text = date_str
            self.form_data['purchase_date'] = selected_date
        else:  # expiry
            if hasattr(self, 'expiry_date_button'):
                self.expiry_date_button.text = date_str
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

        dialog = ModalView(size_hint=(0.82, None), height=dp(220), auto_dismiss=True)

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(16),
            size_hint=(1, None),
            height=dp(220),
        )
        self._decorate_modal_panel(root)

        title_label = Label(
            text=title,
            size_hint_y=None,
            height=dp(32),
            halign="left",
            valign="middle",
            bold=True,
            color=COLORS["error_dark"],
        )
        _bind_label_text(title_label)
        msg_label = Label(
            text=message,
            size_hint_y=1,
            halign="left",
            valign="top",
            color=COLORS["text_secondary"],
            font_size=dp(get_font_size("body_medium")),
        )
        msg_label.bind(
            size=lambda inst, val: setattr(inst, "text_size", (val[0], None))
        )
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
            msg_label.font_name = CHINESE_FONT

        root.add_widget(title_label)
        root.add_widget(msg_label)

        btn_bar = BoxLayout(
            size_hint_y=None,
            height=dp(48),
            padding=(0, dp(8), 0, 0),
            spacing=dp(12),
        )
        btn_bar.add_widget(BoxLayout())  # 占位，让按钮靠右

        ok_btn = FridgeButton(
            text="确定",
            size_hint=(None, None),
            width=dp(96),
            height=dp(44),
            on_release=lambda _x: dialog.dismiss(),
        )
        btn_bar.add_widget(ok_btn)

        root.add_widget(btn_bar)
        dialog.add_widget(root)
        dialog.open()

    def _show_success_dialog(self, item):
        """显示成功对话框（自定义 ModalView，兼容 KivyMD 2.0）"""
        from kivy.uix.modalview import ModalView

        dialog = ModalView(size_hint=(0.84, None), height=dp(236), auto_dismiss=True)

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(16),
            size_hint=(1, None),
            height=dp(236),
        )
        self._decorate_modal_panel(root)

        title_label = Label(
            text="添加成功",
            size_hint_y=None,
            height=dp(32),
            halign="left",
            valign="middle",
            bold=True,
            color=COLORS["success_dark"],
        )
        _bind_label_text(title_label)
        msg_label = Label(
            text=f"物品 '{item.name}' 已成功添加",
            size_hint_y=1,
            halign="left",
            valign="top",
            color=COLORS["text_secondary"],
            font_size=dp(get_font_size("body_medium")),
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

        continue_btn = FridgeButton(
            text="继续添加",
            size_hint_x=0.5,
            on_release=_on_continue,
        )

        back_btn = FridgeButton(
            text="返回主页",
            variant="primary",
            size_hint_x=0.5,
            on_release=_on_back,
        )

        btn_bar.add_widget(continue_btn)
        btn_bar.add_widget(back_btn)

        root.add_widget(btn_bar)
        dialog.add_widget(root)
        dialog.open()

    def _decorate_modal_panel(self, widget):
        with widget.canvas.before:
            Color(*COLORS["surface"])
            widget._modal_bg = RoundedRectangle(
                pos=widget.pos, size=widget.size, radius=[dp(20)]
            )
        with widget.canvas.after:
            Color(*COLORS["divider"])
            widget._modal_outline = Line(width=dp(1), rounded_rectangle=(0, 0, 0, 0, dp(20)))

        def _update_panel(instance, _value):
            instance._modal_bg.pos = instance.pos
            instance._modal_bg.size = instance.size
            instance._modal_outline.rounded_rectangle = (
                instance.x,
                instance.y,
                instance.width,
                instance.height,
                dp(20),
            )

        widget.bind(pos=_update_panel, size=_update_panel)
        _update_panel(widget, None)

    def _reset_form(self, instance=None):
        """重置表单"""
        # 重置输入字段
        self.name_input.text = ""
        self.desc_input.text = ""
        self.quantity_input.text = "1"
        self.unit_input.text = ""
        self.tag_input.text = ""

        # 重置按钮文本
        if hasattr(self, "purchase_date_button"):
            self.purchase_date_button.text = "点击选择日期"
        if hasattr(self, "expiry_date_button"):
            self.expiry_date_button.text = "点击选择日期"

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
        if hasattr(self, "category_button"):
            self.category_button.text = "食品"

        # 重置提醒 checkbox，修复表单重置后 UI 状态与数据不一致问题
        if hasattr(self, "reminder_checkbox"):
            self.reminder_checkbox.active = True

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
            try:
                self.date_picker.dismiss()
            except Exception:
                pass
            self.date_picker = None


# 测试代码
if __name__ == '__main__':
    from kivy.app import App as KivyApp

    class TestApp(KivyApp):
        def build(self):
            return AddItemScreen()

    TestApp().run()
