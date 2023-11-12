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
import pathlib
import re
import shutil
import sys
import traceback
import warnings
from logging.handlers import TimedRotatingFileHandler

from typing import Any, Dict, List, Optional, Union, cast

from pygments import highlight
from pygments.formatters import TerminalFormatter
from pygments.lexers import get_lexer_by_name
from pythonjsonlogger import jsonlogger
from rich.console import Console
from rich.logging import RichHandler
from rich.text import Text
from rich.theme import Theme

from ._vendor.color_print import color_text


try:
    IPYTHON = get_ipython()  # type: ignore
except NameError:
    IPYTHON = None


__all__ = ["get_logger"]


WARNING_RE = re.compile(r"^.*?\s*?(\w*?Warning): (.*)")


def custom__showtraceback_closure(log):
    def _showtraceback(*args, **kwargs):
        assert IPYTHON

        exc_tuple = IPYTHON._get_exc_info()
        log.handle_exceptions(*exc_tuple)

    if IPYTHON:
        IPYTHON._showtraceback = _showtraceback


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

        self.print_time = False

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
            if self.print_time:
                now = datetime.datetime.now()
                header = color_text(now.strftime("%H:%M:%S "), "lightgrey") + header
        else:
            return logging.Formatter.format(self, record)

        record_cp.msg = "{}{}".format(header, message)

        if levelname == "warning" and record_cp.args and len(record_cp.args) > 0:
            args = cast(List[str], record_cp.args)
            warning_category_groups = WARNING_RE.match(args[0])
            if warning_category_groups is not None:
                wcategory, wtext = warning_category_groups.groups()
                wcategory_colour = color_text("({})".format(wcategory), "cyan")
                message = "{} {}".format(color_text(wtext, ""), wcategory_colour)
                record_cp.args = tuple([message] + list(args[1:]))

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
        args = cast(List[str], record_cp.args)

        # The format of a warnings redirected with warnings.captureWarnings
        # has the format <path>: <category>: message\n  <some-other-stuff>.
        # We reorganise that into a cleaner message. For some reason in this
        # case the message is in record.args instead of in record.msg.
        if (
            record_cp.levelno == logging.WARNING
            and record_cp.args
            and len(record_cp.args) > 0
        ):
            match = re.match(r"^(.*?):\s*?(\w*?Warning): (.*)", args[0])
            if match:
                message = "{1} - {2} [{0}]".format(*match.groups())
                record_cp.args = tuple([message] + list(args[1:]))

        return logging.Formatter.format(self, record_cp)


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """Custom `jsonlogger.JsonFormatter` for the JSON file handler"""

    def add_fields(self, log_record, record, message_dict):
        """Add custom fields to the JSON body"""
        super().add_fields(log_record, record, message_dict)
        if not log_record.get("timestamp"):
            now = datetime.datetime.fromtimestamp(record.created).strftime(
                "%Y-%m-%dT%H:%M:%S.%fZ"
            )  # noqa: E501
            log_record["timestamp"] = now
        log_record["type"] = "log"
        log_record["level"] = record.levelname
        log_record.update(record.__dict__)
        if record.exc_info:
            log_record["error"] = {
                "type": record.exc_info[0].__name__,
                "trace": message_dict["exc_info"],
            }


