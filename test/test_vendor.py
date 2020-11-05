#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2020-08-01
# @Filename: test_vendor.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)


def test_color_print():

    from sdsstools.color_print import color_text

    assert callable(color_text)


def test_releases():

    import sdsstools.releases

    assert sdsstools.releases is not None
