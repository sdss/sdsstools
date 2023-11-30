#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2019-05-08
# @Filename: configuration.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import inspect
import itertools
import os
import pathlib
import re
from copy import deepcopy

from typing import Any, Dict, Optional, Type, TypeVar, Union

import yaml
from typing_extensions import Self


__all__ = ["read_yaml_file", "merge_config", "get_config", "Configuration"]


__ENVVARS__ = {}

# Potential paths where the user configuration file could be. Must not include
# the yml or yaml extension.
DEFAULT_PATHS = [
    "~/.config/sdss/{name}",
    "~/.config/sdss/{name}/{name}",
    "~/.{name}/{name}",
]

env_matcher = re.compile(r"\$\{(.+?)\}")


def env_constructor(loader, node):
    """Extract the matched value, expand env variable, and replace the match."""

    value = node.value
    match = env_matcher.findall(value)
    assert match

    for matched_value in match:
        default_env_var = __ENVVARS__.get(matched_value, "${" + matched_value + "}")
        env_var = os.environ.get(matched_value, default_env_var)
        value = value.replace("${" + matched_value + "}", env_var)

    return value


yaml.add_implicit_resolver("!env", env_matcher)
yaml.add_constructor("!env", env_constructor)


ConfigType = Dict[str, Any]
AnyPath = Union[str, pathlib.Path]


def merge_config(user: ConfigType, default: ConfigType) -> ConfigType:
    """Merges a user configuration with the default one."""

    if isinstance(user, dict) and isinstance(default, dict):
        for kk, vv in default.items():
            if kk not in user:
                user[kk] = vv
            else:
                user[kk] = merge_config(user[kk], vv)

    return user


def get_config(
    name: str,
    config_file: Optional[AnyPath] = None,
    allow_user: bool = True,
    user_path: Optional[AnyPath] = None,
    config_envvar: Optional[str] = None,
    merge_mode: str = "update",
    default_envvars: Dict[str, Any] = {},
) -> "Configuration":
    """Returns a configuration dictionary.

    The configuration dictionary is created by merging the default
    configuration file that is part of the library (normally in
    ``etc/<name>.yml``) with a user configuration file. The path to the user
    configuration file can be defined as an environment variable to be passed
    to this function in ``config_envvar`` or as a path in ``user_path``.
    The environment variable, if exists, always takes precedence.

    Parameters
    ----------
    name
        The name of the package.
    config_file
        The path to the configuration file. If `None`, defaults to
        ``etc/<name>.yml`` relative to the file that called `.get_config`.
    allow_user
        If `True`, looks for an user configuration file and merges is to the
        default configuration. Otherwise it returns just the default
        configuration.
    user_path
        The path to the user configuration file. Defaults to
        ``~/.config/sdss/<name>/<name>.yml``. Ignored if the file does not
        exist.
    config_envvar
        The environment variable that contains the path to the user
        configuration file. Defaults to ``<name>_CONFIG_PATH``. If the
        environment variable exists, the ``user_path`` is ignored.
    merge_mode
        Defines how the default and user dictionaries will be merged. If
        ``update``, the user dictionary will be used to update the default
        configuration. If ``replace``, only the user configuration will be
        returned.
    default_envvars
        Default values for environment variables used in the configuration
        file.

    Returns
    -------
    Configuration
        A `.Configuration` instance.
    """

    assert merge_mode in ["update", "replace"], "invalid merge mode."

    if not config_file:
        try:
            frame = inspect.stack()[1]
            module = inspect.getmodule(frame[0])
            assert module is not None and module.__file__ is not None
            dirname = os.path.dirname(module.__file__)
            config_file = os.path.join(dirname, f"etc/{name}.yml")
        except AttributeError:
            config_file = None

    if allow_user is False:
        return Configuration(base_config=config_file, default_envvars=default_envvars)

    config_envvar = config_envvar or "{}_CONFIG_PATH".format(name.upper())

    if user_path is not None:
        user_path = os.path.expanduser(os.path.expandvars(str(user_path)))
        assert os.path.exists(user_path), f"User path {user_path!r} not found."
    else:
        # Test a few default paths and exit when finds one.
        extensions = [".yaml", ".yml"]
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

    if merge_mode == "update":
        return Configuration(
            custom_config_fn,
            base_config=config_file,
            default_envvars=default_envvars,
        )
    else:
        return Configuration(
            custom_config_fn,
            base_config=None,
            default_envvars=default_envvars,
        )


