# -*- coding: utf-8 -*-
"""
食谱屏幕 - 根据冰箱物品推荐菜谱
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.metrics import dp
from kivy.clock import Clock
from kivy.graphics import Rectangle, Color

from app.utils.font_helper import apply_font_to_widget, CHINESE_FONT_NAME as CHINESE_FONT
from app.ui.theme.design_tokens import COLOR_PALETTE

COLORS = COLOR_PALETTE


class StatCard(BoxLayout):
    """统计卡片"""

    def __init__(self, icon, title, value, color, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint = (1, 1)
        self.padding = dp(12)
        self.spacing = dp(4)
        self._color = color
        self.rnd = None
        self._build_ui(icon, title, value)

    def _build_ui(self, icon, title, value):
        from kivymd.uix.label import MDIcon
        from kivy.graphics import Color, RoundedRectangle

        # 绘制背景
        with self.canvas.before:
            Color(*COLORS['surface'])
            self.rnd = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(12)])

        # 更新背景位置的回调
        self.bind(pos=self._update_bg, size=self._update_bg)

        icon_widget = MDIcon(
            icon=icon,
            theme_text_color="Custom",
            text_color=self._color,
            size_hint_y=None,
            height=dp(24),
            font_size=dp(22),
            halign="center",
        )
        self.add_widget(icon_widget)

        value_label = Label(
            text=value,
            font_size=dp(18),
            bold=True,
            color=COLORS['text_primary'],
            size_hint_y=None,
            height=dp(22),
            halign="center",
        )
        self.add_widget(value_label)

        title_label = Label(
            text=title,
            font_size=dp(11),
            color=COLORS['text_hint'],
            size_hint_y=None,
            height=dp(16),
            halign="center",
        )
        self.add_widget(title_label)

    def _update_bg(self, instance, value):
        if self.rnd:
            self.rnd.pos = self.pos
            self.rnd.size = self.size


class RecipeCard(BoxLayout):
    """食谱卡片"""

    def __init__(self, title, description, time, difficulty, ingredients, **kwargs):
        super().__init__(**kwargs)
        self.orientation = 'vertical'
        self.size_hint_y = None
        self.height = dp(140)
        self.padding = dp(16)
        self.spacing = dp(10)
        self.rnd = None
        self._build_content(title, description, time, difficulty, ingredients)

    def _build_content(self, title, description, time, difficulty, ingredients):
        from kivy.graphics import Color, RoundedRectangle

        # 绘制背景
        with self.canvas.before:
            Color(*COLORS['surface'])
            self.rnd = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(16)])

        # 更新背景位置的回调
        self.bind(pos=self._update_bg, size=self._update_bg)

        # 标题行
        title_row = BoxLayout(size_hint_y=None, height=dp(24))
        title_label = Label(
            text=title,
            font_size=dp(16),
            bold=True,
            color=COLORS['text_primary'],
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="middle",
        )
        title_label.bind(size=lambda ins, val: setattr(ins, 'text_size', val))
        title_row.add_widget(title_label)
        self.add_widget(title_row)

        # 描述
        desc_label = Label(
            text=description,
            font_size=dp(13),
            color=COLORS['text_secondary'],
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
        )
        desc_label.bind(size=lambda ins, val: setattr(ins, 'text_size', val))
        self.add_widget(desc_label)

        # 元数据行
        meta_row = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(16))

        time_lbl = Label(
            text=time,
            font_size=dp(12),
            color=COLORS['text_hint'],
            size_hint_x=None,
            width=dp(60),
            halign="left",
            valign="middle",
        )
        time_lbl.bind(size=lambda ins, val: setattr(ins, 'text_size', val))

        diff_lbl = Label(
            text=difficulty,
            font_size=dp(12),
            color=COLORS['text_hint'],
            size_hint_x=None,
            width=dp(60),
            halign="left",
            valign="middle",
        )
        diff_lbl.bind(size=lambda ins, val: setattr(ins, 'text_size', val))

        meta_row.add_widget(time_lbl)
        meta_row.add_widget(diff_lbl)
        meta_row.add_widget(BoxLayout(size_hint_x=1))  # 填充
        self.add_widget(meta_row)

        # 食材标签
        ing_label = Label(
            text=ingredients,
            font_size=dp(12),
            color=COLORS['primary'],
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
        )
        ing_label.bind(size=lambda ins, val: setattr(ins, 'text_size', val))
        self.add_widget(ing_label)

    def _update_bg(self, instance, value):
        if self.rnd:
            self.rnd.pos = self.pos
            self.rnd.size = self.size


class RecipesScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "recipes"
        self._build_ui()
        Clock.schedule_once(lambda *_: self._load_real_stats(), 0.1)

    def _build_ui(self):
        main_layout = BoxLayout(orientation='vertical', size_hint=(1, 1))

        # 背景色
        with main_layout.canvas.before:
            self.bg_color = Color(*COLORS['background'])
            self.bg_rect = Rectangle(pos=main_layout.pos, size=main_layout.size)

        main_layout.bind(pos=self._update_bg_rect, size=self._update_bg_rect)

        # 创建头部区域
        header = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(80),
            padding=(dp(20), dp(20), dp(20), dp(8)),
            spacing=dp(4),
        )

        title = Label(
            text="食谱推荐",
            font_size=dp(22),
            bold=True,
            color=COLORS['text_primary'],
            size_hint_y=None,
            height=dp(30),
            halign="left",
            valign="middle",
        )
        title.bind(size=lambda ins, val: setattr(ins, 'text_size', val))
        header.add_widget(title)

        subtitle = Label(
            text="根据冰箱里的食材，推荐美味菜谱",
            font_size=dp(13),
            color=COLORS['text_secondary'],
            size_hint_y=None,
            height=dp(20),
            halign="left",
            valign="middle",
        )
        subtitle.bind(size=lambda ins, val: setattr(ins, 'text_size', val))
        header.add_widget(subtitle)

        main_layout.add_widget(header)

        # 统计卡片区域
        stats_container = BoxLayout(
            orientation='vertical',
            size_hint_y=None,
            height=dp(96),
            padding=(dp(16), dp(0), dp(16), dp(12)),
        )

        stats_row = BoxLayout(size_hint_y=None, height=dp(84), spacing=dp(12))

        self.ingredient_card = StatCard("food-apple", "可用食材", "0种", COLORS['primary'])
        self.recipe_card = StatCard("silverware-fork-knife", "可做菜谱", "0道", COLORS['accent'])
        self.expiring_card = StatCard("clock-alert", "即将过期", "0种", COLORS['warning'])

        stats_row.add_widget(self.ingredient_card)
        stats_row.add_widget(self.recipe_card)
        stats_row.add_widget(self.expiring_card)

        stats_container.add_widget(stats_row)
        main_layout.add_widget(stats_container)

        # 分隔线
        separator = BoxLayout(size_hint_y=None, height=dp(1), padding=(dp(16), 0, dp(16), 0))

        sep_color = Color(0, 0, 0, 0.05)
        sep_rect = Rectangle(pos=separator.pos, size=separator.size)

        separator.canvas.before.add(sep_color)
        separator.canvas.before.add(sep_rect)

        separator.bind(pos=lambda ins, val: setattr(sep_rect, 'pos', val))
        separator.bind(size=lambda ins, val: setattr(sep_rect, 'size', val))

        main_layout.add_widget(separator)

        # 菜谱标题
        recipe_header = BoxLayout(
            orientation='horizontal',
            size_hint_y=None,
            height=dp(48),
            padding=(dp(16), dp(8), dp(16), dp(8)),
        )

        recipe_title = Label(
            text="推荐菜谱",
            font_size=dp(16),
            bold=True,
            color=COLORS['text_primary'],
            size_hint_y=None,
            height=dp(24),
            halign="left",
            valign="middle",
        )
        recipe_header.add_widget(recipe_title)
        main_layout.add_widget(recipe_header)

        # 滚动区域
        scroll_view = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=dp(3),
            bar_color=(0.2, 0.5, 0.85, 0.3),
            bar_inactive_color=(0.2, 0.5, 0.85, 0.1),
        )

        # 菜谱列表
        self.recipes_layout = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            size_hint_x=1,
            padding=(dp(16), dp(4), dp(16), dp(20)),
            spacing=dp(12),
        )
        self.recipes_layout.bind(minimum_height=self.recipes_layout.setter('height'))

        # 添加示例菜谱
        sample_recipes = [
            ("番茄炒蛋", "经典家常菜，简单易做", "15分钟", "简单", "番茄、鸡蛋、葱"),
            ("蒜蓉西兰花", "清爽健康，低脂营养", "10分钟", "简单", "西兰花、蒜、盐"),
            ("蛋花汤", "暖胃养身，营养丰富", "12分钟", "中等", "鸡蛋、紫菜、葱花"),
            ("凉拌黄瓜", "夏日开胃，清脆爽口", "5分钟", "简单", "黄瓜、蒜、陈醋"),
            ("红烧肉", "经典硬菜，肥而不腻", "45分钟", "困难", "五花肉、酱油、冰糖"),
            ("蛋炒饭", "快速美味，一人食首选", "8分钟", "简单", "米饭、鸡蛋、葱花"),
        ]

        for title, desc, time, diff, ings in sample_recipes:
            recipe_card = RecipeCard(
                title=title,
                description=desc,
                time=time,
                difficulty=diff,
                ingredients=ings,
            )
            self.recipes_layout.add_widget(recipe_card)

        scroll_view.add_widget(self.recipes_layout)
        main_layout.add_widget(scroll_view)

        self.add_widget(main_layout)

    def _update_bg_rect(self, instance, value):
        if hasattr(self, 'bg_rect'):
            self.bg_rect.pos = instance.pos
            self.bg_rect.size = instance.size

    def _load_real_stats(self):
        """加载真实的统计数据"""
        from app.services.item_service import item_service
        from app.models.item import ItemStatus
        from datetime import date, timedelta

        try:
            # 获取活跃物品
            active_items = item_service.get_items(status=ItemStatus.ACTIVE)

            # 按名称分组统计唯一食材
            ingredient_names = set()
            expiring_count = 0

            today = date.today()
            tomorrow = today + timedelta(days=3)

            for item in active_items:
                ingredient_names.add(item.name)

                # 即将过期统计
                if item.expiry_date:
                    days_until = (item.expiry_date - today).days
                    if 0 <= days_until <= 3:
                        expiring_count += 1

            # 可做菜谱（简单估算，假设每道菜平均需要2-3种食材）
            recipe_count = max(0, len(ingredient_names) // 2)

            # 更新卡片
            for i, card in enumerate([self.ingredient_card, self.recipe_card, self.expiring_card]):
                # children 顺序是: [图标, 值, 标题]
                # 但由于BoxLayout是反向顺序访问的，所以 children[1] 是值
                if i == 0:
                    card.children[1].text = f"{len(ingredient_names)}种"
                elif i == 1:
                    card.children[1].text = f"{recipe_count}道"
                elif i == 2:
                    card.children[1].text = f"{expiring_count}种"

        except Exception as e:
            print(f"加载统计数据失败: {e}")

    def on_enter(self):
        if CHINESE_FONT:
            apply_font_to_widget(self, CHINESE_FONT)
        self._load_real_stats()
