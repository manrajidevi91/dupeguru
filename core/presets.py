# Copyright 2016 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import json
from collections import namedtuple
from typing import Dict, List, Optional

from core.app import AppMode
from core.scanner import ScanType

# Preset data structure
ScanPreset = namedtuple(
    "ScanPreset",
    [
        "name",
        "app_mode",
        "scan_type",
        "min_match_percentage",
        "match_similar_words",
        "word_weighting",
        "mix_file_kind",
        "size_threshold",
        "large_size_threshold",
        "big_file_size_threshold",
        "scanned_tags",
        "match_scaled",
        "match_rotated",
        "include_exists_check",
        "ignore_hardlink_matches",
        "remove_empty_folders",
    ],
)


class PresetManager:
    """Manages scan presets - creation, loading, saving, and deletion."""

    def __init__(self):
        self.presets: Dict[str, ScanPreset] = {}
        self._load_default_presets()

    def _load_default_presets(self):
        """Load built-in default presets."""
        # Standard Edition defaults
        self.presets["Quick Scan"] = ScanPreset(
            name="Quick Scan",
            app_mode=AppMode.STANDARD,
            scan_type=ScanType.CONTENTS,
            min_match_percentage=100,
            match_similar_words=False,
            word_weighting=False,
            mix_file_kind=False,
            size_threshold=0,
            large_size_threshold=0,
            big_file_size_threshold=0,
            scanned_tags=set(),
            match_scaled=False,
            match_rotated=False,
            include_exists_check=True,
            ignore_hardlink_matches=False,
            remove_empty_folders=False,
        )

        self.presets["Deep Scan"] = ScanPreset(
            name="Deep Scan",
            app_mode=AppMode.STANDARD,
            scan_type=ScanType.CONTENTS,
            min_match_percentage=100,
            match_similar_words=False,
            word_weighting=False,
            mix_file_kind=True,
            size_threshold=0,
            large_size_threshold=0,
            big_file_size_threshold=0,
            scanned_tags=set(),
            match_scaled=False,
            match_rotated=False,
            include_exists_check=True,
            ignore_hardlink_matches=False,
            remove_empty_folders=False,
        )

        # Music Edition defaults
        self.presets["Music - Tags"] = ScanPreset(
            name="Music - Tags",
            app_mode=AppMode.MUSIC,
            scan_type=ScanType.TAG,
            min_match_percentage=95,
            match_similar_words=False,
            word_weighting=True,
            mix_file_kind=False,
            size_threshold=0,
            large_size_threshold=0,
            big_file_size_threshold=0,
            scanned_tags={"artist", "album", "title"},
            match_scaled=False,
            match_rotated=False,
            include_exists_check=True,
            ignore_hardlink_matches=False,
            remove_empty_folders=False,
        )

        # Picture Edition defaults
        self.presets["Pictures - Contents"] = ScanPreset(
            name="Pictures - Contents",
            app_mode=AppMode.PICTURE,
            scan_type=ScanType.FUZZYBLOCK,
            min_match_percentage=90,
            match_similar_words=False,
            word_weighting=False,
            mix_file_kind=False,
            size_threshold=0,
            large_size_threshold=0,
            big_file_size_threshold=0,
            scanned_tags=set(),
            match_scaled=False,
            match_rotated=False,
            include_exists_check=True,
            ignore_hardlink_matches=False,
            remove_empty_folders=False,
        )

    def create_preset(
        self,
        name: str,
        app_mode: AppMode,
        scan_type: ScanType,
        min_match_percentage: int = 95,
        match_similar_words: bool = False,
        word_weighting: bool = False,
        mix_file_kind: bool = True,
        size_threshold: int = 0,
        large_size_threshold: int = 0,
        big_file_size_threshold: int = 0,
        scanned_tags: Optional[set] = None,
        match_scaled: bool = False,
        match_rotated: bool = False,
        include_exists_check: bool = True,
        ignore_hardlink_matches: bool = False,
        remove_empty_folders: bool = False,
    ) -> ScanPreset:
        """Create a new preset."""
        if scanned_tags is None:
            scanned_tags = set()

        preset = ScanPreset(
            name=name,
            app_mode=app_mode,
            scan_type=scan_type,
            min_match_percentage=min_match_percentage,
            match_similar_words=match_similar_words,
            word_weighting=word_weighting,
            mix_file_kind=mix_file_kind,
            size_threshold=size_threshold,
            large_size_threshold=large_size_threshold,
            big_file_size_threshold=big_file_size_threshold,
            scanned_tags=scanned_tags,
            match_scaled=match_scaled,
            match_rotated=match_rotated,
            include_exists_check=include_exists_check,
            ignore_hardlink_matches=ignore_hardlink_matches,
            remove_empty_folders=remove_empty_folders,
        )
        self.presets[name] = preset
        return preset

    def get_preset(self, name: str) -> Optional[ScanPreset]:
        """Get a preset by name."""
        return self.presets.get(name)

    def get_all_presets(self) -> List[ScanPreset]:
        """Get all presets."""
        return list(self.presets.values())

    def get_presets_for_mode(self, app_mode: AppMode) -> List[ScanPreset]:
        """Get all presets for a specific app mode."""
        return [p for p in self.presets.values() if p.app_mode == app_mode]

    def update_preset(
        self,
        name: str,
        **kwargs
    ) -> Optional[ScanPreset]:
        """Update an existing preset."""
        if name not in self.presets:
            return None

        old_preset = self.presets[name]
        # Create new preset with updated values
        preset_dict = old_preset._asdict()
        preset_dict.update(kwargs)

        self.presets[name] = ScanPreset(**preset_dict)
        return self.presets[name]

    def delete_preset(self, name: str) -> bool:
        """Delete a preset. Returns True if deleted, False if not found."""
        if name in self.presets:
            del self.presets[name]
            return True
        return False

    def rename_preset(self, old_name: str, new_name: str) -> bool:
        """Rename a preset. Returns True if renamed, False if old_name not found."""
        if old_name not in self.presets:
            return False

        old_preset = self.presets[old_name]
        preset_dict = old_preset._asdict()
        preset_dict["name"] = new_name

        self.presets[new_name] = ScanPreset(**preset_dict)
        del self.presets[old_name]
        return True

    def to_dict_list(self) -> List[dict]:
        """Convert all presets to a list of dicts for serialization."""
        result = []
        for preset in self.presets.values():
            preset_dict = preset._asdict()
            # Convert AppMode to string for JSON serialization
            preset_dict["app_mode"] = preset.app_mode.name
            # Convert ScanType to int for JSON serialization
            preset_dict["scan_type"] = preset.scan_type
            # Convert set to list for JSON serialization
            preset_dict["scanned_tags"] = list(preset.scanned_tags)
            result.append(preset_dict)
        return result

    def from_dict_list(self, data: List[dict]):
        """Load presets from a list of dicts (deserialization)."""
        for preset_dict in data:
            # Convert string back to AppMode
            if isinstance(preset_dict.get("app_mode"), str):
                preset_dict["app_mode"] = AppMode[preset_dict["app_mode"]]
            # Convert scanned_tags back to set
            if "scanned_tags" in preset_dict and isinstance(preset_dict["scanned_tags"], list):
                preset_dict["scanned_tags"] = set(preset_dict["scanned_tags"])

            self.presets[preset_dict["name"]] = ScanPreset(**preset_dict)

    def save_to_json(self, filepath: str):
        """Save all presets to a JSON file."""
        data = self.to_dict_list()
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

    def load_from_json(self, filepath: str):
        """Load presets from a JSON file."""
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.from_dict_list(data)
        except (FileNotFoundError, json.JSONDecodeError, KeyError):
            # If file doesn't exist or is invalid, just keep defaults
            pass