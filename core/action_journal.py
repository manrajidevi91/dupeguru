# Created By: VisionClean Implementation
# Copyright 2025 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import logging
from collections import namedtuple
from enum import Enum


class ActionType(Enum):
    """Types of actions that can be recorded and undone."""
    DELETE = "delete"
    MOVE = "move"
    COPY = "copy"
    MARK = "mark"
    UNMARK = "unmark"
    REMOVE = "remove"
    MAKE_REFERENCE = "make_reference"


ActionRecord = namedtuple(
    "ActionRecord",
    [
        "action_type",  # ActionType
        "files",  # List of file objects that were affected
        "destinations",  # For move/copy: list of destination paths
        "previous_marks",  # For mark/unmark: dict of file -> previous mark state
        "previous_references",  # For make_reference: dict of group -> previous ref
        "timestamp",  # When the action was performed
    ]
)


class ActionJournal:
    """
    Tracks destructive actions for undo capability.
    
    Maintains a history of actions that modify files, marking state,
    or group structure, allowing the last action to be undone.
    """
    
    def __init__(self, max_history=10):
        """
        Initialize the action journal.
        
        Args:
            max_history: Maximum number of actions to keep in history
        """
        self.max_history = max_history
        self.history = []  # List of ActionRecord objects
        self.logger = logging.getLogger("core.action_journal")
    
    def record_delete(self, files):
        """Record a delete action."""
        record = ActionRecord(
            action_type=ActionType.DELETE,
            files=files,
            destinations=None,
            previous_marks=None,
            previous_references=None,
            timestamp=self._get_timestamp()
        )
        self._add_record(record)
        self.logger.info(f"Recorded delete of {len(files)} files")
    
    def record_move(self, file_dest_pairs):
        """Record a move action.
        
        Args:
            file_dest_pairs: List of (file, destination_path) tuples
        """
        files = [f for f, _ in file_dest_pairs]
        destinations = [d for _, d in file_dest_pairs]
        
        record = ActionRecord(
            action_type=ActionType.MOVE,
            files=files,
            destinations=destinations,
            previous_marks=None,
            previous_references=None,
            timestamp=self._get_timestamp()
        )
        self._add_record(record)
        self.logger.info(f"Recorded move of {len(files)} files")
    
    def record_copy(self, file_dest_pairs):
        """Record a copy action."""
        files = [f for f, _ in file_dest_pairs]
        destinations = [d for _, d in file_dest_pairs]
        
        record = ActionRecord(
            action_type=ActionType.COPY,
            files=files,
            destinations=destinations,
            previous_marks=None,
            previous_references=None,
            timestamp=self._get_timestamp()
        )
        self._add_record(record)
        self.logger.info(f"Recorded copy of {len(files)} files")
    
    def record_mark(self, results, files):
        """Record a mark action, capturing previous mark state."""
        previous_marks = {f: results.is_marked(f) for f in files}
        
        record = ActionRecord(
            action_type=ActionType.MARK,
            files=files,
            destinations=None,
            previous_marks=previous_marks,
            previous_references=None,
            timestamp=self._get_timestamp()
        )
        self._add_record(record)
        self.logger.info(f"Recorded mark of {len(files)} files")
    
    def record_unmark(self, results, files):
        """Record an unmark action, capturing previous mark state."""
        previous_marks = {f: results.is_marked(f) for f in files}
        
        record = ActionRecord(
            action_type=ActionType.UNMARK,
            files=files,
            destinations=None,
            previous_marks=previous_marks,
            previous_references=None,
            timestamp=self._get_timestamp()
        )
        self._add_record(record)
        self.logger.info(f"Recorded unmark of {len(files)} files")
    
    def record_remove(self, results, files, groups):
        """Record a remove action, capturing group state.
        
        Args:
            results: Results object
            files: Files that were removed
            groups: Groups that were affected
        """
        # Capture previous reference state for affected groups
        previous_references = {}
        for group in groups:
            if group.ref:
                previous_references[group] = group.ref
        
        record = ActionRecord(
            action_type=ActionType.REMOVE,
            files=files,
            destinations=None,
            previous_marks=None,
            previous_references=previous_references,
            timestamp=self._get_timestamp()
        )
        self._add_record(record)
        self.logger.info(f"Recorded remove of {len(files)} files from {len(groups)} groups")
    
    def record_make_reference(self, results, file_obj, group):
        """Record a make reference action."""
        # Capture the previous reference
        previous_ref = group.ref
        
        previous_references = {group: previous_ref} if previous_ref else {}
        
        record = ActionRecord(
            action_type=ActionType.MAKE_REFERENCE,
            files=[file_obj],
            destinations=None,
            previous_marks=None,
            previous_references=previous_references,
            timestamp=self._get_timestamp()
        )
        self._add_record(record)
        self.logger.info(f"Recorded make reference for {file_obj}")
    
    def can_undo(self):
        """Check if there's an action that can be undone."""
        return len(self.history) > 0
    
    def get_last_action(self):
        """Get the last action record without removing it."""
        if not self.history:
            return None
        return self.history[-1]
    
    def get_action_description(self, record):
        """Get a human-readable description of an action."""
        if record.action_type == ActionType.DELETE:
            return f"Deleted {len(record.files)} files"
        elif record.action_type == ActionType.MOVE:
            return f"Moved {len(record.files)} files"
        elif record.action_type == ActionType.COPY:
            return f"Copied {len(record.files)} files"
        elif record.action_type == ActionType.MARK:
            return f"Marked {len(record.files)} files"
        elif record.action_type == ActionType.UNMARK:
            return f"Unmarked {len(record.files)} files"
        elif record.action_type == ActionType.REMOVE:
            return f"Removed {len(record.files)} files from results"
        elif record.action_type == ActionType.MAKE_REFERENCE:
            return f"Changed reference file"
        else:
            return "Unknown action"
    
    def clear_history(self):
        """Clear all action history."""
        self.history.clear()
        self.logger.info("Cleared action history")
    
    def _add_record(self, record):
        """Add a record to history, maintaining max size."""
        self.history.append(record)
        # Keep only the most recent actions
        if len(self.history) > self.max_history:
            removed = self.history.pop(0)
            self.logger.debug(f"Removed old action from history: {removed.action_type}")
    
    def _get_timestamp(self):
        """Get current timestamp."""
        from datetime import datetime
        return datetime.now()
    
    def get_history_summary(self):
        """Get a summary of all actions in history."""
        summary = []
        for i, record in enumerate(reversed(self.history)):
            desc = self.get_action_description(record)
            summary.append(f"{len(self.history) - i}. {desc}")
        return summary