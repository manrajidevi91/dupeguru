# Created By: VisionClean Implementation
# Copyright 2025 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import json
import os.path as op
import logging
from typing import List, Dict, Any, Callable
from enum import Enum


class SelectionRule(Enum):
    """Rules for selecting duplicates within a group."""
    SELECT_ALL_EXCEPT_BEST = "select_all_except_best"
    KEEP_NEWEST = "keep_newest"
    KEEP_OLDEST = "keep_oldest"
    KEEP_HIGHEST_RESOLUTION = "keep_highest_resolution"
    KEEP_LARGEST = "keep_largest"
    KEEP_SMALLEST = "keep_smallest"


class AutoCleanProfile:
    """
    A predefined cleanup configuration.
    
    Profiles define which duplicates to mark for deletion based on
    selection rules and filters.
    """
    
    def __init__(self, name: str, description: str = ""):
        """
        Initialize a profile.
        
        Args:
            name: Profile name
            description: Human-readable description
        """
        self.name = name
        self.description = description
        self.selection_rule = SelectionRule.SELECT_ALL_EXCEPT_BEST
        self.filters = []  # List of filter criteria
        self.min_similarity = None  # Minimum similarity threshold
        self.max_similarity = None  # Maximum similarity threshold
        self.min_file_size = None  # Minimum file size (bytes)
        self.max_file_size = None  # Maximum file size (bytes)
        self.apply_to_marked = False  # Only apply to already marked groups
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert profile to dictionary for JSON serialization."""
        return {
            "name": self.name,
            "description": self.description,
            "selection_rule": self.selection_rule.value,
            "filters": self.filters,
            "min_similarity": self.min_similarity,
            "max_similarity": self.max_similarity,
            "min_file_size": self.min_file_size,
            "max_file_size": self.max_file_size,
            "apply_to_marked": self.apply_to_marked,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AutoCleanProfile':
        """Create profile from dictionary."""
        profile = cls(data["name"], data.get("description", ""))
        profile.selection_rule = SelectionRule(data.get("selection_rule", "select_all_except_best"))
        profile.filters = data.get("filters", [])
        profile.min_similarity = data.get("min_similarity")
        profile.max_similarity = data.get("max_similarity")
        profile.min_file_size = data.get("min_file_size")
        profile.max_file_size = data.get("max_file_size")
        profile.apply_to_marked = data.get("apply_to_marked", False)
        return profile
    
    def matches_group(self, group, results) -> bool:
        """
        Check if a group matches this profile's criteria.
        
        Args:
            group: Duplicate group to check
            results: Results object for checking marks
        
        Returns:
            True if group matches profile criteria
        """
        # Check if group has marked files (if required)
        if self.apply_to_marked:
            has_marked = any(results.is_marked(d) for d in group.dupes)
            if not has_marked:
                return False
        
        # Check similarity threshold
        if hasattr(group, 'percentage'):
            if self.min_similarity is not None and group.percentage < self.min_similarity:
                return False
            if self.max_similarity is not None and group.percentage > self.max_similarity:
                return False
        
        # Check file size
        if hasattr(group.ref, 'size'):
            ref_size = group.ref.size
            if self.min_file_size is not None and ref_size < self.min_file_size:
                return False
            if self.max_file_size is not None and ref_size > self.max_file_size:
                return False
        
        return True


class AutoCleanManager:
    """
    Manages auto-clean profiles and execution.
    
    Provides functionality to:
    - Create and save custom profiles
    - Preview what would be marked
    - Execute auto-clean with confirmation
    - Load and delete profiles
    """
    
    def __init__(self, profile_dir: str):
        """
        Initialize the manager.
        
        Args:
            profile_dir: Directory where profile files are stored
        """
        self.profile_dir = profile_dir
        self.logger = logging.getLogger("core.auto_clean")
        
        # Create profile directory if it doesn't exist
        if not op.exists(profile_dir):
            os.makedirs(profile_dir)
            self.logger.info(f"Created profile directory: {profile_dir}")
    
    def get_default_profiles(self) -> List[AutoCleanProfile]:
        """Get list of default built-in profiles."""
        return [
            self._create_keep_newest_profile(),
            self._create_keep_oldest_profile(),
            self._create_keep_highest_resolution_profile(),
            self._create_keep_largest_profile(),
            self._create_high_similarity_profile(),
        ]
    
    def _create_keep_newest_profile(self) -> AutoCleanProfile:
        """Create profile that keeps newest files."""
        profile = AutoCleanProfile(
            "Keep Newest",
            "Mark all duplicates except the newest file in each group. "
            "Useful for keeping recent versions of files."
        )
        profile.selection_rule = SelectionRule.KEEP_NEWEST
        return profile
    
    def _create_keep_oldest_profile(self) -> AutoCleanProfile:
        """Create profile that keeps oldest files."""
        profile = AutoCleanProfile(
            "Keep Oldest",
            "Mark all duplicates except the oldest file in each group. "
            "Useful for keeping original versions."
        )
        profile.selection_rule = SelectionRule.KEEP_OLDEST
        return profile
    
    def _create_keep_highest_resolution_profile(self) -> AutoCleanProfile:
        """Create profile that keeps highest resolution images."""
        profile = AutoCleanProfile(
            "Keep Highest Resolution",
            "Mark all duplicates except the highest resolution image. "
            "Best for photo collections."
        )
        profile.selection_rule = SelectionRule.KEEP_HIGHEST_RESOLUTION
        return profile
    
    def _create_keep_largest_profile(self) -> AutoCleanProfile:
        """Create profile that keeps largest files."""
        profile = AutoCleanProfile(
            "Keep Largest",
            "Mark all duplicates except the largest file in each group. "
            "Useful for keeping high-quality versions."
        )
        profile.selection_rule = SelectionRule.KEEP_LARGEST
        return profile
    
    def _create_high_similarity_profile(self) -> AutoCleanProfile:
        """Create profile for high-similarity duplicates."""
        profile = AutoCleanProfile(
            "High Similarity Cleanup",
            "Mark duplicates in groups with >90% similarity. "
            "Aggressive cleanup for near-identical files."
        )
        profile.selection_rule = SelectionRule.SELECT_ALL_EXCEPT_BEST
        profile.min_similarity = 90
        return profile
    
    def save_profile(self, profile: AutoCleanProfile) -> str:
        """
        Save a profile to disk.
        
        Args:
            profile: Profile to save
        
        Returns:
            Path to saved profile file
        """
        profile_path = op.join(self.profile_dir, f"{profile.name}.json")
        
        try:
            with open(profile_path, 'w', encoding='utf-8') as f:
                json.dump(profile.to_dict(), f, indent=2, ensure_ascii=False)
            
            self.logger.info(f"Saved profile: {profile.name}")
            return profile_path
        except Exception as e:
            self.logger.error(f"Failed to save profile: {e}")
            raise
    
    def load_profile(self, profile_name: str) -> AutoCleanProfile:
        """
        Load a profile from disk.
        
        Args:
            profile_name: Name of the profile (without .json)
        
        Returns:
            Loaded profile or None if not found
        """
        profile_path = op.join(self.profile_dir, f"{profile_name}.json")
        
        if not op.exists(profile_path):
            self.logger.warning(f"Profile not found: {profile_name}")
            return None
        
        try:
            with open(profile_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            profile = AutoCleanProfile.from_dict(data)
            self.logger.info(f"Loaded profile: {profile_name}")
            return profile
        except Exception as e:
            self.logger.error(f"Failed to load profile: {e}")
            return None
    
    def list_profiles(self) -> List[str]:
        """
        List all available custom profiles.
        
        Returns:
            List of profile names
        """
        try:
            files = os.listdir(self.profile_dir)
            profiles = [f[:-5] for f in files if f.endswith('.json')]
            return sorted(profiles)
        except Exception as e:
            self.logger.error(f"Failed to list profiles: {e}")
            return []
    
    def delete_profile(self, profile_name: str) -> bool:
        """
        Delete a profile.
        
        Args:
            profile_name: Name of the profile to delete
        
        Returns:
            True if deleted
        """
        profile_path = op.join(self.profile_dir, f"{profile_name}.json")
        
        try:
            if op.exists(profile_path):
                os.remove(profile_path)
                self.logger.info(f"Deleted profile: {profile_name}")
                return True
            return False
        except Exception as e:
            self.logger.error(f"Failed to delete profile: {e}")
            return False
    
    def preview_profile(self, profile: AutoCleanProfile, results, presenter) -> Dict[str, Any]:
        """
        Preview what would be marked by a profile.
        
        Args:
            profile: Profile to apply
            results: Results object
            presenter: GroupPresenter for selection rules
        
        Returns:
            Preview statistics dict
        """
        groups_to_process = []
        total_files_to_mark = 0
        space_to_free = 0
        
        for group in results.groups:
            # Check if group matches profile criteria
            if not profile.matches_group(group, results):
                continue
            
            groups_to_process.append(group)
            
            # Apply selection rule to get files that would be marked
            files_to_mark = self._apply_selection_rule(profile.selection_rule, group, presenter)
            
            # Calculate statistics
            total_files_to_mark += len(files_to_mark)
            for file_obj in files_to_mark:
                if hasattr(file_obj, 'size'):
                    space_to_free += file_obj.size
        
        return {
            "groups_to_process": len(groups_to_process),
            "total_files_to_mark": total_files_to_mark,
            "space_to_free_bytes": space_to_free,
            "total_groups": len(results.groups),
        }
    
    def _apply_selection_rule(self, rule: SelectionRule, group, presenter) -> List:
        """Apply a selection rule to a group."""
        if rule == SelectionRule.SELECT_ALL_EXCEPT_BEST:
            return presenter.select_all_except_best(group)
        elif rule == SelectionRule.KEEP_NEWEST:
            return presenter.keep_newest(group)
        elif rule == SelectionRule.KEEP_OLDEST:
            return presenter.keep_oldest(group)
        elif rule == SelectionRule.KEEP_HIGHEST_RESOLUTION:
            return presenter.keep_highest_resolution(group)
        elif rule == SelectionRule.KEEP_LARGEST:
            return presenter.keep_largest(group)
        elif rule == SelectionRule.KEEP_SMALLEST:
            return presenter.keep_smallest(group)
        else:
            return []
    
    def execute_profile(self, profile: AutoCleanProfile, results, presenter) -> int:
        """
        Execute a profile to mark files.
        
        Args:
            profile: Profile to apply
            results: Results object
            presenter: GroupPresenter for selection rules
        
        Returns:
            Number of files marked
        """
        files_marked = 0
        
        for group in results.groups:
            # Check if group matches profile criteria
            if not profile.matches_group(group, results):
                continue
            
            # Apply selection rule
            files_to_mark = self._apply_selection_rule(profile.selection_rule, group, presenter)
            
            # Mark the files
            for file_obj in files_to_mark:
                if results.is_markable(file_obj):
                    results.mark(file_obj)
                    files_marked += 1
        
        self.logger.info(f"Profile '{profile.name}' marked {files_marked} files")
        return files_marked