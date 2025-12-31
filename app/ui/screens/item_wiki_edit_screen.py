from kivy.uix.screenmanager import Screen
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.scrollview import ScrollView
from kivy.uix.label import Label
from kivy.uix.button import Button
from kivy.uix.spinner import Spinner
from kivy.uix.textinput import TextInput
from kivy.metrics import dp
from kivy.graphics import Color, RoundedRectangle
from kivy.clock import Clock
from kivymd.app import MDApp

import logging
from app.services.wiki_service import wiki_service
from app.ui.theme.design_tokens import COLOR_PALETTE, DESIGN_TOKENS
from app.utils.font_helper import CHINESE_FONT_NAME as CHINESE_FONT

logger = logging.getLogger(__name__)

COLORS = COLOR_PALETTE
FONTS = DESIGN_TOKENS


class ItemWikiEditScreen(Screen):
    """物品Wiki编辑页"""
    wiki_id = None
    wiki_name = ""
    
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "item_wiki_edit"
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
        )
        if CHINESE_FONT:
            self._category_spinner.font_name = CHINESE_FONT
        form_box.add_widget(self._category_spinner)
        
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
        
        form_box.height = dp(16) * 2 + dp(20) * 8 + dp(44) * 5 + dp(100) * 2 + dp(12) * 8
        content_box.add_widget(form_box)
        
        scroll.add_widget(content_box)
        main_layout.add_widget(scroll)
        
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
                self._name_input.text = wiki_item['name']
                self._description_input.text = wiki_item['description'] or ""
                self._unit_input.text = wiki_item['default_unit'] or ""
                self._expiry_input.text = str(wiki_item['suggested_expiry_days']) if wiki_item['suggested_expiry_days'] else ""
                self._location_input.text = wiki_item['storage_location'] or ""
                self._notes_input.text = wiki_item['notes'] or ""
                
                if wiki_item['category_name']:
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
            
            logger.info(f"准备保存Wiki: name={name}, category_id={category_id}, description={description}, unit={default_unit}, expiry={suggested_expiry_days}, location={storage_location}, notes={notes}")
            
            if self.wiki_id:
                logger.info(f"更新现有Wiki: {self.wiki_id}")
                success = wiki_service.update_wiki(
                    self.wiki_id,
                    name=name,
                    description=description,
                    default_unit=default_unit,
                    suggested_expiry_days=suggested_expiry_days,
                    storage_location=storage_location,
                    notes=notes,
                    category_id=category_id,
                )
                
                logger.info(f"更新结果: {success}")
                if success:
                    logger.info(f"物品Wiki更新成功: {name}")
                    self._navigate_back()
                else:
                    logger.error("物品Wiki更新失败")
            else:
                logger.info(f"创建新Wiki")
                new_wiki = wiki_service.create_wiki(
                    name=name,
                    description=description,
                    default_unit=default_unit,
                    suggested_expiry_days=suggested_expiry_days,
                    storage_location=storage_location,
                    notes=notes,
                    category_id=category_id,
                )
                
                logger.info(f"创建结果: {new_wiki}")
                if new_wiki:
                    logger.info(f"物品Wiki创建成功: {name}")
                    self.wiki_id = new_wiki['id']
                    self._navigate_back()
                else:
                    logger.error("物品Wiki创建失败")
                    
        except Exception as e:
            logger.error(f"保存物品Wiki失败: {str(e)}")
    
    def _navigate_back(self):
        app = MDApp.get_running_app()
        if hasattr(app, "screen_manager"):
            detail_screen = app.screen_manager.get_screen("item_wiki_detail")
            if detail_screen:
                detail_screen.load_wiki_item(self._name_input.text)
            app.screen_manager.current = "item_wiki_detail"
    
    def on_enter(self):
        pass
    
    def on_leave(self):
        pass
