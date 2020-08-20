#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2020-08-01
# @Filename: test_logger.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import asyncio
import logging
import logging.handlers
import os
import uuid
import warnings

import pytest

from sdsstools import get_logger
from sdsstools.logger import get_exception_formatted


@pytest.fixture
def logger_no_fh():

    _logger = get_logger(str(uuid.uuid4()))

    yield _logger

    handlers = _logger.warnings_logger.handlers
    for handler in handlers:
        _logger.warnings_logger.removeHandler(handler)


@pytest.fixture
def logger(tmp_path, logger_no_fh):

    log_file = tmp_path / 'logs' / 'test_log.log'
    logger_no_fh.start_file_logger(log_file)

    yield logger_no_fh

    handlers = logger_no_fh.warnings_logger.handlers
    for handler in handlers:
        logger_no_fh.warnings_logger.removeHandler(handler)


def test_logger(logger, caplog):

    assert len(logger.handlers) == 2

    logger.debug('DEBUG')
    logger.info('INFO')
    logger.warning('WARNING')
    logger.error('ERROR')

    assert caplog.record_tuples == [(logger.name, logging.DEBUG, 'DEBUG'),
                                    (logger.name, logging.INFO, 'INFO'),
                                    (logger.name, logging.WARNING, 'WARNING'),
                                    (logger.name, logging.ERROR, 'ERROR')]

    assert logger.fh is not None
    assert isinstance(logger.fh, logging.handlers.TimedRotatingFileHandler)
    assert logger.log_filename is not None
    assert len(open(str(logger.log_filename), 'r').read().splitlines()) == 4

    assert len(logger.get_last_error()) is not None


def test_set_level(caplog, logger):

    logger.set_level(logging.ERROR)

    with caplog.at_level(logging.ERROR):
        logger.info('INFO')

    assert len(caplog.records) == 0
    assert len(open(str(logger.log_filename), 'r').read().splitlines()) == 0


def test_warning_raised(logger):

    with pytest.warns(UserWarning):
        warnings.warn('A warning', UserWarning)


def test_warning(logger, caplog):

    warnings.warn('A warning', UserWarning)

    assert len(logger.warnings_logger.handlers) == 2
    assert logger.warnings_logger.handlers[0] == logger.handlers[0]

    assert 'A warning' in caplog.messages[0]
    assert len(open(str(logger.log_filename), 'r').read().splitlines()) == 1


def test_exception_formatting(logger):

    with pytest.raises(ValueError) as excinfo:
        raise ValueError('An error')

    exc_text = get_exception_formatted(excinfo.type, excinfo.value, excinfo.tb)

    assert exc_text is not None
    assert 'An error' in exc_text
    assert '\x1b[91mValueError\x1b[39;49;00m' in exc_text


def test_catch_exception(logger, caplog):

    with pytest.raises(ValueError) as excinfo:
        raise ValueError('An error')

    logger._catch_exceptions(excinfo.type, excinfo.value, excinfo.tb)

    assert caplog.record_tuples[0][1] == logging.ERROR


def test_save_log(logger):

    logger.info('INFO')

    dest = os.path.dirname(logger.log_filename) + '/../copied_log.log'
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

    logger_no_fh.start_file_logger(tmp_path / 'no_rotating.log', rotating=False)
    assert isinstance(logger_no_fh.fh, logging.FileHandler)


def test_log_non_standard_level(logger, caplog):

    logger.log(170, 'A log message')

    assert caplog.record_tuples == [(logger.name, 170, 'A log message')]


@pytest.mark.asyncio
async def test_asyncio_exception_handler(logger, caplog, event_loop):

    async def coro_raise():
        raise ValueError('An error in a task.')

    event_loop.set_exception_handler(logger.asyncio_exception_handler)

    event_loop.create_task(coro_raise())

    await asyncio.sleep(0.01)

    assert caplog.record_tuples[0][1] == logging.ERROR
    assert 'An error in a task.' in caplog.record_tuples[0][2]
