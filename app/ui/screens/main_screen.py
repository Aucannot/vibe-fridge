# -*- coding: utf-8 -*-
"""
主屏幕 - 显示物品清单和主要功能
Modernized UI with Material Design 3 principles
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.scrollview import ScrollView
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.modalview import ModalView
from kivy.graphics import Color, Rectangle, RoundedRectangle, Ellipse, Line
from kivy.metrics import dp
from kivy.properties import (
    StringProperty, ListProperty, ObjectProperty, NumericProperty, BooleanProperty
)
from kivy.clock import Clock
from kivy.animation import Animation
from kivymd.app import MDApp
from kivymd.uix.list import MDList
from kivymd.uix.button import MDFabButton, MDButton, MDIconButton, MDButtonText
from kivymd.uix.card import MDCard
from kivymd.uix.dialog import MDDialog
from kivymd.uix.textfield import MDTextField
from datetime import date, timedelta
import os

from app.services.item_service import item_service, statistics_service
from app.models.item import ItemCategory, ItemStatus
from app.utils.logger import setup_logger
from app.utils.font_helper import apply_font_to_widget, CHINESE_FONT_NAME as CHINESE_FONT
from app.ui.theme.design_tokens import COLOR_PALETTE, DESIGN_TOKENS

logger = setup_logger(__name__)

COLORS = COLOR_PALETTE

def get_token_color(key):
    return COLORS.get(key, (0.5, 0.5, 0.5, 1))


class AnimatedCard(MDCard):
    """带动画效果的卡片 - Modern Material Design 3 Card"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.elevation = 0
        self.radius = [dp(24)]
        self.padding = dp(20)
        self.md_bg_color = COLORS['surface']
        self.shadow_radius = 16
        self.shadow_offset = (0, dp(8))
        self._hovered = False
        self._pressed = False

    def on_parent(self, widget, parent):
        self._fade_in()

    def _fade_in(self, *args):
        self.opacity = 0
        self.y -= dp(30)
        anim = Animation(
            opacity=1,
            y=self.y + dp(30),
            duration=0.4,
            t='out_cubic'
        )
        anim.start(self)

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._pressed = True
            self._animate_scale(0.96)
            return True
        return super().on_touch_down(touch)

    def on_touch_up(self, touch):
        if self._pressed:
            self._pressed = False
            self._animate_scale(1.0)
        return super().on_touch_up(touch)

    def _animate_scale(self, scale):
        if hasattr(self, 'scale'):
            Animation(
                scale_x=scale,
                scale_y=scale,
                duration=0.1,
                t='out_quad'
            ).start(self)


class HoverButton(Button):
    """带悬停效果的按钮 - Modern Elevated Button"""
    is_hovering = BooleanProperty(False)
    is_pressed = BooleanProperty(False)

    def __init__(self, hover_color=None, pressed_color=None, **kwargs):
        super().__init__(**kwargs)
        self.hover_color = hover_color or COLORS['primary_container']
        self.pressed_color = pressed_color or COLORS['primary_light']
        self.original_bg = list(self.background_color) if hasattr(self, 'background_color') else list(COLORS['primary'])
        self.bind(on_touch_move=self._on_hover)
        self.bind(on_touch_down=self._on_press)
        self.bind(on_touch_up=self._on_release)

    def _on_hover(self, instance, touch):
        if self.collide_point(*touch.pos):
            if not self.is_hovering:
                self.is_hovering = True
                if not self.is_pressed:
                    self._update_hover_state()
        else:
            if self.is_hovering:
                self.is_hovering = False
                if not self.is_pressed:
                    self._update_hover_state()
        return False

    def _on_press(self, instance, touch):
        if self.collide_point(*touch.pos):
            self.is_pressed = True
            Animation(
                background_color=self.pressed_color,
                duration=0.08,
                t='out_quad'
            ).start(self)

    def _on_release(self, instance, touch):
        if self.is_pressed:
            self.is_pressed = False
            if self.is_hovering:
                Animation(
                    background_color=self.hover_color,
                    duration=0.12,
                    t='out_cubic'
                ).start(self)
            else:
                Animation(
                    background_color=self.original_bg,
                    duration=0.12,
                    t='out_cubic'
                ).start(self)

    def _update_hover_state(self):
        if self.is_hovering and not self.is_pressed:
            Animation(
                background_color=self.hover_color,
                duration=0.15,
                t='out_cubic'
            ).start(self)
        elif not self.is_pressed:
            Animation(
                background_color=self.original_bg,
                duration=0.15,
                t='out_cubic'
            ).start(self)


