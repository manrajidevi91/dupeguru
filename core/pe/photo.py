# Copyright 2016 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import logging
from PIL import Image
from hscommon.util import get_file_ext, format_size
from core.pe._block import getblocks2

from core.util import format_timestamp, format_perc, format_dupe_count
from core import fs
from core.pe import exif

class Photo(fs.File):
    INITIAL_INFO = fs.File.INITIAL_INFO.copy()
    INITIAL_INFO.update({"dimensions": (0, 0), "exif_timestamp": ""})
    __slots__ = fs.File.__slots__ + tuple(INITIAL_INFO.keys())

    # These extensions are supported on all platforms
    HANDLED_EXTS = {"png", "jpg", "jpeg", "gif", "bmp", "tiff", "tif", "webp"}

    def _plat_get_dimensions(self):
        try:
            with Image.open(str(self.path)) as img:
                return img.size
        except Exception:
            return (0, 0)

    def _plat_get_blocks(self, block_count_per_side, orientation):
        try:
            with Image.open(str(self.path)) as img:
                # dupeGuru expects RGB for p-hashing
                if img.mode != 'RGB':
                    img = img.convert('RGB')
                
                # Apply orientation transforms if needed
                # orientations 1-8 are EXIF orientations
                if orientation == 2: # Flip Horizontal
                    img = img.transpose(Image.FLIP_LEFT_RIGHT)
                elif orientation == 3: # Rotate 180
                    img = img.transpose(Image.ROTATE_180)
                elif orientation == 4: # Flip Vertical
                    img = img.transpose(Image.FLIP_TOP_BOTTOM)
                elif orientation == 5: # Transpose (Flip H + Rotate 270)
                    img = img.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_270)
                elif orientation == 6: # Rotate 270
                    img = img.transpose(Image.ROTATE_270)
                elif orientation == 7: # Transverse (Flip H + Rotate 90)
                    img = img.transpose(Image.FLIP_LEFT_RIGHT).transpose(Image.ROTATE_90)
                elif orientation == 8: # Rotate 90
                    img = img.transpose(Image.ROTATE_90)
                
                return getblocks2(img, block_count_per_side)
        except Exception as e:
            logging.warning(f"Error getting blocks for {self.path}: {e}")
            return []

    def get_orientation(self):
        if not hasattr(self, "_cached_orientation"):
            try:
                with self.path.open("rb") as fp:
                    exifdata = exif.get_fields(fp)
                    orientations = exifdata.get("Orientation", [1])
                    self._cached_orientation = orientations[0]
            except Exception:
                self._cached_orientation = 1
        return self._cached_orientation

    def _get_exif_timestamp(self):
        try:
            with self.path.open("rb") as fp:
                exifdata = exif.get_fields(fp)
                return exifdata.get("DateTimeOriginal", "")
        except Exception:
            logging.info("Couldn't read EXIF of picture: %s", self.path)
        return ""

    @classmethod
    def can_handle(cls, path):
        return fs.File.can_handle(path) and get_file_ext(path.name).lower().lstrip('.') in cls.HANDLED_EXTS

    def get_display_info(self, group, delta):
        size = self.size
        mtime = self.mtime
        dimensions = self.dimensions
        m = group.get_match_of(self)
        if m:
            percentage = m.percentage
            dupe_count = 0
            if delta:
                r = group.ref
                size -= r.size
                mtime -= r.mtime
                # dimensions = get_delta_dimensions(dimensions, r.dimensions)
        else:
            percentage = group.percentage
            dupe_count = len(group.dupes)
        dupe_folder_path = getattr(self, "display_folder_path", self.folder_path)
        return {
            "name": self.name,
            "folder_path": str(dupe_folder_path),
            "size": format_size(size, 0, 1, False),
            "extension": self.extension,
            "dimensions": f"{dimensions[0]} x {dimensions[1]}",
            "exif_timestamp": self.exif_timestamp,
            "mtime": format_timestamp(mtime, delta and m),
            "percentage": format_perc(percentage),
            "dupe_count": format_dupe_count(dupe_count),
        }

    def _read_info(self, field):
        fs.File._read_info(self, field)
        if field == "dimensions":
            self.dimensions = self._plat_get_dimensions()
            if self.get_orientation() in {5, 6, 7, 8}:
                self.dimensions = (self.dimensions[1], self.dimensions[0])
        elif field == "exif_timestamp":
            self.exif_timestamp = self._get_exif_timestamp()

    def get_blocks(self, block_count_per_side, orientation: int = None):
        if orientation is None:
            return self._plat_get_blocks(block_count_per_side, self.get_orientation())
        else:
            return self._plat_get_blocks(block_count_per_side, orientation)

# Set the class directly
PLAT_SPECIFIC_PHOTO_CLASS = Photo
PhotoFile = Photo # Alias for app.py
