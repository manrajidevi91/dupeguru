# Created By: VisionClean Implementation
# Copyright 2025 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import logging
from enum import Enum
from typing import List, Callable, Any
from datetime import datetime


class SortCriteria(Enum):
    """Sorting criteria for duplicate groups."""
    GROUP_ID = "group_id"  # By group ID (default)
    PERCENTAGE = "percentage"  # By similarity (most similar first)
    SIZE = "size"  # By file size (largest first)
    RESOLUTION = "resolution"  # By resolution (highest first)
    SPACE_SAVED = "space_saved"  # By space that could be saved
    DUPE_COUNT = "dupe_count"  # By number of duplicates
    MODIFICATION_DATE = "modification_date"  # By date (newest first)


class FilterCriteria(Enum):
    """Filter criteria for duplicate groups."""
    SIMILARITY = "similarity"  # Filter by similarity threshold
    FILE_SIZE = "file_size"  # Filter by file size range
    RESOLUTION = "resolution"  # Filter by resolution range
    DATE = "date"  # Filter by date range
    MARKED = "marked"  # Filter by marked status
    REFERENCE = "reference"  # Filter by reference status


class FilterOperator(Enum):
    """Operators for filter comparisons."""
    EQUALS = "=="
    NOT_EQUALS = "!="
    GREATER_THAN = ">"
    GREATER_THAN_OR_EQUAL = ">="
    LESS_THAN = "<"
    LESS_THAN_OR_EQUAL = "<="
    CONTAINS = "contains"
    BETWEEN = "between"


class Filter:
    """A single filter condition."""
    
    def __init__(self, criteria: FilterCriteria, operator: FilterOperator, value: Any, value2: Any = None):
        """
        Initialize a filter.
        
        Args:
            criteria: What to filter on
            operator: How to compare
            value: The value to compare against
            value2: Second value for BETWEEN operator
        """
        self.criteria = criteria
        self.operator = operator
        self.value = value
        self.value2 = value2
    
    def matches(self, group) -> bool:
        """Check if a group matches this filter."""
        try:
            if self.criteria == FilterCriteria.SIMILARITY:
                return self._check_similarity(group)
            elif self.criteria == FilterCriteria.FILE_SIZE:
                return self._check_file_size(group)
            elif self.criteria == FilterCriteria.RESOLUTION:
                return self._check_resolution(group)
            elif self.criteria == FilterCriteria.DATE:
                return self._check_date(group)
            elif self.criteria == FilterCriteria.MARKED:
                return self._check_marked(group)
            elif self.criteria == FilterCriteria.REFERENCE:
                return self._check_reference(group)
            return True
        except Exception as e:
            logging.warning(f"Filter error: {e}")
            return False
    
    def _check_similarity(self, group) -> bool:
        """Check similarity filter."""
        similarity = group.percentage
        return self._compare_numeric(similarity, self.value)
    
    def _check_file_size(self, group) -> bool:
        """Check file size filter."""
        # Use the reference file's size
        size = group.ref.size
        return self._compare_numeric(size, self.value)
    
    def _check_resolution(self, group) -> bool:
        """Check resolution filter."""
        if not hasattr(group.ref, 'dimensions'):
            return False
        dimensions = group.ref.dimensions
        if not dimensions:
            return False
        # Total pixels
        resolution = dimensions[0] * dimensions[1]
        return self._compare_numeric(resolution, self.value)
    
    def _check_date(self, group) -> bool:
        """Check date filter."""
        if not hasattr(group.ref, 'mtime'):
            return False
        mod_time = group.ref.mtime
        return self._compare_datetime(mod_time, self.value)
    
    def _check_marked(self, group) -> bool:
        """Check marked filter."""
        # Check if any file in group is marked
        from core.results import Results
        # We need access to results to check marking
        # This will be set externally
        return False  # Placeholder
    
    def _check_reference(self, group) -> bool:
        """Check reference filter."""
        # This filter is more about selection logic
        return True  # Placeholder
    
    def _compare_numeric(self, actual: float, target: float) -> bool:
        """Compare numeric values."""
        if self.operator == FilterOperator.EQUALS:
            return actual == target
        elif self.operator == FilterOperator.NOT_EQUALS:
            return actual != target
        elif self.operator == FilterOperator.GREATER_THAN:
            return actual > target
        elif self.operator == FilterOperator.GREATER_THAN_OR_EQUAL:
            return actual >= target
        elif self.operator == FilterOperator.LESS_THAN:
            return actual < target
        elif self.operator == FilterOperator.LESS_THAN_OR_EQUAL:
            return actual <= target
        elif self.operator == FilterOperator.BETWEEN:
            return self.value2 is not None and self.value <= actual <= self.value2
        return True
    
    def _compare_datetime(self, actual: datetime, target: datetime) -> bool:
        """Compare datetime values."""
        if self.operator == FilterOperator.EQUALS:
            return actual == target
        elif self.operator == FilterOperator.NOT_EQUALS:
            return actual != target
        elif self.operator == FilterOperator.GREATER_THAN:
            return actual > target
        elif self.operator == FilterOperator.GREATER_THAN_OR_EQUAL:
            return actual >= target
        elif self.operator == FilterOperator.LESS_THAN:
            return actual < target
        elif self.operator == FilterOperator.LESS_THAN_OR_EQUAL:
            return actual <= target
        elif self.operator == FilterOperator.BETWEEN:
            return self.value2 is not None and self.value <= actual <= self.value2
        return True


