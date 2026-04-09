# Copyright 2024 dupeGuru Web Team
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import logging
from PIL import Image
from hscommon.trans import tr
from core.engine import Match
import math

def _get_histogram(path):
    with Image.open(str(path)) as img:
        if img.mode != 'RGB':
            img = img.convert('RGB')
        return img.histogram()

def correlation(h1, h2):
    if len(h1) != len(h2):
        return 0
    mu1 = sum(h1) / len(h1)
    mu2 = sum(h2) / len(h2)
    s1 = sum((x - mu1)**2 for x in h1)
    s2 = sum((x - mu2)**2 for x in h2)
    if s1 == 0 or s2 == 0:
        return 0
    num = sum((x - mu1) * (y - mu2) for x, y in zip(h1, h2))
    return num / math.sqrt(s1 * s2)

def getmatches(files, threshold, j):
    histograms = {}
    for f in j.iter_with_progress(files, tr("Analyzing histograms % d/%d")):
        try:
            histograms[f] = _get_histogram(f.path)
        except Exception as e:
            logging.warning(f"Could not analyze histogram for {f.path}: {e}")

    matches = []
    file_list = list(histograms.keys())
    for i in range(len(file_list)):
        for k in range(i + 1, len(file_list)):
            f1, f2 = file_list[i], file_list[k]
            corr = correlation(histograms[f1], histograms[f2])
            percentage = int(corr * 100)
            if percentage >= threshold:
                matches.append(Match(f1, f2, percentage))
    return matches
