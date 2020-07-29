#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2019-12-30
# @Filename: cli.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import os

import yaml

from sdsstools import __version__
from sdsstools.metadata import get_metadata_files


def main():
    """Invokes the tasks defined in _tasks.py, with some configuration."""

    try:
        from invoke import Collection, Program  # isort:skip
        from sdsstools import _tasks            # isort:skip
    except (ImportError, ModuleNotFoundError):
        raise ImportError('Cannot find invoke. Make sure sdsstools '
                          'is installed for development.')

    # Use the metadata file to determine the root of the package.
    metadata_file = get_metadata_files('.')
    if metadata_file is None:
        raise RuntimeError('cannot find the root of the package.')

    os.chdir(os.path.dirname(metadata_file))

    # Override the configuration if there is an invoke.yaml file next to the
    # metadata file.
    if os.path.exists('./invoke.yaml'):
        config = yaml.safe_load(open('invoke.yaml'))
        print('Using configuration file invoke.yaml')
    else:
        config = None

    program = Program(version=__version__,
                      namespace=Collection.from_module(_tasks, config=config))
    program.run()


if __name__ == '__main__':

    main()
