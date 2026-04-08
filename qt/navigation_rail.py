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

from PyQt5.QtCore import Qt, pyqtSignal, QSize, QPropertyAnimation, QEasingCurve
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QLabel, 
    QScrollArea, QFrame, QListWidget, QListWidgetItem, 
    QComboBox, QSlider, QToolButton, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QIcon, QFont, QColor

from hscommon.trans import trget
from hscommon.util import format_size

tr = trget("ui")


class FolderItemWidget(QWidget):
    """Custom widget for folder items in the sidebar list."""
    removeClicked = pyqtSignal(str)  # Folder path
    
    def __init__(self, folder_path, parent=None):
        super().__init__(parent)
        self.folder_path = folder_path
        self.setObjectName("FolderItem")
        self._setup_ui()
        
    def _setup_ui(self):
        layout = QHBoxLayout(self)
        layout.setContentsMargins(8, 6, 8, 6)
        layout.setSpacing(8)
        
        # Icon
        self.icon_label = QLabel("📁")
        self.icon_label.setStyleSheet("font-size: 14px;")
        layout.addWidget(self.icon_label)
        
        # Path label (elided)
        self.path_label = QLabel(self.folder_path)
        self.path_label.setStyleSheet("font-size: 12px; color: #d1d5db;")
        self.path_label.setToolTip(self.folder_path)
        layout.addWidget(self.path_label)
        
        layout.addStretch()
        
        # Remove button (hidden by default)
        self.remove_btn = QToolButton()
        self.remove_btn.setText("×")
        self.remove_btn.setFixedSize(20, 20)
        self.remove_btn.setCursor(Qt.PointingHandCursor)
        self.remove_btn.setStyleSheet("""
            QToolButton {
                background: transparent;
                color: #ef4444;
                border: none;
                font-size: 16px;
                font-weight: bold;
            }
            QToolButton:hover {
                background: rgba(239, 68, 68, 0.1);
                border-radius: 4px;
            }
        """)
        self.remove_btn.clicked.connect(lambda: self.removeClicked.emit(self.folder_path))
        self.remove_btn.hide()
        layout.addWidget(self.remove_btn)

    def enterEvent(self, event):
        self.remove_btn.show()
        super().enterEvent(event)
        
    def leaveEvent(self, event):
        self.remove_btn.hide()
        super().leaveEvent(event)


