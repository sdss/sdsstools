#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2017-10-11
# @Filename: logger.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import copy
import datetime
import logging
import os
import re
import shutil
import sys
import traceback
import warnings
from logging.handlers import TimedRotatingFileHandler

from typing import Optional, Union, cast

from pygments import highlight
from pygments.formatters import TerminalFormatter  # type: ignore
from pygments.lexers import get_lexer_by_name

from ._vendor.color_print import color_text


__all__ = ["get_logger"]


WARNING_RE = re.compile(r"^.*?\s*?(\w*?Warning): (.*)")


def get_exception_formatted(tp, value, tb):
    """Adds colours to tracebacks."""

    tbtext = "".join(traceback.format_exception(tp, value, tb))
    lexer = get_lexer_by_name("pytb", stripall=True)
    formatter = TerminalFormatter()
    return highlight(tbtext, lexer, formatter)


class StreamFormatter(logging.Formatter):
    """Custom `Formatter <logging.Formatter>` for the stream handler."""

    base_fmt = "%(message)s"

    def __init__(self, fmt=base_fmt):
        logging.Formatter.__init__(self, fmt)

    def format(self, record):

        colours = {
            "info": "blue",
            "debug": "magenta",
            "warning": "yellow",
            "critical": "red",
            "error": "red",
        }

        record_cp = copy.copy(record)

        levelname = record_cp.levelname.lower()
        message = record_cp.msg

        if levelname.lower() in colours:
            level_colour = colours[levelname]
            header = color_text("[{}]: ".format(levelname.upper()), level_colour)
        else:
            return logging.Formatter.format(self, record)

        record_cp.msg = "{}{}".format(header, message)

        if levelname == "warning" and len(record_cp.args) > 0:
            warning_category_groups = WARNING_RE.match(record_cp.args[0])
            if warning_category_groups is not None:
                wcategory, wtext = warning_category_groups.groups()
                wcategory_colour = color_text("({})".format(wcategory), "cyan")
                message = "{} {}".format(color_text(wtext, ""), wcategory_colour)
                record_cp.args = tuple([message] + list(record_cp.args[1:]))

        return logging.Formatter.format(self, record_cp)


class FileFormatter(logging.Formatter):
    """Custom `Formatter <logging.Formatter>` for the file handler."""

    base_fmt = "%(asctime)s - %(levelname)s - %(message)s"
    ansi_escape = re.compile(r"\x1b[^m]*m")

    def __init__(self, fmt=base_fmt):
        logging.Formatter.__init__(self, fmt)

    def format(self, record):

        # Copy the record so that any modifications we make do not
        # affect how the record is displayed in other handlers.
        record_cp = copy.copy(record)

        record_cp.msg = self.ansi_escape.sub("", record_cp.msg)

        # The format of a warnings redirected with warnings.captureWarnings
        # has the format <path>: <category>: message\n  <some-other-stuff>.
        # We reorganise that into a cleaner message. For some reason in this
        # case the message is in record.args instead of in record.msg.
        if record_cp.levelno == logging.WARNING and len(record_cp.args) > 0:
            match = re.match(r"^(.*?):\s*?(\w*?Warning): (.*)", record_cp.args[0])
            if match:
                message = "{1} - {2} [{0}]".format(*match.groups())
                record_cp.args = tuple([message] + list(record_cp.args[1:]))

        return logging.Formatter.format(self, record_cp)


