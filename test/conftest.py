#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2020-07-29
# @Filename: conftest.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from sdsstools import log


# Disable sdsstools logging since it may interfere with the logger tests.
log.warnings_logger.removeHandler(log.sh)
log.removeHandler(log.sh)
log.sh = None
