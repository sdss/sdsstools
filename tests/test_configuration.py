#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2020-07-29
# @Filename: test_configuration.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import copy
import inspect
import io
import multiprocessing
import os
import unittest.mock

import pytest
from yaml import safe_load

from sdsstools import Configuration, get_config
from sdsstools.configuration import DEFAULT_PATHS, read_yaml_file


BASE_CONFIG_FILE = os.path.join(os.path.dirname(__file__), "etc/test.yml")


BASE = """
cat1:
    key1: base_value

cat2:
    key2: 1
"""

EXTENDABLE = """
#

#!extends {base_path}

cat1:
    # test
    key1: value1
"""


@pytest.fixture(autouse=True)
def cleanup():
    yield

    if "TEST_CONFIG_PATH" in os.environ:
        del os.environ["TEST_CONFIG_PATH"]


@pytest.fixture
def config_file(tmp_path):
    content = """
    cat1:
        key1: another_value
    """

    tmp_file = tmp_path / "test_config.yml"
    tmp_file.write_text(content)

    yield tmp_file

    tmp_file.unlink()


@pytest.fixture
def update_default_paths(config_file):
    orig_paths = DEFAULT_PATHS.copy()

    DEFAULT_PATHS[:] = [config_file.parent / "{name}_config"]

    yield

    DEFAULT_PATHS[:] = orig_paths


@pytest.fixture
def set_envvar():
    os.environ["A_TEST_VARIABLE"] = "blah"
    os.environ["ANOTHER_VARIABLE"] = "foo"
    yield
    del os.environ["A_TEST_VARIABLE"]
    del os.environ["ANOTHER_VARIABLE"]


@pytest.fixture
def extendable(tmp_path):
    base_path = tmp_path / "base.yaml"
    base_path.write_text(BASE)

    yield io.StringIO(EXTENDABLE.format(base_path=str(base_path))), base_path


def test_configuration(config_file):
    config = Configuration()
    assert config == {}

    config = Configuration(config_file)
    assert config["cat1"]["key1"] == "another_value"

    config = Configuration(base_config=config_file)
    assert config["cat1"]["key1"] == "another_value"


def test_configuration_user(config_file):
    config = Configuration(config_file, base_config=BASE_CONFIG_FILE)
    assert config["cat1"]["key1"] == "another_value"
    assert config["cat1"]["key2"] == 1


def test_configuration_envvar(set_envvar):
    config = Configuration(BASE_CONFIG_FILE)
    assert config["cat2"]["key4"] == "blah"
    assert config["cat2"]["key5"] == "blah/Downloads/foo"


def test_configuration_envvar_defaults():
    config = Configuration(BASE_CONFIG_FILE, default_envvars={"A_TEST_VARIABLE": "foo"})
    assert config["cat2"]["key4"] == "foo"


def test_configuration_envvar_with_fallback():
    config = Configuration(BASE_CONFIG_FILE)
    assert config["cat2"]["key6"] == "my default value"


def test_configurations_bad_value():
    with pytest.raises(ValueError):
        Configuration(1)  # type: ignore


def test_configuration_dict():
    config = Configuration(
        {"cat1": {"key2": 4}, "key3": 3},
        base_config=BASE_CONFIG_FILE,
    )
    assert config["cat1"]["key1"] == "value"
    assert config["cat1"]["key2"] == 4
    assert config["key3"] == 3


def test_configuration_base_dict():
    config = {"cat1": {"key1": 1}}
    conf = Configuration(base_config=config)

    assert conf._BASE == config
    assert conf._BASE_CONFIG_FILE is None
    assert conf._CONFIG_FILE is None


def test_configuration_user_dict():
    config = Configuration(base_config=BASE_CONFIG_FILE)
    assert config._BASE_CONFIG_FILE == BASE_CONFIG_FILE
    assert config._CONFIG_FILE == BASE_CONFIG_FILE
    assert config.keys() != {}

    config.load({}, use_base=False)
    assert list(config.keys()) == []


def test_configuration_reload(config_file):
    config = Configuration(config_file, base_config=BASE_CONFIG_FILE)
    assert config["cat1"]["key1"] == "another_value"
    assert config["cat1"]["key2"] == 1

    # Modify config_file
    with open(config_file, "w") as f:
        f.write(
            """
cat1:
    key1: new_value
"""
        )

    config.reload()
    assert config["cat1"]["key1"] == "new_value"
    assert config["cat1"]["key2"] == 1


def test_configuration_reload_no_base(config_file):
    config = Configuration(config_file)
    assert config["cat1"]["key1"] == "another_value"

    # Modify config_file
    with open(config_file, "w") as f:
        f.write(
            """
cat1:
    key1: new_value
"""
        )

    config.reload()
    assert config["cat1"]["key1"] == "new_value"


def test_configuration_reload_no_change(config_file):
    config = Configuration(config_file, base_config=safe_load(BASE))
    config.reload()

    assert config["cat1"]["key1"] == "another_value"
    assert config["cat2"]["key2"] == 1

    assert len(config) == 2
    assert len(config["cat1"]) == 1
    assert len(config["cat2"]) == 1


