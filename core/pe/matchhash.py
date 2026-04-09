# Copyright 2024 dupeGuru Web Team
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import logging
from PIL import Image
import imagehash
from hscommon.trans import tr
from core.engine import Match

def _get_matches_general(files, hash_func, threshold, j):
    hashes = {}
    for f in j.iter_with_progress(files, tr("Hashing %d/%d pictures")):
        try:
            with Image.open(str(f.path)) as img:
                hashes[f] = hash_func(img)
        except Exception as e:
            logging.warning(f"Could not hash {f.path}: {e}")

    matches = []
    file_list = list(hashes.keys())
    for i in range(len(file_list)):
        for k in range(i + 1, len(file_list)):
            f1, f2 = file_list[i], file_list[k]
            distance = hashes[f1] - hashes[f2]
            # Standard 64-bit hash
            percentage = int((1 - (distance / 64.0)) * 100)
            if percentage >= threshold:
                matches.append(Match(f1, f2, percentage))
    return matches

def getmatches_phash(files, threshold, j):
    return _get_matches_general(files, imagehash.phash, threshold, j)

def getmatches_dhash(files, threshold, j):
    return _get_matches_general(files, imagehash.dhash, threshold, j)

def getmatches_ahash(files, threshold, j):
    return _get_matches_general(files, imagehash.whash, threshold, j) # whash is often preferred over ahash
