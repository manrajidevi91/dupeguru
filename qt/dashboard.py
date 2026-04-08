# Copyright 2016 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from PyQt5.QtCore import Qt, QMimeData, pyqtSignal
from PyQt5.QtGui import QDragEnterEvent, QDropEvent
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QScrollArea,
    QFrame,
    QFileDialog,
    QMessageBox,
    QGridLayout,
    QComboBox,
)
from PyQt5.QtGui import QIcon, QPixmap, QFont

from hscommon.trans import trget
from core.app import AppMode

tr = trget("ui")


class RecentScanCard(QFrame):
    """A card widget representing a recent scan result."""
    
    clicked = pyqtSignal(str)
    
    def __init__(self, path, parent=None):
        super().__init__(parent)
        self.path = path
        self._setup_ui()
        
    def _setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(1)
        self.setCursor(Qt.PointingHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Icon and title
        title_layout = QHBoxLayout()
        
        # Try to extract a nice display name from path
        import os
        display_name = os.path.basename(self.path) if self.path else "Unknown"
        if len(display_name) > 30:
            display_name = display_name[:27] + "..."
        
        title_label = QLabel(display_name)
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(10)
        title_label.setFont(title_font)
        title_label.setWordWrap(True)
        
        title_layout.addWidget(title_label)
        layout.addLayout(title_layout)
        
        # Path as subtitle
        path_label = QLabel(self.path)
        path_font = QFont()
        path_font.setPointSize(8)
        path_label.setFont(path_font)
        path_label.setStyleSheet("color: gray;")
        path_label.setWordWrap(True)
        layout.addWidget(path_label)
        
        self.setMinimumSize(200, 100)
        self.setMaximumSize(300, 120)
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.path)
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background-color: #f0f0f0;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self.setStyleSheet("""
            QFrame {
                background-color: white;
                border: 1px solid #ccc;
                border-radius: 5px;
            }
        """)
        super().leaveEvent(event)


class Dashboard(QWidget):
    """Main dashboard screen - the new landing page for dupeGuru."""
    
    startScanRequested = pyqtSignal()
    loadResultsRequested = pyqtSignal(str)
    showDirectoriesRequested = pyqtSignal()
    showPreferencesRequested = pyqtSignal()
    showPresetsRequested = pyqtSignal()
    foldersDropped = pyqtSignal(list)
    
    def __init__(self, app, **kwargs):
        super().__init__(**kwargs)
        self.app = app
        self.specific_actions = set()
        self.recent_cards = []
        self._setup_ui()
        self._setup_connections()
        self._load_recent_scans()
        
    def _setup_ui(self):
        self.setWindowTitle(tr("dupeGuru Dashboard"))
        self.setMinimumSize(800, 600)
        self.setAcceptDrops(True)
        
        main_layout = QVBoxLayout(self)
        main_layout.setContentsMargins(20, 20, 20, 20)
        main_layout.setSpacing(20)
        
        # Header section
        header_layout = QHBoxLayout()
        header_layout.setSpacing(15)
        
        # Logo/Title area
        title_layout = QVBoxLayout()
        title_label = QLabel(tr("dupeGuru"))
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(18)
        title_label.setFont(title_font)
        title_layout.addWidget(title_label)
        
        subtitle_label = QLabel(tr("Find and remove duplicate files"))
        subtitle_font = QFont()
        subtitle_font.setPointSize(10)
        subtitle_label.setFont(subtitle_font)
        subtitle_label.setStyleSheet("color: gray;")
        title_layout.addWidget(subtitle_label)
        
        header_layout.addLayout(title_layout)
        header_layout.addStretch()
        
        # Application mode selector
        mode_layout = QHBoxLayout()
        mode_label = QLabel(tr("Mode:"))
        mode_label.setSizePolicy(mode_label.sizePolicy().Preferred, mode_label.sizePolicy().Fixed)
        mode_layout.addWidget(mode_label)
        
        self.app_mode_combo = QComboBox()
        self.app_mode_combo.addItem(tr("Standard"))
        self.app_mode_combo.addItem(tr("Music"))
        self.app_mode_combo.addItem(tr("Picture"))
        # Set current mode
        current_mode = self.app.model.app_mode
        if current_mode == AppMode.PICTURE:
            self.app_mode_combo.setCurrentIndex(2)
        elif current_mode == AppMode.MUSIC:
            self.app_mode_combo.setCurrentIndex(1)
        mode_layout.addWidget(self.app_mode_combo)
        
        header_layout.addLayout(mode_layout)
        
        # More Options button
        self.options_button = QPushButton(tr("More Options"))
        self.options_button.setMaximumWidth(120)
        header_layout.addWidget(self.options_button)
        
        main_layout.addLayout(header_layout)
        
        # Primary Actions section
        actions_label = QLabel(tr("Quick Actions"))
        actions_font = QFont()
        actions_font.setBold(True)
        actions_font.setPointSize(12)
        actions_label.setFont(actions_font)
        main_layout.addWidget(actions_label)
        
        actions_layout = QHBoxLayout()
        actions_layout.setSpacing(15)
        
        # Start Scan button
        self.start_scan_button = QPushButton(tr("Start New Scan"))
        self.start_scan_button.setMinimumHeight(60)
        self.start_scan_button.setMinimumWidth(200)
        self.start_scan_button.setStyleSheet("""
            QPushButton {
                background-color: #4CAF50;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #45a049;
            }
            QPushButton:pressed {
                background-color: #3d8b40;
            }
        """)
        actions_layout.addWidget(self.start_scan_button)
        
        # Load Results button
        self.load_results_button = QPushButton(tr("Load Saved Results"))
        self.load_results_button.setMinimumHeight(60)
        self.load_results_button.setMinimumWidth(200)
        self.load_results_button.setStyleSheet("""
            QPushButton {
                background-color: #2196F3;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #0b7dda;
            }
            QPushButton:pressed {
                background-color: #0a6ebd;
            }
        """)
        actions_layout.addWidget(self.load_results_button)
        
        # Directories button
        self.directories_button = QPushButton(tr("Manage Directories"))
        self.directories_button.setMinimumHeight(60)
        self.directories_button.setMinimumWidth(200)
        self.directories_button.setStyleSheet("""
            QPushButton {
                background-color: #FF9800;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #e68900;
            }
            QPushButton:pressed {
                background-color: #cc7a00;
            }
        """)
        actions_layout.addWidget(self.directories_button)
        
        # Manage Presets button
        self.presets_button = QPushButton(tr("Manage Presets"))
        self.presets_button.setMinimumHeight(60)
        self.presets_button.setMinimumWidth(200)
        self.presets_button.setStyleSheet("""
            QPushButton {
                background-color: #9C27B0;
                color: white;
                border: none;
                border-radius: 5px;
                font-size: 14px;
                font-weight: bold;
            }
            QPushButton:hover {
                background-color: #7B1FA2;
            }
            QPushButton:pressed {
                background-color: #6A1B9A;
            }
        """)
        actions_layout.addWidget(self.presets_button)
        
        actions_layout.addStretch()
        main_layout.addLayout(actions_layout)
        
        # Drag & Drop zone
        self.drop_zone_label = QLabel(tr("Or drag and drop folders here to scan"))
        self.drop_zone_label.setAlignment(Qt.AlignCenter)
        self.drop_zone_label.setMinimumHeight(80)
        self.drop_zone_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
                color: #666;
                font-size: 13px;
            }
        """)
        main_layout.addWidget(self.drop_zone_label)
        
        # Recent Scans section
        recent_label = QLabel(tr("Recent Scans"))
        recent_font = QFont()
        recent_font.setBold(True)
        recent_font.setPointSize(12)
        recent_label.setFont(recent_font)
        main_layout.addWidget(recent_label)
        
        # Scroll area for recent scans
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setMinimumHeight(200)
        self.scroll_area.setMaximumHeight(300)
        self.scroll_area.setFrameStyle(QFrame.NoFrame)
        
        self.recent_widget = QWidget()
        self.recent_layout = QGridLayout(self.recent_widget)
        self.recent_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.recent_layout.setSpacing(15)
        self.scroll_area.setWidget(self.recent_widget)
        
        main_layout.addWidget(self.scroll_area)
        
        # Status bar / Progress area placeholder
        self.progress_label = QLabel(tr("Ready"))
        self.progress_label.setStyleSheet("color: gray; font-size: 11px;")
        main_layout.addWidget(self.progress_label)
        
    def _setup_connections(self):
        """Connect signals to slots."""
        self.start_scan_button.clicked.connect(self.startScanRequested)
        self.load_results_button.clicked.connect(self._load_results)
        self.directories_button.clicked.connect(self.showDirectoriesRequested)
        self.presets_button.clicked.connect(self.showPresetsRequested)
        self.options_button.clicked.connect(self.showPreferencesRequested)
        self.app_mode_combo.currentIndexChanged.connect(self._app_mode_changed)
        
    def _load_results(self):
        """Show file dialog to load results."""
        title = tr("Select a results file to load")
        files = ";;".join([tr("dupeGuru Results (*.dupeguru)"), tr("All Files (*.*)")])
        destination = QFileDialog.getOpenFileName(self, title, "", files)[0]
        if destination:
            self.loadResultsRequested.emit(destination)
            
    def _app_mode_changed(self, index):
        """Handle application mode change."""
        if index == 2:
            mode = AppMode.PICTURE
        elif index == 1:
            mode = AppMode.MUSIC
        else:
            mode = AppMode.STANDARD
        self.app.model.app_mode = mode
        
    def _load_recent_scans(self):
        """Load and display recent scan results."""
        # Clear existing cards
        for card in self.recent_cards:
            card.deleteLater()
        self.recent_cards.clear()
        
        # Get recent items from preferences
        recent_items = getattr(self.app.prefs, 'recentResults', [])
        
        if not recent_items:
            # Show empty state
            empty_label = QLabel(tr("No recent scans"))
            empty_label.setStyleSheet("color: gray; font-size: 13px;")
            self.recent_layout.addWidget(empty_label, 0, 0)
            return
        
        # Create cards for recent scans
        row, col = 0, 0
        max_cols = 4
        
        for path in recent_items[:10]:  # Show max 10 recent scans
            card = RecentScanCard(path, self)
            card.clicked.connect(self.loadResultsRequested)
            self.recent_cards.append(card)
            self.recent_layout.addWidget(card, row, col)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
                
    def refresh_recent_scans(self):
        """Refresh the recent scans display."""
        self._load_recent_scans()
        
    def set_progress(self, message):
        """Update the progress/status message."""
        self.progress_label.setText(message)
        
    # Drag and Drop handlers
    def dragEnterEvent(self, event: QDragEnterEvent):
        """Handle drag enter event."""
        if event.mimeData().hasUrls():
            event.acceptProposedAction()
            self.drop_zone_label.setStyleSheet("""
                QLabel {
                    border: 2px dashed #4CAF50;
                    border-radius: 10px;
                    background-color: #e8f5e9;
                    color: #2e7d32;
                    font-size: 13px;
                }
            """)
            
    def dragLeaveEvent(self, event):
        """Handle drag leave event."""
        self.drop_zone_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
                color: #666;
                font-size: 13px;
            }
        """)
        
    def dropEvent(self, event: QDropEvent):
        """Handle drop event."""
        mime_data = event.mimeData()
        if mime_data.hasUrls():
            folders = []
            for url in mime_data.urls():
                path = url.toLocalFile()
                if path:
                    folders.append(path)
            
            if folders:
                self.foldersDropped.emit(folders)
                
        # Reset drop zone style
        self.drop_zone_label.setStyleSheet("""
            QLabel {
                border: 2px dashed #ccc;
                border-radius: 10px;
                background-color: #f9f9f9;
                color: #666;
                font-size: 13px;
            }
        """)
        
        event.acceptProposedAction()