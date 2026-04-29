# -*- coding: utf-8 -*-
"""
设置屏幕
"""

import os

from kivy.graphics import Color, Line, Rectangle, RoundedRectangle
from kivy.metrics import dp
from kivy.properties import BooleanProperty
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.label import Label
from kivy.uix.modalview import ModalView
from kivy.uix.screenmanager import Screen
from kivy.uix.scrollview import ScrollView
from kivymd.uix.card import MDCard
from kivymd.uix.label import MDIcon

from app.services.database import db_service
from app.services.order_import_service import (
    DEFAULT_MODEL,
    LEGACY_SILICONFLOW_API_KEY_ENV,
    LEGACY_SILICONFLOW_API_KEY_SETTING,
    LEGACY_SILICONFLOW_MODEL_ENV,
    LEGACY_SILICONFLOW_MODEL_SETTING,
    SILICONFLOW_API_KEY_ENV,
    SILICONFLOW_API_KEY_SETTING,
    SILICONFLOW_MODEL_ENV,
    SILICONFLOW_MODEL_SETTING,
)
from app.ui.screens.add_item_screen import FridgeButton, FridgeTextInput
from app.ui.theme.design_tokens import COLOR_PALETTE, get_card_style, get_font_size
from app.utils.font_helper import CHINESE_FONT_NAME as CHINESE_FONT
from app.utils.font_helper import apply_font_to_widget

COLORS = COLOR_PALETTE
SECTION_CARD = get_card_style("section")
LIST_CARD = get_card_style("list")


def _bind_label_text(widget, horizontal_padding=0):
    widget.bind(
        size=lambda inst, val: setattr(
            inst, "text_size", (max(0, val[0] - horizontal_padding), None)
        )
    )


class SettingsSectionHeader(Label):
    def __init__(self, text, **kwargs):
        super().__init__(**kwargs)
        self.text = text
        self.size_hint_y = None
        self.height = dp(26)
        self.halign = "left"
        self.valign = "middle"
        self.font_size = dp(get_font_size("label_large"))
        self.color = COLORS["primary"]
        _bind_label_text(self)
        if CHINESE_FONT:
            self.font_name = CHINESE_FONT