class RecursiveDict(Dict[str, Any]):
    """A dictionary in which ``__getitem__`` and ``get`` behave recursively.

    This subclass of ``dict`` behaves like a normal dictionary but ``.get()``
    has been overridden to behave recursively. ``__getitem__`` points to
    ``.get()`` with ``default=None``. For example ::

        >> dd = RecursiveDict({'a': {'b': 1}})
        >> dd['a.b']
        1
        >> dd['a.c']
        None
        >> dd.get('a.c', default=-1)
        -1

    Parameters
    ----------
    value
        The initial value of the dictionary.
    strict_mode
        When set to `True`, the objects essentially behaves like a normal
        dictionary.

    """

    def __init__(self, value: dict[str, Any] = {}, strict_mode: bool = False):
        self.strict_mode = strict_mode

        dict.__init__(self, value)

    def __getitem__(self, __key: str) -> Any:
        if self.strict_mode:
            return super().__getitem__(__key)

        return self.get(__key)

    def get(self, __key: str, default: Any = None, strict: bool | None = None) -> Any:
        if (strict is None and self.strict_mode is True) or strict is True:
            return dict.get(self, __key, default)

        current = dict(self)
        for item in __key.split("."):
            if isinstance(current, dict):
                current = current.get(item, default)
            else:
                return default

        if isinstance(current, dict):
            current = self.__class__(current, strict_mode=self.strict_mode)

        return current


class Configuration(RecursiveDict):
    """A configuration class.

    Parameters
    ----------
    config
        The path to the configuration file or the already parsed configuration
        as a dictionary.
    base_config
        A base configuration or file that the input configuration will update.
    default_envvars
        Default values for environment variables used in the configuration
        file.
    strict_mode
        See `.RecursiveDict`.

    """

    def __init__(
        self,
        config: Optional[Union[AnyPath, ConfigType]] = None,
        base_config: Optional[Union[AnyPath, ConfigType]] = None,
        default_envvars: Dict[str, Any] = {},
        strict_mode: bool = False,
    ):
        global __ENVVARS__

        self.strict_mode = strict_mode

        self._BASE: dict[str, Any] = {}
        self._CONFIG: dict[str, Any] = {}

        self._BASE_CONFIG_FILE: AnyPath | None = None
        self._CONFIG_FILE: AnyPath | None = None

        if base_config:
            self._BASE = self._parse_config(base_config, use_base=False)
            if isinstance(base_config, dict):
                self._BASE_CONFIG_FILE = None
            else:
                self._BASE_CONFIG_FILE = os.path.realpath(str(base_config))
        else:
            self._BASE = {}
            self._BASE_CONFIG_FILE = None

        if isinstance(config, dict):
            self._CONFIG = config
        else:
            self._CONFIG_FILE = config

        __ENVVARS__ = default_envvars

        self.load(config)

    def copy(self):
        return deepcopy(self)

    def __copy__(self):
        return deepcopy(self)

    def _parse_config(self, config, use_base=True):
        """Parses the configuration and merges it with the base one."""

        if use_base is False or self._BASE is None:
            if isinstance(config, dict):
                return config
            elif isinstance(config, (str, pathlib.Path)):
                return read_yaml_file(config)
            else:
                raise ValueError("Invalid config of type {}".format(type(config)))

        return merge_config(self._parse_config(config, use_base=False), self._BASE)

    def load(self, config: Optional[Union[AnyPath, ConfigType]] = None, use_base=True):
        """Loads a configuration file.

        Parameters
        ----------
        config
            The configuration file or dictionary to load. If a base
            configuration was defined when the object was instantiated, it
            will be merged. If ``config=None``, the object will revert to the
            base configuration.
        use_base
            Merge the new configuration with the base config.

        """

        self.clear()

        if config is None:
            super().__init__(self._BASE, strict_mode=self.strict_mode)
            self._CONFIG_FILE = self._BASE_CONFIG_FILE
            return

        super().__init__(
            self._parse_config(config, use_base=use_base),
            strict_mode=self.strict_mode,
        )

        # Save name of the configuration file (if the input is a file).
        if isinstance(config, (str, pathlib.Path)):
            self._CONFIG_FILE = str(config)
        else:
            self._CONFIG_FILE = None

    def reload(self) -> Self:
        """Reloads the configuration.

        This will only have an effect if the configuration has been loaded from
        files, in which case the files will be read again.

        """

        if self._BASE_CONFIG_FILE is not None:
            self._BASE = self._parse_config(self._BASE_CONFIG_FILE, use_base=False)

        self.load(self._CONFIG_FILE or dict(self))

        return self


ReturnClass = TypeVar("ReturnClass", bound=dict)


def read_yaml_file(
    path: AnyPath,
    use_extends: bool = True,
    loader: Any = yaml.FullLoader,
    return_class: Type[ReturnClass] = Configuration,
) -> ReturnClass:
    """Read a YAML file and returns a dictionary."""

    if isinstance(path, (str, pathlib.Path)):
        fp = open(path, "r")
    else:
        fp = path

    fp.seek(0)
    config: Union[ConfigType, None] = yaml.load(fp, Loader=loader)

    if config is None or config == {}:
        return return_class({})

    if use_extends:
        fp.seek(0)
        for line in fp.readlines():
            if line.strip().startswith("#!extends"):
                base_file = line.strip().split()[1]
                if not os.path.isabs(base_file) and hasattr(fp, "buffer"):
                    base_file = os.path.join(os.path.dirname(str(path)), base_file)
                if not os.path.exists(base_file):
                    raise FileExistsError(f"cannot find !extends file {base_file}.")

                base = read_yaml_file(base_file, use_extends=False, return_class=dict)
                new_config = merge_config(base, config)
                return return_class(new_config)

            elif line.strip().startswith("#") or line.strip() == "":
                continue

    return return_class(config)
