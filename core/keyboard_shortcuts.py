# Created By: VisionClean Implementation
# Copyright 2025 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import os.path as op
import json
import logging
from typing import Dict, Optional


class KeyboardShortcut:
    """Represents a single keyboard shortcut."""
    
    def __init__(self, action_id: str, default_key: str, modifiers: str = ""):
        """
        Initialize a keyboard shortcut.
        
        Args:
            action_id: Unique identifier for the action
            default_key: Default key (e.g., "Delete", "F5")
            modifiers: Key modifiers (e.g., "Ctrl+", "Shift+Ctrl+")
        """
        self.action_id = action_id
        self.default_key = default_key
        self.default_modifiers = modifiers
        self.current_key = default_key
        self.current_modifiers = modifiers
    
    def to_dict(self) -> dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "action_id": self.action_id,
            "key": self.current_key,
            "modifiers": self.current_modifiers,
        }
    
    def from_dict(self, data: dict):
        """Load from dictionary."""
        self.current_key = data.get("key", self.default_key)
        self.current_modifiers = data.get("modifiers", self.default_modifiers)
    
    def reset_to_default(self):
        """Reset to default shortcut."""
        self.current_key = self.default_key
        self.current_modifiers = self.default_modifiers
    
    @property
    def display_string(self) -> str:
        """Get display string (e.g., 'Ctrl+Delete')."""
        return f"{self.current_modifiers}{self.current_key}"