def test_get_config_etc():
    config = get_config("test", allow_user=False)
    assert isinstance(config, Configuration)
    assert config["cat1"]["key1"] == "value"

    config = get_config("test", allow_user=True)
    assert isinstance(config, Configuration)
    assert config["cat1"]["key1"] == "value"


def test_get_config_etc_with_user(config_file):
    config = get_config("test", allow_user=True, user_path=config_file)
    assert isinstance(config, Configuration)
    assert config["cat1"]["key1"] == "another_value"


def test_get_config_etc_with_user_str(config_file):
    config = get_config("test", allow_user=True, user_path=str(config_file))
    assert isinstance(config, Configuration)
    assert config["cat1"]["key1"] == "another_value"


def test_get_config_default_path(update_default_paths):
    config = get_config("test")
    assert config["cat1"]["key1"] == "another_value"


def test_get_config_envvar_path(config_file):
    os.environ["TEST_CONFIG_PATH"] = str(config_file)

    config = get_config("test")
    assert config["cat1"]["key1"] == "another_value"


def test_get_config_no_update(config_file):
    config = get_config(
        "test",
        config_file=BASE_CONFIG_FILE,
        user_path=config_file,
        merge_mode="replace",
    )

    assert config["cat1"]["key1"] == "another_value"
    assert "cat2" not in config


@unittest.mock.patch.object(inspect, "stack", side_effect=AttributeError)
def test_get_config_bad_module(mock_func):
    config = get_config("test")
    assert config == {}


def test_extends(extendable):
    stream, __ = extendable
    data = read_yaml_file(stream)

    assert data["cat1"]["key1"] == "base_value"
    assert "cat2" in data


def test_extends_file_not_found(extendable):
    stream, base_path = extendable
    base_path.unlink()

    with pytest.raises(FileExistsError):
        read_yaml_file(stream)


def test_dont_extend(extendable):
    stream, __ = extendable
    data = read_yaml_file(stream, use_extends=False)

    assert data["cat1"]["key1"] == "value1"
    assert "cat2" not in data


def test_extends_from_file(tmp_path):
    base_path = tmp_path / "subdir" / "base.yaml"
    (tmp_path / "subdir").mkdir()
    base_path.touch()
    base_path.write_text(BASE)

    extendable_path = tmp_path / "extendable.yaml"
    extendable_relative = EXTENDABLE.format(base_path="subdir/base.yaml")
    extendable_path.write_text(extendable_relative)

    data = read_yaml_file(extendable_path)

    assert data["cat1"]["key1"] == "base_value"
    assert "cat2" in data


def test_read_empty_yaml(tmp_path):
    path = tmp_path / "base.yaml"
    path.touch()

    data = read_yaml_file(path)

    assert data == {}


def test_configuration_copy():
    config = {"cat1": {"key1": 1}}
    conf = Configuration(base_config=config)

    copy1 = conf.copy()
    assert isinstance(copy1, Configuration)
    assert copy1["cat1"] != conf["key1"]

    copy2 = copy.copy(conf)
    assert isinstance(copy2, Configuration)
    assert copy2["cat1"] != conf["key1"]

    copy3 = copy.deepcopy(conf)
    assert isinstance(copy3, Configuration)
    assert copy3["cat1"] != conf["key1"]


def test_configuration_recursive_getitem():
    config = {"cat1": {"key1": 1}}
    conf = Configuration(base_config=config)

    assert conf["cat1.key1"] == 1
    assert conf["cat1.key2"] is None


def test_configuration_recursive_getitem_strict():
    config = {"cat1": {"key1": 1}}
    conf = Configuration(base_config=config)

    conf.strict_mode = True

    assert conf["cat1"]["key1"] == 1

    with pytest.raises(KeyError):
        conf["cat1.key2"]

    conf.strict_mode = False

    assert conf.get("cat1.key1", strict=True) is None


def test_configuration_recursive_get():
    config = {"cat1": {"key1": 1}}
    conf = Configuration(base_config=config)

    assert conf.get("cat1.key1") == 1
    assert conf.get("cat1.key2") is None
    assert conf.get("cat1.key2", default=-1) == -1
    assert conf.get("cat1.key1.a1", default=-1) == -1


def test_configuration_recursive_inherits():
    config = {"cat1": {"key1": 1}}
    conf = Configuration(base_config=config)

    assert isinstance(conf["cat1"], Configuration)
    assert isinstance(conf["cat1.key1"], int)


def test_configuration_assignment():
    config = {"cat1": {"key1": {"subkey1": 1}}}
    conf = Configuration(base_config=config)

    conf["cat1"]["key1"] = {"subkey2": 2}

    assert conf == {"cat1": {"key1": {"subkey2": 2}}}
    assert isinstance(conf["cat1"]["key1"], Configuration)


def test_configuration_assignment_dot():
    config = {"cat1": {"key1": {"subkey1": 1}}}
    conf = Configuration(base_config=config)

    conf["cat1.key1"] = {"subkey2": 2}
    assert len(conf) == 2
    assert conf["cat1.key1"] == {"subkey2": 2}


def _process(config):
    assert config["cat1"]["key1"] == "another_value"


def test_configuration_with_multiprocessing(config_file):
    config = Configuration(config_file)
    config.propagate_type = False
    with multiprocessing.Pool(2) as pool:
        pool.apply(_process, (config,))
