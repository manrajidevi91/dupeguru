# Copyright 2016 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from PyQt5.QtCore import Qt, pyqtSignal, QPointF, QRectF
from PyQt5.QtGui import QPixmap, QImage, QPainter, QPainterPath
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QFrame,
    QScrollArea,
    QPushButton,
    QSplitter,
    QToolButton,
    QGridLayout,
    QGroupBox,
)
from PyQt5.QtSvg import QSvgWidget

from hscommon.trans import trget
from hscommon.util import format_size
from core.group_presenter import FileMetadata

tr = trget("ui")


class ImageViewer(QFrame):
    """
    A single image viewer with zoom and pan support.
    
    Features:
    - Displays image with zoom/pan
    - Synchronized with other viewers
    - Shows metadata overlay
    """
    
    zoomChanged = pyqtSignal(float)
    panChanged = pyqtSignal(QPointF)
    
    def __init__(self, metadata, parent=None):
        super().__init__(parent)
        self.metadata = metadata
        self.zoom_level = 1.0
        self.pan_offset = QPointF(0, 0)
        self.is_dragging = False
        self.last_mouse_pos = QPointF(0, 0)
        
        self._setup_ui()
        self._load_image()
        
    def _setup_ui(self):
        """Setup the image viewer UI."""
        self.setFrameStyle(QFrame.StyledPanel | QFrame.Sunken)
        self.setLineWidth(2)
        self.setMinimumSize(300, 300)
        self.setCursor(Qt.OpenHandCursor)
        
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        
        # Image label
        self.image_label = QLabel()
        self.image_label.setAlignment(Qt.AlignCenter)
        self.image_label.setStyleSheet("background-color: #1e1e1e;")
        layout.addWidget(self.image_label)
        
        # Metadata overlay
        self.metadata_label = QLabel()
        self.metadata_label.setStyleSheet("""
            QLabel {
                background-color: rgba(0, 0, 0, 150);
                color: white;
                padding: 8px;
                border-radius: 4px;
            }
        """)
        self.metadata_label.setWordWrap(True)
        self._update_metadata_display()
    
    def _load_image(self):
        """Load and display the image."""
        try:
            # Try to load the image
            path = str(self.metadata.file.path)
            pixmap = QPixmap(path)
            
            if not pixmap.isNull():
                self.pixmap = pixmap
                self._update_display()
            else:
                self.image_label.setText("No Image")
        except Exception as e:
            self.image_label.setText(f"Error: {str(e)}")
    
    def _update_display(self):
        """Update the displayed image with current zoom and pan."""
        if not hasattr(self, 'pixmap'):
            return
        
        # Create a scaled pixmap
        scaled_pixmap = self.pixmap.scaled(
            int(self.pixmap.width() * self.zoom_level),
            int(self.pixmap.height() * self.zoom_level),
            Qt.KeepAspectRatio,
            Qt.SmoothTransformation
        )
        
        # Apply pan offset
        painter = QPainter(scaled_pixmap)
        painter.translate(self.pan_offset)
        painter.end()
        
        self.image_label.setPixmap(scaled_pixmap)
    
    def _update_metadata_display(self):
        """Update the metadata overlay text."""
        meta = self.metadata
        
        # Build metadata text
        lines = [
            f"<b>{meta.name}</b>",
            f"Size: {meta.size_formatted}",
        ]
        
        if meta.dimensions:
            w, h = meta.dimensions
            lines.append(f"Resolution: {w}×{h}")
        
        if meta.modification_date:
            lines.append(f"Modified: {meta.modification_date.strftime('%Y-%m-%d %H:%M')}")
        
        if meta.is_reference:
            lines.insert(0, "<span style='color: #4CAF50;'>★ REFERENCE</span>")
        
        if meta.is_marked:
            lines.insert(0, "<span style='color: #f44336;'>✓ MARKED</span>")
        
        self.metadata_label.setText("<br>".join(lines))
    
    def set_zoom(self, zoom):
        """Set zoom level (1.0 = 100%)."""
        self.zoom_level = max(0.1, min(10.0, zoom))
        self._update_display()
        self.zoomChanged.emit(self.zoom_level)
    
    def set_pan(self, offset):
        """Set pan offset."""
        self.pan_offset = offset
        self._update_display()
        self.panChanged.emit(offset)
    
    def reset_view(self):
        """Reset zoom and pan to default."""
        self.zoom_level = 1.0
        self.pan_offset = QPointF(0, 0)
        self._update_display()
    
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = True
            self.last_mouse_pos = event.pos()
            self.setCursor(Qt.ClosedHandCursor)
        super().mousePressEvent(event)
    
    def mouseMoveEvent(self, event):
        if self.is_dragging:
            delta = event.pos() - self.last_mouse_pos
            self.last_mouse_pos = event.pos()
            new_offset = self.pan_offset + delta
            self.set_pan(new_offset)
        super().mouseMoveEvent(event)
    
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.is_dragging = False
            self.setCursor(Qt.OpenHandCursor)
        super().mouseReleaseEvent(event)
    
    def wheelEvent(self, event):
        """Handle mouse wheel for zooming."""
        if event.modifiers() & Qt.ControlModifier:
            # Zoom
            delta = event.angleDelta().y()
            if delta > 0:
                self.set_zoom(self.zoom_level * 1.1)
            else:
                self.set_zoom(self.zoom_level / 1.1)
        else:
            # Pan
            delta = event.angleDelta()
            new_offset = self.pan_offset + QPointF(delta.x(), delta.y())
            self.set_pan(new_offset)
        super().wheelEvent(event)


