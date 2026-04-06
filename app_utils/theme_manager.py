"""
Theme Manager for ShioajiConsoleAP

This module provides centralized theme management for the application,
supporting both light and dark themes with easy switching.
"""

from typing import Any, Dict, Optional, Callable, List
from config.ui_config import ui_config, LightColorScheme, DarkColorScheme


class ThemeManager:
    """
    主題管理器

    提供主題切換、TTK 樣式配置和組件顏色取得等功能。
    """

    def __init__(self):
        self._theme_change_callbacks: List[Callable] = []

    @property
    def current_theme(self) -> str:
        """取得當前主題名稱"""
        return ui_config.current_theme

    @property
    def colors(self):
        """取得當前主題的配色"""
        return ui_config.colors

    def register_theme_change_callback(self, callback: Callable) -> None:
        """
        註冊主題變更回調函數

        Args:
            callback: 當主題變更時會被呼叫的函數
        """
        if callback not in self._theme_change_callbacks:
            self._theme_change_callbacks.append(callback)

    def unregister_theme_change_callback(self, callback: Callable) -> None:
        """
        取消註冊主題變更回調函數

        Args:
            callback: 要移除的回調函數
        """
        if callback in self._theme_change_callbacks:
            self._theme_change_callbacks.remove(callback)

    def apply_theme(self, root, theme_name: str) -> None:
        """
        套用指定主題到整個應用程式

        Args:
            root: Tkinter root window
            theme_name: 主題名稱 ('light' 或 'dark')
        """
        ui_config.set_theme(theme_name)

        # 套用預設字體
        ui_config.apply_default_fonts(root)

        # 取得 ttk.Style
        import tkinter.ttk as ttk
        style = ttk.Style()

        # 套用主題樣式
        if theme_name == "dark":
            self.apply_ttk_dark_style(style)
        else:
            self.apply_ttk_light_style(style)

        # 套用根視窗背景
        root.configure(bg=self.colors.BG_PRIMARY)

        # 通知所有回調函數
        for callback in self._theme_change_callbacks:
            try:
                callback(theme_name)
            except Exception as e:
                print(f"Theme change callback error: {e}")

    def apply_ttk_dark_style(self, style) -> None:
        """
        套用深色 TTK 樣式

        Args:
            style: ttk.Style 物件
        """
        colors = ui_config.get_theme_colors("dark")
        base = ui_config.font_config.base_size
        family = ui_config.font_config.family

        # 全域樣式
        style.configure('.',
            background=colors.BG_PRIMARY,
            foreground=colors.TEXT_PRIMARY,
            font=(family, base))

        # TFrame
        style.configure('TFrame',
            background=colors.BG_PRIMARY)

        # TLabel
        style.configure('TLabel',
            background=colors.BG_PRIMARY,
            foreground=colors.TEXT_PRIMARY,
            font=(family, base))

        # TLabelframe
        style.configure('TLabelframe',
            background=colors.BG_PRIMARY,
            foreground=colors.TEXT_PRIMARY)
        style.configure('TLabelframe.Label',
            background=colors.BG_PRIMARY,
            foreground=colors.TEXT_PRIMARY,
            font=(family, base, 'bold'))

        # TButton
        style.configure('TButton',
            background=colors.BUTTON_BG,
            foreground=colors.TEXT_PRIMARY,
            borderwidth=0,
            focuscolor='none',
            padding=(12, 6),
            font=(family, base))
        style.map('TButton',
            background=[('active', colors.BUTTON_HOVER), ('pressed', colors.BUTTON_PRESSED)],
            foreground=[('disabled', colors.TEXT_MUTED)])

        # TEntry
        style.configure('TEntry',
            fieldbackground=colors.BG_TERTIARY,
            foreground=colors.TEXT_PRIMARY,
            bordercolor=colors.BORDER,
            insertcolor=colors.TEXT_PRIMARY,
            font=(family, base))
        style.map('TEntry',
            fieldbackground=[('focus', colors.BG_TERTIARY)],
            bordercolor=[('focus', colors.BORDER_FOCUS)])

        # TCombobox
        style.configure('TCombobox',
            fieldbackground=colors.BG_TERTIARY,
            background=colors.BG_TERTIARY,
            foreground=colors.TEXT_PRIMARY,
            arrowcolor=colors.TEXT_PRIMARY,
            font=(family, base))
        style.map('TCombobox',
            fieldbackground=[('readonly', colors.BG_TERTIARY)],
            selectbackground=[('readonly', colors.ROW_SELECTED)])

        # Treeview
        style.configure('Treeview',
            background=colors.BG_SECONDARY,
            foreground=colors.TEXT_PRIMARY,
            fieldbackground=colors.BG_SECONDARY,
            rowheight=int(base * 1.8),
            font=(family, base))
        style.configure('Treeview.Heading',
            background=colors.BUTTON_BG,
            foreground=colors.TEXT_PRIMARY,
            font=(family, base, 'bold'))
        style.map('Treeview',
            background=[('selected', colors.ROW_SELECTED)],
            foreground=[('selected', colors.TEXT_PRIMARY)])
        style.map('Treeview.Heading',
            background=[('active', colors.BUTTON_HOVER)])

        # TNotebook (分頁)
        style.configure('TNotebook',
            background=colors.BG_PRIMARY,
            borderwidth=0)
        style.configure('TNotebook.Tab',
            background=colors.BG_TERTIARY,
            foreground=colors.TEXT_SECONDARY,
            padding=(12, 6),
            font=(family, base))
        style.map('TNotebook.Tab',
            background=[('selected', colors.BG_PRIMARY)],
            foreground=[('selected', colors.TEXT_PRIMARY)])

        # TCheckbutton
        style.configure('TCheckbutton',
            background=colors.BG_PRIMARY,
            foreground=colors.TEXT_PRIMARY,
            font=(family, base))
        style.map('TCheckbutton',
            background=[('active', colors.BG_PRIMARY)])

        # TRadiobutton
        style.configure('TRadiobutton',
            background=colors.BG_PRIMARY,
            foreground=colors.TEXT_PRIMARY,
            font=(family, base))
        style.map('TRadiobutton',
            background=[('active', colors.BG_PRIMARY)])

        # TProgressbar
        style.configure('TProgressbar',
            background=colors.ACCENT,
            troughcolor=colors.BG_TERTIARY)

        # TScrollbar
        style.configure('TScrollbar',
            background=colors.BG_TERTIARY,
            troughcolor=colors.BG_PRIMARY,
            arrowcolor=colors.TEXT_PRIMARY)

        # Vertical.TScrollbar
        style.configure('Vertical.TScrollbar',
            background=colors.BG_TERTIARY)
        style.map('Vertical.TScrollbar',
            background=[('active', colors.BUTTON_HOVER)])

        # Horizontal.TScrollbar
        style.configure('Horizontal.TScrollbar',
            background=colors.BG_TERTIARY)
        style.map('Horizontal.TScrollbar',
            background=[('active', colors.BUTTON_HOVER)])

    def apply_ttk_light_style(self, style) -> None:
        """
        套用淺色 TTK 樣式

        Args:
            style: ttk.Style 物件
        """
        colors = ui_config.get_theme_colors("light")
        base = ui_config.font_config.base_size
        family = ui_config.font_config.family

        # 全域樣式
        style.configure('.',
            background=colors.BG_PRIMARY,
            foreground=colors.TEXT_PRIMARY,
            font=(family, base))

        # TFrame
        style.configure('TFrame',
            background=colors.BG_PRIMARY)

        # TLabel
        style.configure('TLabel',
            background=colors.BG_PRIMARY,
            foreground=colors.TEXT_PRIMARY,
            font=(family, base))

        # TLabelframe
        style.configure('TLabelframe',
            background=colors.BG_PRIMARY,
            foreground=colors.TEXT_PRIMARY)
        style.configure('TLabelframe.Label',
            background=colors.BG_PRIMARY,
            foreground=colors.TEXT_PRIMARY,
            font=(family, base, 'bold'))

        # TButton
        style.configure('TButton',
            background=colors.BUTTON_BG,
            foreground=colors.TEXT_PRIMARY,
            borderwidth=1,
            padding=(12, 6),
            font=(family, base))
        style.map('TButton',
            background=[('active', colors.BUTTON_HOVER), ('pressed', colors.BUTTON_PRESSED)],
            foreground=[('disabled', colors.TEXT_MUTED)])

        # TEntry
        style.configure('TEntry',
            fieldbackground=colors.BG_PRIMARY,
            foreground=colors.TEXT_PRIMARY,
            bordercolor=colors.BORDER,
            insertcolor=colors.TEXT_PRIMARY,
            font=(family, base))

        # TCombobox
        style.configure('TCombobox',
            fieldbackground=colors.BG_PRIMARY,
            background=colors.BG_PRIMARY,
            foreground=colors.TEXT_PRIMARY,
            font=(family, base))

        # Treeview
        style.configure('Treeview',
            background=colors.BG_PRIMARY,
            foreground=colors.TEXT_PRIMARY,
            fieldbackground=colors.BG_PRIMARY,
            rowheight=int(base * 1.8),
            font=(family, base))
        style.configure('Treeview.Heading',
            background=colors.BG_SECONDARY,
            foreground=colors.TEXT_PRIMARY,
            font=(family, base, 'bold'))
        style.map('Treeview',
            background=[('selected', colors.ROW_SELECTED)])

        # TNotebook
        style.configure('TNotebook',
            background=colors.BG_PRIMARY,
            borderwidth=0)
        style.configure('TNotebook.Tab',
            background=colors.BG_SECONDARY,
            foreground=colors.TEXT_SECONDARY,
            padding=(12, 6),
            font=(family, base))
        style.map('TNotebook.Tab',
            background=[('selected', colors.BG_PRIMARY)],
            foreground=[('selected', colors.TEXT_PRIMARY)])

        # TCheckbutton
        style.configure('TCheckbutton',
            background=colors.BG_PRIMARY,
            foreground=colors.TEXT_PRIMARY,
            font=(family, base))

        # TRadiobutton
        style.configure('TRadiobutton',
            background=colors.BG_PRIMARY,
            foreground=colors.TEXT_PRIMARY,
            font=(family, base))

        # TProgressbar
        style.configure('TProgressbar',
            background=colors.ACCENT,
            troughcolor=colors.BG_TERTIARY)

        # TScrollbar
        style.configure('TScrollbar',
            background=colors.BG_SECONDARY,
            troughcolor=colors.BG_PRIMARY)

    def get_widget_colors(self) -> Dict[str, str]:
        """
        取得當前主題的組件顏色字典

        Returns:
            包含所有組件顏色的字典
        """
        colors = self.colors
        return {
            'bg_primary': colors.BG_PRIMARY,
            'bg_secondary': colors.BG_SECONDARY,
            'bg_tertiary': colors.BG_TERTIARY,
            'text_primary': colors.TEXT_PRIMARY,
            'text_secondary': colors.TEXT_SECONDARY,
            'text_muted': colors.TEXT_MUTED,
            'accent': colors.ACCENT,
            'accent_hover': colors.ACCENT_HOVER,
            'border': colors.BORDER,
            'border_focus': colors.BORDER_FOCUS,
            'success': colors.SUCCESS,
            'error': colors.ERROR,
            'warning': colors.WARNING,
            'info': colors.INFO,
            'row_even': colors.ROW_EVEN,
            'row_odd': colors.ROW_ODD,
            'row_selected': colors.ROW_SELECTED,
            'button_bg': colors.BUTTON_BG,
            'button_hover': colors.BUTTON_HOVER,
            'button_pressed': colors.BUTTON_PRESSED,
        }

    def apply_to_tk_text(self, text_widget) -> None:
        """
        套用主題樣式到 tk.Text 組件

        Args:
            text_widget: tk.Text 組件
        """
        colors = self.colors
        text_widget.configure(
            bg=colors.BG_TERTIARY,
            fg=colors.TEXT_PRIMARY,
            insertbackground=colors.TEXT_PRIMARY,
            selectbackground=colors.ROW_SELECTED,
            selectforeground=colors.TEXT_PRIMARY
        )

    def apply_to_scrolledtext(self, scrolledtext_widget) -> None:
        """
        套用主題樣式到 ScrolledText 組件

        Args:
            scrolledtext_widget: ScrolledText 組件
        """
        self.apply_to_tk_text(scrolledtext_widget)

    def apply_to_menu(self, menu) -> None:
        """
        套用主題樣式到 Menu 組件

        Args:
            menu: tk.Menu 組件
        """
        colors = self.colors
        menu.configure(
            bg=colors.BG_SECONDARY,
            fg=colors.TEXT_PRIMARY,
            activebackground=colors.ACCENT,
            activeforeground=colors.TEXT_PRIMARY,
            selectcolor=colors.ACCENT
        )

    def get_dateentry_colors(self) -> Dict[str, str]:
        """
        取得 DateEntry 組件的配色

        Returns:
            DateEntry 顏色設定字典
        """
        colors = self.colors
        if self.current_theme == "dark":
            return {
                'background': colors.BG_TERTIARY,
                'foreground': colors.TEXT_PRIMARY,
                'headersbackground': colors.BG_SECONDARY,
                'headersforeground': colors.TEXT_PRIMARY,
                'selectbackground': colors.ACCENT,
                'selectforeground': colors.TEXT_PRIMARY,
                'normalbackground': colors.BG_TERTIARY,
                'normalforeground': colors.TEXT_PRIMARY,
                'weekendbackground': colors.BG_TERTIARY,
                'weekendforeground': colors.TEXT_SECONDARY,
                'othermonthforeground': colors.TEXT_MUTED,
                'othermonthbackground': colors.BG_SECONDARY,
                'othermonthweforeground': colors.TEXT_MUTED,
                'othermonthwebackground': colors.BG_SECONDARY,
            }
        else:
            return {
                'background': 'white',
                'foreground': 'black',
            }


# 全域單例
theme_manager = ThemeManager()