class KeyboardShortcutManager:
    """
    Manages keyboard shortcuts for the application.
    
    Provides functionality to:
    - Define default shortcuts
    - Customize shortcuts
    - Save/load shortcuts
    - Reset to defaults
    """
    
    def __init__(self, config_path: str):
        """
        Initialize the shortcut manager.
        
        Args:
            config_path: Path to save/load shortcut configuration
        """
        self.config_path = config_path
        self.shortcuts: Dict[str, KeyboardShortcut] = {}
        self.logger = logging.getLogger("core.keyboard_shortcuts")
        
        self._initialize_default_shortcuts()
        self.load_shortcuts()
    
    def _initialize_default_shortcuts(self):
        """Initialize default keyboard shortcuts."""
        # Navigation
        self.shortcuts["next_group"] = KeyboardShortcut("next_group", "Down", "")
        self.shortcuts["previous_group"] = KeyboardShortcut("previous_group", "Up", "")
        self.shortcuts["first_group"] = KeyboardShortcut("first_group", "Home", "")
        self.shortcuts["last_group"] = KeyboardShortcut("last_group", "End", "")
        
        # Selection
        self.shortcuts["toggle_mark"] = KeyboardShortcut("toggle_mark", "Space", "")
        self.shortcuts["mark_all"] = KeyboardShortcut("mark_all", "A", "Ctrl+")
        self.shortcuts["mark_none"] = KeyboardShortcut("mark_none", "D", "Ctrl+Shift+")
        self.shortcuts["invert_marks"] = KeyboardShortcut("invert_marks", "I", "Ctrl+")
        
        # Deletion actions
        self.shortcuts["delete_marked"] = KeyboardShortcut("delete_marked", "Delete", "")
        self.shortcuts["send_to_trash"] = KeyboardShortcut("send_to_trash", "Delete", "Shift+")
        
        # File operations
        self.shortcuts["open_selected"] = KeyboardShortcut("open_selected", "O", "Ctrl+")
        self.shortcuts["reveal_selected"] = KeyboardShortcut("reveal_selected", "R", "Ctrl+")
        self.shortcuts["rename_selected"] = KeyboardShortcut("rename_selected", "F2", "")
        
        # Views and dialogs
        self.shortcuts["open_compare"] = KeyboardShortcut("open_compare", "C", "Ctrl+")
        self.shortcuts["open_directories"] = KeyboardShortcut("open_directories", "D", "Ctrl+")
        self.shortcuts["open_preferences"] = KeyboardShortcut("open_preferences", "P", "Ctrl+")
        
        # Scanning
        self.shortcuts["start_scan"] = KeyboardShortcut("start_scan", "F5", "")
        self.shortcuts["stop_scan"] = KeyboardShortcut("stop_scan", "F6", "")
        
        # Results management
        self.shortcuts["export_results"] = KeyboardShortcut("export_results", "E", "Ctrl+")
        self.shortcuts["save_results"] = KeyboardShortcut("save_results", "S", "Ctrl+")
        self.shortcuts["load_results"] = KeyboardShortcut("load_results", "O", "Ctrl+Shift+")
        
        # Session management
        self.shortcuts["save_session"] = KeyboardShortcut("save_session", "S", "Ctrl+Shift+")
        self.shortcuts["load_session"] = KeyboardShortcut("load_session", "L", "Ctrl+Shift+")
        
        # Actions
        self.shortcuts["undo"] = KeyboardShortcut("undo", "Z", "Ctrl+")
        self.shortcuts["redo"] = KeyboardShortcut("redo", "Y", "Ctrl+")
        self.shortcuts["apply_filter"] = KeyboardShortcut("apply_filter", "F", "Ctrl+")
        self.shortcuts["clear_filter"] = KeyboardShortcut("clear_filter", "F", "Ctrl+Shift+")
        
        # Auto-clean
        self.shortcuts["quick_clean"] = KeyboardShortcut("quick_clean", "K", "Ctrl+")
        
        # Help
        self.shortcuts["show_help"] = KeyboardShortcut("show_help", "F1", "")
    
    def get_shortcut(self, action_id: str) -> Optional[KeyboardShortcut]:
        """Get a shortcut by action ID."""
        return self.shortcuts.get(action_id)
    
    def set_shortcut(self, action_id: str, key: str, modifiers: str = "") -> bool:
        """
        Customize a shortcut.
        
        Args:
            action_id: Action to customize
            key: New key
            modifiers: New modifiers
        
        Returns:
            True if set successfully
        """
        if action_id not in self.shortcuts:
            self.logger.warning(f"Unknown action ID: {action_id}")
            return False
        
        shortcut = self.shortcuts[action_id]
        shortcut.current_key = key
        shortcut.current_modifiers = modifiers
        
        self.save_shortcuts()
        return True
    
    def reset_shortcut(self, action_id: str) -> bool:
        """Reset a shortcut to default."""
        if action_id not in self.shortcuts:
            return False
        
        self.shortcuts[action_id].reset_to_default()
        self.save_shortcuts()
        return True
    
    def reset_all_shortcuts(self):
        """Reset all shortcuts to defaults."""
        for shortcut in self.shortcuts.values():
            shortcut.reset_to_default()
        self.save_shortcuts()
    
    def save_shortcuts(self) -> bool:
        """Save shortcuts to file."""
        try:
            data = {
                "version": "1.0",
                "shortcuts": [s.to_dict() for s in self.shortcuts.values()],
            }
            
            with open(self.config_path, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved keyboard shortcuts to {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to save shortcuts: {e}")
            return False
    
    def load_shortcuts(self) -> bool:
        """Load shortcuts from file."""
        if not op.exists(self.config_path):
            self.logger.info("No shortcuts file found, using defaults")
            return False
        
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            for shortcut_data in data.get("shortcuts", []):
                action_id = shortcut_data.get("action_id")
                if action_id in self.shortcuts:
                    self.shortcuts[action_id].from_dict(shortcut_data)
            
            self.logger.info(f"Loaded keyboard shortcuts from {self.config_path}")
            return True
        except Exception as e:
            self.logger.error(f"Failed to load shortcuts: {e}")
            return False
    
    def get_all_shortcuts(self) -> Dict[str, str]:
        """Get all shortcuts as action_id -> display_string mapping."""
        return {
            action_id: shortcut.display_string
            for action_id, shortcut in self.shortcuts.items()
        }
    
    def get_shortcuts_by_category(self) -> Dict[str, Dict[str, str]]:
        """Get shortcuts organized by category for UI display."""
        categories = {
            "Navigation": ["next_group", "previous_group", "first_group", "last_group"],
            "Selection": ["toggle_mark", "mark_all", "mark_none", "invert_marks"],
            "Deletion": ["delete_marked", "send_to_trash"],
            "File Operations": ["open_selected", "reveal_selected", "rename_selected"],
            "Views": ["open_compare", "open_directories", "open_preferences"],
            "Scanning": ["start_scan", "stop_scan"],
            "Results": ["export_results", "save_results", "load_results"],
            "Sessions": ["save_session", "load_session"],
            "Actions": ["undo", "redo", "apply_filter", "clear_filter"],
            "Auto-Clean": ["quick_clean"],
            "Help": ["show_help"],
        }
        
        result = {}
        for category, action_ids in categories.items():
            result[category] = {
                action_id: self.shortcuts[action_id].display_string
                for action_id in action_ids
                if action_id in self.shortcuts
            }
        
        return result