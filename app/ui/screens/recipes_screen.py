# -*- coding: utf-8 -*-
"""
食谱屏幕
"""

from datetime import date, timedelta

from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivymd.uix.label import MDIcon

from app.services.item_service import item_service
from app.models.item import ItemStatus
from app.ui.theme.design_tokens import COLOR_PALETTE, get_card_style, get_font_size
from app.utils.font_helper import CHINESE_FONT_NAME as CHINESE_FONT
from app.utils.font_helper import apply_font_to_widget

COLORS = COLOR_PALETTE
LIST_CARD = get_card_style("list")


def _bind_label_text(widget, horizontal_padding=0):
    widget.bind(
        size=lambda inst, val: setattr(
            inst, "text_size", (max(0, val[0] - horizontal_padding), None)
        )
    )


class MetricTile(BoxLayout):
    def __init__(self, icon, title, accent, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(14)
        self.spacing = dp(6)
        self._accent = accent
        self.size_hint = (1, 1)
        self._value_label = None
        self._build_ui(icon, title)
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _build_ui(self, icon, title):
        icon_row = BoxLayout(size_hint_y=None, height=dp(28))
        icon_row.add_widget(
            MDIcon(
                icon=icon,
                theme_text_color="Custom",
                text_color=self._accent,
                halign="left",
                valign="middle",
                font_size=dp(20),
            )
        )
        self.add_widget(icon_row)

        self._value_label = Label(
            text="0",
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("headline_small")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(self._value_label)
        if CHINESE_FONT:
            self._value_label.font_name = CHINESE_FONT
        self.add_widget(self._value_label)

        title_label = Label(
            text=title,
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(title_label)
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        self.add_widget(title_label)

    def set_value(self, text):
        self._value_label.text = text

    def _redraw(self, *_args):
        radius = dp(LIST_CARD["radius"])
        self.canvas.before.clear()
        self.canvas.after.clear()
        with self.canvas.before:
            Color(*COLORS["surface"])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        with self.canvas.after:
            Color(*COLORS["divider"])
            Line(
                width=dp(1),
                rounded_rectangle=(self.x, self.y, self.width, self.height, radius),
            )


class RecipeCard(BoxLayout):
    def __init__(self, title, description, time_text, difficulty, ingredients, accent, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.size_hint_y = None
        self.height = dp(168)
        self.padding = dp(LIST_CARD["padding"])
        self.spacing = dp(10)
        self._accent = accent
        self._build_ui(title, description, time_text, difficulty, ingredients)
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _build_ui(self, title, description, time_text, difficulty, ingredients):
        header = BoxLayout(size_hint_y=None, height=dp(24))
        title_label = Label(
            text=title,
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_medium")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(title_label)
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        header.add_widget(title_label)
        self.add_widget(header)

        desc_label = Label(
            text=description,
            size_hint_y=None,
            height=dp(40),
            halign="left",
            valign="top",
            font_size=dp(get_font_size("body_medium")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(desc_label)
        if CHINESE_FONT:
            desc_label.font_name = CHINESE_FONT
        self.add_widget(desc_label)

        meta_row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))
        meta_row.add_widget(self._create_chip(time_text, COLORS["surface_cool"], COLORS["secondary"]))
        meta_row.add_widget(self._create_chip(difficulty, COLORS["surface_warm"], COLORS["accent"]))
        meta_row.add_widget(BoxLayout())
        self.add_widget(meta_row)

        ingredients_title = Label(
            text="推荐食材",
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("label_medium")),
            color=self._accent,
        )
        _bind_label_text(ingredients_title)
        if CHINESE_FONT:
            ingredients_title.font_name = CHINESE_FONT
        self.add_widget(ingredients_title)

        ingredients_label = Label(
            text=ingredients,
            halign="left",
            valign="top",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(ingredients_label)
        if CHINESE_FONT:
            ingredients_label.font_name = CHINESE_FONT
        self.add_widget(ingredients_label)

    def _create_chip(self, text, bg_color, text_color):
        chip = Label(
            text=text,
            size_hint=(None, None),
            width=max(dp(74), dp(18) + len(text) * dp(8)),
            height=dp(28),
            halign="center",
            valign="middle",
            font_size=dp(get_font_size("label_medium")),
            color=text_color,
        )
        chip.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        if CHINESE_FONT:
            chip.font_name = CHINESE_FONT
        with chip.canvas.before:
            Color(*bg_color)
            bg = RoundedRectangle(pos=chip.pos, size=chip.size, radius=[dp(14)])
        chip.bind(
            pos=lambda inst, _val: setattr(bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(bg, "size", inst.size),
        )
        return chip

    def _redraw(self, *_args):
        radius = dp(LIST_CARD["radius"])
        self.canvas.before.clear()
        self.canvas.after.clear()
        with self.canvas.before:
            Color(*COLORS["surface"])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        with self.canvas.after:
            Color(*COLORS["divider"])
            Line(
                width=dp(1),
                rounded_rectangle=(self.x, self.y, self.width, self.height, radius),
            )


class RecipesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "recipes"
        self.ingredient_card = None
        self.recipe_card = None
        self.expiring_card = None
        self._build_ui()

    def _build_ui(self):
        root = BoxLayout(orientation="vertical")
        with root.canvas.before:
            Color(*COLORS["background"])
            self._bg_rect = Rectangle(pos=root.pos, size=root.size)
        root.bind(
            pos=lambda inst, _val: setattr(self._bg_rect, "pos", inst.pos),
            size=lambda inst, _val: setattr(self._bg_rect, "size", inst.size),
        )

        root.add_widget(self._create_header())

        scroll = ScrollView(
            do_scroll_x=False,
            bar_width=dp(3),
            bar_color=(*COLORS["primary"][:3], 0.25),
            bar_inactive_color=(*COLORS["primary"][:3], 0.1),
        )
        content = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=(dp(16), dp(14), dp(16), dp(24)),
            spacing=dp(14),
        )
        content.bind(minimum_height=content.setter("height"))

        content.add_widget(self._create_metrics_row())
        content.add_widget(self._create_section_title())

        for recipe in self._sample_recipes():
            content.add_widget(RecipeCard(**recipe))

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _create_header(self):
        header = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(92),
            padding=(dp(20), dp(18), dp(20), dp(12)),
            spacing=dp(2),
        )
        with header.canvas.before:
            Color(*COLORS["surface"])
            self._header_bg = Rectangle(pos=header.pos, size=header.size)
        with header.canvas.after:
            Color(*COLORS["divider"])
            self._header_divider = Line(points=[])
        header.bind(
            pos=lambda inst, _val: setattr(self._header_bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(self._header_bg, "size", inst.size),
        )
        header.bind(pos=self._update_header_divider, size=self._update_header_divider)

        title = Label(
            text="食谱推荐",
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("headline_small")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(title)
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        header.add_widget(title)

        subtitle = Label(
            text="根据库存情况组织可做菜谱和即将过期食材。",
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_medium")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(subtitle)
        if CHINESE_FONT:
            subtitle.font_name = CHINESE_FONT
        header.add_widget(subtitle)
        return header

    def _create_metrics_row(self):
        row = BoxLayout(size_hint_y=None, height=dp(112), spacing=dp(10))
        self.ingredient_card = MetricTile(
            icon="food-apple",
            title="可用食材",
            accent=COLORS["primary"],
        )
        self.recipe_card = MetricTile(
            icon="silverware-fork-knife",
            title="可做菜谱",
            accent=COLORS["secondary"],
        )
        self.expiring_card = MetricTile(
            icon="clock-alert-outline",
            title="3 天内过期",
            accent=COLORS["warning"],
        )
        row.add_widget(self.ingredient_card)
        row.add_widget(self.recipe_card)
        row.add_widget(self.expiring_card)
        return row

    def _create_section_title(self):
        box = BoxLayout(orientation="vertical", size_hint_y=None, height=dp(22), spacing=dp(0))

        title = Label(
            text="推荐菜谱",
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_medium")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(title)
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        box.add_widget(title)
        return box

    def _sample_recipes(self):
        return [
            {
                "title": "番茄炒蛋",
                "description": "高频家常菜，适合把即将过熟的番茄和鸡蛋快速消耗掉。",
                "time_text": "15 分钟",
                "difficulty": "简单",
                "ingredients": "番茄、鸡蛋、葱、少量糖和盐",
                "accent": COLORS["primary"],
            },
            {
                "title": "蒜蓉西兰花",
                "description": "清爽快炒，适合把短保蔬菜优先处理，降低蔫掉浪费。",
                "time_text": "10 分钟",
                "difficulty": "简单",
                "ingredients": "西兰花、蒜、盐、少量食用油",
                "accent": COLORS["secondary"],
            },
            {
                "title": "蛋花汤",
                "description": "适合库存较少时的补位菜谱，准备时间短，容错率高。",
                "time_text": "12 分钟",
                "difficulty": "中等",
                "ingredients": "鸡蛋、紫菜、葱花、白胡椒",
                "accent": COLORS["accent"],
            },
            {
                "title": "蛋炒饭",
                "description": "优先利用剩饭和零散配菜，适合作为库存清理型菜谱。",
                "time_text": "8 分钟",
                "difficulty": "简单",
                "ingredients": "米饭、鸡蛋、葱花、冷藏剩菜",
                "accent": COLORS["primary"],
            },
        ]

    def _update_header_divider(self, instance, _value):
        self._header_divider.points = [instance.x, instance.y, instance.right, instance.y]

    def _load_real_stats(self):
        try:
            active_items = item_service.get_items(status=ItemStatus.ACTIVE)
            ingredient_names = set()
            expiring_count = 0

            today = date.today()
            threshold = today + timedelta(days=3)

            for item in active_items:
                ingredient_names.add(item.name)
                if item.expiry_date and today <= item.expiry_date <= threshold:
                    expiring_count += 1

            recipe_count = max(0, len(ingredient_names) // 2)
            self.ingredient_card.set_value(f"{len(ingredient_names)} 种")
            self.recipe_card.set_value(f"{recipe_count} 道")
            self.expiring_card.set_value(f"{expiring_count} 种")
        except Exception:
            self.ingredient_card.set_value("0 种")
            self.recipe_card.set_value("0 道")
            self.expiring_card.set_value("0 种")

    def on_enter(self):
        if CHINESE_FONT:
            apply_font_to_widget(self, CHINESE_FONT)
        self._load_real_stats()
