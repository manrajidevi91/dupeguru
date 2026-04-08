# Copyright 2016 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from PyQt5.QtCore import Qt, pyqtSignal, QTimer
from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QScrollArea,
    QGridLayout,
    QLabel,
    QPushButton,
    QLineEdit,
    QComboBox,
    QFrame,
    QProgressBar,
)
from PyQt5.QtGui import QFont

from hscommon.trans import trget
from hscommon.util import format_size

from qt.group_card import GroupCard

tr = trget("ui")


class CardGridView(QWidget):
    """
    A grid view displaying duplicate groups as cards.
    
    Features:
    - Lazy loading for large result sets
    - Search and filtering
    - Group selection
    - Visual affordances for marked files
    """
    
    groupSelected = pyqtSignal(object)
    fileClicked = pyqtSignal(object, object)
    actionTriggered = pyqtSignal(object, str)
    selectionChanged = pyqtSignal()
    
    def __init__(self, results, parent=None):
        super().__init__(parent)
        self.results = results
        self.group_cards = {}  # group -> card widget
        self.selected_groups = set()
        self.current_filter = ""
        self.current_sort = "default"
        self.batch_size = 20  # Number of cards to load at once
        self.loaded_count = 0
        
        self._setup_ui()
        self._load_initial_cards()
        
    def _setup_ui(self):
        """Setup the card grid UI."""
        layout = QVBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)
        
        # Toolbar
        toolbar = QFrame()
        toolbar.setStyleSheet("background-color: #f5f5f5; border-bottom: 1px solid #ddd;")
        toolbar_layout = QHBoxLayout(toolbar)
        toolbar_layout.setContentsMargins(12, 8, 12, 8)
        toolbar_layout.setSpacing(12)
        
        # Search box
        search_label = QLabel(tr("Search:"))
        toolbar_layout.addWidget(search_label)
        
        self.search_box = QLineEdit()
        self.search_box.setPlaceholderText(tr("Filter by filename..."))
        self.search_box.setMaximumWidth(300)
        self.search_box.textChanged.connect(self._on_search_changed)
        toolbar_layout.addWidget(self.search_box)
        
        toolbar_layout.addStretch()
        
        # Sort combo
        sort_label = QLabel(tr("Sort by:"))
        toolbar_layout.addWidget(sort_label)
        
        self.sort_combo = QComboBox()
        self.sort_combo.addItem(tr("Default"))
        self.sort_combo.addItem(tr("Largest Groups"))
        self.sort_combo.addItem(tr("Most Similar"))
        self.sort_combo.addItem(tr("Most Space"))
        self.sort_combo.addItem(tr("Highest Resolution"))
        self.sort_combo.currentIndexChanged.connect(self._on_sort_changed)
        toolbar_layout.addWidget(self.sort_combo)
        
        # Select all button
        self.select_all_button = QPushButton(tr("Select All"))
        self.select_all_button.clicked.connect(self._select_all)
        toolbar_layout.addWidget(self.select_all_button)
        
        # Clear selection button
        self.clear_selection_button = QPushButton(tr("Clear Selection"))
        self.clear_selection_button.clicked.connect(self._clear_selection)
        toolbar_layout.addWidget(self.clear_selection_button)
        
        layout.addWidget(toolbar)
        
        # Status bar
        status_bar = QFrame()
        status_bar.setStyleSheet("background-color: #e3f2fd; padding: 8px;")
        status_layout = QHBoxLayout(status_bar)
        status_layout.setContentsMargins(12, 4, 12, 4)
        
        self.status_label = QLabel(tr("Loading results..."))
        status_font = QFont()
        status_font.setPointSize(10)
        self.status_label.setFont(status_font)
        status_layout.addWidget(self.status_label)
        
        status_layout.addStretch()
        
        # Progress bar for loading
        self.progress_bar = QProgressBar()
        self.progress_bar.setMaximumWidth(200)
        self.progress_bar.setVisible(False)
        status_layout.addWidget(self.progress_bar)
        
        layout.addWidget(status_bar)
        
        # Scroll area for cards
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setFrameStyle(QFrame.NoFrame)
        
        # Container widget for grid
        self.grid_widget = QWidget()
        self.grid_layout = QGridLayout(self.grid_widget)
        self.grid_layout.setAlignment(Qt.AlignLeft | Qt.AlignTop)
        self.grid_layout.setSpacing(16)
        self.grid_layout.setContentsMargins(16, 16, 16, 16)
        
        self.scroll_area.setWidget(self.grid_widget)
        layout.addWidget(self.scroll_area)
        
        # Connect scroll event for lazy loading
        self.scroll_area.verticalScrollBar().valueChanged.connect(self._on_scroll)
    
    def _load_initial_cards(self):
        """Load initial batch of group cards."""
        groups = self._get_filtered_groups()
        total = len(groups)
        
        self._update_progress(0, total)
        
        # Load first batch
        self._load_cards_batch(0, self.batch_size)
        
        # Setup timer for lazy loading
        self._load_timer = QTimer()
        self._load_timer.timeout.connect(self._load_next_batch)
        self._load_timer.setSingleShot(True)
        
        self._update_status()
    
    def _load_cards_batch(self, start_idx, count):
        """Load a batch of group cards."""
        groups = self._get_filtered_groups()
        end_idx = min(start_idx + count, len(groups))
        
        for idx in range(start_idx, end_idx):
            group = groups[idx]
            if group not in self.group_cards:
                self._create_card(group, idx)
        
        self.loaded_count = end_idx
        self._update_progress(self.loaded_count, len(groups))
        self._update_status()
    
    def _load_next_batch(self):
        """Load next batch of cards (lazy loading)."""
        groups = self._get_filtered_groups()
        if self.loaded_count < len(groups):
            self._load_cards_batch(self.loaded_count, self.batch_size)
    
    def _create_card(self, group, index):
        """Create a card for a group."""
        # Get summary from presenter
        summary = self.results.presenter.get_group_summary(group, index)
        
        # Create card widget
        card = GroupCard(group, summary, self.grid_widget)
        card.groupSelected.connect(self._on_group_selected)
        card.fileClicked.connect(self.fileClicked.emit)
        card.actionTriggered.connect(self.actionTriggered.emit)
        
        # Add to grid
        row = index // 3
        col = index % 3
        self.grid_layout.addWidget(card, row, col)
        
        # Store reference
        self.group_cards[group] = card
        
        # Restore selection state
        if group in self.selected_groups:
            card.set_selected(True)
    
    def _get_filtered_groups(self):
        """Get filtered and sorted list of groups."""
        groups = list(self.results.groups)
        
        # Apply filter
        if self.current_filter:
            import re
            try:
                filter_re = re.compile(self.current_filter, re.IGNORECASE)
                groups = [g for g in groups if 
                         any(filter_re.search(str(f.path)) for f in g.dupes)]
            except re.error:
                pass
        
        # Apply sort
        if self.current_sort == "largest":
            groups.sort(key=lambda g: sum(f.size for f in g.dupes), reverse=True)
        elif self.current_sort == "similar":
            # Sort by average similarity
            def avg_similarity(g):
                if not g.matches:
                    return 0
                return sum(m.percentage for m in g.matches) / len(g.matches)
            groups.sort(key=avg_similarity, reverse=True)
        elif self.current_sort == "space":
            # Sort by space saved (total size - ref size)
            def space_saved(g):
                ref = g.ref
                ref_size = ref.size if ref else 0
                return sum(f.size for f in g.dupes) - ref_size
            groups.sort(key=space_saved, reverse=True)
        elif self.current_sort == "resolution":
            # Sort by max resolution (for images)
            def max_resolution(g):
                max_pixels = 0
                for f in g.dupes:
                    if hasattr(f, 'dimensions') and f.dimensions:
                        pixels = f.dimensions[0] * f.dimensions[1]
                        max_pixels = max(max_pixels, pixels)
                return max_pixels
            groups.sort(key=max_resolution, reverse=True)
        
        return groups
    
    def _on_scroll(self, value):
        """Handle scroll event for lazy loading."""
        scrollbar = self.scroll_area.verticalScrollBar()
        if value >= scrollbar.maximum() - 100:  # Near bottom
            # Load next batch after a short delay
            self._load_timer.start(100)
    
    def _on_search_changed(self, text):
        """Handle search text change."""
        self.current_filter = text
        self._refresh_cards()
    
    def _on_sort_changed(self, index):
        """Handle sort combo change."""
        sort_modes = ["default", "largest", "similar", "space", "resolution"]
        self.current_sort = sort_modes[index]
        self._refresh_cards()
    
    def _on_group_selected(self, group):
        """Handle group selection."""
        if group in self.selected_groups:
            self.selected_groups.remove(group)
            if group in self.group_cards:
                self.group_cards[group].set_selected(False)
        else:
            self.selected_groups.add(group)
            if group in self.group_cards:
                self.group_cards[group].set_selected(True)
        
        self.selectionChanged.emit()
    
    def _select_all(self):
        """Select all groups."""
        groups = self._get_filtered_groups()
        for group in groups:
            self.selected_groups.add(group)
            if group in self.group_cards:
                self.group_cards[group].set_selected(True)
        self.selectionChanged.emit()
    
    def _clear_selection(self):
        """Clear all selections."""
        for group in list(self.selected_groups):
            if group in self.group_cards:
                self.group_cards[group].set_selected(False)
        self.selected_groups.clear()
        self.selectionChanged.emit()
    
    def _refresh_cards(self):
        """Refresh the card grid (reload all cards)."""
        # Clear existing cards
        for card in self.group_cards.values():
            card.deleteLater()
        self.group_cards.clear()
        
        # Reset layout
        for i in reversed(range(self.grid_layout.count())):
            self.grid_layout.itemAt(i).widget().setParent(None)
        
        # Reload
        self.loaded_count = 0
        self._load_initial_cards()
    
    def _update_progress(self, current, total):
        """Update progress bar."""
        if total > 0:
            self.progress_bar.setMaximum(total)
            self.progress_bar.setValue(current)
            self.progress_bar.setVisible(current < total)
        else:
            self.progress_bar.setVisible(False)
    
    def _update_status(self):
        """Update status label."""
        groups = self._get_filtered_groups()
        total = len(groups)
        selected = len([g for g in groups if g in self.selected_groups])
        
        # Calculate total space
        total_size = 0
        marked_size = 0
        for group in groups:
            for file_obj in group.dupes:
                total_size += file_obj.size
                if self.results.is_marked(file_obj):
                    marked_size += file_obj.size
        
        total_text = format_size(total_size, 1)
        marked_text = format_size(marked_size, 1)
        
        status = tr(f"{selected} / {total} groups selected | Total: {total_text} | Marked: {marked_text}")
        self.status_label.setText(status)
    
    def refresh(self):
        """Refresh the view (update all cards)."""
        for group, card in self.group_cards.items():
            card.update_content()
        self._update_status()
    
    def get_selected_groups(self):
        """Get list of selected groups."""
        return list(self.selected_groups)
    
    def get_selected_files(self):
        """Get list of selected files from selected groups."""
        selected_files = []
        for group in self.selected_groups:
            for file_obj in group.dupes:
                if self.results.is_marked(file_obj):
                    selected_files.append(file_obj)
        return selected_files