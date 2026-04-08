from PyQt5.QtCore import Qt, pyqtSignal, QSize, QRect, QPoint
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QFrame, 
    QScrollArea, QPushButton, QCheckBox, QSpacerItem, QSizePolicy
)
from PyQt5.QtGui import QPixmap, QFont, QColor, QPainter, QIcon

from hscommon.trans import trget
from hscommon.util import format_size

tr = trget("ui")


class FileEntryWidget(QFrame):
    """A widget for a single file entry within a group."""
    
    clicked = pyqtSignal(object)  # file_obj
    markedChanged = pyqtSignal(object, bool) # file_obj, is_marked
    
    def __init__(self, group, file_obj, results, is_reference=False, parent=None):
        super().__init__(parent)
        self.group = group
        self.file_obj = file_obj
        self.results = results
        self.is_reference = is_reference
        
        # Determine styling class
        self.setProperty("class", "ReferenceEntry" if is_reference else "DuplicateEntry")
        
        self._setup_ui()
        self.update_state()
        
    def _setup_ui(self):
        self.layout = QHBoxLayout(self)
        if not self.is_reference:
            self.layout.setContentsMargins(48, 12, 12, 12)
        else:
            self.layout.setContentsMargins(12, 12, 12, 12)
        self.layout.setSpacing(16)
        
        # Thumbnail
        self.thumbnail = QLabel()
        self.thumbnail.setFixedSize(64 if self.is_reference else 56, 64 if self.is_reference else 56)
        self.thumbnail.setObjectName("ThumbnailContainer")
        self.thumbnail.setAlignment(Qt.AlignCenter)
        self.layout.addWidget(self.thumbnail)
        
        # Info Vertical Layout
        info_layout = QVBoxLayout()
        info_layout.setSpacing(2)
        
        # Name + Badge Row
        name_row = QHBoxLayout()
        name_row.setSpacing(8)
        
        self.name_label = QLabel(self.file_obj.name)
        self.name_label.setObjectName("EntryName")
        name_row.addWidget(self.name_label)
        
        if self.is_reference:
            self.badge = QLabel(tr("REFERENCE"))
            self.badge.setObjectName("ReferenceBadge")
            name_row.addWidget(self.badge)
        
        name_row.addStretch()
        info_layout.addLayout(name_row)
        
        # Path label
        self.path_label = QLabel(str(self.file_obj.path))
        self.path_label.setObjectName("EntryPath")
        info_layout.addWidget(self.path_label)
        
        # Metadata Row (Size / Match)
        meta_row = QHBoxLayout()
        meta_row.setSpacing(12)
        
        size_text = format_size(self.file_obj.size, 1)
        self.size_label = QLabel(size_text)
        self.size_label.setObjectName("EntryMeta")
        meta_row.addWidget(self.size_label)
        
        if not self.is_reference:
            match = self.results.get_match(self.file_obj)
            if match:
                self.match_label = QLabel(f"{tr('Match')}: {match.percentage}%")
                self.match_label.setObjectName("MatchBadge")
                meta_row.addWidget(self.match_label)
        
        meta_row.addStretch()
        info_layout.addLayout(meta_row)
        
        self.layout.addLayout(info_layout)
        
        # Action (Checkbox or Lock)
        self.action_container = QWidget()
        action_layout = QVBoxLayout(self.action_container)
        action_layout.setContentsMargins(0, 0, 0, 0)
        
        if self.is_reference:
            self.lock_label = QLabel("🔒")
            self.lock_label.setObjectName("LockIcon")
            action_layout.addWidget(self.lock_label)
        else:
            self.checkbox = QCheckBox()
            self.checkbox.setCursor(Qt.PointingHandCursor)
            self.checkbox.stateChanged.connect(self._on_checkbox_changed)
            action_layout.addWidget(self.checkbox)
            
        self.layout.addWidget(self.action_container)

    def update_state(self):
        """Update visual state based on marked/selected results."""
        is_marked = self.results.is_marked(self.file_obj)
        if not self.is_reference:
            self.checkbox.blockSignals(True)
            self.checkbox.setChecked(is_marked)
            self.checkbox.blockSignals(False)
            
        # Update styling based on marked state
        if is_marked:
            self.setProperty("marked", True)
        else:
            self.setProperty("marked", False)
        
        self.style().unpolish(self)
        self.style().polish(self)

    def _on_checkbox_changed(self, state):
        self.markedChanged.emit(self.file_obj, state == Qt.Checked)

    def mouseDoubleClickEvent(self, event):
        self.clicked.emit(self.file_obj)
        super().mouseDoubleClickEvent(event)