class CategoryChip(BoxLayout):
    """分类筛选标签 - Modern Filter Chip"""
    __events__ = ('on_release',)
    
    text = StringProperty()
    is_selected = BooleanProperty(False)
    
    def __init__(self, text, is_selected=False, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.is_selected = is_selected
        self.orientation = 'horizontal'
        self.size_hint_x = None
        self.size_hint_y = None
        self.height = dp(40)
        self.padding = (dp(18), dp(0), dp(18), dp(0))
        self.spacing = dp(8)
        self._setup_ui()
        self.bind(children=self._update_width)
    
    def _update_width(self, *args):
        if self.children:
            self.width = sum(child.width for child in self.children) + self.padding[0] + self.padding[2] + self.spacing * max(0, len(self.children) - 1)
    
    def _setup_ui(self):
        from kivymd.uix.label import MDIcon
        
        icon_name = "filter-variant" if self.is_selected else "filter-outline"
        
        icon = MDIcon(
            icon=icon_name,
            theme_text_color="Custom",
            text_color=COLORS['primary'] if self.is_selected else COLORS['text_secondary'],
            size_hint_x=None,
            width=dp(22),
            halign="center",
            valign="middle",
            font_size=dp(18),
        )
        self.add_widget(icon)
        
        label = Label(
            text=self.text,
            size_hint_x=None,
            size_hint_y=None,
            height=dp(40),
            halign="center",
            valign="middle",
            color=COLORS['primary'] if self.is_selected else COLORS['text_secondary'],
            font_size=dp(14),
            bold=self.is_selected,
        )
        label.bind(size=lambda inst, val: (
            setattr(inst, "text_size", (val[0] if val[0] > 0 else None, None)),
            self._update_width()
        ))
        if CHINESE_FONT:
            label.font_name = CHINESE_FONT
        self.add_widget(label)
        
        self._update_background()
        Clock.schedule_once(lambda dt: self._update_width(), 0)
    
    def _update_background(self):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.is_selected:
                Color(*COLORS['primary'])
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(20)])
            else:
                Color(*COLORS['surface_variant'])
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(20)])
        self.bind(pos=self._update_rect, size=self._update_rect)
    
    def _update_rect(self, *args):
        self.canvas.before.clear()
        with self.canvas.before:
            if self.is_selected:
                Color(*COLORS['primary'])
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(20)])
            else:
                Color(*COLORS['surface_variant'])
                RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(20)])
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dispatch('on_release')
        return super().on_touch_down(touch) if hasattr(super(), 'on_touch_down') else False
    
    def on_release(self, *args):
        pass
    
    def on_status_changed(self, *args):
        pass


class StatCard(BoxLayout):
    """统计卡片 - Modern Metric Card with Accent"""
    __events__ = ('on_release',)

    def __init__(self, title, value, icon, color, accent_color, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.padding = dp(16)
        self.spacing = dp(6)
        self._stat_color = color
        self._stat_accent = accent_color
        self._is_selected = False
        self._build_ui(title, value, icon)
        self._setup_touch_events()

    def _build_ui(self, title, value, icon):
        from kivymd.uix.label import MDIcon

        icon_row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(8))

        self.icon_widget = MDIcon(
            icon=icon,
            theme_text_color="Custom",
            text_color=self._stat_color,
            size_hint_x=None,
            width=dp(24),
            halign="center",
            font_size=dp(20),
        )

        self.value_label = Label(
            text=value,
            size_hint_y=None,
            height=dp(32),
            halign="left",
            valign="bottom",
            color=self._stat_color,
            font_size=dp(28),
            bold=True,
            font_name=None if not CHINESE_FONT else CHINESE_FONT,
        )
        self.value_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1])))

        icon_row.add_widget(self.icon_widget)
        icon_row.add_widget(self.value_label)
        self.add_widget(icon_row)

        title_label = Label(
            text=title,
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="top",
            color=COLORS['text_hint'],
            font_size=dp(11),
            font_name=None if not CHINESE_FONT else CHINESE_FONT,
        )
        title_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1])))

        self._draw_background()

        accent_bar = BoxLayout(
            size_hint_y=None,
            height=dp(3),
            size_hint_x=1,
            padding=(0, dp(3), 0, 0),
        )
        with accent_bar.canvas.before:
            Color(*self._stat_color[:4])
            RoundedRectangle(
                pos=accent_bar.pos,
                size=(accent_bar.width * 0.15, accent_bar.height),
                radius=[dp(2)]
            )
        accent_bar.bind(pos=lambda inst, val: self._update_accent_bar(inst), size=lambda inst, val: self._update_accent_bar(inst))

        container = BoxLayout(orientation='vertical', spacing=dp(4))
        container.add_widget(title_label)
        container.add_widget(accent_bar)
        self.add_widget(container)

    def _update_accent_bar(self, instance):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(*self._stat_color[:4])
            RoundedRectangle(
                pos=instance.pos,
                size=(instance.width * 0.15, instance.height),
                radius=[dp(2)]
            )

    def _draw_background(self):
        with self.canvas.before:
            Color(*COLORS['surface'])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(20)])
        self._update_selection_border()

        self.bind(pos=self._update_bg, size=self._update_bg)

    def _update_bg(self, *args):
        self.canvas.before.clear()
        if self._is_selected:
            bg_color = (self._stat_color[0], self._stat_color[1], self._stat_color[2], 0.15)
        else:
            bg_color = COLORS['surface']
        with self.canvas.before:
            Color(*bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(20)])
    
    def _update_selection_border(self):
        self._update_bg()
    
    def set_selected(self, selected):
        self._is_selected = selected
        self._update_bg()
    
    def update_value(self, value):
        if hasattr(self, 'value_label'):
            self.value_label.text = value
            Animation(
                opacity=0.5, duration=0.1, t='out_quad'
            ).start(self.value_label)
            Animation(
                opacity=1, duration=0.2, t='in_out_quad'
            ).start(self.value_label)
    
    def _setup_touch_events(self):
        self._is_pressed = False
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self._is_pressed = True
            self._update_press_effect()
            return True
        return super().on_touch_down(touch) if hasattr(super(), 'on_touch_down') else False
    
    def on_touch_up(self, touch):
        if self._is_pressed and self.collide_point(*touch.pos):
            self.dispatch('on_release')
        self._is_pressed = False
        self._update_press_effect()
        return super().on_touch_up(touch) if hasattr(super(), 'on_touch_up') else False
    
    def _update_press_effect(self):
        self.canvas.before.clear()
        if self._is_pressed:
            bg_color = (self._stat_color[0], self._stat_color[1], self._stat_color[2], 0.3)
        elif self._is_selected:
            bg_color = (self._stat_color[0], self._stat_color[1], self._stat_color[2], 0.15)
        else:
            bg_color = COLORS['surface']
        with self.canvas.before:
            Color(*bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(20)])
    
    def on_release(self, *args):
        pass


