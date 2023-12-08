#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2020-08-01
# @Filename: test_vendor.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import pathlib

from sdsstools import yanny
from sdsstools._vendor.color_print import color_text


def test_color_print():
    assert callable(color_text)


def test_yanny():
    yy = yanny(str(pathlib.Path(__file__).parent / "etc/confSummaryF-145.par"))

    assert yy is not None
    assert yy["configuration_id"] == "145"
    assert len(yy["FIBERMAP"]) == 33
