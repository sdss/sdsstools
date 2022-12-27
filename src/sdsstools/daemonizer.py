#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2020-08-06
# @Filename: daemonizer.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import asyncio
import inspect
import os
import signal
import subprocess
import sys
from datetime import datetime
from functools import partial, wraps
from shutil import move

from typing import Any, Callable, Optional, Union

import click
from click.decorators import pass_context
from daemonocle import Daemon


__all__ = ["cli_coro", "DaemonGroup"]


def cli_coro(
    signals=(signal.SIGHUP, signal.SIGTERM, signal.SIGINT),
    shutdown_func=None,
):
    """Decorator function that allows defining coroutines with click."""

    def decorator_cli_coro(f):
        @wraps(f)
        def wrapper(*args, **kwargs):
            loop = asyncio.get_event_loop()
            if shutdown_func:
                for ss in signals:
                    loop.add_signal_handler(ss, shutdown_func, ss, loop)
            return loop.run_until_complete(f(*args, **kwargs))

        return wrapper

    return decorator_cli_coro


@click.command()
@click.option(
    "--debug",
    is_flag=True,
    help="Do NOT detach and run in the background.",
)
@click.option(
    "--log-file",
    type=str,
    help="Redirects stdout and stderr to a file (rotates logs). Ignored if --debug.",
)
@click.option(
    "--pid_file", type=str, help="PID file to keep track of the daemon execution."
)
@pass_context
def start(ctx, debug, log_file, pid_file):
    """Start the daemon."""

    # We want to make sure that the Starting <name> ... OK is still output
    # to stdout. We override the worker so that the first thing it does is to
    # create the log and redirect stdout and stderr there. Then call the
    # original worker.

    if pid_file:
        ctx.parent.command.pid_file = pid_file

    log_file = log_file or ctx.parent.command.log_file

    if log_file and debug is False:  # pragma: no cover
        orig_worker = ctx.parent.command.daemon.worker

        log_file = os.path.realpath(os.path.expanduser(os.path.expandvars(log_file)))
        if os.path.exists(log_file):
            date = datetime.now()
            suffix = date.strftime(".%Y-%m-%d_%H:%M:%S")
            move(log_file, log_file + suffix)

        os.makedirs(os.path.dirname(log_file), exist_ok=True)

        def new_worker():
            f = open(log_file, "w")
            sys.stdout = f
            sys.stderr = f
            orig_worker()

        ctx.parent.command.daemon.worker = new_worker

    if debug:
        ctx.parent.command.daemon.worker()
    else:
        ctx.parent.command.daemon.do_action("start")


@click.command()
@pass_context
def stop(ctx):
    """Stop the daemon."""

    ctx.parent.command.daemon.do_action("stop")


@click.command()
@pass_context
def restart(ctx):
    """Restart the daemon."""

    ctx.parent.command.daemon.do_action("restart")


@click.command()
@pass_context
def status(ctx):
    """Report if the daemon is running."""

    ctx.parent.command.daemon.do_action("status")


class DaemonGroup(click.Group):
    """A Click Group class to create and manage a daemonocle daemon.

    When used with ``@click.group`` it provides a Click group with commands
    ``start``, ``stop``, ``restart``, and ``status``
    """

    def __init__(
        self,
        *args,
        callback: Union[Callable[[Any], Any], None] = None,
        log_file: Optional[str] = None,
        **kwargs,
    ):
        if "prog" not in kwargs:
            raise RuntimeError("Daemon prog not defined.")

        prog = kwargs.pop("prog")

        # Here kwargs are the parameters in the @click.group decorator.
        # pidfile is deprecated in Daemon and instead we should use pid_file, but some
        # code already use pidfile so let's support both but not at the same time.
        if "pidfile" in kwargs and "pid_file" in kwargs:
            raise RuntimeError("pid_file and pidfile are mutually exclusive.")

        base_pidfile = f"/var/tmp/{prog}.pid"
        if "pid_file" in kwargs:
            pid_file = kwargs.pop("pid_file", base_pidfile)
        elif "pidfile" in kwargs:
            pid_file = kwargs.pop("pidfile", base_pidfile)
        else:
            pid_file = base_pidfile

        daemon_params = {}
        signature = inspect.signature(Daemon).parameters
        for param in kwargs.copy():
            if param in signature and param != "name":
                daemon_params.update({param: kwargs.pop(param)})

        self.log_file = log_file

        self.daemon = Daemon(pid_file=pid_file, **daemon_params)

        # Callback is the function that @click.group decorates. What we
        # do is store it because it will become the worker for the daemon,
        # but then set it to none because we don't want the code in the group
        # function to be executed outside the daemon.
        self.group_cb = callback
        callback = None

        self.ignore_unknown_options = True
        super().__init__(*args, callback=callback, **kwargs)

        self.add_command(start)
        self.add_command(stop)
        self.add_command(restart)
        self.add_command(status)

    def list_commands(self, ctx):
        """Get a list of subcommands."""
        return ["start", "stop", "restart", "status"]

    def get_command(self, ctx, name):
        """Get a callable command object."""

        if name not in Daemon.list_actions():
            return None

        # Assign the daemon worker as the partial of the group callback
        # with the parameters received (these are the parameters of the
        # group, not of the command).
        assert self.group_cb
        self.daemon.worker = partial(self.group_cb, **ctx.params)

        return self.commands[name]


@click.command()
@click.argument(
    "ACTION",
    type=click.Choice(
        [
            "start",
            "stop",
            "restart",
            "status",
            "debug",
        ]
    ),
)
@click.argument("NAME", type=str)
@click.argument("COMMAND", type=str, nargs=-1, required=False)
@click.option(
    "--log-file",
    type=click.Path(dir_okay=False),
    help="Redirects stdout and stderr to a file (rotates logs). Ignored if --debug.",
)
def daemonize(
    action: str,
    name: str,
    command: Union[str, None] = None,
    log_file: Union[str, None] = None,
):  # pragma: no cover
    """Executes a command as a daemon.

    Runs a COMMAND as a detached daemon assigning it a given NAME. The daemon can
    be stopped by calling daemonize stop NAME or its status checked with
    daemonize status NAME.

    If --log-file is used, a rotating log file with the STDOUT and STDERR of the
    worker subprocess will be generated. If STATUS is "debug", runs the worker
    subprocess without detaching.

    """

    def worker():
        if command is None:
            return

        if log_file:
            path = os.path.realpath(os.path.expanduser(os.path.expandvars(log_file)))
            if os.path.exists(path):
                date = datetime.now()
                suffix = date.strftime(".%Y-%m-%d_%H:%M:%S")
                move(path, path + suffix)

            os.makedirs(os.path.dirname(path), exist_ok=True)

            f = open(log_file, "w")
            sys.stdout = f
            sys.stderr = f

        subprocess.run(
            " ".join(command),
            shell=True,
            capture_output=False,
            cwd=os.getcwd(),
        )

    pid_file = f"/var/tmp/{name}.pid"

    if action == "debug":
        log_file = None
        worker()
    else:
        daemon = Daemon(
            worker=worker,
            pid_file=pid_file,
            work_dir=os.getcwd(),
        )
        daemon.do_action(action)
