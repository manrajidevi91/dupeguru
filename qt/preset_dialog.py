# Copyright 2016 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from PyQt5.QtCore import Qt, pyqtSignal
from PyQt5.QtWidgets import (
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QLabel,
    QPushButton,
    QListWidget,
    QLineEdit,
    QComboBox,
    QSpinBox,
    QCheckBox,
    QGroupBox,
    QFormLayout,
    QScrollArea,
    QWidget,
    QMessageBox,
    QTabWidget,
)
from PyQt5.QtGui import QFont

from hscommon.trans import trget
from core.app import AppMode
from core.scanner import ScanType
from core.presets import PresetManager

tr = trget("ui")


class PresetDialog(QDialog):
    """Dialog for creating and editing scan presets."""

    presetChanged = pyqtSignal()

    def __init__(self, parent, app):
        super().__init__(parent)
        self.app = app
        self.preset_manager = app.preset_manager
        self.current_preset_name = None
        self._setup_ui()
        self._load_presets_list()

    def _setup_ui(self):
        self.setWindowTitle(tr("Scan Presets"))
        self.setMinimumSize(700, 500)

        layout = QVBoxLayout(self)

        # Preset list and buttons
        top_layout = QHBoxLayout()

        left_layout = QVBoxLayout()
        label = QLabel(tr("Presets:"))
        left_layout.addWidget(label)

        self.preset_list = QListWidget()
        self.preset_list.currentItemChanged.connect(self._on_preset_selected)
        left_layout.addWidget(self.preset_list)

        # Preset management buttons
        button_layout = QHBoxLayout()
        self.new_button = QPushButton(tr("New"))
        self.new_button.clicked.connect(self._new_preset)
        button_layout.addWidget(self.new_button)

        self.save_button = QPushButton(tr("Save"))
        self.save_button.clicked.connect(self._save_preset)
        button_layout.addWidget(self.save_button)

        self.delete_button = QPushButton(tr("Delete"))
        self.delete_button.clicked.connect(self._delete_preset)
        button_layout.addWidget(self.delete_button)

        left_layout.addLayout(button_layout)
        top_layout.addLayout(left_layout, 1)

        # Preset details on the right
        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_widget = QWidget()
        right_layout = QVBoxLayout(right_widget)

        # Preset name
        form_layout = QFormLayout()
        self.name_edit = QLineEdit()
        form_layout.addRow(tr("Name:"), self.name_edit)
        right_layout.addLayout(form_layout)

        # Scan type
        scan_group = QGroupBox(tr("Scan Settings"))
        scan_layout = QFormLayout()
        
        self.scan_type_combo = QComboBox()
        scan_layout.addRow(tr("Scan Type:"), self.scan_type_combo)

        self.match_percentage_spin = QSpinBox()
        self.match_percentage_spin.setRange(0, 100)
        self.match_percentage_spin.setValue(95)
        scan_layout.addRow(tr("Match Threshold (%):"), self.match_percentage_spin)

        self.match_similar_check = QCheckBox(tr("Match similar words"))
        scan_layout.addRow("", self.match_similar_check)

        self.word_weighting_check = QCheckBox(tr("Word weighting"))
        scan_layout.addRow("", self.word_weighting_check)

        self.mix_file_kind_check = QCheckBox(tr("Mix file kinds"))
        scan_layout.addRow("", self.mix_file_kind_check)

        scan_group.setLayout(scan_layout)
        right_layout.addWidget(scan_group)

        # File filters
        filter_group = QGroupBox(tr("File Filters"))
        filter_layout = QFormLayout()

        self.min_size_spin = QSpinBox()
        self.min_size_spin.setRange(0, 1000000)
        self.min_size_spin.setSuffix(" KB")
        filter_layout.addRow(tr("Min File Size:"), self.min_size_spin)

        self.max_size_spin = QSpinBox()
        self.max_size_spin.setRange(0, 1000000)
        self.max_size_spin.setSuffix(" MB")
        filter_layout.addRow(tr("Max File Size:"), self.max_size_spin)

        self.ignore_hardlink_check = QCheckBox(tr("Ignore hardlink matches"))
        filter_layout.addRow("", self.ignore_hardlink_check)

        filter_group.setLayout(filter_layout)
        right_layout.addWidget(filter_group)

        # Music tags
        self.tags_group = QGroupBox(tr("Music Tags"))
        tags_layout = QVBoxLayout()
        
        self.tag_track_check = QCheckBox(tr("Track"))
        tags_layout.addWidget(self.tag_track_check)
        
        self.tag_artist_check = QCheckBox(tr("Artist"))
        tags_layout.addWidget(self.tag_artist_check)
        
        self.tag_album_check = QCheckBox(tr("Album"))
        tags_layout.addWidget(self.tag_album_check)
        
        self.tag_title_check = QCheckBox(tr("Title"))
        tags_layout.addWidget(self.tag_title_check)
        
        self.tag_genre_check = QCheckBox(tr("Genre"))
        tags_layout.addWidget(self.tag_genre_check)
        
        self.tag_year_check = QCheckBox(tr("Year"))
        tags_layout.addWidget(self.tag_year_check)

        self.tags_group.setLayout(tags_layout)
        right_layout.addWidget(self.tags_group)

        # Picture options
        self.picture_group = QGroupBox(tr("Picture Options"))
        picture_layout = QVBoxLayout()
        
        self.match_scaled_check = QCheckBox(tr("Match scaled pictures"))
        picture_layout.addWidget(self.match_scaled_check)
        
        self.match_rotated_check = QCheckBox(tr("Match rotated pictures"))
        picture_layout.addWidget(self.match_rotated_check)

        self.picture_group.setLayout(picture_layout)
        right_layout.addWidget(self.picture_group)

        # Advanced options
        advanced_group = QGroupBox(tr("Advanced"))
        advanced_layout = QVBoxLayout()
        
        self.include_exists_check = QCheckBox(tr("Check file existence"))
        self.include_exists_check.setChecked(True)
        advanced_layout.addWidget(self.include_exists_check)
        
        self.remove_empty_check = QCheckBox(tr("Remove empty folders"))
        advanced_layout.addWidget(self.remove_empty_check)

        advanced_group.setLayout(advanced_layout)
        right_layout.addWidget(advanced_group)

        right_layout.addStretch()
        right_scroll.setWidget(right_widget)
        top_layout.addWidget(right_scroll, 2)

        layout.addLayout(top_layout)

        # Bottom buttons
        bottom_layout = QHBoxLayout()
        bottom_layout.addStretch()
        
        self.apply_button = QPushButton(tr("Apply to Current Scan"))
        self.apply_button.clicked.connect(self._apply_preset)
        bottom_layout.addWidget(self.apply_button)
        
        self.close_button = QPushButton(tr("Close"))
        self.close_button.clicked.connect(self.accept)
        bottom_layout.addWidget(self.close_button)

        layout.addLayout(bottom_layout)

    def _load_presets_list(self):
        """Load all presets into the list widget."""
        self.preset_list.clear()
        presets = self.preset_manager.get_all_presets()
        for preset in presets:
            self.preset_list.addItem(preset.name)

    def _on_preset_selected(self, current, previous):
        """Handle preset selection."""
        if current is None:
            self.current_preset_name = None
            return

        self.current_preset_name = current.text()
        preset = self.preset_manager.get_preset(self.current_preset_name)

        if preset:
            self._load_preset_to_ui(preset)

    def _load_preset_to_ui(self, preset):
        """Load preset data into the UI."""
        self.name_edit.setText(preset.name)

        # Load scan type based on app mode
        self._update_scan_type_options(preset.app_mode)
        
        # Find and set the scan type
        for i in range(self.scan_type_combo.count()):
            if self.scan_type_combo.itemData(i) == preset.scan_type:
                self.scan_type_combo.setCurrentIndex(i)
                break

        self.match_percentage_spin.setValue(preset.min_match_percentage)
        self.match_similar_check.setChecked(preset.match_similar_words)
        self.word_weighting_check.setChecked(preset.word_weighting)
        self.mix_file_kind_check.setChecked(preset.mix_file_kind)

        # Convert thresholds
        self.min_size_spin.setValue(preset.size_threshold // 1024)  # bytes to KB
        self.max_size_spin.setValue(preset.large_file_threshold // (1024 * 1024))  # bytes to MB

        self.ignore_hardlink_check.setChecked(preset.ignore_hardlink_matches)
        self.include_exists_check.setChecked(preset.include_exists_check)
        self.remove_empty_check.setChecked(preset.remove_empty_folders)

        # Tags
        self.tag_track_check.setChecked("track" in preset.scanned_tags)
        self.tag_artist_check.setChecked("artist" in preset.scanned_tags)
        self.tag_album_check.setChecked("album" in preset.scanned_tags)
        self.tag_title_check.setChecked("title" in preset.scanned_tags)
        self.tag_genre_check.setChecked("genre" in preset.scanned_tags)
        self.tag_year_check.setChecked("year" in preset.scanned_tags)

        # Picture options
        self.match_scaled_check.setChecked(preset.match_scaled)
        self.match_rotated_check.setChecked(preset.match_rotated)

        # Show/hide relevant groups
        self._update_ui_for_mode(preset.app_mode)

    def _update_scan_type_options(self, app_mode):
        """Update scan type combo based on app mode."""
        self.scan_type_combo.clear()

        if app_mode == AppMode.STANDARD:
            self.scan_type_combo.addItem(tr("Filename"), ScanType.FILENAME)
            self.scan_type_combo.addItem(tr("Contents"), ScanType.CONTENTS)
            self.scan_type_combo.addItem(tr("Folders"), ScanType.FOLDERS)
        elif app_mode == AppMode.MUSIC:
            self.scan_type_combo.addItem(tr("Filename"), ScanType.FILENAME)
            self.scan_type_combo.addItem(tr("Filename - Fields"), ScanType.FIELDS)
            self.scan_type_combo.addItem(tr("Filename - Fields (No Order)"), ScanType.FIELDSNOORDER)
            self.scan_type_combo.addItem(tr("Tags"), ScanType.TAG)
            self.scan_type_combo.addItem(tr("Contents"), ScanType.CONTENTS)
        elif app_mode == AppMode.PICTURE:
            self.scan_type_combo.addItem(tr("Contents"), ScanType.FUZZYBLOCK)
            self.scan_type_combo.addItem(tr("EXIF Timestamp"), ScanType.EXIFTIMESTAMP)

    def _update_ui_for_mode(self, app_mode):
        """Show/hide UI elements based on app mode."""
        if app_mode == AppMode.MUSIC:
            self.tags_group.setVisible(True)
            self.picture_group.setVisible(False)
        elif app_mode == AppMode.PICTURE:
            self.tags_group.setVisible(False)
            self.picture_group.setVisible(True)
        else:
            self.tags_group.setVisible(False)
            self.picture_group.setVisible(False)

    def _new_preset(self):
        """Create a new preset."""
        self.current_preset_name = None
        self.name_edit.clear()
        self.name_edit.setFocus()

    def _save_preset(self):
        """Save or update the current preset."""
        name = self.name_edit.text().strip()
        
        if not name:
            QMessageBox.warning(self, tr("Error"), tr("Please enter a preset name."))
            return

        # Get scan type
        scan_type = self.scan_type_combo.currentData()
        if scan_type is None:
            QMessageBox.warning(self, tr("Error"), tr("Please select a scan type."))
            return

        # Determine app mode from scan type
        app_mode = self.app.model.app_mode
        
        # Get selected tags
        scanned_tags = set()
        if self.tag_track_check.isChecked():
            scanned_tags.add("track")
        if self.tag_artist_check.isChecked():
            scanned_tags.add("artist")
        if self.tag_album_check.isChecked():
            scanned_tags.add("album")
        if self.tag_title_check.isChecked():
            scanned_tags.add("title")
        if self.tag_genre_check.isChecked():
            scanned_tags.add("genre")
        if self.tag_year_check.isChecked():
            scanned_tags.add("year")

        # Create or update preset
        self.preset_manager.create_preset(
            name=name,
            app_mode=app_mode,
            scan_type=scan_type,
            min_match_percentage=self.match_percentage_spin.value(),
            match_similar_words=self.match_similar_check.isChecked(),
            word_weighting=self.word_weighting_check.isChecked(),
            mix_file_kind=self.mix_file_kind_check.isChecked(),
            size_threshold=self.min_size_spin.value() * 1024,  # KB to bytes
            large_file_threshold=self.max_size_spin.value() * 1024 * 1024,  # MB to bytes
            big_file_size_threshold=0,
            scanned_tags=scanned_tags,
            match_scaled=self.match_scaled_check.isChecked(),
            match_rotated=self.match_rotated_check.isChecked(),
            include_exists_check=self.include_exists_check.isChecked(),
            ignore_hardlink_matches=self.ignore_hardlink_check.isChecked(),
            remove_empty_folders=self.remove_empty_check.isChecked(),
        )

        self._load_presets_list()
        self.presetChanged.emit()

        # Select the saved preset
        items = self.preset_list.findItems(name, Qt.MatchExactly)
        if items:
            self.preset_list.setCurrentItem(items[0])

        QMessageBox.information(self, tr("Success"), tr("Preset saved successfully."))

    def _delete_preset(self):
        """Delete the current preset."""
        if not self.current_preset_name:
            return

        reply = QMessageBox.question(
            self,
            tr("Delete Preset"),
            tr(f"Are you sure you want to delete '{self.current_preset_name}'?"),
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )

        if reply == QMessageBox.Yes:
            self.preset_manager.delete_preset(self.current_preset_name)
            self._load_presets_list()
            self.presetChanged.emit()
            self.current_preset_name = None

    def _apply_preset(self):
        """Apply the current preset to the scan settings."""
        if not self.current_preset_name:
            QMessageBox.warning(self, tr("Error"), tr("Please select a preset first."))
            return

        preset = self.preset_manager.get_preset(self.current_preset_name)
        if preset:
            # Apply preset to app preferences
            self.app.prefs.filter_hardness = preset.min_match_percentage
            self.app.prefs.mix_file_kind = preset.mix_file_kind
            self.app.prefs.match_similar = preset.match_similar_words
            self.app.prefs.word_weighting = preset.word_weighting
            self.app.prefs.ignore_small_files = preset.size_threshold > 0
            self.app.prefs.small_file_threshold = preset.size_threshold // 1024
            self.app.prefs.ignore_large_files = preset.large_file_threshold > 0
            self.app.prefs.large_file_threshold = preset.large_file_threshold // (1024 * 1024)
            self.app.prefs.ignore_hardlink_matches = preset.ignore_hardlink_matches
            self.app.prefs.include_exists_check = preset.include_exists_check
            self.app.prefs.remove_empty_folders = preset.remove_empty_folders
            self.app.prefs.match_scaled = preset.match_scaled
            self.app.prefs.match_rotated = preset.match_rotated

            # Music tags
            self.app.prefs.scan_tag_track = "track" in preset.scanned_tags
            self.app.prefs.scan_tag_artist = "artist" in preset.scanned_tags
            self.app.prefs.scan_tag_album = "album" in preset.scanned_tags
            self.app.prefs.scan_tag_title = "title" in preset.scanned_tags
            self.app.prefs.scan_tag_genre = "genre" in preset.scanned_tags
            self.app.prefs.scan_tag_year = "year" in preset.scanned_tags

            # Scan type
            self.app.prefs.set_scan_type(preset.app_mode, preset.scan_type)

            # Update app options
            self.app._update_options()

            QMessageBox.information(
                self,
                tr("Success"),
                tr(f"Preset '{self.current_preset_name}' applied to current scan settings.")
            )