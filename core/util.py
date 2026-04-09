# Copyright 2016 Hardcoded Software (http://www.hardcoded.net)
#
# This software is licensed under the "GPLv3" License as described in the "LICENSE" file,
# which should be included with this package. The terms are also available at
# http://www.gnu.org/licenses/gpl-3.0.html

import time
import sys
import os
import os
from typing import Union

from hscommon.util import format_time_decimal


def format_timestamp(t, delta):
    if delta:
        return format_time_decimal(t)
    else:
        if t > 0:
            return time.strftime("%Y/%m/%d %H:%M:%S", time.localtime(t))
        else:
            return "---"


def format_words(w):
    def do_format(w):
        if isinstance(w, list):
            return "(%s)" % ", ".join(do_format(item) for item in w)
        else:
            return w.replace("\n", " ")

    return ", ".join(do_format(item) for item in w)


def format_perc(p):
    return "%0.0f" % p


def format_dupe_count(c):
    return str(c) if c else "---"