class FilterSortManager:
    """
    Manages filtering and sorting of duplicate groups.
    
    Provides a non-destructive way to view filtered/sorted results
    without modifying the underlying scan results.
    """
    
    def __init__(self, results):
        """
        Initialize the manager.
        
        Args:
            results: Results object containing the groups
        """
        self.results = results
        self.active_filters: List[Filter] = []
        self.active_sort = SortCriteria.GROUP_ID
        self.sort_reverse = False
        self.logger = logging.getLogger("core.filter_sort_manager")
    
    def add_filter(self, filter_obj: Filter):
        """Add a filter to active filters."""
        self.active_filters.append(filter_obj)
        self.logger.debug(f"Added filter: {filter_obj.criteria}")
    
    def remove_filter(self, filter_obj: Filter):
        """Remove a filter from active filters."""
        if filter_obj in self.active_filters:
            self.active_filters.remove(filter_obj)
            self.logger.debug(f"Removed filter: {filter_obj.criteria}")
    
    def clear_filters(self):
        """Clear all active filters."""
        self.active_filters.clear()
        self.logger.debug("Cleared all filters")
    
    def set_sort(self, criteria: SortCriteria, reverse: bool = False):
        """Set the active sort criteria."""
        self.active_sort = criteria
        self.sort_reverse = reverse
        self.logger.debug(f"Set sort: {criteria}, reverse={reverse}")
    
    def get_filtered_groups(self):
        """Get groups that match all active filters."""
        if not self.active_filters:
            return self.results.groups
        
        filtered = []
        for group in self.results.groups:
            if all(f.matches(group) for f in self.active_filters):
                filtered.append(group)
        
        self.logger.debug(f"Filtered {len(self.results.groups)} groups to {len(filtered)}")
        return filtered
    
    def get_sorted_groups(self, groups=None):
        """
        Get groups sorted by active criteria.
        
        Args:
            groups: Groups to sort (uses filtered groups if None)
        
        Returns:
            Sorted list of groups
        """
        if groups is None:
            groups = self.get_filtered_groups()
        
        if self.active_sort == SortCriteria.GROUP_ID:
            # No sorting needed
            return groups
        elif self.active_sort == SortCriteria.PERCENTAGE:
            return sorted(groups, key=lambda g: g.percentage, reverse=self.sort_reverse or True)
        elif self.active_sort == SortCriteria.SIZE:
            return sorted(groups, key=self._get_group_size, reverse=self.sort_reverse or True)
        elif self.active_sort == SortCriteria.RESOLUTION:
            return sorted(groups, key=self._get_group_resolution, reverse=self.sort_reverse or True)
        elif self.active_sort == SortCriteria.SPACE_SAVED:
            return sorted(groups, key=self._get_space_saved, reverse=self.sort_reverse or True)
        elif self.active_sort == SortCriteria.DUPE_COUNT:
            return sorted(groups, key=lambda g: len(g), reverse=self.sort_reverse or True)
        elif self.active_sort == SortCriteria.MODIFICATION_DATE:
            return sorted(groups, key=self._get_modification_date, reverse=self.sort_reverse or True)
        else:
            return groups
    
    def get_filtered_and_sorted_groups(self):
        """Get groups after applying filters and sorting."""
        filtered = self.get_filtered_groups()
        sorted_groups = self.get_sorted_groups(filtered)
        return sorted_groups
    
    def _get_group_size(self, group) -> int:
        """Get the size of the reference file."""
        return group.ref.size if hasattr(group.ref, 'size') else 0
    
    def _get_group_resolution(self, group) -> int:
        """Get the total pixels of the reference file."""
        if not hasattr(group.ref, 'dimensions') or not group.ref.dimensions:
            return 0
        w, h = group.ref.dimensions
        return w * h
    
    def _get_space_saved(self, group) -> int:
        """Calculate space that would be saved by removing duplicates."""
        total_size = sum(d.size for d in group if hasattr(d, 'size'))
        ref_size = group.ref.size if hasattr(group.ref, 'size') else 0
        return total_size - ref_size
    
    def _get_modification_date(self, group) -> datetime:
        """Get the modification date of the reference file."""
        if hasattr(group.ref, 'mtime'):
            return group.ref.mtime
        return datetime.min
    
    def get_filter_summary(self) -> str:
        """Get a summary of active filters."""
        if not self.active_filters:
            return "No filters active"
        
        summary = f"{len(self.active_filters)} filter(s): "
        summaries = []
        for f in self.active_filters:
            if f.operator == FilterOperator.BETWEEN:
                summaries.append(f"{f.criteria.value} {f.operator.value} {f.value} and {f.value2}")
            else:
                summaries.append(f"{f.criteria.value} {f.operator.value} {f.value}")
        return summary + ", ".join(summaries)
    
    def get_sort_summary(self) -> str:
        """Get a summary of active sort."""
        direction = "descending" if self.sort_reverse else "ascending"
        return f"Sort: {self.active_sort.value} ({direction})"