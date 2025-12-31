# -*- coding: utf-8 -*-
"""
食谱屏幕 - 根据冰箱物品推荐菜谱
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.properties import ColorProperty
from kivy.clock import Clock

from app.utils.font_helper import apply_font_to_widget, CHINESE_FONT_NAME as CHINESE_FONT


COLORS = {
    "primary": (0.29, 0.56, 0.85, 1),
    "primary_dark": (0.2, 0.45, 0.75, 1),
    "accent": (0.95, 0.6, 0.2, 1),
    "bg": (0.98, 0.98, 0.98, 1),
    "card_bg": (1, 1, 1, 1),
    "text_primary": (0.2, 0.2, 0.2, 1),
    "text_secondary": (0.5, 0.5, 0.5, 1),
    "text_hint": (0.7, 0.7, 0.7, 1),
    "success": (0.3, 0.75, 0.5, 1),
    "warning": (0.95, 0.7, 0.2, 1),
    "divider": (0.9, 0.9, 0.9, 1),
}


class AnimatedCard(BoxLayout):
    bg_color = ColorProperty((1, 1, 1, 1))

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "vertical"
        self.padding = dp(16)
        self.spacing = dp(12)
        self.size_hint_y = None
        self.height = dp(140)
        self.bg_color = COLORS["card_bg"]
        self.bind(size=self._update_canvas, pos=self._update_canvas)

    def _update_canvas(self, *args):
        self.canvas.before.clear()
        from kivy.graphics import Color, RoundedRectangle
        with self.canvas.before:
            Color(*self.bg_color)
            RoundedRectangle(
                size=self.size,
                pos=self.pos,
                radius=[dp(16)]
            )

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            anim = Animation(scale_x=0.97, scale_y=0.97, duration=0.08, t="out_quad")
            anim.bind(on_complete=lambda *_: Animation(
                scale_x=1.0, scale_y=1.0, duration=0.12, t="in_out_quad"
            ).start(self))
            anim.start(self)
        return super().on_touch_down(touch)


class RecipeCard(AnimatedCard):
    def __init__(self, title="", description="", time="", difficulty="", ingredients="", **kwargs):
        super().__init__(**kwargs)
        self.height = dp(160)
        self._build_content(title, description, time, difficulty, ingredients)

    def _build_content(self, title, description, time, difficulty, ingredients):
        title_lbl = Label(
            text=title,
            font_size=dp(18),
            bold=True,
            color=COLORS["text_primary"],
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="middle",
        )
        title_lbl.bind(size=lambda ins, val: setattr(ins, 'text_size', val))

        desc_lbl = Label(
            text=description,
            font_size=dp(13),
            color=COLORS["text_secondary"],
            size_hint_y=None,
            height=dp(36),
            halign="left",
            valign="top",
        )
        desc_lbl.bind(size=lambda ins, val: setattr(ins, 'text_size', val))

        meta_layout = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(16))
        time_lbl = Label(
            text=f"⏱ {time}",
            font_size=dp(12),
            color=COLORS["text_hint"],
            size_hint_x=None,
            width=dp(80),
        )
        diff_lbl = Label(
            text=f"📊 {difficulty}",
            font_size=dp(12),
            color=COLORS["text_hint"],
            size_hint_x=None,
            width=dp(80),
        )
        meta_layout.add_widget(time_lbl)
        meta_layout.add_widget(diff_lbl)

        ing_lbl = Label(
            text=f"🥗 {ingredients}",
            font_size=dp(12),
            color=COLORS["primary"],
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
        )
        ing_lbl.bind(size=lambda ins, val: setattr(ins, 'text_size', val))

        self.add_widget(title_lbl)
        self.add_widget(desc_lbl)
        self.add_widget(meta_layout)
        self.add_widget(ing_lbl)


class RecipesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "recipes"
        self._build_ui()
        Clock.schedule_once(lambda *_: self._animate_entrance(), 0.1)

    def _build_ui(self):
        from kivymd.uix.label import MDIcon
        from kivy.uix.scrollview import ScrollView
        from kivy.uix.gridlayout import GridLayout

        root = FloatLayout()
        bg_label = Label(
            size_hint_y=None,
            height=Window.size[1] if hasattr(Window, 'size') else dp(640),
            pos_hint={'x': 0, 'y': 0},
            color=(0, 0, 0, 0),
        )
        with bg_label.canvas.before:
            from kivy.graphics import Color, Rectangle
            bg_color = Color(*COLORS["bg"])
            bg_rect = Rectangle(size=bg_label.size, pos=bg_label.pos)
        bg_label.bind(size=lambda ins, val: setattr(bg_rect, 'size', val))
        bg_label.bind(pos=lambda ins, val: setattr(bg_rect, 'pos', val))
        root.add_widget(bg_label)

        header = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            height=dp(120),
            padding=(dp(20), dp(16), dp(20), dp(8)),
            pos_hint={'top': 1},
        )
        header.add_widget(Label(
            text="食谱推荐",
            font_size=dp(26),
            bold=True,
            color=COLORS["text_primary"],
            size_hint_y=None,
            height=dp(36),
        ))
        header.add_widget(Label(
            text="根据冰箱里的食材，推荐美味菜谱",
            font_size=dp(14),
            color=COLORS["text_secondary"],
            size_hint_y=None,
            height=dp(20),
        ))
        root.add_widget(header)

        stats_row = BoxLayout(
            size_hint_y=None,
            height=dp(70),
            padding=(dp(16), dp(0), dp(16), dp(0)),
            spacing=dp(12),
        )
        stat_cards = [
            ("🥬", "可用食材", "8种"),
            ("🍳", "可做菜谱", "12道"),
            ("⏰", "即将过期", "2种"),
        ]
        for icon, label, value in stat_cards:
            card = BoxLayout(
                orientation="vertical",
                size_hint_x=1,
                padding=dp(12),
                spacing=dp(4),
            )
            from kivy.graphics import Color, RoundedRectangle
            with card.canvas.before:
                bg_color = Color(*COLORS["card_bg"])
                bg_rect = RoundedRectangle(size=card.size, pos=card.pos, radius=[dp(12)])
            card.bind(size=lambda ins, val: setattr(bg_rect, 'size', val))
            card.bind(pos=lambda ins, val: setattr(bg_rect, 'pos', val))
            card.add_widget(MDIcon(
                icon=icon,
                font_size=dp(24),
                theme_icon_color="Custom",
                icon_color=COLORS["primary"],
            ))
            lbl = Label(
                text=f"{value}",
                font_size=dp(16),
                bold=True,
                color=COLORS["text_primary"],
                size_hint_y=None,
                height=dp(20),
            )
            sub_lbl = Label(
                text=label,
                font_size=dp(11),
                color=COLORS["text_hint"],
                size_hint_y=None,
                height=dp(16),
            )
            card.add_widget(lbl)
            card.add_widget(sub_lbl)
            stats_row.add_widget(card)
        root.add_widget(stats_row)

        section_title = Label(
            text="推荐菜谱",
            font_size=dp(16),
            bold=True,
            color=COLORS["text_primary"],
            size_hint_y=None,
            height=dp(28),
            pos_hint={'x': 0, 'y': 0.52},
            padding_x=dp(16),
        )
        root.add_widget(section_title)

        recipes_layout = GridLayout(
            cols=1,
            size_hint_y=None,
            height=dp(500),
            padding=(dp(16), dp(0), dp(16), dp(16)),
            spacing=dp(12),
        )

        sample_recipes = [
            ("番茄炒蛋", "经典家常菜，5分钟搞定", "15分钟", "简单", "番茄+鸡蛋+葱"),
            ("蒜蓉西兰花", "清爽健康，低脂美味", "10分钟", "简单", "西兰花+蒜+盐"),
            ("蛋花汤", "暖胃养身，营养丰富", "12分钟", "中等", "鸡蛋+紫菜+葱"),
            ("凉拌黄瓜", "夏日开胃小菜", "5分钟", "简单", "黄瓜+蒜+醋"),
        ]
        for title, desc, time, diff, ings in sample_recipes:
            recipe_card = RecipeCard(
                title=title,
                description=desc,
                time=time,
                difficulty=diff,
                ingredients=ings,
            )
            recipes_layout.add_widget(recipe_card)

        scroll = ScrollView(
            size_hint=(1, 0.58),
            pos_hint={'y': 0.05},
            bar_width=dp(4),
            scroll_type=['content'],
        )
        scroll.add_widget(recipes_layout)
        root.add_widget(scroll)

        self.add_widget(root)

    def _animate_entrance(self):
        for i, child in enumerate(self.children):
            if isinstance(child, FloatLayout):
                for j, subchild in enumerate(child.children):
                    anim = Animation(
                        opacity=1,
                        y=subchild.y + dp(20) if hasattr(subchild, 'y') else 0,
                        duration=0.3,
                        t="out_quad"
                    )
                    anim.start(subchild)

    def on_enter(self):
        if CHINESE_FONT:
            apply_font_to_widget(self, CHINESE_FONT)


from kivy.core.window import Window


