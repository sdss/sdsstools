#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2020-08-01
# @Filename: test_metadata.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from sdsstools import get_metadata_files, get_package_version


def test_get_metadata_files(tmp_path):
    package_path = tmp_path / "src" / "package"
    package_path.mkdir(parents=True)

    init_path = package_path / "__init__.py"

    assert get_metadata_files(init_path) is None

    (tmp_path / "setup.py").touch()
    assert get_metadata_files(package_path) == str(tmp_path / "setup.py")
    assert get_metadata_files(tmp_path) == str(tmp_path / "setup.py")
    assert get_metadata_files(init_path) == str(tmp_path / "setup.py")

    (tmp_path / "setup.cfg").touch()
    assert get_metadata_files(init_path) == str(tmp_path / "setup.cfg")

    (tmp_path / "pyproject.toml").touch()
    assert get_metadata_files(init_path) == str(tmp_path / "pyproject.toml")


def test_get_package_version_path(tmp_path):
    package_path = tmp_path / "src" / "package"
    package_path.mkdir(parents=True)

    init_path = package_path / "__init__.py"

    assert get_package_version(path=init_path) is None

    setup_cfg = tmp_path / "setup.cfg"
    setup_cfg.touch()

    assert get_package_version(path=init_path) is None

    setup_cfg.write_text(
        """
[metadata]
name = test-package
version = 0.4.6-alpha.0
"""
    )

    assert get_package_version(path=init_path) == "0.4.6-alpha.0"
    assert get_package_version(path=init_path, pep_440=True) == "0.4.6a0"

    pyproject = tmp_path / "pyproject.toml"
    pyproject.write_text(
        """
[tool.poetry]
name = "sdsstools"
version = "0.2.2"
"""
    )

    assert get_package_version(path=init_path) == "0.2.2"


def test_get_package_version_name():
    assert get_package_version(package_name="click") is not None

    assert get_package_version(package_name="non-existing-package") is None
