#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2019-12-30
# @Filename: metadata.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import configparser
import pathlib

import packaging.version

from ._vendor import toml


try:
    import importlib.metadata as importlib_metadata
except ImportError:
    import importlib_metadata


METADATA_FILES = ['pyproject.toml', 'setup.cfg', 'setup.py']


def get_metadata_files(path):
    """Finds the list of metadata files for a package.

    Returns the path of the ``pyproject.toml``, ``setup.cfg``, or ``setup.py``
    that defines the metadata for the project.

    Parameters
    ----------
    path : str
        The path relative to which to search for metadata files.

    Returns
    -------
    path
        The path to the metadata file, or `None` if none was found.

    """

    path = pathlib.Path(path).absolute()
    if path.is_file():
        path = path.parent

    for mf in METADATA_FILES:
        if (path / mf).exists():
            return str(path / mf)

    # Walk up directories
    for parent in path.parents:
        for mf in METADATA_FILES:
            if (parent / mf).exists():
                return str(parent / mf)

    return None


def get_package_version(path=None, package_name=None, pep_440=False):
    """Returns the version of a package.

    First tries to determine if a metadata file is available and parses it.
    Otherwise, tries to use the egg/wheel information if the package has
    been installed.

    Parameters
    ----------
    path : str
        The path relative to which to search for metadata files.
    package_name : str
        The name of the package.
    pep_440 : bool
        If `True`, normalises the version string according to PEP 440.

    Returns
    -------
    version : str
        The version string, or `None` if it cannot be found.

    """

    assert path or package_name, 'either path or package_name are needed.'

    version = None

    if path:
        metadata_file = get_metadata_files(path)
        if metadata_file:
            if 'pyproject.toml' in str(metadata_file):
                pyproject = toml.load(open(metadata_file))
                if 'tool' in pyproject and 'poetry' in pyproject['tool']:
                    version = pyproject['tool']['poetry']['version']
            elif 'setup.cfg' in str(metadata_file):
                setupcfg = configparser.ConfigParser()
                setupcfg.read(metadata_file)
                if (setupcfg.has_section('metadata') and
                        setupcfg.has_option('metadata', 'version')):
                    version = setupcfg.get('metadata', 'version')

    if package_name and not version:
        try:
            version = importlib_metadata.version(package_name)
        except importlib_metadata.PackageNotFoundError:
            pass

    if version and pep_440:
        version = str(packaging.version.Version(version))

    return version
