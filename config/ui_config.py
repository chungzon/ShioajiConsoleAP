"""
Centralized UI Configuration for ShioajiConsoleAP

This module provides:
- Font management for both Tkinter and PyQt5
- Semantic color scheme (success, error, warning, info)
- Configuration persistence to ui_config.json
- Methods to apply styles to ttk and default fonts
"""

import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from typing import Dict, Optional, Any

# Configuration file path
CONFIG_FILE = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'ui_config.json')


@dataclass
class FontConfig:
    """Font configuration settings"""
    family: str = "Microsoft JhengHei"
    base_size: int = 14

    # Font path for matplotlib (Chinese font support)
    font_path: str = "C:/Windows/Fonts/msjh.ttc"


@dataclass
class LightColorScheme:
    """淺色主題配色 (預設)"""
    # 主要背景色
    BG_PRIMARY: str = "#FFFFFF"      # 主背景
    BG_SECONDARY: str = "#F7FAFC"    # 次要背景 (面板)
    BG_TERTIARY: str = "#EDF2F7"     # 第三層背景 (輸入框)

    # 文字顏色
    TEXT_PRIMARY: str = "#2D3748"    # 主要文字
    TEXT_SECONDARY: str = "#4A5568"  # 次要文字
    TEXT_MUTED: str = "#A0AEC0"      # 淡化文字

    # 強調色
    ACCENT: str = "#3182CE"          # 藍色強調
    ACCENT_HOVER: str = "#2B6CB0"    # 滑鼠懸停

    # 邊框
    BORDER: str = "#E2E8F0"
    BORDER_FOCUS: str = "#3182CE"

    # 狀態顏色
    SUCCESS: str = "#38A169"         # 綠色 - 成功
    ERROR: str = "#E53E3E"           # 紅色 - 錯誤
    WARNING: str = "#DD6B20"         # 橘色 - 警告
    INFO: str = "#3182CE"            # 藍色 - 資訊

    # 表格
    ROW_EVEN: str = "#F7FAFC"
    ROW_ODD: str = "#EDF2F7"
    ROW_SELECTED: str = "#BEE3F8"

    # 按鈕
    BUTTON_BG: str = "#EDF2F7"
    BUTTON_HOVER: str = "#E2E8F0"
    BUTTON_PRESSED: str = "#CBD5E0"


@dataclass
class DarkColorScheme:
    """深色主題配色 (VS Code 風格)"""
    # 主要背景色
    BG_PRIMARY: str = "#1e1e1e"      # 主背景
    BG_SECONDARY: str = "#252526"    # 次要背景 (面板)
    BG_TERTIARY: str = "#2d2d2d"     # 第三層背景 (輸入框)

    # 文字顏色
    TEXT_PRIMARY: str = "#e0e0e0"    # 主要文字
    TEXT_SECONDARY: str = "#9e9e9e"  # 次要文字
    TEXT_MUTED: str = "#6e6e6e"      # 淡化文字

    # 強調色
    ACCENT: str = "#007acc"          # 藍色強調 (VS Code 藍)
    ACCENT_HOVER: str = "#1c8cd9"    # 滑鼠懸停

    # 邊框
    BORDER: str = "#3c3c3c"
    BORDER_FOCUS: str = "#007acc"

    # 狀態顏色 (柔和版本，適合深色背景)
    SUCCESS: str = "#4ec9b0"         # 柔和綠
    ERROR: str = "#f14c4c"           # 柔和紅
    WARNING: str = "#cca700"         # 柔和黃
    INFO: str = "#3794ff"            # 柔和藍

    # 表格
    ROW_EVEN: str = "#252526"
    ROW_ODD: str = "#2d2d2d"
    ROW_SELECTED: str = "#094771"

    # 按鈕
    BUTTON_BG: str = "#3c3c3c"
    BUTTON_HOVER: str = "#4c4c4c"
    BUTTON_PRESSED: str = "#2c2c2c"