class CustomRichHandler(RichHandler):
    """A slightly custom ``RichHandler`` logging handler."""

    def get_level_text(self, record):
        """Get the level name from the record."""

        level_name = record.levelname
        level_text = Text.styled(
            f"[{level_name}]".ljust(9),
            f"logging.level.{level_name.lower()}",
        )
        return level_text


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
        use_rich_handler: bool = False,
        log_level: int = logging.INFO,
        capture_exceptions: bool = True,
        capture_warnings: bool = True,
        fmt: Optional[logging.Formatter] = None,
        rich_handler_kwargs={},
    ):
        """Initialise the logger.

        Parameters
        ----------
        use_rich_handler
            If `True`, uses the ``rich`` library ``RichHandler`` for
            console logging.
        log_level
            The initial logging level for the console handler.
        capture_exceptions
            If `True`, overrides the exception hook and redirects all
            exceptions to the logging system.
        capture_warnings
            Whether to capture warnings and redirect them to the log.
        fmt
            The message format to supply to the stream formatter.
        rich_handler_kwargs
            Keyword arguments to pass to the ``RichHandler`` on init.

        """

        self.use_rich_handler = use_rich_handler

        self.warnings_logger = logging.getLogger("py.warnings")

        # Set levels
        self.setLevel(logging.DEBUG)

        # Clear handlers before recreating.
        for handler in self.handlers.copy():
            if handler in self.warnings_logger.handlers:
                self.warnings_logger.removeHandler(handler)
            self.removeHandler(handler)

        # Sets the console handler
        self.rich_console: Console | None = None

        if use_rich_handler:
            self.rich_console = Console(
                theme=Theme(
                    {
                        "logging.level.debug": "magenta",
                        "logging.level.warning": "yellow",
                        "logging.level.critical": "red",
                        "logging.level.error": "red",
                    }
                )
            )

            self.sh = CustomRichHandler(
                level=log_level,
                console=self.rich_console,
                **rich_handler_kwargs,
            )

        else:
            self.sh = logging.StreamHandler()
            if fmt is not None:
                formatter = StreamFormatter(fmt)  # type: ignore
            else:
                formatter = StreamFormatter()
            self.sh.setFormatter(formatter)

        # Catches exceptions
        if capture_exceptions:
            sys.excepthook = self.handle_exceptions

            if IPYTHON:
                # One more override. We want that any exceptions raised in IPython
                # also gets logged to file, but IPython overrides excepthook completely
                # so here we make a custom call to log.handle_exceptions().
                custom__showtraceback_closure(self)

        self.addHandler(self.sh)
        self.sh.setLevel(log_level)

        # Placeholders for the file handlers.
        self.fh: Union[logging.FileHandler, None] = None
        self.log_filename: Union[str, None] = None

        self.jh: Union[logging.FileHandler, None] = None
        self.json_log_filename: Union[str, None] = None

        # A header that precedes every message.
        self.header = ""

        if capture_warnings:
            self.capture_warnings()

    def handle_exceptions(self, exctype, value, tb):
        """Catches all exceptions and logs them."""

        if self.use_rich_handler:
            self.exception("An exeption was raised.", exc_info=(exctype, value, tb))
        else:
            self.error(get_exception_formatted(exctype, value, tb))

    def capture_warnings(self):
        """Capture warnings.

        When `logging.captureWarnings` is `True`, all the warnings are
        redirected to a logger called ``py.warnings``. We add our handlers
        to the warning logger.

        """

        logging.captureWarnings(True)

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
                self.handle_exceptions(exc_type, exc_value, exc_tb)
        else:
            loop.default_exception_handler(context)

    def save_log(self, path: str):
        assert self.log_filename, "File logger not running."
        shutil.copyfile(self.log_filename, os.path.expanduser(path))
        if self.json_log_filename:
            assert self.json_log_filename, "JSON file logger not running."
            shutil.copyfile(self.json_log_filename, os.path.expanduser(path))

    def _set_file_handler(
        self,
        filepath: str,
        suffix: str,
        rotating: bool = True,
        mode: str = "a",
        when: str = "midnight",
        utc: bool = True,
        at_time: Union[str, datetime.time] = None,
    ):
        if rotating:
            fh = TimedRotatingFileHandler(
                str(filepath), when=when, utc=utc, atTime=at_time
            )
            fh.suffix = suffix  # type: ignore
        else:
            fh = logging.FileHandler(str(filepath), mode=mode)
        return fh

    def start_file_logger(
        self,
        path: str,
        log_level: int = logging.DEBUG,
        mode: str = "a",
        rotating: bool = True,
        rollover: bool = False,
        when: str = "midnight",
        utc: bool = True,
        at_time: Union[str, datetime.time] = None,
        as_json: bool = False,
        with_json: bool = False,
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
        when
            The type of time interval.  Allowed values are those from
            `TimedRotatingFileHandler`.
        utc
            If `True`, times in UTC will be used; otherwise local time is used.
        at_time
            The time of day when rollover occurs, when rollover is set to occur
            at “midnight” or “on a particular weekday”.
        as_json
            If `True`, outputs a JSON log instead of a human log
        with_json
            If `True`, outputs both a JSON log and a human log
        """

        log_file_path = os.path.realpath(os.path.expanduser(path))
        logdir = os.path.dirname(log_file_path)

        SUFFIX = "%Y-%m-%d_%H:%M:%S"

        # set the JSON file path name
        suffix = pathlib.Path(log_file_path).suffix
        if as_json and suffix != ".json":
            log_file_path = log_file_path.replace(suffix, ".json")
        elif with_json:
            json_log_file_path = log_file_path.replace(suffix, ".json")

        try:
            if not os.path.exists(logdir):
                os.makedirs(logdir)

            if os.path.exists(log_file_path) and rotating and rollover:
                now = datetime.datetime.utcnow()
                dst = str(log_file_path) + "." + now.strftime(SUFFIX)
                shutil.move(str(log_file_path), dst)

            # convert at_time to a datetime.time
            if at_time and isinstance(at_time, str):
                at_time = datetime.time.fromisoformat(at_time)

            # get the file handler
            self.fh = self._set_file_handler(
                log_file_path,
                SUFFIX,
                mode=mode,
                rotating=rotating,
                when=when,
                utc=utc,
                at_time=at_time,
            )

            if with_json:
                self.jh = self._set_file_handler(
                    json_log_file_path,
                    SUFFIX,
                    mode=mode,
                    rotating=rotating,
                    when=when,
                    utc=utc,
                    at_time=at_time,
                )

        except (IOError, OSError, ValueError) as ee:
            warnings.warn(
                "log file {0!r} could not be opened for "
                "writing: {1}".format(log_file_path, ee),
                RuntimeWarning,
            )

        else:
            # set the correct file or json formatter
            formatter = CustomJsonFormatter() if as_json else FileFormatter()
            self.fh.setFormatter(formatter)
            self.addHandler(self.fh)
            self.fh.setLevel(log_level)

            if self.warnings_logger:
                self.warnings_logger.addHandler(self.fh)

            self.log_filename = log_file_path

            # set json file handler and formatter
            if with_json and self.jh:
                self.jh.setFormatter(CustomJsonFormatter())
                self.addHandler(self.jh)
                self.jh.setLevel(log_level)
                self.json_log_filename = json_log_file_path
                if self.warnings_logger:
                    self.warnings_logger.addHandler(self.jh)

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


def get_logger(
    name,
    use_rich_handler: bool = False,
    log_level: int = logging.INFO,
    capture_exceptions: bool = True,
    capture_warnings: bool = True,
    fmt: Optional[logging.Formatter] = None,
    rich_handler_kwargs: Dict[str, Any] = {},
) -> SDSSLogger:
    """Gets or creates a new SDSS logger.

    Parameters
    ----------
    use_rich_handler
        If `True`, uses as slightly customised``RichHandler`` from
        the ``rich`` library for console logging.
    log_level
        The initial logging level for the console handler.
    capture_exceptions
        If `True`, overrides the exception hook and redirects all
        exceptions to the logging system.
    capture_warnings
        Whether to capture warnings and redirect them to the log.
    fmt
        The message format to supply to the stream formatter.
    rich_handler_kwargs
        Keyword arguments to pass to the ``RichHandler`` on init.
        By default ``{ "log_time_format": "%X", "show_path": False,
        "rich_tracebacks": True}``.

    """

    orig_logger = logging.getLoggerClass()

    logging.setLoggerClass(SDSSLogger)

    default_rich_handler_kwargs = {
        "log_time_format": "%X",
        "show_path": False,
        "rich_tracebacks": True,
        "tracebacks_show_locals": False,
    }
    default_rich_handler_kwargs.update(rich_handler_kwargs)

    log = cast(SDSSLogger, logging.getLogger(name))
    log.init(
        use_rich_handler=use_rich_handler,
        log_level=log_level,
        capture_exceptions=capture_exceptions,
        capture_warnings=capture_warnings,
        fmt=fmt,
        rich_handler_kwargs=default_rich_handler_kwargs,
    )

    logging.setLoggerClass(orig_logger)

    return log