class ComparisonPanel(QWidget):
    """
    A panel for side-by-side comparison of duplicate images.
    
    Features:
    - Two synchronized image viewers
    - Synchronized zoom and pan
    - Metadata display for both images
    - Zoom controls
    """
    
    comparisonClosed = pyqtSignal()
    
    def __init__(self, file1_metadata, file2_metadata, parent=None):
        super().__init__(parent)
        self.file1_metadata = file1_metadata
        self.file2_metadata = file2_metadata
        self._setup_ui()
        self._connect_signals()
        
    def _setup_ui(self):
        """Setup the comparison panel UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)
        
        # Header
        header_layout = QHBoxLayout()
        
        title = QLabel(tr("Side-by-Side Comparison"))
        title_font = title.font()
        title_font.setBold(True)
        title_font.setPointSize(12)
        title.setFont(title_font)
        header_layout.addWidget(title)
        
        header_layout.addStretch()
        
        # Close button
        close_button = QPushButton(tr("Close"))
        close_button.setMaximumWidth(80)
        close_button.clicked.connect(self.comparisonClosed.emit)
        header_layout.addWidget(close_button)
        
        layout.addLayout(header_layout)
        
        # Zoom controls
        zoom_layout = QHBoxLayout()
        
        zoom_out_button = QPushButton("-")
        zoom_out_button.setMaximumWidth(40)
        zoom_out_button.clicked.connect(self._zoom_out)
        zoom_layout.addWidget(zoom_out_button)
        
        self.zoom_label = QLabel("100%")
        self.zoom_label.setMinimumWidth(50)
        self.zoom_label.setAlignment(Qt.AlignCenter)
        zoom_layout.addWidget(self.zoom_label)
        
        zoom_in_button = QPushButton("+")
        zoom_in_button.setMaximumWidth(40)
        zoom_in_button.clicked.connect(self._zoom_in)
        zoom_layout.addWidget(zoom_in_button)
        
        reset_button = QPushButton(tr("Reset View"))
        reset_button.setMaximumWidth(100)
        reset_button.clicked.connect(self._reset_view)
        zoom_layout.addWidget(reset_button)
        
        sync_label = QLabel(tr("Synchronized:"))
        zoom_layout.addWidget(sync_label)
        
        self.sync_checkbox = QCheckBox()
        self.sync_checkbox.setChecked(True)
        zoom_layout.addWidget(self.sync_checkbox)
        
        zoom_layout.addStretch()
        layout.addLayout(zoom_layout)
        
        # Splitter for two image viewers
        self.splitter = QSplitter(Qt.Horizontal)
        
        # Left viewer (file 1)
        left_group = QGroupBox(tr("Image 1"))
        left_layout = QVBoxLayout(left_group)
        
        self.viewer1 = ImageViewer(self.file1_metadata)
        left_layout.addWidget(self.viewer1)
        
        # Metadata for file 1
        meta1_group = QGroupBox(tr("Metadata"))
        meta1_layout = QVBoxLayout(meta1_group)
        self.meta1_label = QLabel()
        self.meta1_label.setWordWrap(True)
        self._populate_metadata(self.meta1_label, self.file1_metadata)
        meta1_layout.addWidget(self.meta1_label)
        left_layout.addWidget(meta1_group)
        
        self.splitter.addWidget(left_group)
        
        # Right viewer (file 2)
        right_group = QGroupBox(tr("Image 2"))
        right_layout = QVBoxLayout(right_group)
        
        self.viewer2 = ImageViewer(self.file2_metadata)
        right_layout.addWidget(self.viewer2)
        
        # Metadata for file 2
        meta2_group = QGroupBox(tr("Metadata"))
        meta2_layout = QVBoxLayout(meta2_group)
        self.meta2_label = QLabel()
        self.meta2_label.setWordWrap(True)
        self._populate_metadata(self.meta2_label, self.file2_metadata)
        meta2_layout.addWidget(self.meta2_label)
        right_layout.addWidget(meta2_group)
        
        self.splitter.addWidget(right_group)
        
        # Set initial splitter sizes (50/50)
        self.splitter.setSizes([500, 500])
        
        layout.addWidget(self.splitter)
    
    def _connect_signals(self):
        """Connect signals between viewers for synchronization."""
        self.viewer1.zoomChanged.connect(self._on_viewer1_zoom)
        self.viewer1.panChanged.connect(self._on_viewer1_pan)
        self.viewer2.zoomChanged.connect(self._on_viewer2_zoom)
        self.viewer2.panChanged.connect(self._on_viewer2_pan)
    
    def _populate_metadata(self, label, metadata):
        """Populate metadata label with file information."""
        lines = [
            f"<b>Name:</b> {metadata.name}",
            f"<b>Path:</b> {metadata.path}",
            f"<b>Size:</b> {metadata.size_formatted}",
        ]
        
        if metadata.dimensions:
            w, h = metadata.dimensions
            lines.append(f"<b>Resolution:</b> {w}×{h}")
        
        if metadata.modification_date:
            lines.append(f"<b>Modified:</b> {metadata.modification_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        if metadata.creation_date:
            lines.append(f"<b>Created:</b> {metadata.creation_date.strftime('%Y-%m-%d %H:%M:%S')}")
        
        label.setText("<br>".join(lines))
    
    def _on_viewer1_zoom(self, zoom):
        """Handle zoom change in viewer 1."""
        self.zoom_label.setText(f"{int(zoom * 100)}%")
        if self.sync_checkbox.isChecked():
            self.viewer2.set_zoom(zoom)
    
    def _on_viewer1_pan(self, offset):
        """Handle pan change in viewer 1."""
        if self.sync_checkbox.isChecked():
            self.viewer2.set_pan(offset)
    
    def _on_viewer2_zoom(self, zoom):
        """Handle zoom change in viewer 2."""
        self.zoom_label.setText(f"{int(zoom * 100)}%")
        if self.sync_checkbox.isChecked():
            self.viewer1.set_zoom(zoom)
    
    def _on_viewer2_pan(self, offset):
        """Handle pan change in viewer 2."""
        if self.sync_checkbox.isChecked():
            self.viewer1.set_pan(offset)
    
    def _zoom_in(self):
        """Zoom in both viewers."""
        new_zoom = self.viewer1.zoom_level * 1.1
        self.viewer1.set_zoom(new_zoom)
        if not self.sync_checkbox.isChecked():
            self.viewer2.set_zoom(new_zoom)
    
    def _zoom_out(self):
        """Zoom out both viewers."""
        new_zoom = self.viewer1.zoom_level / 1.1
        self.viewer1.set_zoom(new_zoom)
        if not self.sync_checkbox.isChecked():
            self.viewer2.set_zoom(new_zoom)
    
    def _reset_view(self):
        """Reset view for both viewers."""
        self.viewer1.reset_view()
        self.viewer2.reset_view()


from PyQt5.QtWidgets import QCheckBox