# -*- coding: utf-8 -*-
"""
历史屏幕 - 显示已食用和已过期的物品
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.scrollview import ScrollView
from kivy.graphics import Color, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.animation import Animation
from kivy.utils import get_color_from_hex
from kivymd.uix.label import MDIcon
from datetime import date

from app.services.item_service import item_service
from app.utils.logger import setup_logger
from app.utils.font_helper import apply_font_to_widget, CHINESE_FONT_NAME as CHINESE_FONT
from app.ui.theme.design_tokens import COLOR_PALETTE

logger = setup_logger(__name__)

COLORS = COLOR_PALETTE


class HistoryItemCard(BoxLayout):
    """历史物品卡片"""
    __events__ = ('on_restore', 'on_delete')

    def __init__(self, item_data, **kwargs):
        super().__init__(**kwargs)
        self.item_id = str(item_data.id)
        self.item_name = item_data.name
        self.category = item_data.wiki.category.name if item_data.wiki and item_data.wiki.category else "其他"
        self.expiry_date = item_data.expiry_date.strftime('%Y-%m-%d') if item_data.expiry_date else '无'
        self.quantity = item_data.quantity
        self.status = item_data.status.value
        self.consumed_at = item_data.consumed_at.strftime('%Y-%m-%d %H:%M') if item_data.consumed_at else None

        if item_data.expiry_date:
            delta = item_data.expiry_date - date.today()
            self.days_until_expiry = delta.days
        else:
            self.days_until_expiry = 0

        self.orientation = "horizontal"
        self.size_hint_y = None
        self.size_hint_x = 1
        self.height = dp(96)
        self.padding = (dp(16), dp(10), dp(8), dp(10))
        self.spacing = dp(14)

        self._setup_ui()
        self._setup_background()

        if CHINESE_FONT:
            apply_font_to_widget(self, CHINESE_FONT)

    def _setup_ui(self):
        icon_map = {
            "食品": "food-apple",
            "日用品": "home",
            "药品": "medical-bag",
            "化妆品": "face-woman",
            "其他": "package-variant",
        }
        icon_name = icon_map.get(self.category, "package-variant")
        status_color = self._get_status_color()

        icon = MDIcon(
            icon=icon_name,
            theme_text_color="Custom",
            text_color=status_color,
            size_hint_x=None,
            width=dp(48),
            size_hint_y=None,
            height=dp(76),
            halign="center",
            valign="middle",
            font_size=dp(28),
        )
        self.add_widget(icon)

        text_box = BoxLayout(
            orientation="vertical",
            padding=(dp(4), dp(2)),
            spacing=dp(6),
            size_hint_x=1,
            size_hint_y=None,
        )
        text_box.bind(minimum_height=lambda inst, val: setattr(inst, "height", val))

        headline_text = f"{self.item_name}"
        if self.quantity > 1:
            headline_text += f" ×{self.quantity}"

        name_label = Label(
            text=headline_text,
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            color=COLORS['text_primary'],
            font_size=dp(18),
            bold=True,
        )
        name_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            name_label.font_name = CHINESE_FONT
        text_box.add_widget(name_label)

        status_text = self._get_main_status_text()
        supporting_label = Label(
            text=f"{self.category}  ·  {status_text}",
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
            color=COLORS['text_secondary'],
            font_size=dp(14),
        )
        supporting_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            supporting_label.font_name = CHINESE_FONT
        text_box.add_widget(supporting_label)

        if self.expiry_date != "无":
            date_text = self._get_date_text()
            date_label = Label(
                text=date_text,
                size_hint_y=None,
                height=dp(22),
                halign="left",
                valign="middle",
                color=self._get_status_color(),
                font_size=dp(13),
            )
            date_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
            if CHINESE_FONT:
                date_label.font_name = CHINESE_FONT
            text_box.add_widget(date_label)

        self.add_widget(text_box)

    def _get_status_color(self):
        if self.status == 'consumed':
            return COLORS['success']
        elif self.days_until_expiry < 0:
            return COLORS['error']
        else:
            return COLORS['text_secondary']

    def _get_main_status_text(self):
        if self.status == 'consumed':
            return "已食用"
        elif self.days_until_expiry < 0:
            return "已过期"
        else:
            return "正常"

    def _get_date_text(self):
        if self.status == 'consumed' and self.consumed_at:
            return f"食用时间: {self.consumed_at}"
        elif self.days_until_expiry < 0:
            return f"过期: {self.expiry_date}"
        else:
            return f"过期: {self.expiry_date}"

    def _setup_background(self):
        bg_color = self._get_bg_color()
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])
        self.bind(pos=self._update_rect, size=self._update_rect)

    def _get_bg_color(self):
        if self.status == 'consumed':
            return COLORS['success_container'] if 'success_container' in COLORS else (0.9, 0.98, 0.93, 1)
        else:
            return COLORS['error_container'] if 'error_container' in COLORS else (0.98, 0.93, 0.93, 1)

    def _update_rect(self, *args):
        self.canvas.before.clear()
        bg_color = self._get_bg_color()
        with self.canvas.before:
            Color(*bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])

    def on_restore(self, *args):
        """恢复物品"""
        pass

    def on_delete(self, *args):
        """删除物品"""
        pass

    def on_touch_up(self, touch):
        if self.collide_point(*touch.pos):
            # 显示操作菜单
            self.dispatch('on_restore')
        return super().on_touch_up(touch)


class HistoryScreen(Screen):
    """历史屏幕 - 显示已食用和已过期的物品"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = 'history'
        self._item_widgets = {}
        self._build_ui()

    def _build_ui(self):
        main_layout = BoxLayout(orientation='vertical', size_hint=(1, 1))

        with main_layout.canvas.before:
            Color(*COLORS['background'])
            self.bg_rect = Rectangle(pos=main_layout.pos, size=main_layout.size)

        main_layout.bind(pos=self._update_bg_rect, size=self._update_bg_rect)

        self._create_header(main_layout)
        self._create_list_section(main_layout)

        self.add_widget(main_layout)

    def _update_bg_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def _create_header(self, parent):
        header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(52),
            padding=(dp(16), dp(8), dp(16), dp(8)),
        )

        title_label = Label(
            text="历史记录",
            font_size=dp(20),
            bold=True,
            color=COLORS['text_primary'],
            halign="left",
            valign="middle",
        )
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        header.add_widget(title_label)

        desc_label = Label(
            text="已食用和已过期的物品",
            font_size=dp(13),
            color=COLORS['text_hint'],
            halign="left",
            valign="middle",
        )
        if CHINESE_FONT:
            desc_label.font_name = CHINESE_FONT
        header.add_widget(desc_label)

        parent.add_widget(header)

    def _create_list_section(self, parent):
        scroll_view = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=dp(3),
            bar_color=(0.2, 0.5, 0.85, 0.3),
            bar_inactive_color=(0.2, 0.5, 0.85, 0.1),
        )

        with scroll_view.canvas.before:
            Color(*COLORS['background'])
            self.scroll_bg = Rectangle(pos=scroll_view.pos, size=scroll_view.size)

        scroll_view.bind(pos=self._update_scroll_bg, size=self._update_scroll_bg)

        self.item_list_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            size_hint_x=1,
            padding=(dp(12), dp(8), dp(12), dp(16)),
            spacing=dp(8),
        )
        self.item_list_layout.bind(minimum_height=self.item_list_layout.setter('height'))

        scroll_view.add_widget(self.item_list_layout)
        parent.add_widget(scroll_view)

    def _update_scroll_bg(self, instance, value):
        self.scroll_bg.pos = instance.pos
        self.scroll_bg.size = instance.size

    def _load_items(self):
        self.item_list_layout.clear_widgets()
        self._item_widgets.clear()

        try:
            items = item_service.get_history_items()

            if not items:
                self._show_empty_state()
                return

            for i, item in enumerate(items):
                item_widget = HistoryItemCard(item)
                item_widget.bind(on_restore=lambda inst, item_id=item.id: self._on_restore_item(item_id))
                item_widget.opacity = 0
                item_widget.y -= dp(10)
                self.item_list_layout.add_widget(item_widget)
                self._item_widgets[str(item.id)] = item_widget

                Clock.schedule_once(
                    lambda dt, w=item_widget: Animation(
                        opacity=1,
                        y=w.y + dp(10),
                        duration=0.25,
                        t='out_cubic'
                    ).start(w),
                    i * 0.05
                )

        except Exception as e:
            logger.error(f"加载历史物品失败: {e}")
            self._show_empty_state()

    def _show_empty_state(self):
        empty_container = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(200),
            padding=dp(32),
        )

        empty_icon = MDIcon(
            icon="history",
            theme_text_color="Custom",
            text_color=COLORS['text_hint'],
            size_hint_y=None,
            height=dp(64),
            font_size=dp(48),
        )
        empty_container.add_widget(empty_icon)

        empty_text = Label(
            text="暂无历史记录",
            font_size=dp(18),
            color=COLORS['text_secondary'],
            size_hint_y=None,
            height=dp(32),
        )
        if CHINESE_FONT:
            empty_text.font_name = CHINESE_FONT
        empty_container.add_widget(empty_text)

        hint_text = Label(
            text="已食用或已过期的物品会显示在这里",
            font_size=dp(14),
            color=COLORS['text_hint'],
            size_hint_y=None,
            height=dp(28),
        )
        if CHINESE_FONT:
            hint_text.font_name = CHINESE_FONT
        empty_container.add_widget(hint_text)

        self.item_list_layout.add_widget(empty_container)

    def _on_restore_item(self, item_id):
        """恢复物品"""
        if item_service.restore_item(str(item_id)):
            logger.info(f"物品已恢复: {item_id}")
            self._load_items()

    def on_enter(self):
        """进入屏幕时调用"""
        self._load_items()
        if CHINESE_FONT:
            apply_font_to_widget(self, CHINESE_FONT)

    def on_leave(self):
        """离开屏幕时调用"""
        pass
