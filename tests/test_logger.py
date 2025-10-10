#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2020-08-01
# @Filename: test_logger.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import asyncio
import json
import logging
import logging.handlers
import os
import sys
import uuid
import warnings

import pytest
from rich.logging import RichHandler

from sdsstools import get_logger
from sdsstools.logger import get_exception_formatted


@pytest.fixture
def logger_no_fh():
    _logger = get_logger(str(uuid.uuid4()))

    yield _logger

    assert _logger.warnings_logger

    handlers = _logger.warnings_logger.handlers
    for handler in handlers:
        _logger.warnings_logger.removeHandler(handler)


@pytest.fixture
def logger(tmp_path, logger_no_fh):
    log_file = tmp_path / "logs" / "test_log.log"
    logger_no_fh.start_file_logger(log_file)

    yield logger_no_fh

    handlers = logger_no_fh.warnings_logger.handlers
    for handler in handlers:
        logger_no_fh.warnings_logger.removeHandler(handler)


def test_logger(logger, caplog):
    assert len(logger.handlers) == 2

    logger.debug("DEBUG")
    logger.info("INFO")
    logger.warning("WARNING")
    logger.error("ERROR")

    assert caplog.record_tuples == [
        (logger.name, logging.DEBUG, "DEBUG"),
        (logger.name, logging.INFO, "INFO"),
        (logger.name, logging.WARNING, "WARNING"),
        (logger.name, logging.ERROR, "ERROR"),
    ]

    assert logger.fh is not None
    assert isinstance(logger.fh, logging.handlers.TimedRotatingFileHandler)
    assert logger.log_filename is not None
    assert len(open(str(logger.log_filename), "r").read().splitlines()) == 4

    assert len(logger.get_last_error()) is not None


def test_set_level(caplog, logger):
    logger.set_level(logging.ERROR)

    with caplog.at_level(logging.ERROR):
        logger.info("INFO")

    assert len(caplog.records) == 0
    assert len(open(str(logger.log_filename), "r").read().splitlines()) == 0


def test_warning_raised(logger):
    with pytest.warns(UserWarning):
        warnings.warn("A warning", UserWarning)


def test_warning(logger, caplog):
    warnings.warn("A warning", UserWarning)

    assert len(logger.warnings_logger.handlers) == 2
    assert logger.warnings_logger.handlers[0] == logger.handlers[0]

    assert "A warning" in caplog.messages[0]

    nlines = 1 if sys.version_info.minor < 11 else 3
    assert len(open(str(logger.log_filename), "r").read().splitlines()) == nlines


def test_exception_formatting(logger):
    with pytest.raises(ValueError) as excinfo:
        raise ValueError("An error")

    exc_text = get_exception_formatted(excinfo.type, excinfo.value, excinfo.tb)

    assert exc_text is not None
    assert "An error" in exc_text
    assert "\x1b[91mValueError\x1b[39;49;00m" in exc_text


def test_catch_exception(logger, caplog):
    with pytest.raises(ValueError) as excinfo:
        raise ValueError("An error")

    logger.handle_exceptions(excinfo.type, excinfo.value, excinfo.tb)

    assert caplog.record_tuples[0][1] == logging.ERROR


def test_save_log(logger):
    logger.info("INFO")

    dest = os.path.dirname(logger.log_filename) + "/../copied_log.log"
    logger.save_log(dest)

    assert os.path.exists(dest)


def test_get_logger_twice(logger):
    logger2 = get_logger(logger.name)

    assert logger == logger2


def test_bad_fh_path(logger_no_fh, tmp_path):
    bad_path = str(tmp_path)

    with pytest.warns(RuntimeWarning):
        logger_no_fh.start_file_logger(bad_path)

    assert logger_no_fh.fh is None


def test_fh_no_rotating(logger_no_fh, tmp_path):
    logger_no_fh.start_file_logger(tmp_path / "no_rotating.log", rotating=False)
    assert isinstance(logger_no_fh.fh, logging.FileHandler)


def test_log_non_standard_level(logger, caplog):
    logger.log(170, "A log message")

    assert caplog.record_tuples == [(logger.name, 170, "A log message")]


@pytest.mark.asyncio
async def test_asyncio_exception_handler(logger, caplog):
    async def coro_raise():
        raise ValueError("An error in a task.")

    event_loop = asyncio.get_event_loop()
    event_loop.set_exception_handler(logger.asyncio_exception_handler)

    asyncio.create_task(coro_raise())

    await asyncio.sleep(0.01)

    assert caplog.record_tuples[0][1] == logging.ERROR
    assert "An error in a task." in caplog.record_tuples[0][2]


def test_logger_rotating_rollover(tmp_path):
    log_file = tmp_path / "logs" / "test_log.log"

    logger1 = get_logger(str(uuid.uuid4()))
    logger1.start_file_logger(log_file)

    assert len(list((tmp_path / "logs").glob("*"))) == 1

    logger2 = get_logger(str(uuid.uuid4()))
    logger2.start_file_logger(log_file, rollover=True)

    assert len(list((tmp_path / "logs").glob("*"))) == 2


def test_logger_when_options(tmp_path):
    log_file = tmp_path / "logs" / "test_log.log"

    logger1 = get_logger(str(uuid.uuid4()))
    logger1.start_file_logger(log_file, utc=False, when="M")

    assert logger1.fh.when == "M"
    assert logger1.fh.utc is False


def test_rich_handler_logger(caplog):
    log = get_logger("test", use_rich_handler=True)

    assert isinstance(log.sh, RichHandler)
    assert len(log.handlers) == 1

    log.info("Testing")

    assert "Testing" in caplog.record_tuples[0][2]


def test_catch_exception_rich_logger(tmp_path, mocker):
    logger = get_logger("test", use_rich_handler=True)

    log_file = tmp_path / "logs" / "test_log.log"
    logger.start_file_logger(log_file)

    assert logger.fh

    emit_mock = mocker.MagicMock()
    logger.fh.emit = emit_mock

    with pytest.raises(ValueError) as excinfo:
        raise ValueError("An error")

    logger.handle_exceptions(excinfo.type, excinfo.value, excinfo.tb)
    emit_mock.assert_called()


def test_as_json_logger(tmp_path):
    log_file = tmp_path / "logs" / "test_log.log"

    logger1 = get_logger(str(uuid.uuid4()))
    logger1.start_file_logger(log_file, as_json=True)
    logger1.info("test message")

    files = list((tmp_path / "logs").glob("*"))
    assert len(files) == 1
    assert files[0].name.endswith(".json")
    assert not files[0].name.endswith(".log")

    with open(str(log_file).replace(".log", ".json")) as f:
        data = [json.loads(i) for i in f.readlines()]
        assert len(data) == 1
        assert data[0]["message"] == "test message"


def test_with_json_logger(tmp_path):
    log_file = tmp_path / "logs" / "test_log.log"

    logger1 = get_logger(str(uuid.uuid4()))
    logger1.start_file_logger(log_file, with_json=True)
    logger1.info("test message")

    files = list(sorted((tmp_path / "logs").glob("*")))
    assert len(files) == 2
    assert files[0].name.endswith(".json")
    assert files[1].name.endswith(".log")