class ThemedSwitch(ButtonBehavior, BoxLayout):
    active = BooleanProperty(False)

    def __init__(self, active=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint = (None, None)
        self.size = (dp(56), dp(32))
        self.active = active
        self.bind(pos=self._redraw, size=self._redraw, active=self._redraw)
        self._redraw()

    def _redraw(self, *_args):
        radius = self.height / 2
        inset = dp(3)
        knob_size = self.height - inset * 2
        knob_x = self.right - inset - knob_size if self.active else self.x + inset
        track_color = COLORS["primary"] if self.active else COLORS["surface_variant"]
        border_color = None if self.active else COLORS["divider"]

        self.canvas.before.clear()
        self.canvas.after.clear()
        with self.canvas.before:
            Color(*track_color)
            RoundedRectangle(pos=self.pos, size=self.size, radius=[radius])
        with self.canvas.after:
            if border_color:
                Color(*border_color)
                Line(
                    width=dp(1),
                    rounded_rectangle=(self.x, self.y, self.width, self.height, radius),
                )
            Color(*COLORS["surface"])
            RoundedRectangle(
                pos=(knob_x, self.y + inset),
                size=(knob_size, knob_size),
                radius=[knob_size / 2],
            )

    def on_release(self, *_args):
        self.active = not self.active


class SettingsRow(BoxLayout):
    def __init__(self, icon, title, subtitle="", show_switch=False, danger=False, **kwargs):
        super().__init__(**kwargs)
        self.orientation = "horizontal"
        self.size_hint_y = None
        self.height = dp(82)
        self.padding = (dp(14), dp(12), dp(14), dp(12))
        self.spacing = dp(12)
        self._danger = danger
        self._build_ui(icon, title, subtitle, show_switch)
        self.bind(pos=self._redraw, size=self._redraw)
        self._redraw()

    def _build_ui(self, icon, title, subtitle, show_switch):
        icon_shell = BoxLayout(
            orientation="vertical",
            size_hint=(None, None),
            width=dp(42),
            height=dp(42),
            padding=dp(9),
        )
        with icon_shell.canvas.before:
            Color(
                *(
                    COLORS["error_container"]
                    if self._danger
                    else COLORS["surface_tint"]
                )
            )
            self._icon_bg = RoundedRectangle(
                pos=icon_shell.pos, size=icon_shell.size, radius=[dp(14)]
            )
        icon_shell.bind(
            pos=lambda inst, _val: setattr(self._icon_bg, "pos", inst.pos),
            size=lambda inst, _val: setattr(self._icon_bg, "size", inst.size),
        )
        icon_shell.add_widget(
            MDIcon(
                icon=icon,
                theme_text_color="Custom",
                text_color=COLORS["error"] if self._danger else COLORS["primary"],
                halign="center",
                valign="middle",
                font_size=dp(22),
            )
        )
        self.add_widget(icon_shell)

        text_box = BoxLayout(orientation="vertical", spacing=dp(2))

        title_label = Label(
            text=title,
            size_hint_y=None,
            height=dp(22),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_small")),
            bold=True,
            color=COLORS["error"] if self._danger else COLORS["text_primary"],
        )
        _bind_label_text(title_label)
        if CHINESE_FONT:
            title_label.font_name = CHINESE_FONT
        text_box.add_widget(title_label)

        if subtitle:
            subtitle_label = Label(
                text=subtitle,
                halign="left",
                valign="top",
                font_size=dp(get_font_size("body_small")),
                color=COLORS["text_secondary"],
            )
            _bind_label_text(subtitle_label)
            if CHINESE_FONT:
                subtitle_label.font_name = CHINESE_FONT
            text_box.add_widget(subtitle_label)

        self.add_widget(text_box)

        if show_switch:
            switch = ThemedSwitch(active=False)
            self.add_widget(switch)
        else:
            chevron = MDIcon(
                icon="chevron-right",
                theme_text_color="Custom",
                text_color=COLORS["text_hint"],
                size_hint=(None, None),
                size=(dp(18), dp(18)),
                font_size=dp(18),
            )
            self.add_widget(chevron)

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


class SettingsScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "settings"
        self.model_input = None
        self.api_key_input = None
        self.api_key_row = None
        self.api_key_editor = None
        self.api_status_label = None
        self.model_hint_label = None
        self.api_hint_label = None
        self._editing_api_key = False
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
            spacing=dp(12),
        )
        content.bind(minimum_height=content.setter("height"))

        self._add_section(
            content,
            "通知与提醒",
            [
                ("bell-ring-outline", "过期提醒", "提前推送即将过期物品", True, False),
                ("cart-outline", "购物提醒", "库存不足时提醒补货", True, False),
            ],
        )
        self._add_section(
            content,
            "显示与阅读",
            [
                ("palette-outline", "主题颜色", "当前主题：fresh utility", False, False),
                ("format-size", "字体大小", "当前使用默认字号", False, False),
            ],
        )
        content.add_widget(self._create_ai_settings_card())
        self._add_section(
            content,
            "数据管理",
            [
                ("cloud-sync-outline", "数据同步", "当前仅保存在本机", False, False),
                ("database-export-outline", "数据备份", "导出本地备份文件", False, False),
                ("restore", "恢复数据", "从备份文件恢复库存和 Wiki", False, False),
            ],
        )
        self._add_section(
            content,
            "关于与支持",
            [
                ("information-outline", "关于 vibe-fridge", "版本 1.0.0", False, False),
                ("lifebuoy", "帮助与反馈", "查看常见问题和支持入口", False, False),
            ],
        )

        danger_header = SettingsSectionHeader("危险操作")
        content.add_widget(danger_header)
        content.add_widget(
            SettingsRow(
                icon="delete-outline",
                title="清除所有数据",
                subtitle="仅保留在显式确认后执行",
                danger=True,
            )
        )

        scroll.add_widget(content)
        root.add_widget(scroll)
        self.add_widget(root)

    def _create_ai_settings_card(self):
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

        content.add_widget(SettingsSectionHeader("AI 与订单导入"))

        summary = Label(
            text="为订单截图识别配置视觉模型和 API Key。手机端优先使用应用内保存的配置，桌面端才会回退到 .env。",
            size_hint_y=None,
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(summary)
        summary.bind(
            texture_size=lambda inst, val: setattr(inst, "height", max(dp(36), val[1]))
        )
        if CHINESE_FONT:
            summary.font_name = CHINESE_FONT
        content.add_widget(summary)

        self.model_input = FridgeTextInput(
            hint_text="例如：Qwen/Qwen2-VL-72B-Instruct"
        )
        content.add_widget(self._create_field_block("订单识别模型", self.model_input))

        self.model_hint_label = Label(
            text="",
            size_hint_y=None,
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(self.model_hint_label)
        self.model_hint_label.bind(
            texture_size=lambda inst, val: setattr(inst, "height", max(dp(18), val[1]))
        )
        if CHINESE_FONT:
            self.model_hint_label.font_name = CHINESE_FONT
        content.add_widget(self.model_hint_label)

        self.api_hint_label = Label(
            text="",
            size_hint_y=None,
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(self.api_hint_label)
        self.api_hint_label.bind(
            texture_size=lambda inst, val: setattr(inst, "height", max(dp(18), val[1]))
        )
        if CHINESE_FONT:
            self.api_hint_label.font_name = CHINESE_FONT
        content.add_widget(self.api_hint_label)

        self.api_key_row = BoxLayout(
            orientation="vertical",
            size_hint_y=None,
            spacing=dp(8),
        )
        self.api_key_row.bind(minimum_height=self.api_key_row.setter("height"))
        content.add_widget(self.api_key_row)

        self.api_status_label = Label(
            text="",
            size_hint_y=None,
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("body_small")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(self.api_status_label)
        self.api_status_label.bind(
            texture_size=lambda inst, val: setattr(inst, "height", max(dp(18), val[1]))
        )
        if CHINESE_FONT:
            self.api_status_label.font_name = CHINESE_FONT
        content.add_widget(self.api_status_label)

        self.reset_model_button = FridgeButton(
            text="恢复默认模型",
            size_hint=(1, None),
            height=dp(40),
            on_release=self._restore_default_model,
        )
        content.add_widget(self.reset_model_button)

        button_row = BoxLayout(size_hint_y=None, height=dp(48), spacing=dp(10))
        save_btn = FridgeButton(
            text="保存 AI 配置",
            variant="primary",
            size_hint_x=1,
            on_release=self._save_ai_settings,
        )
        button_row.add_widget(save_btn)
        content.add_widget(button_row)

        card.add_widget(content)
        self._apply_card_outline(card, SECTION_CARD["radius"])
        return card

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
            text="设置",
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
            text="管理提醒、显示方式和数据入口。",
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

    def _add_section(self, parent, title, rows):
        parent.add_widget(SettingsSectionHeader(title))
        for icon, row_title, subtitle, show_switch, danger in rows:
            parent.add_widget(
                SettingsRow(
                    icon=icon,
                    title=row_title,
                    subtitle=subtitle,
                    show_switch=show_switch,
                    danger=danger,
                )
            )

    def _create_field_block(self, title: str, widget):
        block = BoxLayout(orientation="vertical", size_hint_y=None, spacing=dp(6))
        block.bind(minimum_height=block.setter("height"))

        label = Label(
            text=title,
            size_hint_y=None,
            height=dp(18),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("label_large")),
            color=COLORS["text_secondary"],
        )
        _bind_label_text(label)
        if CHINESE_FONT:
            label.font_name = CHINESE_FONT
        block.add_widget(label)
        block.add_widget(widget)
        return block

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

    def _current_model_value(self):
        return (
            self._stored_model_value()
            or os.getenv(SILICONFLOW_MODEL_ENV)
            or os.getenv(LEGACY_SILICONFLOW_MODEL_ENV)
            or DEFAULT_MODEL
        )

    def _current_api_key_value(self):
        return self._stored_api_key_value() or self._env_api_key_value() or ""

    def _stored_model_value(self):
        return db_service.get_setting(
            SILICONFLOW_MODEL_SETTING
        ) or db_service.get_setting(LEGACY_SILICONFLOW_MODEL_SETTING)

    def _stored_api_key_value(self):
        return db_service.get_setting(
            SILICONFLOW_API_KEY_SETTING
        ) or db_service.get_setting(LEGACY_SILICONFLOW_API_KEY_SETTING)

    def _env_api_key_value(self):
        return os.getenv(SILICONFLOW_API_KEY_ENV) or os.getenv(
            LEGACY_SILICONFLOW_API_KEY_ENV
        )

    def _mask_secret(self, value: str) -> str:
        if not value:
            return "未填写"
        if len(value) <= 8:
            return "*" * len(value)
        return f"{value[:4]}****{value[-4:]}"

    def _refresh_ai_settings(self):
        current_model = self._current_model_value()
        if self.model_input is not None:
            self.model_input.text = current_model or ""

        stored_model = self._stored_model_value()
        env_model = os.getenv(SILICONFLOW_MODEL_ENV) or os.getenv(
            LEGACY_SILICONFLOW_MODEL_ENV
        )
        model_source = (
            "来自应用内保存的模型配置"
            if stored_model
            else "来自桌面环境变量模型配置"
            if env_model
            else "当前使用默认模型"
        )
        if self.model_hint_label is not None:
            self.model_hint_label.text = f"{model_source}：{current_model or DEFAULT_MODEL}"
        if hasattr(self, "reset_model_button") and self.reset_model_button is not None:
            self.reset_model_button.text = (
                "已是默认模型"
                if (current_model or DEFAULT_MODEL) == DEFAULT_MODEL
                else "恢复默认模型"
            )

        stored_api_key = self._stored_api_key_value()
        env_api_key = self._env_api_key_value()
        current_api_key = self._current_api_key_value()
        self._render_api_key_section(current_api_key)

        if stored_api_key:
            api_source_text = f"当前使用应用内已保存的 Key：{self._mask_secret(stored_api_key)}"
        elif env_api_key and env_api_key != "your_api_key_here":
            api_source_text = (
                f"当前仅检测到桌面环境变量 Key：{self._mask_secret(env_api_key)}；"
                "如需手机端可用，请点“修改 Key”后保存到应用内"
            )
        else:
            api_source_text = "当前没有可用的 API Key"
        if self.api_hint_label is not None:
            self.api_hint_label.text = api_source_text

        api_ready = bool(current_api_key and current_api_key != "your_api_key_here")
        if self.api_status_label is not None:
            if stored_api_key:
                status_text = "API Key 状态：应用内已保存，可直接用于手机端订单识别"
            elif env_api_key and env_api_key != "your_api_key_here":
                status_text = "API Key 状态：仅桌面环境变量可用；手机端请改为应用内保存"
            else:
                status_text = "API Key 状态：未配置；手机端请先在这里保存"
            self.api_status_label.text = status_text
            self.api_status_label.color = (
                COLORS["success_dark"] if api_ready else COLORS["warning_dark"]
            )

    def _save_ai_settings(self, _instance):
        model_name = self.model_input.text.strip() if self.model_input else ""
        api_key = (
            self.api_key_input.text.strip()
            if self.api_key_input is not None
            else self._stored_api_key_value() or ""
        )
        if not model_name:
            self._show_message_dialog("保存失败", "订单识别模型不能为空。")
            return

        model_success = db_service.set_setting(SILICONFLOW_MODEL_SETTING, model_name)
        key_success = db_service.set_setting(SILICONFLOW_API_KEY_SETTING, api_key)
        if model_success and key_success:
            self._editing_api_key = False
            self._refresh_ai_settings()
            api_result = "已保存本地 API Key" if api_key else "未填写本地 API Key"
            self._show_message_dialog(
                "保存成功",
                f"订单识别模型已更新为：{model_name}\n{api_result}",
            )
        else:
            self._show_message_dialog("保存失败", "AI 配置写入数据库时出错。")

    def _restore_default_model(self, _instance):
        success = db_service.set_setting(SILICONFLOW_MODEL_SETTING, DEFAULT_MODEL)
        if success:
            self._refresh_ai_settings()
            self._show_message_dialog("已恢复默认", f"当前默认模型：{DEFAULT_MODEL}")
        else:
            self._show_message_dialog("恢复失败", "默认模型写入数据库时出错。")

    def _render_api_key_section(self, current_api_key: str):
        if self.api_key_row is None:
            return

        self.api_key_row.clear_widgets()
        has_key = bool(current_api_key and current_api_key != "your_api_key_here")
        should_hide_editor = has_key and not self._editing_api_key

        if should_hide_editor:
            summary_row = BoxLayout(size_hint_y=None, height=dp(44), spacing=dp(10))
            summary_label = Label(
                text=f"订单识别 API Key：{self._mask_secret(current_api_key)}",
                halign="left",
                valign="middle",
                font_size=dp(get_font_size("body_medium")),
                color=COLORS["text_primary"],
            )
            summary_label.bind(
                size=lambda inst, val: setattr(inst, "text_size", (val[0], val[1]))
            )
            if CHINESE_FONT:
                summary_label.font_name = CHINESE_FONT
            summary_row.add_widget(summary_label)
            self.api_key_row.add_widget(summary_row)

            modify_btn = FridgeButton(
                text="修改 Key",
                size_hint=(1, None),
                height=dp(44),
                on_release=self._begin_edit_api_key,
            )
            self.api_key_row.add_widget(modify_btn)
            self.api_key_input = None
            return

        self.api_key_input = FridgeTextInput(
            hint_text="填写硅基流动 API Key",
            password=True,
            password_mask="*",
        )
        self.api_key_input.text = current_api_key or ""
        self.api_key_row.add_widget(
            self._create_field_block("订单识别 API Key", self.api_key_input)
        )

        if has_key:
            cancel_btn = FridgeButton(
                text="取消修改",
                size_hint=(1, None),
                height=dp(44),
                on_release=self._cancel_edit_api_key,
            )
            self.api_key_row.add_widget(cancel_btn)

    def _begin_edit_api_key(self, _instance):
        self._editing_api_key = True
        self._refresh_ai_settings()

    def _cancel_edit_api_key(self, _instance):
        self._editing_api_key = False
        self._refresh_ai_settings()

    def _show_message_dialog(self, title_text: str, message: str):
        dialog = ModalView(size_hint=(0.82, None), height=dp(220), auto_dismiss=True)

        root = BoxLayout(
            orientation="vertical",
            padding=dp(18),
            spacing=dp(16),
            size_hint=(1, None),
            height=dp(220),
        )
        with root.canvas.before:
            Color(*COLORS["surface"])
            root._modal_bg = RoundedRectangle(
                pos=root.pos, size=root.size, radius=[dp(20)]
            )
        with root.canvas.after:
            Color(*COLORS["divider"])
            root._modal_outline = Line(width=dp(1), rounded_rectangle=(0, 0, 0, 0, dp(20)))

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

        root.bind(pos=_update_panel, size=_update_panel)
        _update_panel(root, None)

        title = Label(
            text=title_text,
            size_hint_y=None,
            height=dp(30),
            halign="left",
            valign="middle",
            font_size=dp(get_font_size("title_large")),
            bold=True,
            color=COLORS["text_primary"],
        )
        _bind_label_text(title)
        message_label = Label(
            text=message,
            size_hint_y=1,
            halign="left",
            valign="top",
            font_size=dp(get_font_size("body_medium")),
            color=COLORS["text_secondary"],
        )
        message_label.bind(
            size=lambda inst, val: setattr(inst, "text_size", (val[0], None))
        )
        if CHINESE_FONT:
            title.font_name = CHINESE_FONT
            message_label.font_name = CHINESE_FONT

        root.add_widget(title)
        root.add_widget(message_label)
        root.add_widget(
            FridgeButton(
                text="知道了",
                variant="primary",
                size_hint=(1, None),
                height=dp(44),
                on_release=lambda _btn: dialog.dismiss(),
            )
        )
        dialog.add_widget(root)
        dialog.open()

    def _update_header_divider(self, instance, _value):
        self._header_divider.points = [instance.x, instance.y, instance.right, instance.y]

    def on_enter(self):
        self._refresh_ai_settings()
        if CHINESE_FONT:
            apply_font_to_widget(self, CHINESE_FONT)
