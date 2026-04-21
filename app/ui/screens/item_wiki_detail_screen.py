from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import NumericProperty, StringProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.image import AsyncImage
from kivy.uix.label import Label
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivymd.app import MDApp
from kivymd.uix.label import MDIcon

import logging
import os

from app.services.item_service import item_service
from app.services.wiki_service import wiki_service
from app.ui.theme.design_tokens import COLOR_PALETTE, get_card_style, get_font_size
from app.utils.font_helper import CHINESE_FONT_NAME as CHINESE_FONT

logger = logging.getLogger(__name__)

COLORS = COLOR_PALETTE
HERO_CARD = get_card_style("hero")
LIST_CARD = get_card_style("list")
SECTION_CARD = get_card_style("section")


def _bind_label_text(widget, horizontal_padding=0):
    widget.bind(
        size=lambda inst, val: setattr(
            inst, "text_size", (max(0, val[0] - horizontal_padding), None)
        )
    )


def _bind_auto_height(widget, min_height):
    widget.size_hint_y = None
    widget.height = min_height
    widget.bind(
        texture_size=lambda inst, val: setattr(
            inst, "height", max(min_height, val[1] or min_height)
        )
    )


class SurfaceButton(ButtonBehavior, BoxLayout):
    __events__ = ("on_release",)

    def __init__(self, text="", icon=None, variant="tonal", compact=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint = (None, None)
        self.height = dp(40 if compact else 44)
        self.width = dp(44 if compact and not text else 108)
        self.padding = (dp(10), dp(10))
        self.spacing = dp(6)
        self._pressed = False
        self._variant = variant

        if icon:
            self.add_widget(
                MDIcon(
                    icon=icon,
                    theme_text_color="Custom",
                    text_color=self._text_color(),
                    size_hint=(None, None),
                    size=(dp(18), dp(18)),
                    font_size=dp(18),
                )
            )

        if text:
            label = Label(
                text=text,
                halign="center",
                valign="middle",
                font_size=dp(get_font_size("label_large")),
                color=self._text_color(),
            )
            label.bind(size=lambda inst, val: setattr(inst, "text_size", val))
            if CHINESE_FONT:
                label.font_name = CHINESE_FONT
            self.add_widget(label)

        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _fill_color(self):
        if self._variant == "primary":
            return COLORS["primary_dark"] if self._pressed else COLORS["primary"]
        if self._variant == "surface":
            return COLORS["surface_tint"] if self._pressed else COLORS["surface"]
        return COLORS["surface_tint"] if self._pressed else COLORS["primary_container"]

    def _text_color(self):
        if self._variant == "primary":
            return COLORS["on_primary"]
        if self._variant == "surface":
            return COLORS["text_primary"]
        return COLORS["on_primary_container"]

    def _border_color(self):
        return None if self._variant == "primary" else COLORS["divider"]

    def _redraw(self, *_args):
        radius = dp(16)
        text_color = self._text_color()
        for child in self.children:
            if isinstance(child, Label):
                child.color = text_color
            elif isinstance(child, MDIcon):
                child.text_color = text_color

        self.canvas.before.clear()
        self.canvas.after.clear()
        with self.canvas.before:
            Color(*self._fill_color())
            RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        border = self._border_color()
        if border:
            with self.canvas.after:
                Color(*border)
                Line(
                    width=dp(1),
                    rounded_rectangle=(self.x, self.y, self.width, self.height, radius),
                )

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._pressed = True
            self._redraw()
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        should_dispatch = self._pressed and self.collide_point(*touch.pos)
        self._pressed = False
        self._redraw()
        if should_dispatch:
            self.dispatch("on_release")
            return True
        return super().on_touch_up(touch)

    def on_release(self, *_args):
        pass


class InventoryListItem(ButtonBehavior, BoxLayout):
    """库存列表项"""

    def __init__(self, inventory_item, **kwargs):
        super().__init__(**kwargs)
        self.inventory_id = inventory_item.id
        self.item_name = inventory_item.name
        self.quantity = inventory_item.quantity
        self.unit = inventory_item.unit or ""
        self.production_date = (
            inventory_item.purchase_date.strftime("%Y-%m-%d")
            if inventory_item.purchase_date
            else ""
        )
        self.expiry_date = (
            inventory_item.expiry_date.strftime("%Y-%m-%d")
            if inventory_item.expiry_date
            else ""
        )
        self.status = inventory_item.status.value if inventory_item.status else ""
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(86)
        self.padding = (dp(14), dp(12), dp(14), dp(12))
        self.spacing = dp(12)
        self._pressed = False
        self._build_ui()
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _build_ui(self):
        icon_shell = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=dp(40),
            height=dp(40),
            padding=dp(8),
        )
        with icon_shell.canvas.before:
            Color(*COLORS["surface_tint"])
            self._icon_bg = RoundedRectangle(
                pos=icon_shell.pos, size=icon_shell.size, radius=[dp(14)]
            )
        icon_shell.bind(
            pos=lambda inst, _val: setattr(self._icon_bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(self._icon_bg, "size", inst.size),
        )
        icon_shell.add_widget(
            MDIcon(
                icon="package-variant-closed",
                theme_text_color="Custom",
                text_color=COLORS["primary"],
                halign="center",
                valign="middle",
                font_size=dp(20),
            )
        )
        self.add_widget(icon_shell)

        text_box = BoxLayout(orientation="vertical", spacing=dp(4))

        headline = Label(
            text=f"{self.item_name} ×{self.quantity}{self.unit}",
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_small")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(headline)
        if CHINESE_FONT:
            headline.font_name = CHINESE_FONT
        text_box.add_widget(headline)

        meta_parts = []
        if self.production_date:
            meta_parts.append(f"购买 {self.production_date}")
        if self.expiry_date:
            meta_parts.append(f"过期 {self.expiry_date}")
        meta = " · ".join(meta_parts) if meta_parts else "暂无日期信息"
        meta_label = Label(
            text=meta,
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(meta_label)
        if CHINESE_FONT:
            meta_label.font_name = CHINESE_FONT
        text_box.add_widget(meta_label)

        status_label = Label(
            text=f"状态：{self.status or 'active'}",
            halign="left",
            valign="top",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["primary"],
        )
        _bind_label_text(status_label)
        if CHINESE_FONT:
            status_label.font_name = CHINESE_FONT
        text_box.add_widget(status_label)
        self.add_widget(text_box)

        self.add_widget(
            MDIcon(
                icon="chevron-right",
                theme_text_color="Custom",
                text_color=COLORS["text_hint"],
                size_hint=(None, None),
                size=(dp(18), dp(18)),
                font_size=dp(18),
            )
        )

    def _redraw(self, *_args):
        radius = dp(LIST_CARD["radius"])
        bg_color = COLORS["surface_tint"] if self._pressed else COLORS["surface"]
        self.canvas.before.clear()
        self.canvas.after.clear()
        with self.canvas.before:
            Color(*bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        with self.canvas.after:
            Color(*COLORS["divider"])
            Line(
                width=dp(1),
                rounded_rectangle=(self.x, self.y, self.width, self.height, radius),
            )

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._pressed = True
            self._redraw()
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        should_open = self._pressed and self.collide_point(*touch.pos)
        self._pressed = False
        self._redraw()
        if should_open:
            app = MDApp.get_running_app()
            if hasattr(app, "screen_manager"):
                app.screen_manager.current = "item_detail"
                detail = app.screen_manager.get_screen("item_detail")
                if detail:
                    detail.item_id = self.inventory_id
                    detail._load_item(self.inventory_id)
            return True
        return super().on_touch_up(touch)


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
        self.item_icon = ""
        self._inventory_items = []
        self._item_image = None
        self._image_fallback = None
        self._name_label = None
        self._category_chip = None
        self._unit_chip = None
        self._quantity_label = None
        self._inventory_count_chip = None
        self._summary_meta_label = None
        self._summary_hint_label = None
        self._description_label = None
        self._inventory_list_box = None
        self._stock_metric_value = None
        self._batch_metric_value = None
        self._stock_metric_tile = None
        self._batch_metric_tile = None
        self._summary_card = None
        self._inventory_card = None
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
            padding=(dp(16), dp(12), dp(16), dp(24)),
            spacing=dp(14),
        )
        content.bind(minimum_height=content.setter("height"))

        content.add_widget(self._create_summary_card())
        content.add_widget(self._create_description_card())
        content.add_widget(self._create_inventory_section())

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _create_header(self):
        header = BoxLayout(
            orientation="horizontal",
            size_hint_y=None,
            height=dp(84),
            padding=(dp(16), dp(14), dp(16), dp(10)),
            spacing=dp(10),
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

        back_btn = SurfaceButton(icon="arrow-left", variant="surface", compact=True)
        back_btn.bind(on_release=self._on_back)
        header.add_widget(back_btn)

        title_box = BoxLayout(orientation="vertical", spacing=dp(2))
        title = Label(
            text="物品 Wiki",
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_large")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(title)
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        title_box.add_widget(title)

        subtitle = Label(
            text="通用信息与库存实例",
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(subtitle)
        if CHINESE_FONT:
            subtitle.font_name = CHINESE_FONT
        title_box.add_widget(subtitle)
        header.add_widget(title_box)

        edit_btn = SurfaceButton(text="编辑", icon="pencil-outline", variant="tonal")
        edit_btn.bind(on_release=self._on_edit)
        header.add_widget(edit_btn)
        return header

    def _create_summary_card(self):
        card = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=(dp(18), dp(18), dp(18), dp(18)),
            spacing=dp(14),
        )
        card.bind(minimum_height=card.setter("height"))
        with card.canvas.before:
            Color(*COLORS["surface_elevated"])
            self._hero_bg = RoundedRectangle(
                pos=card.pos, size=card.size, radius=[dp(HERO_CARD["radius"])]
            )
        with card.canvas.after:
            Color(*COLORS["divider"])
            self._hero_outline = Line(
                rounded_rectangle=(0, 0, 0, 0, dp(HERO_CARD["radius"])),
                width=dp(1),
            )
        card.bind(pos=self._update_hero_card, size=self._update_hero_card)

        top_row = BoxLayout(size_hint_y=None, spacing=dp(14))
        top_row.bind(minimum_height=top_row.setter("height"))

        media_shell = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            size=(dp(104), dp(104)),
            padding=dp(12),
        )
        with media_shell.canvas.before:
            Color(*COLORS["surface_tint"])
            self._image_box_bg = RoundedRectangle(
                pos=media_shell.pos, size=media_shell.size, radius=[dp(24)]
            )
        media_shell.bind(
            pos=lambda inst, _val: setattr(self._image_box_bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(self._image_box_bg, "size", inst.size),
        )

        self._item_image = AsyncImage(source="")
        self._image_fallback = MDIcon(
            icon="package-variant-closed",
            theme_text_color="Custom",
            text_color=COLORS["primary"],
            halign="center",
            valign="middle",
            font_size=dp(42),
        )
        media_shell.add_widget(self._item_image)
        media_shell.add_widget(self._image_fallback)
        top_row.add_widget(media_shell)

        info_col = BoxLayout(orientation="vertical", spacing=dp(4), size_hint_y=None)
        info_col.bind(minimum_height=info_col.setter("height"))

        eyebrow = Label(
            text="物品定义",
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("label_medium")),
            color=COLORS["primary"],
        )
        _bind_label_text(eyebrow)
        if CHINESE_FONT:
            eyebrow.font_name = CHINESE_FONT
        info_col.add_widget(eyebrow)

        self._name_label = Label(
            text="",
            height=dp(32),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("headline_small")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(self._name_label)
        _bind_auto_height(self._name_label, dp(32))
        if CHINESE_FONT:
            self._name_label.font_name = CHINESE_FONT
        info_col.add_widget(self._name_label)

        self._summary_meta_label = Label(
            text="",
            height=dp(18),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(self._summary_meta_label)
        _bind_auto_height(self._summary_meta_label, dp(18))
        if CHINESE_FONT:
            self._summary_meta_label.font_name = CHINESE_FONT
        info_col.add_widget(self._summary_meta_label)

        self._summary_hint_label = Label(
            text="",
            halign="left",
            valign="top",
            font_size=dp(get_font_size("body_medium")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(self._summary_hint_label)
        _bind_auto_height(self._summary_hint_label, dp(42))
        if CHINESE_FONT:
            self._summary_hint_label.font_name = CHINESE_FONT
        info_col.add_widget(self._summary_hint_label)

        top_row.add_widget(info_col)
        card.add_widget(top_row)

        chip_row = BoxLayout(size_hint_y=None, height=dp(34), spacing=dp(8))
        self._category_chip = self._make_chip("分类")
        self._unit_chip = self._make_chip("单位")
        self._inventory_count_chip = self._make_chip("库存 0", accent=True)
        chip_row.add_widget(self._category_chip)
        chip_row.add_widget(self._unit_chip)
        chip_row.add_widget(self._inventory_count_chip)
        chip_row.add_widget(BoxLayout())
        card.add_widget(chip_row)

        metric_row = BoxLayout(size_hint_y=None, height=dp(92), spacing=dp(10))
        stock_tile, self._stock_metric_value = self._create_metric_tile("当前库存总量")
        batch_tile, self._batch_metric_value = self._create_metric_tile("库存批次数")
        self._stock_metric_tile = stock_tile
        self._batch_metric_tile = batch_tile
        metric_row.add_widget(stock_tile)
        metric_row.add_widget(batch_tile)
        card.add_widget(metric_row)

        self._quantity_label = Label(
            text="",
            height=dp(18),
            halign="left",
            valign="top",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_hint"],
        )
        _bind_label_text(self._quantity_label)
        _bind_auto_height(self._quantity_label, dp(18))
        if CHINESE_FONT:
            self._quantity_label.font_name = CHINESE_FONT
        card.add_widget(self._quantity_label)
        self._summary_card = card
        return card

    def _create_description_card(self):
        card = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=dp(SECTION_CARD["padding"]),
            spacing=dp(10),
        )
        card.bind(minimum_height=card.setter("height"))
        with card.canvas.before:
            Color(*COLORS["surface"])
            self._desc_bg = RoundedRectangle(
                pos=card.pos, size=card.size, radius=[dp(SECTION_CARD["radius"])]
            )
        with card.canvas.after:
            Color(*COLORS["divider"])
            self._desc_outline = Line(
                rounded_rectangle=(0, 0, 0, 0, dp(SECTION_CARD["radius"])),
                width=dp(1),
            )
        card.bind(pos=self._update_desc_card, size=self._update_desc_card)

        title = Label(
            text="物品描述",
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
        card.add_widget(title)

        self._description_label = Label(
            text="",
            halign="left",
            valign="top",
            font_size=dp(get_font_size("body_medium")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(self._description_label)
        _bind_auto_height(self._description_label, dp(56))
        if CHINESE_FONT:
            self._description_label.font_name = CHINESE_FONT
        card.add_widget(self._description_label)
        self._description_card = card
        return card

    def _create_inventory_section(self):
        card = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=dp(SECTION_CARD["padding"]),
            spacing=dp(12),
        )
        card.bind(minimum_height=card.setter("height"))
        with card.canvas.before:
            Color(*COLORS["surface"])
            self._inventory_bg = RoundedRectangle(
                pos=card.pos, size=card.size, radius=[dp(SECTION_CARD["radius"])]
            )
        with card.canvas.after:
            Color(*COLORS["divider"])
            self._inventory_outline = Line(
                rounded_rectangle=(0, 0, 0, 0, dp(SECTION_CARD["radius"])),
                width=dp(1),
            )
        card.bind(pos=self._update_inventory_card, size=self._update_inventory_card)

        title = Label(
            text="库存记录",
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
        card.add_widget(title)

        subtitle = Label(
            text="",
            size_hint_y=None,
            height=dp(0),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(subtitle)
        if CHINESE_FONT:
            subtitle.font_name = CHINESE_FONT
        card.add_widget(subtitle)

        self._inventory_list_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(10),
        )
        self._inventory_list_box.bind(
            minimum_height=self._inventory_list_box.setter("height")
        )
        card.add_widget(self._inventory_list_box)
        self._inventory_card = card
        return card

    def _make_chip(self, text, accent=False):
        chip = Label(
            text=text,
            size_hint=(None, None),
            width=max(dp(76), dp(30) + len(text) * dp(10)),
            height=dp(34),
            halign="center",
            valign="middle",
            font_size=dp(get_font_size("label_medium")),
            color=COLORS["primary"] if accent else COLORS["text_secondary"],
        )
        chip.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        chip.bind(
            text=lambda inst, val: setattr(
                inst, "width", max(dp(76), dp(30) + len(val) * dp(10))
            )
        )
        if CHINESE_FONT:
            chip.font_name = CHINESE_FONT
        with chip.canvas.before:
            Color(*(COLORS["primary_container"] if accent else COLORS["surface_variant"]))
            bg = RoundedRectangle(pos=chip.pos, size=chip.size, radius=[dp(17)])
        chip.bind(
            pos=lambda inst, _val: setattr(bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(bg, "size", inst.size),
        )
        return chip

    def _create_metric_tile(self, title):
        tile = BoxLayout(
            orientation="vertical",
            size_hint=(1, None),
            height=dp(92),
            padding=(dp(14), dp(14), dp(14), dp(12)),
            spacing=dp(4),
        )
        tile.bind(minimum_height=tile.setter("height"))
        with tile.canvas.before:
            Color(*COLORS["surface_tint"])
            bg = RoundedRectangle(pos=tile.pos, size=tile.size, radius=[dp(16)])
        with tile.canvas.after:
            Color(*COLORS["divider"])
            outline = Line(width=dp(1), rounded_rectangle=(0, 0, 0, 0, dp(16)))
        tile.bind(
            pos=lambda inst, _val: setattr(bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(bg, "size", inst.size),
        )
        tile.bind(
            pos=lambda inst, _val: setattr(
                outline,
                "rounded_rectangle",
                (inst.x, inst.y, inst.width, inst.height, dp(16)),
            ),
            size=lambda inst, _val: setattr(
                outline,
                "rounded_rectangle",
                (inst.x, inst.y, inst.width, inst.height, dp(16)),
            ),
        )

        value = Label(
            text="0",
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_large")),
            bold=True,
            color=COLORS["primary"],
        )
        _bind_label_text(value)
        _bind_auto_height(value, dp(30))
        if CHINESE_FONT:
            value.font_name = CHINESE_FONT
        tile.add_widget(value)

        title_label = Label(
            text=title,
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(title_label)
        _bind_auto_height(title_label, dp(18))
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        tile.add_widget(title_label)
        return tile, value

    def _update_header_divider(self, instance, _value):
        self._header_divider.points = [instance.x, instance.y, instance.right, instance.y]

    def _update_hero_card(self, instance, _value):
        radius = dp(HERO_CARD["radius"])
        self._hero_bg.pos = instance.pos
        self._hero_bg.size = instance.size
        self._hero_outline.rounded_rectangle = (
            instance.x,
            instance.y,
            instance.width,
            instance.height,
            radius,
        )

    def _update_inventory_card(self, instance, _value):
        radius = dp(SECTION_CARD["radius"])
        self._inventory_bg.pos = instance.pos
        self._inventory_bg.size = instance.size
        self._inventory_outline.rounded_rectangle = (
            instance.x,
            instance.y,
            instance.width,
            instance.height,
            radius,
        )

    def _update_desc_card(self, instance, _value):
        radius = dp(SECTION_CARD["radius"])
        self._desc_bg.pos = instance.pos
        self._desc_bg.size = instance.size
        self._desc_outline.rounded_rectangle = (
            instance.x,
            instance.y,
            instance.width,
            instance.height,
            radius,
        )

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
                self.item_icon = ""
                self.item_unit = "个"
            else:
                self.item_name = wiki_item["name"]
                self.item_category = wiki_item["category_name"] or "其他"
                self.item_description = wiki_item["description"] or ""
                self.item_image = wiki_item.get("image_path") or ""
                self.item_icon = wiki_item.get("icon") or "package-variant-closed"
                self.item_unit = wiki_item.get("default_unit") or "个"

            inventory_items = item_service.get_inventory_by_name(item_name)
            self._inventory_items = inventory_items
            self.total_quantity = sum(item.quantity for item in inventory_items)
            self.inventory_count = len(inventory_items)
            self._update_ui()
        except Exception as exc:
            logger.error(f"加载物品wiki信息失败: {exc}")

    def _update_ui(self):
        self._name_label.text = self.item_name
        self._category_chip.text = self.item_category
        self._unit_chip.text = f"单位 {self.item_unit}"
        self._inventory_count_chip.text = f"库存 {self.inventory_count}"
        self._summary_meta_label.text = f"{self.item_category} · 默认单位 {self.item_unit}"
        if self.inventory_count > 0:
            self._summary_hint_label.text = f"共 {self.inventory_count} 批库存实例，当前累计 {self.total_quantity}{self.item_unit}。"
        else:
            self._summary_hint_label.text = "还没有库存记录。"
        self._stock_metric_value.text = f"{self.total_quantity}{self.item_unit}"
        self._batch_metric_value.text = str(self.inventory_count)
        self._quantity_label.text = "定义信息包含分类、默认单位和描述。"

        if self.item_image:
            image_source = self.item_image
            if not image_source.startswith(("http://", "https://", "/")):
                image_source = os.path.abspath(image_source)
            self._item_image.source = image_source
            self._item_image.opacity = 1
            self._image_fallback.icon = "image-outline"
            self._image_fallback.text_color = (0, 0, 0, 0)
        else:
            self._item_image.source = ""
            self._item_image.opacity = 0
            self._image_fallback.icon = self.item_icon or "package-variant-closed"
            self._image_fallback.text_color = COLORS["primary"]

        self._description_label.text = (
            self.item_description
            or "暂无描述。"
        )
        self._inventory_list_box.clear_widgets()
        if not self._inventory_items:
            self._inventory_list_box.add_widget(self._create_empty_inventory_card())
            return

        for inventory_item in self._inventory_items:
            self._inventory_list_box.add_widget(InventoryListItem(inventory_item))

    def _create_empty_inventory_card(self):
        card = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(144),
            padding=(dp(16), dp(20), dp(16), dp(20)),
            spacing=dp(10),
        )
        with card.canvas.before:
            Color(*COLORS["surface_tint"])
            bg = RoundedRectangle(pos=card.pos, size=card.size, radius=[dp(16)])
        with card.canvas.after:
            Color(*COLORS["divider"])
            outline = Line(width=dp(1), rounded_rectangle=(0, 0, 0, 0, dp(16)))
        card.bind(
            pos=lambda inst, _val: setattr(bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(bg, "size", inst.size),
        )
        card.bind(
            pos=lambda inst, _val: setattr(
                outline, "rounded_rectangle", (inst.x, inst.y, inst.width, inst.height, dp(16))
            ),
            size=lambda inst, _val: setattr(
                outline, "rounded_rectangle", (inst.x, inst.y, inst.width, inst.height, dp(16))
            ),
        )

        icon = MDIcon(
            icon="fridge-outline",
            theme_text_color="Custom",
            text_color=COLORS["primary"],
            size_hint_y=None,
            height=dp(32),
            halign="center",
            valign="middle",
            font_size=dp(28),
        )
        card.add_widget(icon)

        title = Label(
            text="暂无库存记录",
            size_hint_y=None,
            height=dp(22),
            halign="center",
            valign="middle",
            font_size=dp(get_font_size("title_small")),
            bold=True,
            color=COLORS["text_primary"],
        )
        title.bind(size=lambda inst, val: setattr(inst, "text_size", val))
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        card.add_widget(title)

        subtitle = Label(
            text="从“添加物品”新增库存记录。",
            halign="center",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        subtitle.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            subtitle.font_name = CHINESE_FONT
        card.add_widget(subtitle)
        return card

    def _on_back(self, _instance):
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            app.screen_manager.current = "items"

    def _on_edit(self, _instance):
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            edit_screen = app.screen_manager.get_screen("item_wiki_edit")
            if edit_screen:
                edit_screen.load_wiki(self.item_name)
            app.screen_manager.current = "item_wiki_edit"
