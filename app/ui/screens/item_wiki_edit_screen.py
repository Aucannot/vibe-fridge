# -*- coding: utf-8 -*-
"""
物品Wiki编辑页
"""

from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner, SpinnerOption
from kivy.uix.textinput import TextInput
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
from kivy.properties import StringProperty, ObjectProperty
from kivymd.app import MDApp

import logging
from app.services.wiki_service import wiki_service
from app.ui.theme.design_tokens import COLOR_PALETTE, DESIGN_TOKENS
from app.ui.widgets.icon_picker import IconPicker
from app.utils.font_helper import CHINESE_FONT_NAME as CHINESE_FONT

logger = logging.getLogger(__name__)

COLORS = COLOR_PALETTE
FONTS = DESIGN_TOKENS


class CustomSpinnerOption(SpinnerOption):
    """自定义下拉选项 - 支持中文字体"""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.background_color = COLORS['surface']
        self.height = dp(44)
        self.font_size = dp(16)
        if CHINESE_FONT:
            self.font_name = CHINESE_FONT


class IconSelectButton(BoxLayout):
    """图标选择按钮组件"""
    __events__ = ('on_release',)

    icon_name = StringProperty("")
    on_icon_change = ObjectProperty(None)

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.size_hint_x = 1
        self.height = dp(48)
        self.padding = (dp(12), dp(8), dp(12), dp(8))
        self.spacing = dp(12)

        self._build_ui()

    def _build_ui(self):
        # 背景色
        with self.canvas.before:
            Color(*COLORS['background'])
            self._bg_rect = RoundedRectangle(pos=self.pos, size=self.size, radius=[dp(8)])
        self.bind(pos=self._update_canvas, size=self._update_canvas)

        # 图标预览
        icon_display = self.icon_name if self.icon_name else "help-circle-outline"
        # 延迟导入 MDIcon
        try:
            from kivymd.uix.label import MDIcon
            self._icon_preview = MDIcon(
                icon=icon_display,
                size_hint_x=None,
                width=dp(32),
                size_hint_y=None,
                height=dp(32),
                font_size=dp(24),
                halign="center",
                valign="middle"
            )
            self._icon_preview.color = COLORS['primary']
            self._icon_is_mdicon = True
        except ImportError:
            # 降级使用 Label
            self._icon_preview = Label(
                text=icon_display,
                size_hint_x=None,
                width=dp(32),
                size_hint_y=None,
                height=dp(32),
                color=COLORS['primary'],
                font_name="MaterialIcons",
                font_size=dp(28),
            )
            self._icon_is_mdicon = False

        self.add_widget(self._icon_preview)

        # 文字说明
        self._label = Label(
            text=self.icon_name if self.icon_name else "点击选择图标",
            size_hint_x=1,
            size_hint_y=None,
            height=dp(32),
            halign="left",
            valign="middle",
            color=COLORS['text_primary'],
            font_size=dp(16),
        )
        if CHINESE_FONT:
            self._label.font_name = CHINESE_FONT
        self.add_widget(self._label)

        # 右侧箭头
        arrow_label = Label(
            text="›",
            size_hint_x=None,
            width=dp(24),
            size_hint_y=None,
            height=dp(32),
            color=COLORS['text_hint'],
        )
        self.add_widget(arrow_label)

    def _update_canvas(self, *args):
        if hasattr(self, '_bg_rect'):
            self._bg_rect.pos = self.pos
            self._bg_rect.size = self.size

    def set_icon(self, icon_name: str):
        """设置图标"""
        self.icon_name = icon_name
        icon_display = icon_name if icon_name else "help-circle-outline"

        # 根据图标类型更新
        if self._icon_is_mdicon:
            # KivyMD MDIcon 组件
            self._icon_preview.icon = icon_display
        else:
            # 使用 Label 显示图标（使用字体）
            self._icon_preview.text = icon_display
            self._icon_preview.font_name = "MaterialIcons"
            self._icon_preview.font_size = dp(28)

        self._label.text = icon_name if icon_name else "点击选择图标"

    def on_touch_down(self, touch):
        if self.collide_point(*touch.pos):
            self.dispatch('on_release')
            return True
        return super().on_touch_down(touch)

    def on_release(self):
        pass


