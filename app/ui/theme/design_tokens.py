# -*- coding: utf-8 -*-
"""
Design System - Centralized UI Design Tokens
Fresh utility palette, typography scale, spacing system, and card presets
for a household inventory and expiry-tracking product.
"""

from kivy.utils import get_color_from_hex


DESIGN_TOKENS = {
    "meta": {
        "product_type": "household inventory tool",
        "style_keywords": [
            "fresh utility",
            "clean refrigeration",
            "high clarity",
            "friendly data density",
        ],
    },
    "colors": {
        "primary": {
            "main": get_color_from_hex("#1B8B7A"),
            "light": get_color_from_hex("#49B7A3"),
            "dark": get_color_from_hex("#136457"),
            "container": get_color_from_hex("#D8F3ED"),
            "on_main": get_color_from_hex("#FFFFFF"),
            "on_container": get_color_from_hex("#0A3932"),
        },
        "secondary": {
            "main": get_color_from_hex("#4E7BC7"),
            "light": get_color_from_hex("#7A9ADD"),
            "dark": get_color_from_hex("#345AA2"),
            "container": get_color_from_hex("#E2EBFF"),
            "on_main": get_color_from_hex("#FFFFFF"),
            "on_container": get_color_from_hex("#1C3563"),
        },
        "tertiary": {
            "main": get_color_from_hex("#E49A41"),
            "light": get_color_from_hex("#F2BA73"),
            "dark": get_color_from_hex("#B8741D"),
            "container": get_color_from_hex("#FFF0DC"),
            "on_main": get_color_from_hex("#FFFFFF"),
            "on_container": get_color_from_hex("#6A3C02"),
        },
        "success": {
            "main": get_color_from_hex("#2E9F6B"),
            "light": get_color_from_hex("#66C38E"),
            "dark": get_color_from_hex("#18784C"),
            "container": get_color_from_hex("#DDF6E8"),
            "on_container": get_color_from_hex("#0F5132"),
        },
        "warning": {
            "main": get_color_from_hex("#D98E04"),
            "light": get_color_from_hex("#F1B94C"),
            "dark": get_color_from_hex("#A86D00"),
            "container": get_color_from_hex("#FFF2CC"),
            "on_container": get_color_from_hex("#674200"),
        },
        "error": {
            "main": get_color_from_hex("#D95C5C"),
            "light": get_color_from_hex("#E98A8A"),
            "dark": get_color_from_hex("#B33D3D"),
            "container": get_color_from_hex("#FDE3E3"),
            "on_container": get_color_from_hex("#6C1F1F"),
        },
        "neutral": {
            "0": get_color_from_hex("#FFFFFF"),
            "4": get_color_from_hex("#FAFCFB"),
            "6": get_color_from_hex("#F6F8F7"),
            "10": get_color_from_hex("#EEF2F1"),
            "12": get_color_from_hex("#E7ECEA"),
            "17": get_color_from_hex("#DBE2E0"),
            "20": get_color_from_hex("#CDD6D4"),
            "30": get_color_from_hex("#A6B2AF"),
            "40": get_color_from_hex("#7C8B87"),
            "50": get_color_from_hex("#5E6B67"),
            "60": get_color_from_hex("#46514E"),
            "70": get_color_from_hex("#2F3836"),
            "80": get_color_from_hex("#1F2624"),
            "87": get_color_from_hex("#151918"),
            "90": get_color_from_hex("#101313"),
            "95": get_color_from_hex("#0A0D0C"),
        },
        "background": {
            "default": get_color_from_hex("#F4F8F7"),
            "elevated": get_color_from_hex("#FFFFFF"),
            "surface_variant": get_color_from_hex("#ECF3F1"),
        },
        "surface": {
            "main": get_color_from_hex("#FFFFFF"),
            "elevated": get_color_from_hex("#FFFFFF"),
            "variant": get_color_from_hex("#ECF3F1"),
            "inverse": get_color_from_hex("#17302C"),
        },
        "outline": get_color_from_hex("#CFDAD7"),
        "outline_variant": get_color_from_hex("#DEE7E4"),
        "surface_tint": get_color_from_hex("#EAF7F4"),
        "surface_cool": get_color_from_hex("#F0F7FB"),
        "surface_warm": get_color_from_hex("#FFF7EC"),
    },
    "typography": {
        "families": {
            "primary": "ChineseFont",
            "fallback": "Roboto",
            "numeric": "Roboto",
            "mono": "Roboto",
        },
        "weights": {
            "regular": 400,
            "medium": 500,
            "semibold": 600,
            "bold": 700,
        },
        "display_large": {"font_size": 57, "line_height": 64, "letter_spacing": -0.25},
        "display_medium": {"font_size": 45, "line_height": 52, "letter_spacing": 0},
        "display_small": {"font_size": 36, "line_height": 44, "letter_spacing": 0},
        "headline_large": {"font_size": 32, "line_height": 40, "letter_spacing": 0},
        "headline_medium": {"font_size": 28, "line_height": 36, "letter_spacing": 0},
        "headline_small": {"font_size": 24, "line_height": 32, "letter_spacing": 0},
        "title_large": {"font_size": 22, "line_height": 28, "letter_spacing": 0},
        "title_medium": {"font_size": 16, "line_height": 24, "letter_spacing": 0.15},
        "title_small": {"font_size": 14, "line_height": 20, "letter_spacing": 0.1},
        "body_large": {"font_size": 16, "line_height": 24, "letter_spacing": 0.5},
        "body_medium": {"font_size": 14, "line_height": 20, "letter_spacing": 0.25},
        "body_small": {"font_size": 12, "line_height": 16, "letter_spacing": 0.4},
        "label_large": {"font_size": 14, "line_height": 20, "letter_spacing": 0.1},
        "label_medium": {"font_size": 12, "line_height": 16, "letter_spacing": 0.5},
        "label_small": {"font_size": 11, "line_height": 16, "letter_spacing": 0.5},
    },
    "spacing": {
        "none": 0,
        "xxs": 2,
        "xs": 4,
        "sm": 8,
        "md": 12,
        "lg": 16,
        "xl": 24,
        "2xl": 32,
        "3xl": 40,
        "4xl": 48,
    },
    "border_radius": {
        "none": 0,
        "sm": 4,
        "md": 8,
        "lg": 12,
        "xl": 16,
        "2xl": 20,
        "3xl": 28,
        "full": 9999,
    },
    "elevation": {
        "none": {"elevation": 0, "shadow_radius": 0, "shadow_offset": (0, 0)},
        "1": {"elevation": 2, "shadow_radius": 8, "shadow_offset": (0, 2)},
        "2": {"elevation": 4, "shadow_radius": 12, "shadow_offset": (0, 4)},
        "3": {"elevation": 6, "shadow_radius": 16, "shadow_offset": (0, 6)},
        "4": {"elevation": 8, "shadow_radius": 20, "shadow_offset": (0, 8)},
        "5": {"elevation": 12, "shadow_radius": 24, "shadow_offset": (0, 10)},
    },
    "card": {
        "hero": {
            "radius": 20,
            "padding": 20,
            "gap": 12,
            "border_width": 0,
            "elevation": "2",
            "background": "surface_elevated",
            "icon_background": "primary_container",
        },
        "section": {
            "radius": 16,
            "padding": 16,
            "gap": 12,
            "border_width": 1,
            "elevation": "1",
            "background": "surface",
            "border_color": "divider",
        },
        "list": {
            "radius": 14,
            "padding": 14,
            "gap": 10,
            "border_width": 1,
            "elevation": "none",
            "background": "surface",
            "border_color": "divider",
        },
        "status": {
            "radius": 14,
            "padding": 14,
            "gap": 8,
            "border_width": 0,
            "elevation": "none",
        },
        "interactive": {
            "press_scale": 0.98,
            "hover_lift": 2,
            "animation_duration": 0.18,
        },
    },
    "animation": {
        "duration_short": 0.15,
        "duration_medium": 0.3,
        "duration_long": 0.5,
        "easing_standard": "in_out_cubic",
        "easing_emphasized": "out_quart",
    },
}


