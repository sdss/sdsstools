#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2023-11-09
# @Filename: __init__.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import sys

from .metadata import get_package_version


__version__ = get_package_version(path=__file__, package_name="sdsstools")

NAME = "sdsstools"


from ._vendor import color_print, toml
from .configuration import *
from .logger import *
from .metadata import *
from .time import get_sjd


# This is a hack to allow doing from sdsstools.color_print import color_text
# which some code already does.
sys.modules["sdsstools.color_print"] = color_print