# 保留舊的 ColorScheme 作為別名 (向後相容)
@dataclass
class ColorScheme:
    """Semantic color definitions (ERP_API style) - 已棄用，請使用 LightColorScheme"""
    # Semantic colors
    SUCCESS: str = "#38A169"   # Green - success, service running
    ERROR: str = "#E53E3E"     # Red - failure, service stopped
    WARNING: str = "#DD6B20"   # Orange - warning
    INFO: str = "#3182CE"      # Blue - information

    # Table colors
    ROW_EVEN: str = "#F7FAFC"
    ROW_ODD: str = "#EDF2F7"
    ROW_SELECTED: str = "#BEE3F8"

    # Additional UI colors
    BACKGROUND: str = "#FFFFFF"
    TEXT: str = "#2D3748"
    BORDER: str = "#E2E8F0"


class UIConfig:
    """
    Centralized UI configuration manager.

    Provides unified font and color management for both Tkinter and PyQt5.
    Configuration is persisted to ui_config.json.
    """

    def __init__(self):
        self.font_config = FontConfig()
        self._current_theme = "dark"  # 預設深色主題
        self._themes = {
            "light": LightColorScheme(),
            "dark": DarkColorScheme()
        }
        self.colors = self._themes[self._current_theme]
        self._tk_fonts: Optional[Dict[str, Any]] = None
        self._qt_fonts: Optional[Dict[str, Any]] = None
        self._font_properties: Optional[Any] = None
        self.load_config()

    @property
    def current_theme(self) -> str:
        """取得當前主題名稱"""
        return self._current_theme

    def get_theme_colors(self, theme_name: str = None):
        """取得指定主題的配色，預設為當前主題"""
        if theme_name is None:
            theme_name = self._current_theme
        return self._themes.get(theme_name, self._themes["dark"])

    def load_config(self) -> None:
        """Load configuration from ui_config.json if it exists"""
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if 'font' in data:
                        self.font_config.family = data['font'].get('family', self.font_config.family)
                        self.font_config.base_size = data['font'].get('base_size', self.font_config.base_size)
                    if 'theme' in data:
                        theme = data['theme']
                        if theme in self._themes:
                            self._current_theme = theme
                            self.colors = self._themes[theme]
            except (json.JSONDecodeError, IOError):
                pass  # Use defaults if config is invalid

    def save_config(self) -> None:
        """Save current configuration to ui_config.json"""
        data = {
            'font': {
                'family': self.font_config.family,
                'base_size': self.font_config.base_size
            },
            'theme': self._current_theme,
            'last_updated': datetime.now().isoformat()
        }
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except IOError:
            pass  # Silently fail if unable to save

    def set_theme(self, theme_name: str) -> None:
        """
        設定主題並儲存配置。

        Args:
            theme_name: 主題名稱 ('light' 或 'dark')
        """
        if theme_name in self._themes:
            self._current_theme = theme_name
            self.colors = self._themes[theme_name]
            self.save_config()

    def set_font_size(self, size: int) -> None:
        """
        Set the base font size and save configuration.

        Args:
            size: Font size in points (12-16 recommended)
        """
        self.font_config.base_size = size
        self._tk_fonts = None  # Reset cached fonts
        self._qt_fonts = None
        self.save_config()

    def get_tk_fonts(self) -> Dict[str, Any]:
        """
        Get Tkinter font dictionary.

        Returns:
            Dictionary of tkinter.font.Font objects:
            - 'title': Large bold font for titles
            - 'heading': Medium bold font for headings
            - 'normal': Standard body text font
            - 'small': Smaller font for secondary text
            - 'button': Font for buttons
            - 'entry': Font for text entries
            - 'log': Font for log/console text
        """
        if self._tk_fonts is not None:
            return self._tk_fonts

        import tkinter.font as tkFont

        base = self.font_config.base_size
        family = self.font_config.family

        self._tk_fonts = {
            'title': tkFont.Font(family=family, size=base + 6, weight="bold"),
            'heading': tkFont.Font(family=family, size=base, weight="bold"),
            'normal': tkFont.Font(family=family, size=base),
            'small': tkFont.Font(family=family, size=base - 2),
            'button': tkFont.Font(family=family, size=base),
            'entry': tkFont.Font(family=family, size=base),
            'log': tkFont.Font(family=family, size=base - 2)
        }
        return self._tk_fonts

    def get_qt_fonts(self) -> Dict[str, Any]:
        """
        Get PyQt5 font dictionary.

        Returns:
            Dictionary of QFont objects:
            - 'title': Large bold font for titles
            - 'heading': Medium bold font for headings
            - 'normal': Standard body text font
            - 'small': Smaller font for secondary text
            - 'bold': Bold version of normal font
            - 'header': Bold font for table headers
        """
        if self._qt_fonts is not None:
            return self._qt_fonts

        from PyQt5.QtGui import QFont

        base = self.font_config.base_size
        family = self.font_config.family

        title_font = QFont(family, base + 6)
        title_font.setBold(True)

        heading_font = QFont(family, base)
        heading_font.setBold(True)

        normal_font = QFont(family, base)

        small_font = QFont(family, base - 2)

        bold_font = QFont(family, base)
        bold_font.setBold(True)

        header_font = QFont(family, base - 2)
        header_font.setBold(True)

        self._qt_fonts = {
            'title': title_font,
            'heading': heading_font,
            'normal': normal_font,
            'small': small_font,
            'bold': bold_font,
            'header': header_font
        }
        return self._qt_fonts

    def get_matplotlib_font(self) -> Any:
        """
        Get matplotlib FontProperties for Chinese text rendering.

        Returns:
            matplotlib.font_manager.FontProperties object
        """
        if self._font_properties is not None:
            return self._font_properties

        from matplotlib import font_manager
        self._font_properties = font_manager.FontProperties(fname=self.font_config.font_path)
        return self._font_properties

    def apply_default_fonts(self, root) -> None:
        """
        Apply default fonts to a Tkinter root window.

        Args:
            root: Tkinter root window (Tk or Toplevel)
        """
        import tkinter.font as tkFont

        base = self.font_config.base_size
        family = self.font_config.family

        # Configure default Tkinter fonts
        default_font = tkFont.nametofont("TkDefaultFont")
        default_font.configure(family=family, size=base)

        text_font = tkFont.nametofont("TkTextFont")
        text_font.configure(family=family, size=base)

        fixed_font = tkFont.nametofont("TkFixedFont")
        fixed_font.configure(family=family, size=base)

    def apply_ttk_style(self, style) -> None:
        """
        Apply consistent styling to ttk widgets.

        Args:
            style: ttk.Style object
        """
        base = self.font_config.base_size
        family = self.font_config.family

        # Global style
        style.configure('.', font=(family, base))

        # Treeview (tables)
        style.configure('Treeview',
                       font=(family, base),
                       rowheight=int(base * 1.8))
        style.configure('Treeview.Heading',
                       font=(family, base, 'bold'))

        # Map selection colors
        style.map('Treeview',
                 background=[('selected', self.colors.ROW_SELECTED)])

        # Buttons
        style.configure('TButton', font=(family, base))

        # Labels
        style.configure('TLabel', font=(family, base))

        # LabelFrame
        style.configure('TLabelFrame', font=(family, base))
        style.configure('TLabelFrame.Label', font=(family, base, 'bold'))

    def get_qt_color(self, color_name: str) -> Any:
        """
        Get a QColor object for the specified semantic color.

        Args:
            color_name: One of 'SUCCESS', 'ERROR', 'WARNING', 'INFO',
                       'ROW_EVEN', 'ROW_ODD', 'ROW_SELECTED'

        Returns:
            QColor object
        """
        from PyQt5.QtGui import QColor

        color_value = getattr(self.colors, color_name, self.colors.TEXT)
        return QColor(color_value)

    def invalidate_font_cache(self) -> None:
        """Clear cached fonts (call after changing font settings)"""
        self._tk_fonts = None
        self._qt_fonts = None
        self._font_properties = None


# Global singleton instance
ui_config = UIConfig()