class GroupWidget(QWidget):
    """A widget displaying a duplicate group in list format."""
    
    fileClicked = pyqtSignal(object)
    
    def __init__(self, group, results, parent=None):
        super().__init__(parent)
        self.group = group
        self.results = results
        self.entries = []
        self._setup_ui()
        
    def _setup_ui(self):
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 16)
        self.layout.setSpacing(4)
        
        # Header Row
        header = QWidget()
        header_layout = QHBoxLayout(header)
        header_layout.setContentsMargins(0, 0, 0, 8)
        
        icon = QLabel("📁")
        icon.setStyleSheet("color: #a3c9ff; font-size: 16px;")
        header_layout.addWidget(icon)
        
        title = QLabel(f"{tr('Group')} {self.group.id}: \"{self.group.ref.name}\"")
        title.setStyleSheet("font-weight: 600; color: #f4f4f5; font-size: 13px;")
        header_layout.addWidget(title)
        header_layout.addStretch()
        
        # Separator line in header
        line = QFrame()
        line.setFrameShape(QFrame.HLine)
        line.setStyleSheet("background-color: rgba(255, 255, 255, 0.05);")
        header_layout.addWidget(line)
        header_layout.setStretchFactor(line, 1)
        
        self.layout.addWidget(header)
        
        # Reference Entry
        ref_widget = FileEntryWidget(self.group, self.group.ref, self.results, is_reference=True)
        ref_widget.clicked.connect(self.fileClicked.emit)
        self.layout.addWidget(ref_widget)
        self.entries.append(ref_widget)
        
        # Indented Duplicates
        for dupe in self.group.dupes:
            if dupe == self.group.ref:
                continue
            dupe_widget = FileEntryWidget(self.group, dupe, self.results, is_reference=False)
            dupe_widget.clicked.connect(self.fileClicked.emit)
            dupe_widget.markedChanged.connect(self._on_marked_changed)
            self.layout.addWidget(dupe_widget)
            self.entries.append(dupe_widget)

    def _on_marked_changed(self, file_obj, is_marked):
        # The actual marking is handled by result_window or app, 
        # but we might need to update other UI elements
        pass

    def update_entries(self):
        """Refresh entries UI."""
        for entry in self.entries:
            entry.update_state()


class ResultsListView(QScrollArea):
    """Modern grouped list view for scan results."""
    
    fileClicked = pyqtSignal(object)
    
    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.results = results
        self.group_widgets = []
        self._setup_ui()
        
    def _setup_ui(self):
        self.setWidgetResizable(True)
        self.setFrameStyle(QFrame.NoFrame)
        self.viewport().setStyleSheet("background: transparent;")
        
        self.container = QWidget()
        self.container.setStyleSheet("background: transparent;")
        self.layout = QVBoxLayout(self.container)
        self.layout.setContentsMargins(24, 16, 24, 16)
        self.layout.setSpacing(24)
        self.layout.addStretch()
        
        self.setWidget(self.container)

    def reload(self, results=None):
        """Reload the entire list."""
        if results:
            self.results = results
            
        # Clear existing
        while self.layout.count() > 1:
            item = self.layout.takeAt(0)
            if item.widget():
                item.widget().deleteLater()
        
        self.group_widgets.clear()
        
        # Add groups
        for group in self.results.groups:
            group_widget = GroupWidget(group, self.results)
            group_widget.fileClicked.connect(self.fileClicked.emit)
            self.layout.insertWidget(self.layout.count() - 1, group_widget)
            self.group_widgets.append(group_widget)

    def refresh(self):
        """Refresh selection/marked states without full reload."""
        for gw in self.group_widgets:
            gw.update_entries()
