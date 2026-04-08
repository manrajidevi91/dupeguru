# Copyright 2016 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from collections import namedtuple
from typing import List, Optional, Set
from datetime import datetime

from hscommon.util import format_size


# Group summary data structure for card presentation
GroupSummary = namedtuple(
    "GroupSummary",
    [
        "group_id",  # Unique identifier for the group
        "group_index",  # Position in results
        "duplicate_count",  # Number of duplicates in group
        "total_size",  # Total size of all duplicates
        "ref_size",  # Size of reference file
        "space_saved",  # Space that would be saved by deleting duplicates
        "best_candidate",  # The file object determined to be the best to keep
        "similarity_range",  # Tuple of (min_similarity, max_similarity) in group
        "has_images",  # Whether group contains image files
        "resolution_summary",  # For images: best resolution info
        "date_range",  # Tuple of (earliest_date, latest_date)
        "file_types",  # Set of file extensions in group
        "marked_count",  # Number of marked files
    ]
)


# File metadata for detailed display
FileMetadata = namedtuple(
    "FileMetadata",
    [
        "file",  # The file object
        "is_reference",  # Whether this is the reference file
        "is_marked",  # Whether this file is marked for deletion
        "size",  # File size
        "size_formatted",  # Human-readable size
        "dimensions",  # For images: (width, height) tuple
        "modification_date",  # File modification timestamp
        "creation_date",  # File creation timestamp (if available)
        "similarity_to_ref",  # For duplicates: similarity percentage
        "folder_path",  # Parent folder path
        "file_type",  # File extension
    ]
)


