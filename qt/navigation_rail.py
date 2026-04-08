# Copyright 2016 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

"""
Navigation Rail component for dupeGuru's modern sidebar design.

This module provides the NavigationRail class which implements
a modern sidebar navigation pattern similar to Windows 11 settings.
"""

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, QScrollArea
from PyQt5.QtGui import QIcon, QFont

from hscommon.trans import trget

tr = trget("ui")


class NavigationRail(QWidget):
    """A sidebar navigation rail for modern UI design.
    
    The navigation rail displays navigation items as icon+label buttons,
    highlights the current page, and emits signals for navigation.
    """
    
    itemClicked = pyqtSignal(str)  # Emitted when an item is clicked, with page name
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.items = []
        self.current_page_name = None
        
        # Get theme manager if available
        self.theme_manager = None
        if parent and hasattr(parent, 'app') and hasattr(parent.app, 'theme_manager'):
            self.theme_manager = parent.app.theme_manager
        
        self._setup_ui()
    
    def _setup_ui(self):
        """Setup the navigation rail UI."""
        # Main layout
        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)
        
        # Scroll area for navigation items
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.scroll_area.setVerticalScrollBarPolicy(Qt.ScrollBarAsNeeded)
        self.scroll_area.setFrameStyle(0)  # No frame
        
        # Container widget for scroll area
        self.scroll_widget = QWidget()
        self.scroll_layout = QVBoxLayout(self.scroll_widget)
        self.scroll_layout.setContentsMargins(8, 16, 8, 16)
        self.scroll_layout.setSpacing(4)
        self.scroll_layout.addStretch()
        
        self.scroll_area.setWidget(self.scroll_widget)
        self.main_layout.addWidget(self.scroll_area)
        
        # Set fixed width for sidebar (matching New_UI.html)
        self.setFixedWidth(260)
    
    def add_section(self, title, items):
        """Add a section of navigation items.
        
        Args:
            title: Section title (e.g., "Application Mode")
            items: List of (icon_name, label, page_name) tuples
        """
        # Section label
        section_label = QLabel(title)
        section_font = QFont()
        section_font.setBold(True)
        section_font.setPointSize(9)
        section_label.setFont(section_font)
        
        # Apply theme color if available
        if self.theme_manager:
            color = self.theme_manager.get_color('on_surface_variant')
            section_label.setStyleSheet(f"color: rgb({color.red()}, {color.green()}, {color.blue()}); padding: 8px 12px;")
        else:
            section_label.setStyleSheet("color: #888; padding: 8px 12px;")
        
        # Insert before stretch
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, section_label)
        
        # Add items
        for icon_name, label, page_name in items:
            self.add_item(icon_name, label, page_name)
    
    def add_item(self, icon_name, label, page_name):
        """Add a navigation item.
        
        Args:
            icon_name: Name of the icon (can be used to load from resources)
            label: Display label for the item
            page_name: Unique identifier for the page
        """
        button = QPushButton(label)
        button.setMinimumHeight(40)
        button.setMaximumHeight(40)
        button.setCursor(Qt.PointingHandCursor)
        
        # Store page name as property
        button.setProperty("pageName", page_name)
        
        # Set styling
        self._style_button(button, False)
        
        # Connect signal
        button.clicked.connect(lambda: self._on_item_clicked(page_name))
        
        # Insert before stretch
        self.scroll_layout.insertWidget(self.scroll_layout.count() - 1, button)
        
        # Store reference
        self.items.append({'button': button, 'page_name': page_name, 'label': label})
        
        return button
    
    def set_current_item(self, page_name):
        """Set the currently active navigation item.
        
        Args:
            page_name: The page name to set as active
        """
        self.current_page_name = page_name
        
        # Update button styles
        for item in self.items:
            is_current = item['page_name'] == page_name
            button = item['button']
            self._style_button(button, is_current)
    
    def _on_item_clicked(self, page_name):
        """Handle navigation item click."""
        self.set_current_item(page_name)
        self.itemClicked.emit(page_name)
    
    def _style_button(self, button, is_selected):
        """Apply styling to a navigation button."""
        if is_selected:
            # Selected state
            if self.theme_manager:
                bg_color = self.theme_manager.get_color('secondary_container')
                text_color = self.theme_manager.get_color('primary')
                border_color = self.theme_manager.get_color('primary')
                
                button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: rgb({bg_color.red()}, {bg_color.green()}, {bg_color.blue()});
                        color: rgb({text_color.red()}, {text_color.green()}, {text_color.blue()});
                        border: none;
                        border-left: 3px solid rgb({border_color.red()}, {border_color.green()}, {border_color.blue()});
                        border-radius: 6px;
                        padding: 12px;
                        text-align: left;
                        font-weight: 600;
                    }}
                """)
            else:
                button.setStyleSheet("""
                    QPushButton {
                        background-color: #2d486b;
                        color: #a3c9ff;
                        border: none;
                        border-left: 3px solid #a3c9ff;
                        border-radius: 6px;
                        padding: 12px;
                        text-align: left;
                        font-weight: 600;
                    }
                """)
        else:
            # Normal state
            if self.theme_manager:
                text_color = self.theme_manager.get_color('on_surface_variant')
                hover_bg = self.theme_manager.get_color('surface_container_highest')
                
                button.setStyleSheet(f"""
                    QPushButton {{
                        background-color: transparent;
                        color: rgb({text_color.red()}, {text_color.green()}, {text_color.blue()});
                        border: none;
                        border-radius: 6px;
                        padding: 12px;
                        text-align: left;
                    }}
                    QPushButton:hover {{
                        background-color: rgb({hover_bg.red()}, {hover_bg.green()}, {hover_bg.blue()});
                    }}
                """)
            else:
                button.setStyleSheet("""
                    QPushButton {
                        background-color: transparent;
                        color: #c0c7d4;
                        border: none;
                        border-radius: 6px;
                        padding: 12px;
                        text-align: left;
                    }
                    QPushButton:hover {
                        background-color: #353535;
                    }
                """)
    
    def apply_theme(self):
        """Apply theme colors to the navigation rail."""
        # Update theme manager reference
        if self.parent() and hasattr(self.parent(), 'app'):
            self.theme_manager = self.parent().app.theme_manager
        
        # Re-style all buttons
        for item in self.items:
            is_current = item['page_name'] == self.current_page_name
            self._style_button(item['button'], is_current)
        
        # Update section labels
        for i in range(self.scroll_layout.count()):
            widget = self.scroll_layout.itemAt(i).widget()
            if isinstance(widget, QLabel) and widget not in [item['button'] for item in self.items]:
                # This is a section label
                if self.theme_manager:
                    color = self.theme_manager.get_color('on_surface_variant')
                    widget.setStyleSheet(f"color: rgb({color.red()}, {color.green()}, {color.blue()}); padding: 8px 12px;")