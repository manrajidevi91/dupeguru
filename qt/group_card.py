# Copyright 2016 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from PyQt5.QtCore import Qt, pyqtSignal, QSize
from PyQt5.QtGui import QPixmap, QPainter, QFont, QCursor
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QPushButton,
    QScrollArea,
    QGridLayout,
    QToolButton,
    QMenu,
    QAction,
)
from PyQt5.QtSvg import QSvgWidget

from hscommon.trans import trget
from core.group_presenter import GroupSummary, FileMetadata

tr = trget("ui")


class FileThumbnail(QFrame):
    """A small thumbnail widget for a file within a group card."""
    
    clicked = pyqtSignal(object)  # File object
    
    def __init__(self, metadata, parent=None):
        super().__init__(parent)
        self.metadata = metadata
        self.is_selected = False
        self._setup_ui()
        
    def _setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(1)
        self.setCursor(Qt.PointingHandCursor)
        self.setMaximumSize(120, 140)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(4)
        
        # Thumbnail/image placeholder
        self.thumbnail = QLabel()
        self.thumbnail.setFixedSize(100, 80)
        self.thumbnail.setStyleSheet("""
            QLabel {
                background-color: #f0f0f0;
                border: 1px solid #ddd;
            }
        """)
        self.thumbnail.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.thumbnail)
        
        # File info
        self.info_label = QLabel()
        self.info_label.setWordWrap(True)
        self.info_label.setStyleSheet("font-size: 9px;")
        layout.addWidget(self.info_label)
        
        # Update display
        self._update_display()
        
    def _update_display(self):
        """Update the thumbnail display with file metadata."""
        meta = self.metadata
        
        # Show file size
        size_text = meta.size_formatted
        if meta.dimensions:
            w, h = meta.dimensions
            size_text += f"\n{w}×{h}"
        
        self.info_label.setText(size_text)
        
        # Visual indication of reference
        if meta.is_reference:
            self.setStyleSheet("""
                QFrame {
                    background-color: #e8f5e9;
                    border: 2px solid #4CAF50;
                    border-radius: 4px;
                }
            """)
        elif meta.is_marked:
            self.setStyleSheet("""
                QFrame {
                    background-color: #ffebee;
                    border: 2px solid #f44336;
                    border-radius: 4px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 1px solid #ddd;
                    border-radius: 4px;
                }
            """)
            
        if self.is_selected:
            self.setStyleSheet(self.styleSheet() + """
                QFrame {
                    border: 3px solid #2196F3;
                }
            """)
    
    def set_selected(self, selected):
        """Set selection state."""
        self.is_selected = selected
        self._update_display()
        
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.clicked.emit(self.metadata.file)
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        if not self.is_selected:
            self.setStyleSheet(self.styleSheet() + """
                QFrame {
                    background-color: #f5f5f5;
                }
            """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._update_display()
        super().leaveEvent(event)


class GroupCard(QFrame):
    """
    A card widget displaying a duplicate group.
    
    Shows:
    - Group title and duplicate count
    - Best image at top
    - Duplicate thumbnails below
    - Similarity, resolution, and file-size badges
    - Visual affordances for selection state
    """
    
    groupSelected = pyqtSignal(object)  # Group object
    fileClicked = pyqtSignal(object, object)  # Group, File
    actionTriggered = pyqtSignal(object, str)  # Group, action_name
    
    def __init__(self, group, summary, parent=None):
        super().__init__(parent)
        self.group = group
        self.summary = summary
        self.selected = False
        self.expanded = False
        self.selected_files = set()
        self._setup_ui()
        
    def _setup_ui(self):
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Raised)
        self.setLineWidth(2)
        self.setCursor(Qt.PointingHandCursor)
        self.setMinimumSize(350, 200)
        self.setMaximumSize(450, 600)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header: title and duplicate count
        header_layout = QHBoxLayout()
        
        title_label = QLabel(tr("Duplicate Group"))
        title_font = QFont()
        title_font.setBold(True)
        title_font.setPointSize(11)
        title_label.setFont(title_font)
        header_layout.addWidget(title_label)
        
        header_layout.addStretch()
        
        # Duplicate count badge
        count_badge = QLabel(str(self.summary.duplicate_count))
        count_badge.setStyleSheet("""
            QLabel {
                background-color: #FF9800;
                color: white;
                border-radius: 12px;
                padding: 4px 12px;
                font-weight: bold;
            }
        """)
        header_layout.addWidget(count_badge)
        
        layout.addLayout(header_layout)
        
        # Best candidate (reference) at top
        if self.summary.best_candidate:
            best_label = QLabel(tr("Best Match"))
            best_label.setStyleSheet("color: #4CAF50; font-weight: bold; font-size: 9px;")
            layout.addWidget(best_label)
            
            ref_metadata = self._get_file_metadata(self.summary.best_candidate)
            if ref_metadata:
                self.best_thumbnail = FileThumbnail(ref_metadata, self)
                self.best_thumbnail.clicked.connect(lambda f: self.fileClicked.emit(self.group, f))
                layout.addWidget(self.best_thumbnail)
        
        # Separator
        separator = QFrame()
        separator.setFrameShape(QFrame.HLine)
        separator.setStyleSheet("background-color: #ddd;")
        layout.addWidget(separator)
        
        # Duplicates section
        dupes_label = QLabel(tr("Duplicates"))
        dupes_label.setStyleSheet("color: #666; font-weight: bold; font-size: 9px;")
        layout.addWidget(dupes_label)
        
        # Scrollable area for duplicates
        self.duplicates_scroll = QScrollArea()
        self.duplicates_scroll.setWidgetResizable(True)
        self.duplicates_scroll.setMaximumHeight(200)
        self.duplicates_scroll.setFrameStyle(QFrame.NoFrame)
        
        self.duplicates_widget = QWidget()
        self.duplicates_layout = QGridLayout(self.duplicates_widget)
        self.duplicates_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.duplicates_layout.setSpacing(8)
        self.duplicates_scroll.setWidget(self.duplicates_widget)
        
        layout.addWidget(self.duplicates_scroll)
        
        # Info badges
        badges_layout = QHBoxLayout()
        badges_layout.setSpacing(8)
        
        # Space saved badge
        space_saved = self.summary.space_saved
        if space_saved > 0:
            from hscommon.util import format_size
            space_text = format_size(space_saved, 1)
            space_badge = QLabel(f"💾 {space_text}")
            space_badge.setStyleSheet("""
                QLabel {
                    background-color: #e3f2fd;
                    color: #1976d2;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 9px;
                }
            """)
            badges_layout.addWidget(space_badge)
        
        # Similarity badge
        min_sim, max_sim = self.summary.similarity_range
        if min_sim > 0:
            sim_badge = QLabel(f"📊 {min_sim}-{max_sim}%")
            sim_badge.setStyleSheet("""
                QLabel {
                    background-color: #fff3e0;
                    color: #f57c00;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 9px;
                }
            """)
            badges_layout.addWidget(sim_badge)
        
        # Resolution badge (for images)
        if self.summary.has_images and self.summary.resolution_summary:
            res = self.summary.resolution_summary
            max_dims = res['max_dimensions']
            res_badge = QLabel(f"🖼️ {max_dims[0]}×{max_dims[1]}")
            res_badge.setStyleSheet("""
                QLabel {
                    background-color: #fce4ec;
                    color: #c2185b;
                    border-radius: 4px;
                    padding: 4px 8px;
                    font-size: 9px;
                }
            """)
            badges_layout.addWidget(res_badge)
        
        badges_layout.addStretch()
        layout.addLayout(badges_layout)
        
        # Quick actions button
        actions_layout = QHBoxLayout()
        actions_layout.addStretch()
        
        self.actions_button = QPushButton("⚙")
        self.actions_button.setMaximumSize(30, 30)
        self.actions_button.setToolTip(tr("Quick Actions"))
        self.actions_button.clicked.connect(self._show_actions_menu)
        actions_layout.addWidget(self.actions_button)
        
        layout.addLayout(actions_layout)
        
        layout.addStretch()
        
        # Load duplicates
        self._load_duplicates()
        
        # Apply initial styling
        self._update_style()
    
    def _get_file_metadata(self, file_obj):
        """Get metadata for a file from the presenter."""
        # Access presenter through results
        results = self.parent().results if hasattr(self.parent(), 'results') else None
        if results and results.presenter:
            return results.presenter.get_file_metadata(file_obj, self.group)
        return None
    
    def _load_duplicates(self):
        """Load duplicate file thumbnails."""
        # Clear existing
        for i in reversed(range(self.duplicates_layout.count())):
            self.duplicates_layout.itemAt(i).widget().setParent(None)
        
        # Add duplicates (skip best candidate)
        row, col = 0, 0
        max_cols = 3
        
        for file_obj in self.group.dupes:
            if file_obj == self.summary.best_candidate:
                continue
            
            metadata = self._get_file_metadata(file_obj)
            if metadata:
                thumbnail = FileThumbnail(metadata, self)
                thumbnail.clicked.connect(lambda f: self.fileClicked.emit(self.group, f))
                
                if file_obj in self.selected_files:
                    thumbnail.set_selected(True)
                
                self.duplicates_layout.addWidget(thumbnail, row, col)
                
                col += 1
                if col >= max_cols:
                    col = 0
                    row += 1
    
    def _update_style(self):
        """Update card styling based on state."""
        if self.selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #e3f2fd;
                    border: 3px solid #2196F3;
                    border-radius: 8px;
                }
            """)
        else:
            self.setStyleSheet("""
                QFrame {
                    background-color: white;
                    border: 2px solid #ddd;
                    border-radius: 8px;
                }
            """)
    
    def _show_actions_menu(self):
        """Show quick actions menu for this group."""
        menu = QMenu(self)
        
        # Select all except best
        select_action = QAction(tr("Select All Except Best"), self)
        select_action.triggered.connect(lambda: self.actionTriggered.emit(self.group, "select_all_except_best"))
        menu.addAction(select_action)
        
        menu.addSeparator()
        
        # Keep newest
        newest_action = QAction(tr("Keep Newest"), self)
        newest_action.triggered.connect(lambda: self.actionTriggered.emit(self.group, "keep_newest"))
        menu.addAction(newest_action)
        
        # Keep oldest
        oldest_action = QAction(tr("Keep Oldest"), self)
        oldest_action.triggered.connect(lambda: self.actionTriggered.emit(self.group, "keep_oldest"))
        menu.addAction(oldest_action)
        
        if self.summary.has_images:
            menu.addSeparator()
            
            # Keep highest resolution
            res_action = QAction(tr("Keep Highest Resolution"), self)
            res_action.triggered.connect(lambda: self.actionTriggered.emit(self.group, "keep_highest_resolution"))
            menu.addAction(res_action)
        
        menu.addSeparator()
        
        # Keep largest
        largest_action = QAction(tr("Keep Largest"), self)
        largest_action.triggered.connect(lambda: self.actionTriggered.emit(self.group, "keep_largest"))
        menu.addAction(largest_action)
        
        # Keep smallest
        smallest_action = QAction(tr("Keep Smallest"), self)
        smallest_action.triggered.connect(lambda: self.actionTriggered.emit(self.group, "keep_smallest"))
        menu.addAction(smallest_action)
        
        # Show menu
        menu.exec_(self.actions_button.mapToGlobal(self.actions_button.rect().bottomLeft()))
    
    def set_selected(self, selected):
        """Set card selection state."""
        self.selected = selected
        self._update_style()
    
    def toggle_selection(self):
        """Toggle card selection."""
        self.selected = not self.selected
        self._update_style()
        if self.selected:
            self.groupSelected.emit(self.group)
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.toggle_selection()
        super().mousePressEvent(event)
    
    def enterEvent(self, event):
        if not self.selected:
            self.setStyleSheet("""
                QFrame {
                    background-color: #f5f5f5;
                    border: 2px solid #2196F3;
                    border-radius: 8px;
                }
            """)
        super().enterEvent(event)
    
    def leaveEvent(self, event):
        self._update_style()
        super().leaveEvent(event)
    
    def update_content(self):
        """Refresh card content if group changed."""
        self._load_duplicates()