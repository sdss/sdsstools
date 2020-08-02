#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2019-05-08
# @Filename: configuration.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import inspect
import itertools
import os
import pathlib
import re

import yaml


__all__ = ['read_yaml_file', 'merge_config', 'get_config', 'Configuration']


__ENVVARS__ = {}

# Potential paths where the user configuration file could be. Must not include
# the yml or yaml extension.
DEFAULT_PATHS = ['~/.config/sdss/{name}',
                 '~/.config/sdss/{name}/{name}',
                 '~/.{name}/{name}']

env_matcher = re.compile(r'\$\{([^}^{]+)\}')


def env_constructor(loader, node):
    """Extract the matched value, expand env variable, and replace the match."""

    value = node.value
    match = env_matcher.match(value)
    env_var = match.group()[2:-1]

    return os.environ.get(env_var, __ENVVARS__.get(env_var, value)) + value[match.end():]


yaml.add_implicit_resolver('!env', env_matcher)
yaml.add_constructor('!env', env_constructor)


def read_yaml_file(path, use_extends=True, loader=yaml.FullLoader):
    """Read a YAML file and returns a dictionary."""

    if isinstance(path, (str, pathlib.Path)):
        fp = open(path, 'r')
    else:
        fp = path

    fp.seek(0)
    config = yaml.load(fp, Loader=loader)

    if use_extends:
        fp.seek(0)
        while True:
            line = fp.readline()
            if line.strip().startswith('#!extends'):
                base_file = line.strip().split()[1]
                if not os.path.isabs(base_file) and hasattr(fp, 'buffer'):
                    base_file = os.path.join(os.path.dirname(path), base_file)
                if not os.path.exists(base_file):
                    raise FileExistsError(f'cannot find !extends file {base_file}.')
                return merge_config(read_yaml_file(base_file),
                                    read_yaml_file(path, use_extends=False))
            elif line.strip().startswith('#') or line.strip() == '':
                continue
            else:
                fp.seek(0)
                break

    return config


def merge_config(user, default):
    """Merges a user configuration with the default one."""

    if isinstance(user, dict) and isinstance(default, dict):
        for kk, vv in default.items():
            if kk not in user:
                user[kk] = vv
            else:
                user[kk] = merge_config(user[kk], vv)

    return user


def get_config(name, config_file=None, allow_user=True, user_path=None,
               config_envvar=None, merge_mode='update', default_envvars={}):
    """Returns a configuration dictionary.

    The configuration dictionary is created by merging the default
    configuration file that is part of the library (normally in
    ``etc/<name>.yml``) with a user configuration file. The path to the user
    configuration file can be defined as an environment variable to be passed
    to this function in ``config_envvar`` or as a path in ``user_path``.
    The environment variable, if exists, always takes precedence.

    Parameters
    ----------
    name : str
        The name of the package.
    config_file : str
        The path to the configuration file. If `None`, defaults to
        ``etc/<name>.yml`` relative to the file that called `.get_config`.
    allow_user : bool
        If `True`, looks for an user configuration file and merges is to the
        default configuration. Otherwise it returns just the default
        configuration.
    user_path : str
        The path to the user configuration file. Defaults to
        ``~/.config/sdss/<name>/<name>.yml``. Ignored if the file does not
        exist.
    config_envvar : str
        The environment variable that contains the path to the user
        configuration file. Defaults to ``<name>_CONFIG_PATH``. If the
        environment variable exists, the ``user_path`` is ignored.
    merge_mode : str
        Defines how the default and user dictionaries will be merged. If
        ``update``, the user dictionary will be used to update the default
        configuration. If ``replace``, only the user configuration will be
        returned.
    default_envvars : dict
        Default values for environment variables used in the configuration
        file.

    Returns
    -------
    .Configuration
        A `.Configuration` instance.

    """

    assert merge_mode in ['update', 'replace'], 'invalid merge mode.'

    if not config_file:
        try:
            frame = inspect.stack()[1]
            module = inspect.getmodule(frame[0])
            dirname = os.path.dirname(module.__file__)
            config_file = os.path.join(dirname, f'etc/{name}.yml')
        except AttributeError:
            config_file = None

    if allow_user is False:
        return Configuration(base_config=config_file,
                             default_envvars=default_envvars)

    config_envvar = config_envvar or '{}_CONFIG_PATH'.format(name.upper())

    if user_path is not None:
        user_path = os.path.expanduser(os.path.expandvars(user_path))
        assert os.path.exists(user_path), f'User path {user_path!r} not found.'
    else:
        # Test a few default paths and exit when finds one.
        extensions = ['.yaml', '.yml']
        for path, extension in itertools.product(DEFAULT_PATHS, extensions):
            path = str(path).format(name=name)
            test_path = os.path.expanduser(path + extension)
            if os.path.exists(test_path):
                user_path = test_path
                break

    if config_envvar in os.environ:
        custom_config_fn = os.environ[config_envvar]
    elif user_path and os.path.exists(user_path):
        custom_config_fn = user_path
    else:
        custom_config_fn = None

    if merge_mode == 'update':
        return Configuration(custom_config_fn, base_config=config_file,
                             default_envvars=default_envvars)
    else:
        return Configuration(custom_config_fn, base_config=None,
                             default_envvars=default_envvars)


class Configuration(dict):
    """A configuration class.

    Parameters
    ----------
    config : str or dict
        The path to the configuration file or the already parsed configuration
        as a dictionary.
    base_config : str or dict
        A base configuration or file that the input configuration will update.
    default_envvars : dict
        Default values for environment variables used in the configuration
        file.

    """

    def __init__(self, config=None, base_config=None, default_envvars={}):

        global __ENVVARS__

        super().__init__()

        if base_config:
            self._BASE = self._parse_config(base_config, use_base=False)
        else:
            self._BASE = {}

        self.CONFIG_FILE = None

        __ENVVARS__ = default_envvars

        self.load(config)

    def _parse_config(self, config, use_base=True):
        """Parses the configuration and merges it with the base one."""

        if use_base is False or self._BASE is None:

            if isinstance(config, dict):
                return config
            elif isinstance(config, (str, pathlib.Path)):
                return read_yaml_file(config)
            else:
                raise ValueError('Invalid config of type {}'.format(type(config)))

        return merge_config(self._parse_config(config, use_base=False), self._BASE)

    def load(self, config=None):
        """Loads a configuration file.

        Parameters
        ----------
        config : str or dict
            The configuration file or dictionary to load. If a base
            configuration was defined when the object was instantiated, it
            will be merged. If ``config=None``, the object will revert to the
            base configuration.

        """

        if config is None:
            config = {}
            self.CONFIG_FILE = None

        super().__init__(self._parse_config(config))

        # Save name of the configuration file (if the input is a file).
        if isinstance(config, (str, pathlib.Path)):
            self.CONFIG_FILE = str(config)