class SDSSLogger(logging.Logger):
    """Custom logging system.

    Parameters
    ----------
    name : str
        The name of the logger.
    """

    def __init__(self, name: str):

        # Placeholder for the last error-level message emitted.
        self._last_error = None

        super(SDSSLogger, self).__init__(name)

    def init(
        self,
        log_level: int = logging.INFO,
        capture_warnings: bool = True,
        fmt: Optional = None,
    ):
        """Initialise the logger.

        Parameters
        ----------
        log_level
            The initial logging level for the console handler.
        capture_warnings
            Whether to capture warnings and redirect them to the log.
        fmt
            The message format to supply to the stream formatter.
        """

        # Set levels
        self.setLevel(logging.DEBUG)

        # Sets the console handler
        self.sh = logging.StreamHandler()
        if fmt is not None:
            formatter = StreamFormatter(fmt)
        else:
            formatter = StreamFormatter()
        self.sh.setFormatter(formatter)
        self.addHandler(self.sh)
        self.sh.setLevel(log_level)

        # Placeholders for the file handler.
        self.fh: Union[logging.FileHandler, None] = None
        self.log_filename: Union[str, None] = None

        # A header that precedes every message.
        self.header = ""

        # Catches exceptions
        sys.excepthook = self._catch_exceptions

        self.warnings_logger: Optional[logging.Logger] = None

        if capture_warnings:
            self.capture_warnings()

    def _catch_exceptions(self, exctype, value, tb):
        """Catches all exceptions and logs them."""

        self.error(get_exception_formatted(exctype, value, tb))

    def capture_warnings(self):
        """Capture warnings.

        When `logging.captureWarnings` is `True`, all the warnings are
        redirected to a logger called ``py.warnings``. We add our handlers
        to the warning logger.

        """

        logging.captureWarnings(True)

        self.warnings_logger = logging.getLogger("py.warnings")

        # Only enable the sh handler if none is attached to the warnings
        # logger yet. Prevents duplicated prints of the warnings.
        for handler in self.warnings_logger.handlers:
            if isinstance(handler, logging.StreamHandler):
                return

        self.warnings_logger.addHandler(self.sh)

    def asyncio_exception_handler(self, loop, context):
        """Handle an uncaught asyncio exception and reports it."""

        exception = context.get("exception", None)

        if exception:
            try:
                raise exception
            except Exception:
                exc_type, exc_value, exc_tb = sys.exc_info()
                self.error(get_exception_formatted(exc_type, exc_value, exc_tb))
        else:
            loop.default_exception_handler(context)

    def save_log(self, path: str):
        assert self.log_filename, "File logger not running."
        shutil.copyfile(self.log_filename, os.path.expanduser(path))

    def start_file_logger(
        self,
        path: str,
        log_level: int = logging.DEBUG,
        mode: str = "a",
        rotating: bool = True,
        rollover: bool = False,
    ):
        """Start file logging.

        Parameters
        ----------
        path
            Path to which to log.
        log_level
            Logging level for the file handler.
        mode
            File mode.
        rotating
            If `True`, rotates the file logger at midnight UTC. Otherwise uses a
            standard `~logging.FileHandler`.
        rollover
            If `True` and ``rotating=True` and the log file already exists, does a
            rollover before starting to log.
        """

        log_file_path = os.path.realpath(os.path.expanduser(path))
        logdir = os.path.dirname(log_file_path)

        SUFFIX = "%Y-%m-%d_%H:%M:%S"

        try:

            if not os.path.exists(logdir):
                os.makedirs(logdir)

            if os.path.exists(log_file_path) and rotating and rollover:
                now = datetime.datetime.utcnow()
                dst = str(log_file_path) + "." + now.strftime(SUFFIX)
                shutil.move(str(log_file_path), dst)

            if rotating:
                self.fh = TimedRotatingFileHandler(
                    str(log_file_path), when="midnight", utc=True
                )
                self.fh.suffix = SUFFIX  # type: ignore
            else:
                self.fh = logging.FileHandler(str(log_file_path), mode=mode)

        except (IOError, OSError) as ee:

            warnings.warn(
                "log file {0!r} could not be opened for "
                "writing: {1}".format(log_file_path, ee),
                RuntimeWarning,
            )

        else:

            self.fh.setFormatter(FileFormatter())
            self.addHandler(self.fh)
            self.fh.setLevel(log_level)

            if self.warnings_logger:
                self.warnings_logger.addHandler(self.fh)

            self.log_filename = log_file_path

    def handle(self, record):
        """Handles a record but first stores it."""

        if hasattr(self, "header") and self.header is not None:
            if not isinstance(record.msg, Exception):
                record.msg = self.header + record.msg

        if record.levelno == logging.ERROR:
            self._last_error = record.getMessage()

        return super().handle(record)

    def get_last_error(self):
        """Returns the last error emitted."""

        return self._last_error

    def set_level(self, level):
        """Sets levels for both sh and (if initialised) fh."""

        self.sh.setLevel(level)

        if self.fh:
            self.fh.setLevel(level)

        if self.warnings_logger:
            for handler in self.warnings_logger.handlers:
                handler.setLevel(level)


def get_logger(name, **kwargs) -> SDSSLogger:
    """Gets or creates a new SDSS logger."""

    orig_logger = logging.getLoggerClass()

    logging.setLoggerClass(SDSSLogger)

    if name in logging.Logger.manager.loggerDict:  # type: ignore
        log = cast(SDSSLogger, logging.getLogger(name))
    else:
        log = cast(SDSSLogger, logging.getLogger(name))
        log.init(**kwargs)

    logging.setLoggerClass(orig_logger)

    return log