class NavigationRail(QWidget):
    """A comprehensive sidebar control panel."""
    
    modeChanged = pyqtSignal(str)   # "Standard", "Music", "Picture"
    startScanClicked = pyqtSignal()
    addFolderClicked = pyqtSignal()
    removeFolderClicked = pyqtSignal(str)
    scanTypeChanged = pyqtSignal(int)
    thresholdChanged = pyqtSignal(int)
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("NavigationRail")
        self.setFixedWidth(260)
        self.items = []
        self.mode_buttons = {}
        
        # Access app-level references if available
        self.app = parent.app if parent and hasattr(parent, 'app') else None
        
        self._setup_ui()
        
    def _setup_ui(self):
        # Main Layout
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.layout.setSpacing(0)
        
        # Scroll Area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameStyle(QFrame.NoFrame)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        
        self.container = QWidget()
        self.scroll_layout = QVBoxLayout(self.container)
        self.scroll_layout.setContentsMargins(0, 8, 0, 16)
        self.scroll_layout.setSpacing(12)
        
        self._add_section_header(tr("Application Mode"))
        mode_layout = QVBoxLayout()
        mode_layout.setSpacing(2)
        
        modes = [
            ("standard", tr("Standard"), "folder"),
            ("music", tr("Music"), "music"),
            ("picture", tr("Picture"), "image")
        ]
        
        for name, label, icon in modes:
            btn = QPushButton(label)
            btn.setObjectName("ModeButton")
            btn.setCheckable(True)
            btn.setCursor(Qt.PointingHandCursor)
            btn.clicked.connect(lambda checked, n=name: self._on_mode_clicked(n))
            mode_layout.addWidget(btn)
            self.mode_buttons[name] = btn
            
        self.scroll_layout.addLayout(mode_layout)
        
        # 2. Folders to Scan Section
        add_folder_btn = QPushButton(f"+ {tr('Add Folder')}")
        add_folder_btn.setObjectName("AddFolderBtn")
        add_folder_btn.setCursor(Qt.PointingHandCursor)
        add_folder_btn.clicked.connect(self.addFolderClicked.emit)
        
        self._add_section_header(tr("Folders to Scan"), action_widget=add_folder_btn)
        
        # Folder List
        self.folder_list_layout = QVBoxLayout()
        self.folder_list_layout.setSpacing(2)
        self.scroll_layout.addLayout(self.folder_list_layout)
        
        # 3. Scan Options Section
        self._add_section_header(tr("Scan Options"))
        
        options_container = QWidget()
        opts_layout = QVBoxLayout(options_container)
        opts_layout.setContentsMargins(16, 0, 16, 0)
        opts_layout.setSpacing(12)
        
        # Scan Type Dropdown
        type_label = QLabel(tr("Scan Type"))
        type_label.setObjectName("ScanOptionsLabel")
        opts_layout.addWidget(type_label)
        
        self.scan_type_combo = QComboBox()
        self.scan_type_combo.setObjectName("NavigationRailDropdown")
        self.scan_type_combo.currentIndexChanged.connect(self.scanTypeChanged.emit)
        opts_layout.addWidget(self.scan_type_combo)
        
        # Threshold Slider
        thresh_header = QHBoxLayout()
        thresh_label = QLabel(tr("Threshold"))
        thresh_label.setObjectName("ScanOptionsLabel")
        thresh_header.addWidget(thresh_label)
        
        thresh_header.addStretch()
        
        self.thresh_value_label = QLabel("95%")
        self.thresh_value_label.setObjectName("ThresholdValueLabel")
        thresh_header.addWidget(self.thresh_value_label)
        
        opts_layout.addLayout(thresh_header)
        
        self.thresh_slider = QSlider(Qt.Horizontal)
        self.thresh_slider.setRange(50, 100)
        self.thresh_slider.setValue(95)
        self.thresh_slider.valueChanged.connect(self._on_thresh_changed)
        opts_layout.addWidget(self.thresh_slider)
        
        self.scroll_layout.addWidget(options_container)
        
        # Bottom spacer before button
        self.scroll_layout.addStretch()
        
        self.scroll_area.setWidget(self.container)
        self.layout.addWidget(self.scroll_area)
        
        # 4. START SCAN Button (Fixed Bottom with Container)
        self.start_container = QWidget()
        self.start_container.setObjectName("StartScanContainer")
        start_container_layout = QVBoxLayout(self.start_container)
        start_container_layout.setContentsMargins(16, 12, 16, 12)
        
        self.start_btn = QPushButton(tr("START SCAN"))
        self.start_btn.setObjectName("StartScanButton")
        self.start_btn.setCursor(Qt.PointingHandCursor)
        self.start_btn.setFixedHeight(48)
        self.start_btn.clicked.connect(self.startScanClicked.emit)
        start_container_layout.addWidget(self.start_btn)
        
        self.layout.addWidget(self.start_container)

    def _add_section_header(self, title, action_widget=None):
        header_widget = QWidget()
        header_layout = QHBoxLayout(header_widget)
        header_layout.setContentsMargins(0, 0, 0, 0)
        header_layout.setSpacing(0)
        
        label = QLabel(title)
        label.setObjectName("SectionHeader")
        header_layout.addWidget(label)
        
        if action_widget:
            header_layout.addStretch()
            header_layout.addWidget(action_widget)
            
        self.scroll_layout.addWidget(header_widget)

    def _on_mode_clicked(self, mode_name):
        # Update UI state
        for name, btn in self.mode_buttons.items():
            btn.setChecked(name == mode_name)
            btn.setProperty("active", name == mode_name)
            # Force style refresh
            btn.style().unpolish(btn)
            btn.style().polish(btn)
        
        self.modeChanged.emit(mode_name)

    def _on_thresh_changed(self, value):
        self.thresh_value_label.setText(f"{value}%")
        self.thresholdChanged.emit(value)

    def set_mode(self, mode_name):
        """External call to set the active mode."""
        self._on_mode_clicked(mode_name)

    def update_folders(self, folder_paths):
        """Update the folder list with new paths."""
        # Clear existing
        while self.folder_list_layout.count():
            item = self.folder_list_layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        # Add new
        for path in folder_paths:
            widget = FolderItemWidget(path)
            widget.removeClicked.connect(self.removeFolderClicked.emit)
            self.folder_list_layout.addWidget(widget)

    def update_scan_types(self, type_list, current_index=0):
        """Update available scan types in dropdown."""
        self.scan_type_combo.blockSignals(True)
        self.scan_type_combo.clear()
        self.scan_type_combo.addItems(type_list)
        self.scan_type_combo.setCurrentIndex(current_index)
        self.scan_type_combo.blockSignals(False)

    def set_threshold(self, value):
        """Update the threshold slider value."""
        self.thresh_slider.blockSignals(True)
        self.thresh_slider.setValue(value)
        self.thresh_value_label.setText(f"{value}%")
        self.thresh_slider.blockSignals(False)