class GroupPresenter:
    """
    Presents result groups in a card-ready format.
    
    This class extends the core Results functionality without modifying it,
    providing derived metadata and helper methods for the new card-based UI.
    """

    def __init__(self, results):
        """Initialize presenter with a Results instance."""
        self.results = results
        self._summaries_cache = {}  # Cache group summaries by group object
        self._metadata_cache = {}  # Cache file metadata by file object

    def get_group_summary(self, group, group_index: int) -> GroupSummary:
        """
        Generate a summary for a group suitable for card display.
        
        Args:
            group: A core.engine.Group instance
            group_index: The group's position in the results
            
        Returns:
            GroupSummary with all derived metadata
        """
        # Check cache first
        if group in self._summaries_cache:
            return self._summaries_cache[group]

        # Calculate summary data
        dupes = group.dupes
        ref = group.ref

        # Basic counts and sizes
        duplicate_count = len([d for d in dupes if not d.is_ref])
        total_size = sum(d.size for d in dupes)
        ref_size = ref.size if ref else 0
        space_saved = total_size - ref_size

        # Determine best candidate to keep
        best_candidate = self._determine_best_candidate(group)

        # Similarity range
        min_sim, max_sim = self._get_similarity_range(group)

        # Image detection and resolution
        has_images = any(self._is_image_file(d) for d in dupes)
        resolution_summary = self._get_resolution_summary(group) if has_images else None

        # Date range
        date_range = self._get_date_range(dupes)

        # File types
        file_types = set()
        for d in dupes:
            try:
                ext = d.path.suffix.lower()
                if ext:
                    file_types.add(ext)
            except (AttributeError, OSError):
                pass

        # Marked count
        marked_count = sum(1 for d in dupes if self.results.is_marked(d))

        summary = GroupSummary(
            group_id=id(group),
            group_index=group_index,
            duplicate_count=duplicate_count,
            total_size=total_size,
            ref_size=ref_size,
            space_saved=space_saved,
            best_candidate=best_candidate,
            similarity_range=(min_sim, max_sim),
            has_images=has_images,
            resolution_summary=resolution_summary,
            date_range=date_range,
            file_types=file_types,
            marked_count=marked_count,
        )

        # Cache it
        self._summaries_cache[group] = summary
        return summary

    def get_file_metadata(self, file_obj, group) -> FileMetadata:
        """
        Get detailed metadata for a file.
        
        Args:
            file_obj: A file object from the group
            group: The group containing the file
            
        Returns:
            FileMetadata with all display information
        """
        # Check cache
        cache_key = (id(file_obj), id(group))
        if cache_key in self._metadata_cache:
            return self._metadata_cache[cache_key]

        ref = group.ref
        is_reference = (file_obj == ref)
        is_marked = self.results.is_marked(file_obj)

        # Size
        size = file_obj.size
        size_formatted = format_size(size, 0)

        # Dimensions (for images)
        dimensions = self._get_image_dimensions(file_obj)

        # Dates
        modification_date = self._get_modification_date(file_obj)
        creation_date = self._get_creation_date(file_obj)

        # Similarity to reference
        similarity_to_ref = None
        if not is_reference and ref:
            match = group.get_match(ref, file_obj)
            if match:
                similarity_to_ref = match.percentage

        # Folder and file type
        try:
            folder_path = str(file_obj.path.parent)
            file_type = file_obj.path.suffix.lower()
        except (AttributeError, OSError):
            folder_path = ""
            file_type = ""

        metadata = FileMetadata(
            file=file_obj,
            is_reference=is_reference,
            is_marked=is_marked,
            size=size,
            size_formatted=size_formatted,
            dimensions=dimensions,
            modification_date=modification_date,
            creation_date=creation_date,
            similarity_to_ref=similarity_to_ref,
            folder_path=folder_path,
            file_type=file_type,
        )

        # Cache it
        self._metadata_cache[cache_key] = metadata
        return metadata

    def get_all_summaries(self) -> List[GroupSummary]:
        """Get summaries for all groups."""
        summaries = []
        for idx, group in enumerate(self.results.groups):
            summary = self.get_group_summary(group, idx)
            summaries.append(summary)
        return summaries

    # --- Group-level selection helpers ---

    def select_all_except_best(self, group) -> List:
        """
        Mark all files in group except the best candidate.
        
        Args:
            group: A core.engine.Group instance
            
        Returns:
            List of file objects that would be marked
        """
        summary = self.get_group_summary(group, 0)
        to_mark = [d for d in group.dupes if d != summary.best_candidate and not d.is_ref]
        return to_mark

    def keep_newest(self, group) -> List:
        """
        Mark all files except the newest (by modification date).
        
        Args:
            group: A core.engine.Group instance
            
        Returns:
            List of file objects that would be marked
        """
        newest = self._get_file_by_date(group.dupes, newest=True)
        if newest:
            return [d for d in group.dupes if d != newest and not d.is_ref]
        return []

    def keep_oldest(self, group) -> List:
        """
        Mark all files except the oldest (by modification date).
        
        Args:
            group: A core.engine.Group instance
            
        Returns:
            List of file objects that would be marked
        """
        oldest = self._get_file_by_date(group.dupes, newest=False)
        if oldest:
            return [d for d in group.dupes if d != oldest and not d.is_ref]
        return []

    def keep_highest_resolution(self, group) -> List:
        """
        For image groups, mark all except highest resolution.
        
        Args:
            group: A core.engine.Group instance
            
        Returns:
            List of file objects that would be marked
        """
        best = self._get_file_by_resolution(group.dupes)
        if best:
            return [d for d in group.dupes if d != best and not d.is_ref]
        return []

    def keep_largest(self, group) -> List:
        """
        Mark all files except the largest by file size.
        
        Args:
            group: A core.engine.Group instance
            
        Returns:
            List of file objects that would be marked
        """
        largest = max(group.dupes, key=lambda d: d.size)
        return [d for d in group.dupes if d != largest and not d.is_ref]

    def keep_smallest(self, group) -> List:
        """
        Mark all files except the smallest by file size.
        
        Args:
            group: A core.engine.Group instance
            
        Returns:
            List of file objects that would be marked
        """
        smallest = min(group.dupes, key=lambda d: d.size)
        return [d for d in group.dupes if d != smallest and not d.is_ref]

    def clear_cache(self):
        """Clear all cached summaries and metadata."""
        self._summaries_cache.clear()
        self._metadata_cache.clear()

    # --- Private helper methods ---

    def _determine_best_candidate(self, group):
        """
        Determine the best file to keep in a group.
        
        Prioritizes:
        1. Reference file (if explicitly set)
        2. For images: highest resolution
        3. Largest file size
        4. Oldest file (more likely to be original)
        """
        ref = group.ref
        if ref:
            return ref

        dupes = group.dupes
        if not dupes:
            return None

        # Check if this is an image group
        has_images = any(self._is_image_file(d) for d in dupes)

        if has_images:
            # For images, prioritize resolution
            best = self._get_file_by_resolution(dupes)
            if best:
                return best

        # Fall back to largest file
        return max(dupes, key=lambda d: d.size)

    def _get_similarity_range(self, group):
        """Get min and max similarity percentages in group."""
        if not group.matches:
            return (0, 0)

        percentages = [m.percentage for m in group.matches]
        return (min(percentages), max(percentages))

    def _is_image_file(self, file_obj):
        """Check if file is an image."""
        try:
            ext = file_obj.path.suffix.lower()
            return ext in {'.jpg', '.jpeg', '.png', '.gif', '.bmp', '.tiff', '.webp'}
        except (AttributeError, OSError):
            return False

    def _get_resolution_summary(self, group):
        """Get resolution information for image group."""
        resolutions = []
        for d in group.dupes:
            dims = self._get_image_dimensions(d)
            if dims:
                resolutions.append(dims[0] * dims[1])  # Total pixels

        if not resolutions:
            return None

        max_res = max(resolutions)
        min_res = min(resolutions)
        return {
            'max_pixels': max_res,
            'min_pixels': min_res,
            'max_dimensions': self._pixels_to_dimensions(max_res),
            'min_dimensions': self._pixels_to_dimensions(min_res),
        }

    def _get_image_dimensions(self, file_obj):
        """Get (width, height) for image file if available."""
        # Try to get dimensions from file attributes
        if hasattr(file_obj, 'dimensions'):
            return file_obj.dimensions
        
        # For picture edition, check for width/height attributes
        if hasattr(file_obj, 'width') and hasattr(file_obj, 'height'):
            return (file_obj.width, file_obj.height)
        
        return None

    def _pixels_to_dimensions(self, pixels):
        """Convert pixel count to approximate dimensions."""
        # Assume 4:3 aspect ratio as default
        import math
        width = int(math.sqrt(pixels * 4 / 3))
        height = int(pixels / width)
        return (width, height)

    def _get_file_by_resolution(self, files):
        """Get file with highest resolution."""
        best_file = None
        best_pixels = 0

        for f in files:
            dims = self._get_image_dimensions(f)
            if dims:
                pixels = dims[0] * dims[1]
                if pixels > best_pixels:
                    best_pixels = pixels
                    best_file = f

        return best_file

    def _get_date_range(self, files):
        """Get (earliest_date, latest_date) from files."""
        dates = []
        for f in files:
            mtime = self._get_modification_date(f)
            if mtime:
                dates.append(mtime)

        if not dates:
            return (None, None)

        return (min(dates), max(dates))

    def _get_modification_date(self, file_obj):
        """Get file modification date."""
        try:
            mtime = file_obj.mtime
            return datetime.fromtimestamp(mtime)
        except (AttributeError, OSError, TypeError):
            return None

    def _get_creation_date(self, file_obj):
        """Get file creation date if available."""
        # Creation date is not always available on all platforms
        try:
            if hasattr(file_obj, 'ctime'):
                return datetime.fromtimestamp(file_obj.ctime)
        except (AttributeError, OSError, TypeError):
            pass
        return None

    def _get_file_by_date(self, files, newest=True):
        """Get file with newest or oldest modification date."""
        files_with_dates = []
        for f in files:
            mtime = self._get_modification_date(f)
            if mtime:
                files_with_dates.append((f, mtime))

        if not files_with_dates:
            return None

        if newest:
            return max(files_with_dates, key=lambda x: x[1])[0]
        else:
            return min(files_with_dates, key=lambda x: x[1])[0]