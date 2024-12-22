#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-04-25
# @Filename: test_time.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import datetime
import os
import socket

import pytest

from sdsstools.time import get_sjd


@pytest.mark.parametrize("observatory", ["APO", "LCO"])
def test_get_sjd(observatory):
    assert isinstance(get_sjd(observatory), int)


def test_get_sjd_fails():
    with pytest.raises(ValueError):
        get_sjd("KPNO")


def test_get_sjd_with_date():
    dt = datetime.datetime(2022, 4, 25, 11, 27, 51, 30690)
    assert get_sjd("APO", date=dt) == 59694


def test_get_sjd_envvar(monkeypatch):
    monkeypatch.setenv("OBSERVATORY", "APO")

    dt = datetime.datetime(2022, 4, 25, 11, 27, 51, 30690)
    assert get_sjd(date=dt) == 59694


@pytest.mark.parametrize("fqdn", ["sdss5-hub.apo.nmsu.edu", "sdss5-hub.lco.cl"])
def test_get_sjd_fqdn(mocker, monkeypatch, fqdn):
    if "OBSERVATORY" in os.environ:
        monkeypatch.delenv("OBSERVATORY")

    mocker.patch.object(socket, "getfqdn", return_value=fqdn)

    dt = datetime.datetime(2022, 4, 25, 11, 27, 51, 30690)
    assert get_sjd(date=dt) == 59694


def test_get_sjd_fqdn_fails(mocker, monkeypatch):
    if "OBSERVATORY" in os.environ:
        monkeypatch.delenv("OBSERVATORY")

    mocker.patch.object(socket, "getfqdn", return_value="somewhere.at.edu")

    with pytest.raises(ValueError):
        get_sjd()

    with pytest.warns(UserWarning):
        get_sjd(raise_error=False)
