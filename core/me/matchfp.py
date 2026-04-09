# Copyright 2024 dupeGuru Web Team
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import logging
try:
    import acoustid
except ImportError:
    acoustid = None

from hscommon.trans import tr
from core.engine import Match

def get_fingerprint(path):
    if acoustid is None:
        return None
    try:
        # returns (duration, fingerprint)
        return acoustid.fingerprint_file(str(path))
    except Exception as e:
        logging.warning(f"Acoustid fingerprint error for {path}: {e}")
        return None

def compare_fingerprints(fp1, fp2):
    # This is a very simplified comparison. 
    # Proper chromaprint comparison is complex.
    # We'll use a simple set intersection of the component integers.
    if not fp1 or not fp2:
        return 0
    # fp is typically a byte array or base64. acoustid returns a bytes object.
    # Here we treat it as a sequence of parts.
    s1 = set(fp1[1])
    s2 = set(fp2[1])
    if not s1 or not s2:
        return 0
    intersection = s1.intersection(s2)
    return (len(intersection) * 2.0) / (len(s1) + len(s2))

def getmatches(files, threshold, j):
    if acoustid is None:
        logging.error("pyacoustid not installed. Skipping audio fingerprinting.")
        return []

    fingerprints = {}
    for f in j.iter_with_progress(files, tr("Fingerprinting %d/%d music files")):
        fp = get_fingerprint(f.path)
        if fp:
            fingerprints[f] = fp

    matches = []
    file_list = list(fingerprints.keys())
    for i in range(len(file_list)):
        for k in range(i + 1, len(file_list)):
            f1, f2 = file_list[i], file_list[k]
            sim = compare_fingerprints(fingerprints[f1], fingerprints[f2])
            percentage = int(sim * 100)
            if percentage >= threshold:
                matches.append(Match(f1, f2, percentage))
    return matches
