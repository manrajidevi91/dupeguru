# Copyright 2016 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

"""
Theme Manager for dupeGuru - Centralized theme and style management.

This module provides the ThemeManager class which handles:
- Dynamic theme switching between light, dark, and auto modes
- Color palette generation based on New_UI.html design
- QSS stylesheet loading and application
- System theme detection for auto mode
"""

from PyQt5.QtCore import QObject, pyqtSignal
from PyQt5.QtGui import QPalette, QColor
from PyQt5.QtWidgets import QApplication

from hscommon import plat
from hscommon.trans import trget

tr = trget("ui")


class ThemeManager(QObject):
    """Centralized theme management system for dupeGuru."""
    
    themeChanged = pyqtSignal(str)  # Emitted when theme changes, with theme name
    
    THEME_DARK = "dark"
    THEME_LIGHT = "light"
    THEME_AUTO = "auto"
    
    def __init__(self, app):
        super().__init__()
        self.app = app
        self.current_theme = self.THEME_DARK
        self.system_dark_mode = False
        self._detect_system_theme()
        
        # Color palettes based on New_UI.html design
        self.dark_palette = {
            'background': QColor(19, 19, 19),  # #131313
            'surface': QColor(19, 19, 19),  # #131313
            'surface_container_low': QColor(27, 27, 28),  # #1b1b1c
            'surface_container': QColor(32, 32, 32),  # #202020
            'surface_container_high': QColor(42, 42, 42),  # #2a2a2a
            'surface_container_highest': QColor(53, 53, 53),  # #353535
            'surface_container_lowest': QColor(14, 14, 14),  # #0e0e0e
            'primary': QColor(163, 201, 255),  # #a3c9ff
            'on_primary': QColor(0, 49, 92),  # #00315c
            'primary_container': QColor(0, 120, 212),  # #0078d4
            'on_primary_container': QColor(255, 255, 255),  # #ffffff
            'secondary': QColor(173, 200, 242),  # #adc8f2
            'on_secondary': QColor(20, 49, 83),  # #143153
            'secondary_container': QColor(45, 72, 107),  # #2d486b
            'on_secondary_container': QColor(156, 183, 223),  # #9cb7df
            'tertiary': QColor(255, 182, 137),  # #ffb689
            'on_tertiary': QColor(81, 35, 0),  # #512300
            'error': QColor(255, 180, 171),  # #ffb4ab
            'on_error': QColor(105, 0, 5),  # #690005
            'error_container': QColor(147, 0, 10),  # #93000a
            'on_error_container': QColor(255, 218, 214),  # #ffdad6
            'outline': QColor(138, 145, 158),  # #8a919e
            'outline_variant': QColor(64, 71, 82),  # #404752
            'on_surface': QColor(229, 226, 225),  # #e5e2e1
            'on_surface_variant': QColor(192, 199, 212),  # #c0c7d4
            'inverse_surface': QColor(229, 226, 225),  # #e5e2e1
            'inverse_on_surface': QColor(48, 48, 48),  # #303030
            'inverse_primary': QColor(0, 96, 171),  # #0060ab
            
            # Application Specific Extras
            'sidebar_bg': QColor(30, 30, 30, 180), # Mica-like semi-transparent
            'badge_bg': QColor(163, 201, 255, 51), # Primary with 0.2 opacity
            'reference_bg': QColor(27, 27, 28), # surface-container-low
            'duplicate_bg': QColor(32, 32, 32), # surface-container
            'duplicate_hover_bg': QColor(42, 42, 42), # surface-container-high
            'indented_line': QColor(255, 255, 255, 13), # border-white/5
            'primary_gradient': "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #a3c9ff, stop:1 #0078d4)"
        }
        
        self.light_palette = {
            'background': QColor(255, 251, 254),  # Light background
            'surface': QColor(255, 251, 254),  # Light surface
            'surface_container_low': QColor(239, 239, 240),  # #efefef
            'surface_container': QColor(233, 233, 233),  # #e9e9e9
            'surface_container_high': QColor(227, 227, 227),  # #e3e3e3
            'surface_container_highest': QColor(221, 221, 221),  # #dddddd
            'surface_container_lowest': QColor(250, 250, 250),
            'primary': QColor(0, 120, 212),  # Windows 11 blue
            'on_primary': QColor(255, 255, 255),  # White text on primary
            'primary_container': QColor(211, 227, 255),  # #d3e3ff
            'on_primary_container': QColor(0, 28, 57),  # #001c39
            'secondary': QColor(108, 135, 175),  # #6c87af
            'on_secondary': QColor(255, 255, 255),  # White text
            'secondary_container': QColor(211, 227, 255),  # Light blue
            'on_secondary_container': QColor(0, 28, 57),  # Dark blue
            'tertiary': QColor(188, 91, 0),  # Orange
            'on_tertiary': QColor(255, 255, 255),  # White
            'error': QColor(186, 26, 26),  # Red
            'on_error': QColor(255, 255, 255),  # White
            'error_container': QColor(255, 218, 214),  # Light red
            'on_error_container': QColor(65, 0, 2),  # Dark red
            'outline': QColor(119, 119, 119),  # Gray outline
            'outline_variant': QColor(198, 198, 198),  # Light outline
            'on_surface': QColor(28, 27, 31),  # Almost black
            'on_surface_variant': QColor(73, 69, 79),  # Dark gray
            'inverse_surface': QColor(49, 48, 51),  # Dark
            'inverse_on_surface': QColor(244, 239, 244),  # Light
            'inverse_primary': QColor(163, 201, 255),  # Light blue
            
            # Application Specific Extras
            'sidebar_bg': QColor(240, 240, 240, 200),
            'badge_bg': QColor(0, 120, 212, 51),
            'reference_bg': QColor(245, 245, 245),
            'duplicate_bg': QColor(255, 255, 255),
            'duplicate_hover_bg': QColor(240, 248, 255),
            'indented_line': QColor(0, 0, 0, 13),
            'primary_gradient': "qlineargradient(x1:0, y1:0, x2:1, y2:1, stop:0 #0078d4, stop:1 #005a9e)"
        }
        
    def get_current_theme(self):
        """Get the currently active theme name."""
        return self.current_theme
    
    def get_active_theme(self):
        """Get the actual theme being used (resolves 'auto' to light or dark)."""
        if self.current_theme == self.THEME_AUTO:
            return self.THEME_DARK if self.system_dark_mode else self.THEME_LIGHT
        return self.current_theme
    
    def set_theme(self, theme_mode):
        """Set the application theme.
        
        Args:
            theme_mode: One of 'light', 'dark', or 'auto'
        """
        self.current_theme = theme_mode
        
        # Resolve auto mode
        active_theme = self.get_active_theme()
        
        # Apply theme
        self._apply_theme(active_theme)
        
        # Emit signal
        self.themeChanged.emit(active_theme)
    
    def update_system_theme(self):
        """Check system theme preference and update if in auto mode."""
        self._detect_system_theme()
        
        # If in auto mode, re-apply theme
        if self.current_theme == self.THEME_AUTO:
            self.set_theme(self.THEME_AUTO)
            
    def _detect_system_theme(self):
        """Internal detection of system dark mode preference."""
        if plat.ISWINDOWS:
            try:
                import winreg
                registry_key = winreg.OpenKey(
                    winreg.HKEY_CURRENT_USER,
                    r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
                )
                # AppsUseLightTheme: 0 = dark mode, 1 = light mode
                apps_use_light_theme, _ = winreg.QueryValueEx(registry_key, "AppsUseLightTheme")
                self.system_dark_mode = apps_use_light_theme == 0
                winreg.CloseKey(registry_key)
            except:
                self.system_dark_mode = False
        else:
            self.system_dark_mode = False
    
    def get_color(self, role):
        """Get a color from the current active palette.
        
        Args:
            role: Color role name (e.g., 'background', 'primary', 'on_primary')
        
        Returns:
            QColor for the requested role
        """
        active_theme = self.get_active_theme()
        palette = self.dark_palette if active_theme == self.THEME_DARK else self.light_palette
        return palette.get(role, QColor(128, 128, 128))  # Default to gray if not found
    
    def get_qss(self):
        """Get the QSS stylesheet for the current theme.
        
        Returns:
            QSS stylesheet string
        """
        active_theme = self.get_active_theme()
        return self._generate_qss(active_theme)
    
    def _generate_qss(self, theme):
        """Generate QSS stylesheet for the given theme."""
        palette = self.dark_palette if theme == self.THEME_DARK else self.light_palette
        is_dark = theme == self.THEME_DARK
        
        qss = f"""
/* Common Styles */
QWidget {{
    background-color: {self._qcolor_to_css(palette['background'])};
    color: {self._qcolor_to_css(palette['on_surface'])};
    font-family: 'Inter', 'Segoe UI', sans-serif;
}}

/* QMainWindow */
QMainWindow {{
    background-color: {self._qcolor_to_css(palette['surface'])};
}}

/* Menu Bar */
QMenuBar {{
    background-color: {self._qcolor_to_css(palette['surface'])};
    color: {self._qcolor_to_css(palette['on_surface'])};
    border-bottom: 1px solid {self._qcolor_to_css(palette['indented_line'])};
    padding: 2px;
}}

QMenuBar::item {{
    background: transparent;
    padding: 4px 10px;
    border-radius: 4px;
}}

QMenuBar::item:selected {{
    background: {self._qcolor_to_css(palette['surface_container_highest'])};
}}

QMenu {{
    background-color: {self._qcolor_to_css(palette['surface_container'])};
    color: {self._qcolor_to_css(palette['on_surface'])};
    border: 1px solid {self._qcolor_to_css(palette['outline_variant'])};
    border-radius: 8px;
    padding: 4px;
}}

QMenu::item {{
    padding: 6px 24px 6px 36px;
    border-radius: 4px;
}}

QMenu::item:selected {{
    background-color: {self._qcolor_to_css(palette['primary'])};
    color: {self._qcolor_to_css(palette['on_primary'])};
}}

/* Sidebar / Navigation Rail */
#NavigationRail {{
    background-color: {self._qcolor_to_css(palette['sidebar_bg'])};
    border-right: 1px solid {self._qcolor_to_css(palette['indented_line'])};
}}

#NavigationRail QLabel#SectionHeader {{
    color: {self._qcolor_to_css(palette['on_surface_variant'])};
    font-size: 11px;
    font-weight: 800;
    text-transform: uppercase;
    letter-spacing: 1px;
    padding: 12px 16px 4px 16px;
    background: transparent;
}}

QPushButton#ModeButton {{
    background-color: transparent;
    border: none;
    border-radius: 8px;
    padding: 10px 16px;
    text-align: left;
    color: {self._qcolor_to_css(palette['on_surface_variant'])};
    font-size: 13px;
    margin: 2px 8px;
}}

QPushButton#ModeButton:hover {{
    background-color: {self._qcolor_to_css(palette['surface_container_highest'])};
    color: {self._qcolor_to_css(palette['on_surface'])};
}}

QPushButton#ModeButton[active="true"] {{
    background-color: {self._qcolor_to_css(palette['surface_container_low'])};
    color: {self._qcolor_to_css(palette['primary'])};
    border-left: 4px solid {self._qcolor_to_css(palette['primary'])};
    font-weight: 600;
}}

/* Folder List Item */
QWidget#FolderItem {{
    background-color: {self._qcolor_to_css(palette['surface_container_low'])};
    border: 1px solid transparent;
    border-radius: 8px;
    margin: 4px 8px;
}}

QWidget#FolderItem:hover {{
    border: 1px solid {self._qcolor_to_css(palette['outline_variant'])};
}}

#NavigationRail QPushButton#AddFolderBtn {{
    background: transparent;
    color: {self._qcolor_to_css(palette['primary'])};
    font-size: 11px;
    font-weight: bold;
    border: none;
    padding-right: 16px;
}}

#NavigationRail QPushButton#AddFolderBtn:hover {{
    text-decoration: underline;
}}

#NavigationRail QToolButton#ChangeFolderBtn {{
    background: rgba(163, 201, 255, 26);
    color: {self._qcolor_to_css(palette['primary'])};
    border: 1px solid {self._qcolor_to_css(palette['primary'])};
    border-radius: 4px;
    padding: 2px 8px;
    font-size: 11px;
    font-weight: bold;
}}

#NavigationRail QToolButton#ChangeFolderBtn:hover {{
    background: rgba(163, 201, 255, 51);
}}

/* START SCAN Button */
QWidget#StartScanContainer {{
    border-top: 1px solid {self._qcolor_to_css(palette['indented_line'])};
    background: transparent;
}}
QPushButton#StartScanButton {{
    background: {palette['primary_gradient']};
    color: {self._qcolor_to_css(palette['on_primary']) if is_dark else "#ffffff"};
    border: none;
    border-radius: 12px;
    padding: 12px 16px;
    font-size: 14px;
    font-weight: 800;
    letter-spacing: 1px;
    margin: 0;
}}

QPushButton#StartScanButton:pressed {{
    background: {self._qcolor_to_css(palette['primary_container'])};
}}

/* Scan Options Controls */
QLabel#ScanOptionsLabel {{
    font-size: 11px;
    color: {self._qcolor_to_css(palette['on_surface_variant'])};
    font-weight: bold;
    background: transparent;
}}

QLabel#ThresholdValueLabel {{
    font-size: 11px;
    color: {self._qcolor_to_css(palette['primary'])};
    font-weight: bold;
    background: transparent;
}}

QComboBox#NavigationRailDropdown {{
    margin: 4px 0;
}}

QComboBox {{
    background-color: {self._qcolor_to_css(palette['surface_container_low'])};
    border: 1px solid {self._qcolor_to_css(palette['outline_variant'])};
    border-radius: 8px;
    padding: 6px 12px;
    min-height: 24px;
}}

QComboBox::drop-down {{
    border: none;
    width: 32px;
}}

QComboBox::down-arrow {{
    image: none;
    border-left: 5px solid transparent;
    border-right: 5px solid transparent;
    border-top: 5px solid {self._qcolor_to_css(palette['outline'])};
    width: 0;
    height: 0;
    margin-right: 12px;
}}

QComboBox::down-arrow:on {{
    border-top: none;
    border-bottom: 5px solid {self._qcolor_to_css(palette['primary'])};
}}

QComboBox QAbstractItemView {{
    background-color: {self._qcolor_to_css(palette['surface_container'])};
    border: 1px solid {self._qcolor_to_css(palette['outline_variant'])};
    selection-background-color: {self._qcolor_to_css(palette['primary'])};
    outline: none;
    border-radius: 8px;
    margin-top: 4px;
}}

QSlider::groove:horizontal {{
    border: none;
    height: 4px;
    background: {self._qcolor_to_css(palette['surface_container_highest'])};
    margin: 2px 0;
    border-radius: 2px;
}}

QSlider::handle:horizontal {{
    background: {self._qcolor_to_css(palette['primary'])};
    border: none;
    width: 14px;
    height: 14px;
    margin: -5px 0;
    border-radius: 7px;
}}

/* Results Header */
QLabel#ResultsHeaderTitle {{
    background: transparent;
    font-size: 24px;
    font-weight: 600;
    color: {self._qcolor_to_css(palette['on_surface'])};
}}

QLabel#ResultsHeaderLabel {{
    background: transparent;
    font-size: 11px;
    font-weight: 800;
    color: {self._qcolor_to_css(palette['primary'])};
    text-transform: uppercase;
    letter-spacing: 2px;
}}

/* Result Entry Cards */
QFrame[class="ReferenceEntry"] {{
    background-color: {self._qcolor_to_css(palette['reference_bg'])};
    border: 1px solid {self._qcolor_to_css(palette['outline_variant'])};
    border-radius: 12px;
}}

QFrame[class="DuplicateEntry"] {{
    background-color: {self._qcolor_to_css(palette['duplicate_bg'])};
    border-radius: 12px;
}}

QFrame[class="DuplicateEntry"]:hover {{
    background-color: {self._qcolor_to_css(palette['duplicate_hover_bg'])};
}}

/* Badges */
QLabel#ReferenceBadge {{
    background-color: {self._qcolor_to_css(palette['badge_bg'])};
    color: {self._qcolor_to_css(palette['primary'])};
    border-radius: 10px;
    padding: 2px 8px;
    font-size: 10px;
    font-weight: 800;
}}

/* Action Buttons in Results Header */
QPushButton#ActionBtn {{
    background-color: {self._qcolor_to_css(palette['surface_container_high'])};
    border: 1px solid {self._qcolor_to_css(palette['outline_variant'])};
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
}}

QPushButton#ActionBtn:hover {{
    background-color: {self._qcolor_to_css(palette['surface_container_highest'])};
}}

QPushButton#DeleteSelectedBtn {{
    background-color: rgba(255, 180, 171, 26); /* error with low alpha */
    color: {self._qcolor_to_css(palette['error'])};
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: 600;
    font-size: 13px;
}}

QPushButton#DeleteSelectedBtn:hover {{
    background-color: rgba(255, 180, 171, 51);
}}

/* Entry Sub-items */
QLabel#EntryName {{
    background: transparent;
    font-size: 13px;
    font-weight: 700;
    color: {self._qcolor_to_css(palette['on_surface'])};
}}

QLabel#EntryPath {{
    background: transparent;
    font-size: 11px;
    color: {self._qcolor_to_css(palette['on_surface_variant'])};
}}

QLabel#EntryMeta {{
    background: transparent;
    font-size: 10px;
    color: {self._qcolor_to_css(palette['outline'])};
}}

QLabel#MatchBadge {{
    background: transparent;
    font-size: 10px;
    font-weight: 800;
    color: {self._qcolor_to_css(palette['primary'])};
}}

QLabel#LockIcon {{
    background: transparent;
    font-size: 16px;
    opacity: 0.5;
}}

QLabel#ThumbnailContainer {{
    background-color: {self._qcolor_to_css(palette['surface_container_lowest'])};
    border-radius: 8px;
}}

/* QScrollBar */
QScrollBar:vertical {{
    background-color: transparent;
    width: 6px;
    margin: 0;
}}

QScrollBar::handle:vertical {{
    background-color: {self._qcolor_to_css(palette['outline_variant'])};
    border-radius: 3px;
    min-height: 30px;
}}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {{
    height: 0px;
}}

/* Custom Checkbox */
QCheckBox::indicator {{
    width: 20px;
    height: 20px;
    border: 2px solid {self._qcolor_to_css(palette['outline_variant'])};
    border-radius: 6px;
    background-color: {self._qcolor_to_css(palette['surface_container_lowest'])};
}}

QCheckBox::indicator:checked {{
    background-color: {self._qcolor_to_css(palette['primary'])};
    border-color: {self._qcolor_to_css(palette['primary'])};
}}

/* Status Bar */
#FooterBar {{
    background-color: {self._qcolor_to_css(palette['background'])};
    border-top: 1px solid {self._qcolor_to_css(palette['indented_line'])};
}}
"""
        return qss
    
    def _apply_theme(self, theme):
        """Apply the theme to the application.
        
        Args:
            theme: 'light' or 'dark'
        """
        palette = self.dark_palette if theme == self.THEME_DARK else self.light_palette
        
        # Apply QPalette to QApplication
        qpalette = QApplication.palette()
        qpalette.setColor(QPalette.Window, palette['surface'])
        qpalette.setColor(QPalette.WindowText, palette['on_surface'])
        qpalette.setColor(QPalette.Base, palette['surface_container_low'])
        qpalette.setColor(QPalette.AlternateBase, palette['surface_container'])
        qpalette.setColor(QPalette.ToolTipBase, palette['surface_container_highest'])
        qpalette.setColor(QPalette.ToolTipText, palette['on_surface'])
        qpalette.setColor(QPalette.Text, palette['on_surface'])
        qpalette.setColor(QPalette.Button, palette['surface_container_high'])
        qpalette.setColor(QPalette.ButtonText, palette['on_surface'])
        qpalette.setColor(QPalette.BrightText, palette['primary'])
        qpalette.setColor(QPalette.Link, palette['primary'])
        qpalette.setColor(QPalette.Highlight, palette['primary_container'])
        qpalette.setColor(QPalette.HighlightedText, palette['on_primary_container'])
        
        QApplication.setPalette(qpalette)
        
        # Apply QSS stylesheet
        qss = self._generate_qss(theme)
        QApplication.instance().setStyleSheet(qss)
    
    def _qcolor_to_css(self, color):
        """Convert QColor to CSS color string."""
        if color.alpha() < 255:
            return f"rgba({color.red()}, {color.green()}, {color.blue()}, {color.alpha() / 255.0})"
        return f"rgb({color.red()}, {color.green()}, {color.blue()})"
    
    def _adjust_brightness(self, color, amount):
        """Adjust brightness of a color by amount (-255 to 255)."""
        r = max(0, min(255, color.red() + amount))
        g = max(0, min(255, color.green() + amount))
        b = max(0, min(255, color.blue() + amount))
        return f"rgb({r}, {g}, {b})"