class ItemListItem(BoxLayout):
    """物品列表项 - Modern List Item with Swipe Actions"""
    __events__ = ('on_release', 'on_status_changed')
    
    item_id = StringProperty()
    item_name = StringProperty()
    category = StringProperty()
    expiry_date = StringProperty()
    days_until_expiry = NumericProperty(0)
    quantity = NumericProperty(1)
    
    def __init__(self, item_data, **kwargs):
        super().__init__(**kwargs)
        self.item_id = item_data.id
        self.item_name = item_data.name
        self.category = item_data.category.value
        self.expiry_date = item_data.expiry_date.strftime('%Y-%m-%d') if item_data.expiry_date else '无'
        
        if item_data.expiry_date:
            from datetime import date
            today = date.today()
            delta = item_data.expiry_date - today
            self.days_until_expiry = delta.days
        else:
            self.days_until_expiry = 0
        
        self.quantity = item_data.quantity
        self.status = item_data.status.value
        self.is_consumed = self.status == 'consumed'
        
        self.is_hovering = False
        self.is_pressed = False
        self.checkbox_widget = None
        self.item_name_label = None
        self.strikethrough_line = None
        self.supporting_label = None
        self.tertiary_label = None
        self.icon_widget = None
        
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.size_hint_x = 1
        self.height = dp(96)
        self.padding = (dp(16), dp(10), dp(8), dp(10))
        self.spacing = dp(14)
        
        self._setup_ui()
        self._setup_background()
        
        if self.is_consumed:
            self._show_consumed_state()
        
        if CHINESE_FONT:
            apply_font_to_widget(self, CHINESE_FONT)
    
    def _setup_ui(self):
        self._add_icon()
        self._add_text_content()
        self._add_checkbox()
    
    def _add_icon(self):
        from kivymd.uix.label import MDIcon
        
        icon_map = {
            ItemCategory.FOOD.value: "food-apple",
            ItemCategory.DAILY_NECESSITIES.value: "home",
            ItemCategory.MEDICINE.value: "medical-bag",
            ItemCategory.COSMETICS.value: "face-woman",
            ItemCategory.OTHERS.value: "package-variant",
        }
        icon_name = icon_map.get(self.category, "package-variant")
        
        icon_color = self._get_status_color()
        
        icon = MDIcon(
            icon=icon_name,
            theme_text_color="Custom",
            text_color=icon_color,
            size_hint_x=None,
            width=dp(48),
            size_hint_y=None,
            height=dp(76),
            halign="center",
            valign="middle",
            font_size=dp(28),
        )
        self.icon_widget = icon
        self.add_widget(icon)
    
    def _add_text_content(self):
        text_box = BoxLayout(
            orientation="vertical",
            padding=(dp(4), dp(2)),
            spacing=dp(6),
            size_hint_x=1,
        )
        text_box.bind(minimum_height=lambda inst, val: setattr(inst, "height", val))
        
        headline_text = f"{self.item_name}"
        if self.quantity > 1:
            headline_text += f" ×{self.quantity}"
        
        self.item_name_label = Label(
            text=headline_text,
            size_hint_y=None,
            height=dp(28),
            halign="left",
            valign="middle",
            color=COLORS['text_primary'],
            font_size=dp(18),
            bold=True,
            font_name=None if not CHINESE_FONT else CHINESE_FONT,
        )
        self.item_name_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        text_box.add_widget(self.item_name_label)
        
        category_map = {
            ItemCategory.FOOD.value: "食品",
            ItemCategory.DAILY_NECESSITIES.value: "日用品",
            ItemCategory.MEDICINE.value: "药品",
            ItemCategory.COSMETICS.value: "化妆品",
            ItemCategory.OTHERS.value: "其他",
        }
        category_text = category_map.get(self.category, "其他")
        
        status_color = self._get_status_color()
        status_text = self._get_status_text()
        
        supporting_text = f"{category_text}  ·  {status_text}"
        supporting_label = Label(
            text=supporting_text,
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
            color=status_color,
            font_size=dp(14),
        )
        supporting_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
        if CHINESE_FONT:
            supporting_label.font_name = CHINESE_FONT
        self.supporting_label = supporting_label
        text_box.add_widget(supporting_label)
        
        if self.expiry_date != "无":
            days_text = self._get_days_text()
            tertiary_text = f"{self.expiry_date}  ·  {days_text}"
            tertiary_color = self._get_days_color()
            
            tertiary_label = Label(
                text=tertiary_text,
                size_hint_y=None,
                height=dp(22),
                halign="left",
                valign="middle",
                color=tertiary_color,
                font_size=dp(13),
            )
            tertiary_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], None)))
            if CHINESE_FONT:
                tertiary_label.font_name = CHINESE_FONT
            self.tertiary_label = tertiary_label
            text_box.add_widget(tertiary_label)
        
        self.add_widget(text_box)
    
    def _add_checkbox(self):
        from kivymd.uix.selectioncontrol import MDCheckbox
        
        checkbox = MDCheckbox(
            size_hint=(None, None),
            size=(dp(32), dp(32)),
            pos_hint={'center_y': 0.5},
            active=self.is_consumed,
            color_active=COLORS['primary'],
            color_inactive=COLORS['text_hint'],
        )
        checkbox.bind(on_active=self._on_checkbox_active)
        self.checkbox_widget = checkbox
        
        checkbox_container = BoxLayout(
            size_hint_x=None,
            width=dp(48),
            pos_hint={'center_y': 0.5}
        )
        checkbox_container.add_widget(checkbox)
        self.add_widget(checkbox_container)
    
    def _get_status_color(self):
        if self.expiry_date == "无":
            return COLORS['text_secondary']
        elif self.days_until_expiry < 0:
            return COLORS['error']
        elif self.days_until_expiry <= 3:
            return COLORS['warning']
        else:
            return COLORS['success']
    
    def _get_status_text(self):
        if self.expiry_date == "无":
            return "无过期"
        elif self.days_until_expiry < 0:
            return "已过期"
        elif self.days_until_expiry <= 3:
            return "即将过期"
        else:
            return "正常"
    
    def _get_days_text(self):
        if self.days_until_expiry < 0:
            return f"过期{-self.days_until_expiry}天"
        elif self.days_until_expiry == 0:
            return "今天过期"
        else:
            return f"剩余{self.days_until_expiry}天"
    
    def _get_days_color(self):
        if self.days_until_expiry < 0:
            return COLORS['error']
        elif self.days_until_expiry <= 3:
            return COLORS['warning']
        else:
            return COLORS['text_secondary']
    
    def _setup_background(self):
        bg_color = self._get_bg_color()
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])
        self.bind(pos=self._update_rect, size=self._update_rect)
    
    def _get_bg_color(self):
        if self.is_consumed:
            return COLORS['surface_variant']
        elif self.expiry_date == "无":
            return COLORS['surface']
        elif self.days_until_expiry < 0:
            return COLORS['error_container']
        elif self.days_until_expiry <= 3:
            return COLORS['warning_container']
        else:
            return COLORS['surface']
    
    def _update_rect(self, *args):
        self.canvas.before.clear()
        bg_color = self._get_bg_color()
        with self.canvas.before:
            Color(*bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])
    
    def on_touch_move(self, touch):
        is_hovering = self.collide_point(*touch.pos)
        if is_hovering != self.is_hovering:
            self.is_hovering = is_hovering
            self._update_hover_effect()
        return False
    
    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            if self.checkbox_widget and self.checkbox_widget.collide_point(*touch.pos):
                return self.checkbox_widget.on_touch_down(touch)
            self.is_pressed = True
            self._update_press_effect()
            return True
        return super().on_touch_down(touch) if hasattr(super(), 'on_touch_down') else False
    
    def on_touch_up(self, touch):
        if self.is_pressed and self.collide_point(*touch.pos):
            if not (self.checkbox_widget and self.checkbox_widget.collide_point(*touch.pos)):
                self.dispatch('on_release')
        self.is_pressed = False
        self.is_hovering = self.collide_point(*touch.pos)
        self._update_hover_effect()
        return super().on_touch_up(touch) if hasattr(super(), 'on_touch_up') else False
    
    def on_release(self, *args):
        pass
    
    def on_status_changed(self, *args):
        pass
    
    def _update_hover_effect(self):
        bg_color = self._get_hover_color()
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])
    
    def _get_hover_color(self):
        base = self._get_bg_color()
        if self.is_pressed:
            if base[3] == 1:
                return (base[0] * 0.94, base[1] * 0.94, base[2] * 0.94, 1)
            return base
        elif self.is_hovering:
            return COLORS['surface']
        return base
    
    def _update_press_effect(self):
        bg_color = self._get_hover_color()
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*bg_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])
    
    def _on_checkbox_active(self, checkbox, value):
        if value:
            if not self.is_consumed:
                self.is_consumed = True
                self._mark_as_consumed()
        else:
            if self.is_consumed:
                self.is_consumed = False
                self._restore_item()
    
    def _mark_as_consumed(self):
        item_service.mark_as_consumed(self.item_id)
        self._show_consumed_state()
        self.dispatch('on_status_changed')
    
    def _restore_item(self):
        item_service.restore_item(self.item_id)
        self._hide_consumed_state()
        self.dispatch('on_status_changed')
    
    def _show_consumed_state(self):
        self.canvas.before.clear()
        with self.canvas.before:
            Color(*COLORS['surface_variant'])
            RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])
        
        if self.item_name_label:
            self.item_name_label.color = COLORS['text_hint']
        if self.supporting_label:
            self.supporting_label.color = COLORS['text_hint']
        if self.tertiary_label:
            self.tertiary_label.color = COLORS['text_hint']
        if self.icon_widget:
            self.icon_widget.text_color = COLORS['text_hint']
    
    def _hide_consumed_state(self):
        self.canvas.before.clear()
        if self.item_name_label:
            self.item_name_label.color = COLORS['text_primary']
        if self.supporting_label:
            self.supporting_label.color = self._get_status_color()
        if self.tertiary_label:
            self.tertiary_label.color = self._get_days_color()
        if self.icon_widget:
            self.icon_widget.text_color = self._get_status_color()
        self._setup_background()


