# -*- coding: utf-8 -*-
"""
Design System - Centralized UI Design Tokens
Modern color palette, typography scale, spacing system, and elevation tokens
"""

from kivy.utils import get_color_from_hex

DESIGN_TOKENS = {
    "colors": {
        "primary": {
            "main": get_color_from_hex("#6366F1"),
            "light": get_color_from_hex("#818CF8"),
            "dark": get_color_from_hex("#4F46E5"),
            "container": get_color_from_hex("#E0E7FF"),
            "on_main": get_color_from_hex("#FFFFFF"),
            "on_container": get_color_from_hex("#1E1B4B"),
        },
        "secondary": {
            "main": get_color_from_hex("#EC4899"),
            "light": get_color_from_hex("#F472B6"),
            "dark": get_color_from_hex("#DB2777"),
            "container": get_color_from_hex("#FCE7F3"),
            "on_main": get_color_from_hex("#FFFFFF"),
            "on_container": get_color_from_hex("#831843"),
        },
        "tertiary": {
            "main": get_color_from_hex("#14B8A6"),
            "light": get_color_from_hex("#2DD4BF"),
            "dark": get_color_from_hex("#0D9488"),
            "container": get_color_from_hex("#CCFBF1"),
            "on_main": get_color_from_hex("#FFFFFF"),
            "on_container": get_color_from_hex("#134E4A"),
        },
        "success": {
            "main": get_color_from_hex("#22C55E"),
            "light": get_color_from_hex("#4ADE80"),
            "dark": get_color_from_hex("#16A34A"),
            "container": get_color_from_hex("#DCFCE7"),
            "on_container": get_color_from_hex("#166534"),
        },
        "warning": {
            "main": get_color_from_hex("#F59E0B"),
            "light": get_color_from_hex("#FBBF24"),
            "dark": get_color_from_hex("#D97706"),
            "container": get_color_from_hex("#FEF3C7"),
            "on_container": get_color_from_hex("#92400E"),
        },
        "error": {
            "main": get_color_from_hex("#EF4444"),
            "light": get_color_from_hex("#F87171"),
            "dark": get_color_from_hex("#DC2626"),
            "container": get_color_from_hex("#FEE2E2"),
            "on_container": get_color_from_hex("#991B1B"),
        },
        "neutral": {
            "0": get_color_from_hex("#FFFFFF"),
            "4": get_color_from_hex("#FAFAFA"),
            "6": get_color_from_hex("#F5F5F5"),
            "10": get_color_from_hex("#F0F0F0"),
            "12": get_color_from_hex("#EAEAEA"),
            "17": get_color_from_hex("#E5E5E5"),
            "20": get_color_from_hex("#D4D4D4"),
            "30": get_color_from_hex("#A3A3A3"),
            "40": get_color_from_hex("#737373"),
            "50": get_color_from_hex("#525252"),
            "60": get_color_from_hex("#404040"),
            "70": get_color_from_hex("#262626"),
            "80": get_color_from_hex("#171717"),
            "87": get_color_from_hex("#0D0D0D"),
            "90": get_color_from_hex("#050505"),
            "95": get_color_from_hex("#0A0A0A"),
        },
        "background": {
            "default": get_color_from_hex("#FAFAFA"),
            "elevated": get_color_from_hex("#FFFFFF"),
            "surface_variant": get_color_from_hex("#F4F4F5"),
        },
        "surface": {
            "main": get_color_from_hex("#FFFFFF"),
            "elevated": get_color_from_hex("#FFFFFF"),
            "variant": get_color_from_hex("#F4F4F5"),
            "inverse": get_color_from_hex("#18181B"),
        },
        "outline": get_color_from_hex("#D4D4D8"),
        "outline_variant": get_color_from_hex("#E4E4E7"),
    },
    "typography": {
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
        "2xl": 24,
        "3xl": 28,
        "full": 9999,
    },
    "elevation": {
        "none": {"elevation": 0, "shadow_radius": 0, "shadow_offset": (0, 0)},
        "1": {"elevation": 2, "shadow_radius": 4, "shadow_offset": (0, 1)},
        "2": {"elevation": 4, "shadow_radius": 4, "shadow_offset": (0, 2)},
        "3": {"elevation": 6, "shadow_radius": 8, "shadow_offset": (0, 3)},
        "4": {"elevation": 8, "shadow_radius": 10, "shadow_offset": (0, 4)},
        "5": {"elevation": 12, "shadow_radius": 14, "shadow_offset": (0, 6)},
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
    "text_primary": DESIGN_TOKENS["colors"]["neutral"]["70"],
    "text_secondary": DESIGN_TOKENS["colors"]["neutral"]["50"],
    "text_hint": DESIGN_TOKENS["colors"]["neutral"]["40"],
    "text_on_primary": DESIGN_TOKENS["colors"]["primary"]["on_main"],
    "divider": DESIGN_TOKENS["colors"]["outline_variant"],
    "overlay": (*DESIGN_TOKENS["colors"]["neutral"]["80"][:3], 0.5),
    "expired": DESIGN_TOKENS["colors"]["error"]["main"],
    "expiring": DESIGN_TOKENS["colors"]["warning"]["main"],
    "normal": DESIGN_TOKENS["colors"]["success"]["main"],
    "accent": DESIGN_TOKENS["colors"]["tertiary"]["main"],
    "accent_light": DESIGN_TOKENS["colors"]["tertiary"]["light"],
    "chip_selected": DESIGN_TOKENS["colors"]["primary"]["container"],
    "chip_unselected": DESIGN_TOKENS["colors"]["surface"]["variant"],
}

def get_font_size(style):
    return DESIGN_TOKENS["typography"][style]["font_size"]

def get_line_height(style):
    return DESIGN_TOKENS["typography"][style]["line_height"]

def get_spacing(size):
    return DESIGN_TOKENS["spacing"][size]

def get_border_radius(size):
    return DESIGN_TOKENS["border_radius"][size]

def get_elevation(level):
    return DESIGN_TOKENS["elevation"][level]
