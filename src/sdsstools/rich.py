#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2026-09-30
# @Filename: rich.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from typing import Literal

from rich.console import Console
from rich.progress import (
    BarColumn,
    MofNCompleteColumn,
    Progress,
    ProgressColumn,
    SpinnerColumn,
    TaskProgressColumn,
    TextColumn,
    TimeElapsedColumn,
    TimeRemainingColumn,
)
from rich.status import Status


__all__ = ["RichMessage", "get_progress_bar", "status"]


TIME_MODE_T = Literal["elapsed", "remaining", "none"]


def get_progress_bar(
    *columns: ProgressColumn,
    console: Console | None = None,
    time_mode: TIME_MODE_T = "elapsed",
    completion_mode: Literal["percentage", "mofn", "none"] = "mofn",
    spinner: bool | str = "dots",
    **kwargs,
) -> Progress:
    """Returns a :class:`rich.progress.Progress` object with the requested columns.

    Parameters
    ----------
    *columns
        Any number of :class:`rich.progress.ProgressColumn` objects to add to the
        progress bar. If provided, the remaining arguments will be ignored.
    console
        A :class:`rich.console.Console` object to use for the progress bar.
        If ``None``, a new console will be created.
    time_mode
        The type of time counter to use for the progress bar. Can be ``"elapsed"``,
        ``"remaining"``, or ``"none"``.
    completion_mode
        Whether to show the completion as a ``'percentage'``, ``'mofn'``, or ``'none'``.
    spinner
        Whether to show a spinner in the progress bar. Can be a spinner name
        (e.g., ``"dots"``, ``"bouncingBar"``, etc.) or ``False`` to disable the spinner.
    kwargs
        Additional keyword arguments to pass to the :class:`rich.progress.Progress`
        constructor.

    """

    if console is None:
        console = Console()

    if spinner is True:
        spinner = "dots"

    if not columns:
        cols: list[ProgressColumn] = [
            TextColumn("[progress.description]{task.description}"),
            BarColumn(),
        ]

        if spinner:
            cols.insert(0, SpinnerColumn(spinner_name=spinner))

        if completion_mode == "percentage":
            cols.append(TaskProgressColumn())
        elif completion_mode == "mofn":
            cols.append(MofNCompleteColumn())
        else:
            pass

        if time_mode == "elapsed":
            cols.append(TimeElapsedColumn())
        elif time_mode == "remaining":
            cols.append(TimeRemainingColumn())
        else:
            pass

        columns = tuple(cols)

    return Progress(*columns, console=console, transient=True, **kwargs)


def status(
    message: str,
    console: Console | None = None,
    spinner: str = "bouncingBar",
    spinner_style="blue",
    speed: float = 1.0,
    refresh_per_second: float = 12.5,
) -> Status:
    """Returns a custom status context manager for the console."""

    if console is None:
        console = Console()

    return console.status(
        message,
        spinner=spinner,
        spinner_style=spinner_style,
        speed=speed,
        refresh_per_second=refresh_per_second,
    )


class RichMessage:
    """A class to print messages to the console using ``rich`` with a uniform format.

    This class is just a thing wrapper around a ``rich.console.Console.print``.
    It provides methods to print messages with different levels of severity
    (info, warning, error) using colored text and uniform formatting.

    Parameters
    ----------
    console
        A :class:`rich.console.Console` object to use for printing messages.
        If ``None``, a new console will be created.
    full_color
        If ``True``, the message will be printed with full color. If ``False``,
        only the prefix will be colored.

    """

    def __init__(self, console: Console | None = None, full_color: bool = False):
        self.console = console or Console()
        self.full_color = full_color

    def info(self, message: str):
        """Prints an info message."""

        self.__print_with_prefix(r"[blue]\[i]", message)

    def warning(self, message: str):
        """Prints a warning message."""

        self.__print_with_prefix("[yellow][!]", message)

    def error(self, message: str):
        """Prints an error message."""

        self.__print_with_prefix("[red][✖]", message)

    def success(self, message: str):
        """Prints a success message."""

        self.__print_with_prefix("[green][✔]", message)

    def __print_with_prefix(self, prefix: str, message: str):
        """Prints a message with a custom prefix."""

        if self.full_color:
            self.console.print(f"{prefix} {message}[/]")
        else:
            self.console.print(f"{prefix}[/] {message}")

    def print(self, message: str):
        """Prints a message with a custom style."""

        self.console.print(f"{message}")