class MainScreen(Screen):
    """主屏幕"""
    
    selected_category = ObjectProperty(allownone=True)
    selected_filter = ObjectProperty(allownone=True)
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.size_hint = (1, 1)  # 确保 Screen 填满父容器
        self.name = 'main'
        self._build_ui()
        self._load_items()
        self._create_category_menu()
        Clock.schedule_interval(self._refresh_items, 60)
        Clock.schedule_interval(self._cleanup_consumed_items, 3600)
    
    def _build_ui(self):
        main_layout = BoxLayout(orientation='vertical', size_hint=(1, 1))
        
        with main_layout.canvas.before:
            Color(*COLORS['background'])
            self.bg_rect = Rectangle(pos=main_layout.pos, size=main_layout.size)
        
        main_layout.bind(pos=self._update_bg_rect, size=self._update_bg_rect)
        
        self._create_header(main_layout)

        filter_bar = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(44),
            padding=(dp(16), dp(6), dp(16), dp(6)),
            spacing=dp(10),
        )

        filter_label = Label(
            text="筛选",
            font_size=dp(13),
            color=COLORS['text_secondary'],
            size_hint_x=None,
            width=dp(32),
            halign="right",
            valign="middle",
        )
        filter_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1])))
        if CHINESE_FONT:
            apply_font_to_widget(filter_label, CHINESE_FONT)

        self.filter_btn = HoverButton(
            text="全部",
            size_hint_x=None,
            width=dp(68),
            height=dp(28),
            font_size=dp(13),
            background_color=COLORS['accent'],
            background_normal='',
            border=(0, 0, 0, 0),
        )
        self.filter_btn.bind(on_release=lambda x: self._show_category_menu())
        if CHINESE_FONT:
            apply_font_to_widget(self.filter_btn, CHINESE_FONT)

        filter_bar.add_widget(filter_label)
        filter_bar.add_widget(self.filter_btn)

        with filter_bar.canvas.before:
            Color(*COLORS['surface'])
            RoundedRectangle(pos=filter_bar.pos, size=filter_bar.size, radius=[dp(12)])
        filter_bar.bind(pos=self._update_filter_bar_bg, size=self._update_filter_bar_bg)

        main_layout.add_widget(filter_bar)
        
        self._create_stats_section(main_layout)
        self._create_list_section(main_layout)
        
        self.add_widget(main_layout)
    
    def _show_category_menu(self):
        self.category_menu.open()
    
    def _create_header(self, parent):
        header = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(80),
        )

        with header.canvas.before:
            Color(0.45, 0.72, 1.0, 1)
            RoundedRectangle(pos=header.pos, size=header.size, radius=[0])
            Color(0.25, 0.52, 0.88, 1)
            RoundedRectangle(pos=header.pos, size=(header.size[0], header.size[1] * 0.5), radius=[0])

        header.bind(pos=self._update_header_rect, size=self._update_header_rect)

        title_row = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(36),
            padding=(dp(16), dp(10), dp(16), dp(10)),
        )

        title_label = Label(
            text="V I B E",
            font_size=dp(20),
            bold=True,
            color=(1, 1, 1, 0.95),
            size_hint_x=None,
            width=dp(80),
            halign="right",
            valign="middle",
        )
        title_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1])))
        if CHINESE_FONT:
            apply_font_to_widget(title_label, CHINESE_FONT)

        title_row.add_widget(title_label)

        brand_label = Label(
            text="fridge",
            font_size=dp(20),
            color=(1, 1, 1, 0.75),
            size_hint_x=None,
            width=dp(60),
            halign="left",
            valign="middle",
        )
        brand_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1])))
        if CHINESE_FONT:
            apply_font_to_widget(brand_label, CHINESE_FONT)

        title_row.add_widget(brand_label)

        header.add_widget(title_row)

        parent.add_widget(header)

    def _update_header_rect(self, instance, value):
        # 清除旧的 canvas 绘制
        instance.canvas.before.clear()
        
        # 重新绘制背景
        with instance.canvas.before:
            Color(0.45, 0.72, 1.0, 1)
            RoundedRectangle(pos=instance.pos, size=instance.size, radius=[0])
            Color(0.25, 0.52, 0.88, 1)
            RoundedRectangle(
                pos=(instance.pos[0], instance.pos[1]), 
                size=(instance.size[0], instance.size[1] * 0.5), 
                radius=[0]
            )
    
    def _update_bg_rect(self, instance, value):
        self.bg_rect.pos = instance.pos
        self.bg_rect.size = instance.size

    def _update_filter_bar_bg(self, instance, value):
        for child in instance.canvas.before.children:
            if isinstance(child, RoundedRectangle):
                child.pos = instance.pos
                child.size = instance.size
                break

    def _update_header_bg(self, instance, value):
        h = instance.height
        self.header_rect_top.pos = instance.pos
        self.header_rect_top.size = (instance.width, h * 0.55)
        self.header_rect_bottom.pos = (instance.pos[0], instance.pos[1] + h * 0.45)
        self.header_rect_bottom.size = (instance.width, h * 0.55)
    
    def _on_category_selected(self, category):
        self.selected_category = category
        
        category_names = {
            None: "全部",
            ItemCategory.FOOD.value: "食品",
            ItemCategory.DAILY_NECESSITIES.value: "日用品",
            ItemCategory.MEDICINE.value: "药品",
            ItemCategory.COSMETICS.value: "化妆品",
            ItemCategory.OTHERS.value: "其他",
        }
        
        if hasattr(self, 'filter_btn'):
            self.filter_btn.text = category_names.get(category, "全部")
        
        self._load_items()
    
    def _on_filter_selected(self, filter_type):
        self.selected_filter = filter_type
        
        if hasattr(self, 'total_card'):
            self.total_card.set_selected(filter_type is None)
        if hasattr(self, 'expiring_card'):
            self.expiring_card.set_selected(filter_type == 'expiring')
        if hasattr(self, 'expired_card'):
            self.expired_card.set_selected(filter_type == 'expired')
        
        self._load_items()
    
    def _create_stats_section(self, parent):
        stats_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(120),
            padding=(dp(16), dp(12), dp(16), dp(12)),
        )
        
        stats_label = Label(
            text="概览",
            font_size=dp(15),
            bold=True,
            color=COLORS['text_secondary'],
            size_hint_y=None,
            height=dp(24),
            halign="left",
        )
        if CHINESE_FONT:
            stats_label.font_name = CHINESE_FONT
        stats_container.add_widget(stats_label)
        
        cards_row = BoxLayout(size_hint_y=None, height=dp(84), spacing=dp(12))
        
        self.total_card = StatCard(
            "总物品",
            "0",
            "package-variant",
            COLORS['primary'],
            COLORS['primary_light'],
        )
        self.total_card.bind(on_release=lambda x: self._on_filter_selected(None))
        cards_row.add_widget(self.total_card)
        
        self.expiring_card = StatCard(
            "即将过期",
            "0",
            "clock-alert",
            COLORS['expiring'],
            (1, 0.95, 0.85, 1),
        )
        self.expiring_card.bind(on_release=lambda x: self._on_filter_selected('expiring'))
        cards_row.add_widget(self.expiring_card)
        
        self.expired_card = StatCard(
            "已过期",
            "0",
            "alert-circle",
            COLORS['expired'],
            (1, 0.9, 0.9, 1),
        )
        self.expired_card.bind(on_release=lambda x: self._on_filter_selected('expired'))
        cards_row.add_widget(self.expired_card)
        
        stats_container.add_widget(cards_row)
        
        parent.add_widget(stats_container)
        
        self.total_card.set_selected(True)
    
    def _create_list_section(self, parent):
        list_header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(36),
            padding=(dp(16), dp(4), dp(16), dp(4)),
        )
        
        list_title = Label(
            text="物品清单",
            font_size=dp(15),
            bold=True,
            color=COLORS['text_secondary'],
            size_hint_x=1,
            halign="left",
            valign="middle",
        )
        list_title.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1])))
        if CHINESE_FONT:
            list_title.font_name = CHINESE_FONT
        list_header.add_widget(list_title)
        
        self.item_count_label = Label(
            text="0 项",
            font_size=dp(13),
            color=COLORS['text_hint'],
            size_hint_x=None,
            width=dp(60),
            halign="right",
            valign="middle",
        )
        self.item_count_label.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1])))
        if CHINESE_FONT:
            self.item_count_label.font_name = CHINESE_FONT
        list_header.add_widget(self.item_count_label)
        
        parent.add_widget(list_header)
        
        scroll_view = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=dp(3),
            bar_color=(0.2, 0.5, 0.85, 0.3),
            bar_inactive_color=(0.2, 0.5, 0.85, 0.1),
        )
        
        with scroll_view.canvas.before:
            Color(*COLORS['background'])
            scroll_bg = Rectangle(pos=scroll_view.pos, size=scroll_view.size)
        
        scroll_view.bind(pos=self._update_scroll_bg, size=self._update_scroll_bg)
        
        self.item_list_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            size_hint_x=1,
            padding=(dp(12), dp(4), dp(12), dp(16)),
            spacing=dp(8),
        )
        self.item_list_layout.bind(minimum_height=self.item_list_layout.setter('height'))
        
        scroll_view.add_widget(self.item_list_layout)
        parent.add_widget(scroll_view)
    
    def _update_scroll_bg(self, instance, value):
        pass
    
    def _create_category_menu(self):
        self.category_menu = ModalView(
            size_hint=(0.9, None),
            auto_dismiss=True,
            background_color=(0, 0, 0, 0.3),
        )
        self.category_menu.size_hint_y = None
        self.category_menu.height = dp(480)
        
        main_box = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            padding=dp(0),
        )
        main_box.bind(minimum_height=main_box.setter('height'))
        
        content_box = BoxLayout(
            orientation="vertical",
            padding=dp(24),
            spacing=dp(16),
            size_hint_y=None,
            height=dp(480),
        )
        
        with content_box.canvas.before:
            Color(1, 1, 1, 1)
            RoundedRectangle(size=content_box.size, pos=content_box.pos, radius=[dp(20)])
        content_box.bind(pos=self._update_modal_rect, size=self._update_modal_rect)
        
        title = Label(
            text="选择类别",
            size_hint_y=None,
            height=dp(48),
            font_size=dp(20),
            bold=True,
            color=COLORS['text_primary'],
            halign="center",
            valign="middle",
        )
        title.bind(size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1])))
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
        content_box.add_widget(title)
        
        button_container = BoxLayout(
            orientation="vertical",
            spacing=dp(10),
            size_hint_y=None,
        )
        button_container.bind(minimum_height=button_container.setter('height'))
        
        categories = [
            ("所有类别", None),
            ("食品", ItemCategory.FOOD),
            ("日用品", ItemCategory.DAILY_NECESSITIES),
            ("药品", ItemCategory.MEDICINE),
            ("化妆品", ItemCategory.COSMETICS),
            ("其他", ItemCategory.OTHERS),
        ]
        
        for cat_text, cat_value in categories:
            btn = self._create_category_button(cat_text, cat_value)
            button_container.add_widget(btn)
        
        content_box.add_widget(button_container)
        
        close_btn = MDButton(
            style="outlined",
            size_hint_y=None,
            height=dp(48),
            radius=[dp(12)],
            line_color=COLORS['primary'],
            on_release=lambda x: self.category_menu.dismiss()
        )
        close_text = MDButtonText(
            text="取消",
            font_size=dp(15),
            theme_text_color="Custom",
            text_color=COLORS['primary'],
            theme_font_name="Custom"
        )
        if CHINESE_FONT:
            close_text.font_name = CHINESE_FONT
        close_btn.add_widget(close_text)
        content_box.add_widget(close_btn)
        
        main_box.add_widget(content_box)
        self.category_menu.add_widget(main_box)
    
    def _create_category_button(self, text, category_value):
        is_selected = (
            (self.selected_category is None and category_value is None) or
            (self.selected_category == category_value)
        )
        
        btn = MDButton(
            style="filled" if is_selected else "outlined",
            md_bg_color=COLORS['primary'] if is_selected else COLORS['surface'],
            size_hint_y=None,
            height=dp(52),
            radius=[dp(12)],
            line_color=COLORS['primary'] if not is_selected else (0, 0, 0, 0),
        )
        btn_text = MDButtonText(
            text=text,
            font_size=dp(15),
            theme_text_color="Custom",
            text_color=(1, 1, 1, 1) if is_selected else COLORS['text_primary'],
            theme_font_name="Custom"
        )
        if CHINESE_FONT:
            btn_text.font_name = CHINESE_FONT
        btn.add_widget(btn_text)
        
        btn.bind(
            on_release=lambda inst, v=category_value: [
                self._on_category_selected(v),
                self.category_menu.dismiss()
            ]
        )
        
        return btn
    
    def _update_modal_rect(self, instance, value):
        instance.canvas.before.clear()
        with instance.canvas.before:
            Color(1, 1, 1, 1)
            RoundedRectangle(size=instance.size, pos=instance.pos, radius=[dp(20)])
    
    def _load_items(self):
        self.item_list_layout.clear_widgets()
        
        try:
            items = item_service.get_items(category=self.selected_category)
            
            expiry_stats = statistics_service.get_expiry_stats()
            total_items = len(items)
            expiring_count = expiry_stats.get('soon_expiring', 0)
            expired_count = expiry_stats.get('expired', 0)
            
            self.total_card.update_value(str(total_items))
            self.expiring_card.update_value(str(expiring_count))
            self.expired_card.update_value(str(expired_count))
            
            if not items:
                self._show_empty_state()
                return
            
            from datetime import date
            
            if self.selected_filter == 'expiring':
                items = [item for item in items if item.expiry_date and 
                         0 <= (item.expiry_date - date.today()).days <= 3]
            elif self.selected_filter == 'expired':
                items = [item for item in items if item.expiry_date and 
                         (item.expiry_date - date.today()).days < 0]
            
            if not items:
                self._show_empty_state()
                return
            
            for i, item in enumerate(items):
                item_widget = ItemListItem(item)
                item_widget.bind(
                    on_release=lambda inst, item_id=item.id: self._on_item_click(item_id),
                    on_status_changed=lambda inst: self._load_items()
                )
                item_widget.opacity = 0
                item_widget.y -= dp(10)
                self.item_list_layout.add_widget(item_widget)
                
                Clock.schedule_once(
                    lambda dt, w=item_widget: Animation(
                        opacity=1,
                        y=w.y + dp(10),
                        duration=0.25,
                        t='out_cubic'
                    ).start(w),
                    i * 0.05
                )
            
            self.item_count_label.text = f"{len(items)} 项"
            
        except Exception as e:
            logger.error(f"加载物品失败: {e}")
            self._show_empty_state()
    
    def _show_empty_state(self):
        empty_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(200),
            padding=dp(32),
        )
        
        from kivymd.uix.label import MDIcon
        
        empty_icon = MDIcon(
            icon="fridge-outline",
            theme_text_color="Custom",
            text_color=COLORS['text_hint'],
            size_hint_y=None,
            height=dp(64),
            font_size=dp(48),
        )
        empty_container.add_widget(empty_icon)
        
        empty_text = Label(
            text="冰箱空空的",
            font_size=dp(18),
            color=COLORS['text_secondary'],
            size_hint_y=None,
            height=dp(32),
        )
        if CHINESE_FONT:
            empty_text.font_name = CHINESE_FONT
        empty_container.add_widget(empty_text)
        
        hint_text = Label(
            text="点击底部 + 添加你的第一个食材",
            font_size=dp(14),
            color=COLORS['text_hint'],
            size_hint_y=None,
            height=dp(28),
        )
        if CHINESE_FONT:
            hint_text.font_name = CHINESE_FONT
        empty_container.add_widget(hint_text)
        
        self.item_list_layout.add_widget(empty_container)
        self.item_count_label.text = "0 项"
    
    def _on_item_click(self, item_id):
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            app.screen_manager.current = "item_detail"
            detail = app.screen_manager.get_screen("item_detail")
            if detail:
                detail.item_id = item_id
                detail._load_item(item_id)
    
    def _refresh_items(self, dt):
        self._load_items()
    
    def _cleanup_consumed_items(self, dt):
        try:
            item_service.cleanup_consumed_items()
        except Exception as e:
            logger.error(f"清理已消耗物品失败: {e}")
    
    def on_enter(self):
        self._load_items()
    
    def on_leave(self):
        pass
