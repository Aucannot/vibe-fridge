# -*- coding: utf-8 -*-
"""
字体辅助工具 - 确保中文字体正确应用到所有组件
"""
from kivy.core.text import LabelBase
from kivy.config import Config
import os
import sys


def register_chinese_font():
    """注册中文字体并返回字体名称"""
    chinese_font_name = None
    
    try:
        # macOS 中文字体
        if sys.platform == 'darwin':
            font_paths = [
                '/System/Library/Fonts/STHeiti Light.ttc',  # 黑体-简
                '/System/Library/Fonts/Supplemental/Songti.ttc',  # 宋体
            ]
            
            # 尝试通过 fc-list 查找 PingFang 字体文件
            try:
                import subprocess
                result = subprocess.run(['fc-list', ':lang=zh'], 
                                      capture_output=True, text=True, timeout=2)
                if result.returncode == 0 and result.stdout:
                    for line in result.stdout.split('\n'):
                        if 'PingFang' in line or 'pingfang' in line.lower():
                            if ':' in line:
                                potential_path = line.split(':')[0].strip()
                                if os.path.exists(potential_path) and potential_path.endswith(('.ttc', '.ttf')):
                                    font_paths.insert(0, potential_path)
                                    print(f"通过 fc-list 找到字体路径: {potential_path}")
                                    break
            except Exception as e:
                print(f"使用 fc-list 查找字体失败: {e}")
            
            # 尝试注册找到的字体文件
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        LabelBase.register(name='ChineseFont',
                                          fn_regular=font_path,
                                          fn_bold=font_path)
                        chinese_font_name = 'ChineseFont'
                        print(f"成功注册中文字体文件: {font_path}")
                        break
                    except Exception as e:
                        print(f"注册字体文件失败 {font_path}: {e}")
                        continue
        
        # Linux 中文字体
        elif sys.platform.startswith('linux'):
            font_paths = [
                '/usr/share/fonts/truetype/wqy/wqy-microhei.ttc',
                '/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc',
                '/usr/share/fonts/truetype/arphic/uming.ttc',
            ]
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        LabelBase.register(name='ChineseFont',
                                          fn_regular=font_path,
                                          fn_bold=font_path)
                        chinese_font_name = 'ChineseFont'
                        print(f"成功注册中文字体文件: {font_path}")
                        break
                    except Exception as e:
                        continue
        
        # Windows 中文字体
        elif sys.platform == 'win32':
            font_paths = [
                'C:/Windows/Fonts/msyh.ttc',
                'C:/Windows/Fonts/simsun.ttc',
                'C:/Windows/Fonts/simhei.ttf',
            ]
            for font_path in font_paths:
                if os.path.exists(font_path):
                    try:
                        LabelBase.register(name='ChineseFont',
                                          fn_regular=font_path,
                                          fn_bold=font_path)
                        chinese_font_name = 'ChineseFont'
                        print(f"成功注册中文字体文件: {font_path}")
                        break
                    except Exception as e:
                        continue
        
        # 设置默认字体
        if chinese_font_name:
            Config.set('kivy', 'default_font', [chinese_font_name, 'Roboto'])
            print(f"已设置默认字体为: {chinese_font_name}")
        else:
            print("警告: 无法找到中文字体文件，中文可能显示为方框")
    
    except Exception as e:
        import logging
        logging.warning(f"无法注册中文字体: {e}")
        print(f"字体注册异常: {e}")
    
    return chinese_font_name


def apply_font_to_widget(widget, font_name):
    """
    为组件应用中文字体。

    注意：不要改写图标控件（如 MDIconButton、MDIcon、MDListItemLeadingIcon、MDListItemTrailingIcon），
    它们依赖自己的 icon 字体，否则左侧图标会变成乱码。
    """
    if not font_name or widget is None:
        return

    try:
        from kivy.uix.label import Label
        from kivy.uix.textinput import TextInput
        try:
            from kivymd.uix.button import MDButtonText, MDIconButton
            from kivymd.uix.label import MDIcon
            from kivymd.uix.list import (
                MDListItemLeadingIcon, MDListItemTrailingIcon, 
                MDListItemIcon
            )
        except Exception:
            MDButtonText = type("Dummy", (), {})
            MDIconButton = type("Dummy", (), {})
            MDIcon = type("Dummy", (), {})
            MDListItemLeadingIcon = type("Dummy", (), {})
            MDListItemTrailingIcon = type("Dummy", (), {})
            MDListItemIcon = type("Dummy", (), {})

        # 排除所有图标控件，避免影响图标显示
        # 使用类名检查，避免isinstance检查失败的问题
        widget_type_name = type(widget).__name__
        
        # 检查是否是图标控件
        is_icon_widget = (
            widget_type_name == 'MDIcon' or
            widget_type_name == 'MDIconButton' or
            widget_type_name == 'MDListItemLeadingIcon' or
            widget_type_name == 'MDListItemTrailingIcon' or
            widget_type_name == 'MDListItemIcon'
        )
        
        if is_icon_widget:
            return  # 直接返回，不处理子组件

        # 只对纯文本类控件设置字体
        text_types = (Label, TextInput, MDButtonText)

        # 确保不是图标控件（因为MDIcon可能继承自Label）
        if isinstance(widget, text_types) and not is_icon_widget:
            if hasattr(widget, "font_name"):
                widget.font_name = font_name

        # 递归处理子组件
        if hasattr(widget, "children"):
            for child in widget.children:
                apply_font_to_widget(child, font_name)
    except Exception:
        return

