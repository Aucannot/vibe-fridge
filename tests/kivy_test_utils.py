# -*- coding: utf-8 -*-
"""Helpers for executable Kivy/KivyMD screen tests."""

from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivymd.app import MDApp


_TEST_APP = None


class TestMDApp(MDApp):
    def build(self):
        return BoxLayout()


def ensure_kivymd_app():
    """Create the MDApp context KivyMD widgets require during construction."""
    global _TEST_APP

    running_app = App.get_running_app()
    if running_app is not None and hasattr(running_app, "theme_cls"):
        _TEST_APP = running_app
        return running_app

    _TEST_APP = TestMDApp()
    _TEST_APP._run_prepare()
    return _TEST_APP
