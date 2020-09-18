#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2020-09-17
# @Filename: utils.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import time


class Timer:
    """Convenience context manager to time events.

    Modified from https://bit.ly/3ebdp3y.

    """

    def __enter__(self):
        self.start = time.time()
        self.end = None
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start

    @property
    def elapsed(self):

        if self.end:
            return self.interval

        return time.time() - self.start
