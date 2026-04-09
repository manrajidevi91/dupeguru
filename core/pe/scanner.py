# Copyright 2016 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

from hscommon.trans import tr

from core.scanner import Scanner, ScanType, ScanOption

from core.pe import matchblock, matchexif, matchhash, matchhistogram


class ScannerPE(Scanner):
    cache_path = None
    match_scaled = False
    match_rotated = False

    @staticmethod
    def get_scan_options():
        return [
            ScanOption(ScanType.FUZZYBLOCK, tr("Fuzzy Block")),
            ScanOption(ScanType.PHASH, tr("Perceptual Hash")),
            ScanOption(ScanType.DHASH, tr("Difference Hash")),
            ScanOption(ScanType.AHASH, tr("Average Hash")),
            ScanOption(ScanType.HISTOGRAM, tr("Histogram Comparison")),
            ScanOption(ScanType.EXIFTIMESTAMP, tr("EXIF Timestamp")),
            ScanOption(ScanType.CONTENTS, tr("Contents")),
        ]

    def _getmatches(self, files, j):
        if self.scan_type == ScanType.FUZZYBLOCK:
            return matchblock.getmatches(
                files,
                cache_path=self.cache_path,
                threshold=self.min_match_percentage,
                match_scaled=self.match_scaled,
                match_rotated=self.match_rotated,
                j=j,
            )
        elif self.scan_type == ScanType.PHASH:
            return matchhash.getmatches_phash(files, self.min_match_percentage, j)
        elif self.scan_type == ScanType.DHASH:
            return matchhash.getmatches_dhash(files, self.min_match_percentage, j)
        elif self.scan_type == ScanType.AHASH:
            return matchhash.getmatches_ahash(files, self.min_match_percentage, j)
        elif self.scan_type == ScanType.HISTOGRAM:
            return matchhistogram.getmatches(files, self.min_match_percentage, j)
        elif self.scan_type == ScanType.EXIFTIMESTAMP:
            return matchexif.getmatches(files, self.match_scaled, j)
        elif self.scan_type == ScanType.CONTENTS:
            return super()._getmatches(files, j)
        else:
            raise ValueError(f"Invalid scan type: {self.scan_type}")