class ItemWikiEditScreen(Screen):
    """物品Wiki编辑页"""
    wiki_id = None
    wiki_name = ""
    wiki_icon = ""
    _icon_picker = None

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "item_wiki_edit"
        self.form_data = {
            'name': '',
            'icon': '',
            'category': '',
            'default_unit': '',
            'suggested_expiry_days': '',
            'storage_location': '',
            'description': '',
            'notes': ''
        }
        self._build_ui()

    def _build_ui(self):
        main_layout = BoxLayout(orientation="vertical", padding=dp(16), spacing=dp(16))

        scroll = ScrollView(
            size_hint=(1, 1),
            do_scroll_x=False,
            bar_width=dp(3),
            bar_color=COLORS['primary'],
            bar_inactive_color=COLORS['divider'],
        )

        content_box = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(16))
        content_box.bind(minimum_height=content_box.setter("height"))

        title_label = Label(
            text="编辑物品Wiki",
            font_size=dp(24),
            color=COLORS['text_primary'],
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(32),
            text_size=(None, dp(32)),
            bold=True,
        )
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        content_box.add_widget(title_label)

        form_box = BoxLayout(orientation="vertical", size_hint_y=None, size_hint_x=1, padding=dp(16), spacing=dp(12))
        with form_box.canvas.before:
            Color(*COLORS['surface'])
            form_rect = RoundedRectangle(pos=form_box.pos, size=form_box.size, radius=[dp(12)])
        form_box.bind(pos=lambda i, v: setattr(form_rect, 'pos', v), size=lambda i, v: setattr(form_rect, 'size', v))

        # 图标选择
        icon_label = Label(
            text="物品图标",
            font_size=dp(14),
            color=COLORS['text_secondary'],
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(20),
            text_size=(None, dp(20)),
        )
        if CHINESE_FONT:
            icon_label.font_name = CHINESE_FONT
        form_box.add_widget(icon_label)

        self._icon_button = IconSelectButton()
        self._icon_button.bind(on_release=self._on_icon_select)
        form_box.add_widget(self._icon_button)

        # 物品名称
        name_label = Label(
            text="物品名称",
            font_size=dp(14),
            color=COLORS['text_secondary'],
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(20),
            text_size=(None, dp(20)),
        )
        if CHINESE_FONT:
            name_label.font_name = CHINESE_FONT
        form_box.add_widget(name_label)

        self._name_input = TextInput(
            size_hint_y=None,
            height=dp(44),
            font_size=dp(16),
            background_color=COLORS['background'],
            foreground_color=COLORS['text_primary'],
            cursor_color=COLORS['primary'],
            multiline=False,
            padding=(dp(12), dp(12)),
        )
        if CHINESE_FONT:
            self._name_input.font_name = CHINESE_FONT
        form_box.add_widget(self._name_input)

        # 分类选择
        category_label = Label(
            text="分类",
            font_size=dp(14),
            color=COLORS['text_secondary'],
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(20),
            text_size=(None, dp(20)),
        )
        if CHINESE_FONT:
            category_label.font_name = CHINESE_FONT
        form_box.add_widget(category_label)

        self._category_spinner = Spinner(
            size_hint_y=None,
            height=dp(44),
            font_size=dp(16),
            background_color=COLORS['background'],
            text="选择分类",
            values=[],
            option_cls='CustomSpinnerOption',
        )
        if CHINESE_FONT:
            self._category_spinner.font_name = CHINESE_FONT
        form_box.add_widget(self._category_spinner)

        # 默认单位
        unit_label = Label(
            text="默认单位",
            font_size=dp(14),
            color=COLORS['text_secondary'],
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(20),
            text_size=(None, dp(20)),
        )
        if CHINESE_FONT:
            unit_label.font_name = CHINESE_FONT
        form_box.add_widget(unit_label)

        self._unit_input = TextInput(
            size_hint_y=None,
            height=dp(44),
            font_size=dp(16),
            background_color=COLORS['background'],
            foreground_color=COLORS['text_primary'],
            cursor_color=COLORS['primary'],
            multiline=False,
            padding=(dp(12), dp(12)),
            hint_text="例如：个、盒、瓶、袋等",
        )
        if CHINESE_FONT:
            self._unit_input.font_name = CHINESE_FONT
        form_box.add_widget(self._unit_input)

        # 建议保质期
        expiry_label = Label(
            text="建议保质期（天）",
            font_size=dp(14),
            color=COLORS['text_secondary'],
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(20),
            text_size=(None, dp(20)),
        )
        if CHINESE_FONT:
            expiry_label.font_name = CHINESE_FONT
        form_box.add_widget(expiry_label)

        self._expiry_input = TextInput(
            size_hint_y=None,
            height=dp(44),
            font_size=dp(16),
            background_color=COLORS['background'],
            foreground_color=COLORS['text_primary'],
            cursor_color=COLORS['primary'],
            multiline=False,
            padding=(dp(12), dp(12)),
            hint_text="例如：7、30、365等",
            input_filter="int",
        )
        if CHINESE_FONT:
            self._expiry_input.font_name = CHINESE_FONT
        form_box.add_widget(self._expiry_input)

        # 存放位置
        location_label = Label(
            text="存放位置",
            font_size=dp(14),
            color=COLORS['text_secondary'],
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(20),
            text_size=(None, dp(20)),
        )
        if CHINESE_FONT:
            location_label.font_name = CHINESE_FONT
        form_box.add_widget(location_label)

        self._location_input = TextInput(
            size_hint_y=None,
            height=dp(44),
            font_size=dp(16),
            background_color=COLORS['background'],
            foreground_color=COLORS['text_primary'],
            cursor_color=COLORS['primary'],
            multiline=False,
            padding=(dp(12), dp(12)),
            hint_text="例如：冷藏、常温、冷冻等",
        )
        if CHINESE_FONT:
            self._location_input.font_name = CHINESE_FONT
        form_box.add_widget(self._location_input)

        # 描述
        description_label = Label(
            text="物品描述",
            font_size=dp(14),
            color=COLORS['text_secondary'],
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(20),
            text_size=(None, dp(20)),
        )
        if CHINESE_FONT:
            description_label.font_name = CHINESE_FONT
        form_box.add_widget(description_label)

        self._description_input = TextInput(
            size_hint_y=None,
            height=dp(100),
            font_size=dp(14),
            background_color=COLORS['background'],
            foreground_color=COLORS['text_primary'],
            cursor_color=COLORS['primary'],
            multiline=True,
            padding=(dp(12), dp(12)),
            hint_text="输入物品的详细描述...",
        )
        if CHINESE_FONT:
            self._description_input.font_name = CHINESE_FONT
        form_box.add_widget(self._description_input)

        # 备注
        notes_label = Label(
            text="备注",
            font_size=dp(14),
            color=COLORS['text_secondary'],
            halign="left",
            valign="middle",
            size_hint_y=None,
            height=dp(20),
            text_size=(None, dp(20)),
        )
        if CHINESE_FONT:
            notes_label.font_name = CHINESE_FONT
        form_box.add_widget(notes_label)

        self._notes_input = TextInput(
            size_hint_y=None,
            height=dp(100),
            font_size=dp(14),
            background_color=COLORS['background'],
            foreground_color=COLORS['text_primary'],
            cursor_color=COLORS['primary'],
            multiline=True,
            padding=(dp(12), dp(12)),
            hint_text="输入其他备注信息...",
        )
        if CHINESE_FONT:
            self._notes_input.font_name = CHINESE_FONT
        form_box.add_widget(self._notes_input)

        form_box.height = dp(16) * 2 + dp(20) * 9 + dp(44) * 5 + dp(48) + dp(100) * 2 + dp(12) * 9
        content_box.add_widget(form_box)

        scroll.add_widget(content_box)
        main_layout.add_widget(scroll)

        # 按钮栏
        button_box = BoxLayout(orientation="horizontal", size_hint_y=None, height=dp(48), spacing=dp(12))

        cancel_button = Button(
            text="取消",
            size_hint_x=1,
            font_size=dp(16),
            background_color=COLORS['surface'],
            color=COLORS['text_secondary'],
        )
        if CHINESE_FONT:
            cancel_button.font_name = CHINESE_FONT
        cancel_button.bind(on_release=self._on_cancel)
        button_box.add_widget(cancel_button)

        save_button = Button(
            text="保存",
            size_hint_x=1,
            font_size=dp(16),
            background_color=COLORS['primary'],
            color=(1, 1, 1, 1),
        )
        if CHINESE_FONT:
            save_button.font_name = CHINESE_FONT
        save_button.bind(on_release=self._on_save)
        button_box.add_widget(save_button)

        main_layout.add_widget(button_box)

        self.add_widget(main_layout)

    def load_wiki(self, wiki_name: str):
        """加载要编辑的物品Wiki"""
        try:
            self.wiki_name = wiki_name
            wiki_item = wiki_service.get_wiki_by_name(wiki_name)

            if wiki_item:
                self.wiki_id = wiki_item['id']
                self.wiki_icon = wiki_item.get('icon', '')

                # 填充表单
                self._name_input.text = wiki_item['name']
                self._icon_button.set_icon(self.wiki_icon)
                self._description_input.text = wiki_item.get('description') or ""
                self._unit_input.text = wiki_item.get('default_unit') or ""
                self._expiry_input.text = str(wiki_item.get('suggested_expiry_days', '')) if wiki_item.get('suggested_expiry_days') else ""
                self._location_input.text = wiki_item.get('storage_location') or ""
                self._notes_input.text = wiki_item.get('notes') or ""

                if wiki_item.get('category_name'):
                    self._category_spinner.text = wiki_item['category_name']
            else:
                logger.warning(f"物品Wiki不存在: {wiki_name}")
                self._name_input.text = wiki_name

            self._load_categories()

        except Exception as e:
            logger.error(f"加载物品Wiki失败: {str(e)}")

    def _load_categories(self):
        """加载分类列表"""
        try:
            categories = wiki_service.get_all_categories()
            category_names = [cat.name for cat in categories]
            self._category_spinner.values = category_names

            if not category_names:
                self._category_spinner.text = "暂无分类"

        except Exception as e:
            logger.error(f"加载分类列表失败: {str(e)}")

    def _on_icon_select(self, instance):
        """打开图标选择器"""
        if self._icon_picker is None:
            self._icon_picker = IconPicker(current_icon=self.wiki_icon)
            self._icon_picker.on_icon_selected = self._icon_selected
        else:
            self._icon_picker.current_icon = self.wiki_icon
            self._icon_picker.selected_icon = self.wiki_icon

        self._icon_picker.show()

    def _icon_selected(self, icon_name: str):
        """图标选择回调"""
        self.wiki_icon = icon_name
        self._icon_button.set_icon(icon_name)

    def _on_cancel(self, instance):
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            app.screen_manager.current = "item_wiki_detail"

    def _on_save(self, instance):
        try:
            name = self._name_input.text.strip()
            if not name:
                logger.warning("物品名称不能为空")
                return

            category_name = self._category_spinner.text
            category_id = None
            if category_name and category_name != "选择分类" and category_name != "暂无分类":
                categories = wiki_service.get_all_categories()
                for cat in categories:
                    if cat.name == category_name:
                        category_id = cat.id
                        break

            description = self._description_input.text.strip() or None
            default_unit = self._unit_input.text.strip() or None
            suggested_expiry_days = None
            if self._expiry_input.text.strip():
                try:
                    suggested_expiry_days = int(self._expiry_input.text.strip())
                except ValueError:
                    pass
            storage_location = self._location_input.text.strip() or None
            notes = self._notes_input.text.strip() or None

            logger.info(f"准备保存Wiki: name={name}, icon={self.wiki_icon}, category_id={category_id}")

            updates = {
                'name': name,
                'icon': self.wiki_icon or None,
                'description': description,
                'default_unit': default_unit,
                'suggested_expiry_days': suggested_expiry_days,
                'storage_location': storage_location,
                'notes': notes,
            }
            if category_id:
                updates['category_id'] = category_id

            if self.wiki_id:
                success = wiki_service.update_wiki(self.wiki_id, **updates)
                if success:
                    logger.info(f"物品Wiki更新成功: {name}")
                    self._navigate_back()
                else:
                    logger.error("物品Wiki更新失败")
            else:
                new_wiki = wiki_service.create_wiki(**updates)
                if new_wiki:
                    logger.info(f"物品Wiki创建成功: {name}")
                    self.wiki_id = new_wiki['id']
                    self.wiki_name = name
                    self._navigate_back()
                else:
                    logger.error("物品Wiki创建失败")

        except Exception as e:
            logger.error(f"保存物品Wiki失败: {str(e)}")

    def _navigate_back(self):
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            # 返回详情页后，让 ItemsScreen 刷新
            items_screen = app.screen_manager.get_screen("items")
            if items_screen:
                items_screen.refresh_data()

            detail_screen = app.screen_manager.get_screen("item_wiki_detail")
            if detail_screen:
                detail_screen.load_wiki_item(self._name_input.text)
            app.screen_manager.current = "item_wiki_detail"

    def on_enter(self):
        pass

    def on_leave(self):
        pass
