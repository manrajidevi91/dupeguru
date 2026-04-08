# Created By: VisionClean Implementation
# Copyright 2025 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import os
import os.path as op
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Optional, List, Dict, Any


class SessionData:
    """
    Represents a complete scan session.
    
    Captures all state needed to restore a scan session including:
    - Scan configuration/preset
    - Selected directories
    - Results and marking state
    - Applied filters and sorts
    - Action history
    - Timestamps for incremental scanning
    """
    
    def __init__(self):
        """Initialize an empty session."""
        self.version = "1.0"
        self.app_mode = None  # AppMode enum value
        self.scan_time = None  # datetime when scan was performed
        self.directories = []  # List of directory paths
        self.preset = {}  # Scan preset/options used
        self.results_xml_path = None  # Path to results XML file
        self.marked_files = []  # List of marked file paths
        self.filters = []  # Active filter criteria
        self.sort_criteria = None  # Active sort criteria
        self.action_history = []  # Action journal entries
        self.file_hashes = {}  # File path -> hash for incremental scanning
        self.folder_timestamps = {}  # Folder path -> last modified time
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert session to dictionary for JSON serialization."""
        return {
            "version": self.version,
            "app_mode": self.app_mode,
            "scan_time": self.scan_time.isoformat() if self.scan_time else None,
            "directories": self.directories,
            "preset": self.preset,
            "results_xml_path": self.results_xml_path,
            "marked_files": self.marked_files,
            "filters": self.filters,
            "sort_criteria": self.sort_criteria,
            "action_history": self.action_history,
            "file_hashes": self.file_hashes,
            "folder_timestamps": self.folder_timestamps,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'SessionData':
        """Create SessionData from dictionary (JSON deserialization)."""
        session = cls()
        session.version = data.get("version", "1.0")
        session.app_mode = data.get("app_mode")
        
        scan_time_str = data.get("scan_time")
        session.scan_time = datetime.fromisoformat(scan_time_str) if scan_time_str else None
        
        session.directories = data.get("directories", [])
        session.preset = data.get("preset", {})
        session.results_xml_path = data.get("results_xml_path")
        session.marked_files = data.get("marked_files", [])
        session.filters = data.get("filters", [])
        session.sort_criteria = data.get("sort_criteria")
        session.action_history = data.get("action_history", [])
        session.file_hashes = data.get("file_hashes", {})
        session.folder_timestamps = data.get("folder_timestamps", {})
        
        return session


class SessionManager:
    """
    Manages saving and loading of scan sessions.
    
    Provides functionality to:
    - Save complete scan sessions
    - Load sessions to restore state
    - Track incremental scan metadata
    - Detect changed files/folders
    - Manage session file lifecycle
    """
    
    def __init__(self, session_dir: str):
        """
        Initialize the session manager.
        
        Args:
            session_dir: Directory where session files are stored
        """
        self.session_dir = session_dir
        self.logger = logging.getLogger("core.session_manager")
        
        # Create session directory if it doesn't exist
        if not op.exists(session_dir):
            os.makedirs(session_dir)
            self.logger.info(f"Created session directory: {session_dir}")
    
    def save_session(self, session: SessionData, session_name: str) -> str:
        """
        Save a session to disk.
        
        Args:
            session: SessionData to save
            session_name: Name for this session
        
        Returns:
            Path to the saved session file
        """
        # Create session file path
        session_path = op.join(self.session_dir, f"{session_name}.json")
        
        # Save session metadata as JSON
        try:
            with open(session_path, 'w', encoding='utf-8') as f:
                json.dump(session.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved session to {session_path}")
            return session_path
        except Exception as e:
            self.logger.error(f"Failed to save session: {e}")
            raise
    
    def load_session(self, session_name: str) -> Optional[SessionData]:
        """
        Load a session from disk.
        
        Args:
            session_name: Name of the session to load
        
        Returns:
            SessionData object or None if not found
        """
        session_path = op.join(self.session_dir, f"{session_name}.json")
        
        if not op.exists(session_path):
            self.logger.warning(f"Session file not found: {session_path}")
            return None
        
        try:
            with open(session_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            session = SessionData.from_dict(data)
            self.logger.info(f"Loaded session from {session_path}")
            return session
        except Exception as e:
            self.logger.error(f"Failed to load session: {e}")
            return None
    
    def list_sessions(self) -> List[str]:
        """
        List all available sessions.
        
        Returns:
            List of session names (without .json extension)
        """
        try:
            files = os.listdir(self.session_dir)
            sessions = [f[:-5] for f in files if f.endswith('.json')]
            return sorted(sessions)
        except Exception as e:
            self.logger.error(f"Failed to list sessions: {e}")
            return []
    
    def delete_session(self, session_name: str) -> bool:
        """
        Delete a session.
        
        Args:
            session_name: Name of the session to delete
        
        Returns:
            True if deleted, False otherwise
        """
        session_path = op.join(self.session_dir, f"{session_name}.json")
        
        try:
            if op.exists(session_path):
                os.remove(session_path)
                self.logger.info(f"Deleted session: {session_name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete session: {e}")
            return False
    
    def detect_folder_changes(self, session: SessionData) -> Dict[str, bool]:
        """
        Detect which folders have changed since the session was created.
        
        Compares stored folder timestamps with current filesystem timestamps.
        
        Args:
            session: Session with folder timestamps to check
        
        Returns:
            Dict mapping folder path -> has_changed (bool)
        """
        changes = {}
        
        for folder_path, stored_time_str in session.folder_timestamps.items():
            try:
                # Parse stored timestamp
                stored_time = datetime.fromisoformat(stored_time_str)
                
                # Get current folder modification time
                current_time = datetime.fromtimestamp(os.path.getmtime(folder_path))
                
                # Folder has changed if current time is newer
                changes[folder_path] = current_time > stored_time
                
                if changes[folder_path]:
                    self.logger.debug(f"Folder changed: {folder_path}")
            except Exception as e:
                self.logger.warning(f"Error checking folder {folder_path}: {e}")
                changes[folder_path] = True  # Assume changed on error
        
        return changes
    
    def update_folder_timestamps(self, folders: List[str], session: SessionData):
        """
        Update folder timestamps in a session.
        
        Args:
            folders: List of folder paths to update
            session: Session to update
        """
        for folder_path in folders:
            try:
                mtime = os.path.getmtime(folder_path)
                session.folder_timestamps[folder_path] = datetime.fromtimestamp(mtime).isoformat()
            except Exception as e:
                self.logger.warning(f"Error getting timestamp for {folder_path}: {e}")
    
    def has_any_changes(self, session: SessionData) -> bool:
        """
        Check if any folders in the session have changed.
        
        Args:
            session: Session to check
        
        Returns:
            True if any folder has changed
        """
        changes = self.detect_folder_changes(session)
        return any(changes.values())
    
    def get_session_summary(self, session: SessionData) -> str:
        """
        Get a human-readable summary of a session.
        
        Args:
            session: Session to summarize
        
        Returns:
            Summary string
        """
        lines = [
            f"Scan Time: {session.scan_time.strftime('%Y-%m-%d %H:%M:%S') if session.scan_time else 'Unknown'}",
            f"Directories: {len(session.directories)}",
            f"Mode: {session.app_mode}",
        ]
        
        if session.marked_files:
            lines.append(f"Marked Files: {len(session.marked_files)}")
        
        if session.filters:
            lines.append(f"Filters: {len(session.filters)}")
        
        return "\n".join(lines)