COLOR_PALETTE = {
    "primary": DESIGN_TOKENS["colors"]["primary"]["main"],
    "primary_light": DESIGN_TOKENS["colors"]["primary"]["light"],
    "primary_dark": DESIGN_TOKENS["colors"]["primary"]["dark"],
    "primary_container": DESIGN_TOKENS["colors"]["primary"]["container"],
    "on_primary": DESIGN_TOKENS["colors"]["primary"]["on_main"],
    "on_primary_container": DESIGN_TOKENS["colors"]["primary"]["on_container"],
    "secondary": DESIGN_TOKENS["colors"]["secondary"]["main"],
    "secondary_light": DESIGN_TOKENS["colors"]["secondary"]["light"],
    "secondary_dark": DESIGN_TOKENS["colors"]["secondary"]["dark"],
    "secondary_container": DESIGN_TOKENS["colors"]["secondary"]["container"],
    "on_secondary": DESIGN_TOKENS["colors"]["secondary"]["on_main"],
    "on_secondary_container": DESIGN_TOKENS["colors"]["secondary"]["on_container"],
    "tertiary": DESIGN_TOKENS["colors"]["tertiary"]["main"],
    "tertiary_light": DESIGN_TOKENS["colors"]["tertiary"]["light"],
    "tertiary_dark": DESIGN_TOKENS["colors"]["tertiary"]["dark"],
    "tertiary_container": DESIGN_TOKENS["colors"]["tertiary"]["container"],
    "success": DESIGN_TOKENS["colors"]["success"]["main"],
    "success_light": DESIGN_TOKENS["colors"]["success"]["light"],
    "success_dark": DESIGN_TOKENS["colors"]["success"]["dark"],
    "success_container": DESIGN_TOKENS["colors"]["success"]["container"],
    "warning": DESIGN_TOKENS["colors"]["warning"]["main"],
    "warning_light": DESIGN_TOKENS["colors"]["warning"]["light"],
    "warning_dark": DESIGN_TOKENS["colors"]["warning"]["dark"],
    "warning_container": DESIGN_TOKENS["colors"]["warning"]["container"],
    "error": DESIGN_TOKENS["colors"]["error"]["main"],
    "error_light": DESIGN_TOKENS["colors"]["error"]["light"],
    "error_dark": DESIGN_TOKENS["colors"]["error"]["dark"],
    "error_container": DESIGN_TOKENS["colors"]["error"]["container"],
    "background": DESIGN_TOKENS["colors"]["background"]["default"],
    "surface": DESIGN_TOKENS["colors"]["surface"]["main"],
    "surface_elevated": DESIGN_TOKENS["colors"]["surface"]["elevated"],
    "surface_variant": DESIGN_TOKENS["colors"]["surface"]["variant"],
    "surface_tint": DESIGN_TOKENS["colors"]["surface_tint"],
    "surface_cool": DESIGN_TOKENS["colors"]["surface_cool"],
    "surface_warm": DESIGN_TOKENS["colors"]["surface_warm"],
    "text_primary": DESIGN_TOKENS["colors"]["neutral"]["80"],
    "text_secondary": DESIGN_TOKENS["colors"]["neutral"]["60"],
    "text_tertiary": DESIGN_TOKENS["colors"]["neutral"]["50"],
    "text_hint": DESIGN_TOKENS["colors"]["neutral"]["40"],
    "text_on_primary": DESIGN_TOKENS["colors"]["primary"]["on_main"],
    "divider": DESIGN_TOKENS["colors"]["outline_variant"],
    "overlay": (*DESIGN_TOKENS["colors"]["neutral"]["80"][:3], 0.5),
    "expired": DESIGN_TOKENS["colors"]["error"]["main"],
    "expiring": DESIGN_TOKENS["colors"]["warning"]["main"],
    "normal": DESIGN_TOKENS["colors"]["success"]["main"],
    "info": DESIGN_TOKENS["colors"]["secondary"]["main"],
    "info_container": DESIGN_TOKENS["colors"]["secondary"]["container"],
    "accent": DESIGN_TOKENS["colors"]["tertiary"]["main"],
    "accent_light": DESIGN_TOKENS["colors"]["tertiary"]["light"],
    "accent_container": DESIGN_TOKENS["colors"]["tertiary"]["container"],
    "fresh": DESIGN_TOKENS["colors"]["primary"]["main"],
    "storage_cold": DESIGN_TOKENS["colors"]["secondary"]["main"],
    "storage_warm": DESIGN_TOKENS["colors"]["tertiary"]["main"],
    "chip_selected": DESIGN_TOKENS["colors"]["primary"]["container"],
    "chip_unselected": DESIGN_TOKENS["colors"]["surface"]["variant"],
    "status_success_bg": DESIGN_TOKENS["colors"]["success"]["container"],
    "status_warning_bg": DESIGN_TOKENS["colors"]["warning"]["container"],
    "status_error_bg": DESIGN_TOKENS["colors"]["error"]["container"],
}


def get_font_size(style):
    return DESIGN_TOKENS["typography"][style]["font_size"]


def get_line_height(style):
    return DESIGN_TOKENS["typography"][style]["line_height"]


def get_font_family(role="primary"):
    return DESIGN_TOKENS["typography"]["families"][role]


def get_spacing(size):
    return DESIGN_TOKENS["spacing"][size]


def get_border_radius(size):
    return DESIGN_TOKENS["border_radius"][size]


def get_elevation(level):
    return DESIGN_TOKENS["elevation"][level]


def get_card_style(name):
    return DESIGN_TOKENS["card"][name]
