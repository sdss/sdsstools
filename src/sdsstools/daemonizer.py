#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2020-08-06
# @Filename: daemonizer.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import asyncio
import inspect
import signal
import sys
from functools import partial, wraps

import click
from click.decorators import pass_context
from daemonocle import Daemon


__all__ = ['cli_coro', 'DaemonGroup']


def cli_coro(signals=(signal.SIGHUP, signal.SIGTERM, signal.SIGINT),
             shutdown_func=None):
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
@click.option('--debug', is_flag=True,
              help='Do NOT detach and run in the background.')
@click.option('--log', type=str,
              help='Redirects stdout and stderr to a file (append mode).')
@pass_context
def start(ctx, debug, log):
    """Start the daemon."""

    # We want to make sure that the Starting <name> ... OK is still output
    # to stdout. We override the worker so that the first thing it does is to
    # create the log and redirect stdout and stderr there. Then call the
    # original worker.

    if log:  # pragma: no cover
        orig_worker = ctx.parent.command.daemon.worker

        def new_worker():
            f = open(log, 'a')
            sys.stdout = f
            sys.stderr = f
            orig_worker()

        ctx.parent.command.daemon.worker = new_worker

    if debug:
        ctx.parent.command.daemon.worker()
    else:
        ctx.parent.command.daemon.do_action('start')


@click.command()
@pass_context
def stop(ctx):
    """Stop the daemon."""

    ctx.parent.command.daemon.do_action('stop')


@click.command()
@pass_context
def restart(ctx):
    """Restart the daemon."""

    ctx.parent.command.daemon.do_action('restart')


@click.command()
@pass_context
def status(ctx):
    """Report if the daemon is running."""

    ctx.parent.command.daemon.do_action('status')


class DaemonGroup(click.Group):
    """A Click Group class to create and manage a daemonocle daemon.

    When used with ``@click.group`` it provides a Click group with commands
    ``start``, ``stop``, ``restart``, and ``status``

    """

    def __init__(self, *args, callback=None, **kwargs):

        if 'prog' not in kwargs:
            raise RuntimeError('Daemon prog not defined.')

        prog = kwargs.pop('prog')

        # Here kwargs are the parameters in the @click.group decorator.
        pidfile = kwargs.pop('pidfile', f'/var/tmp/{prog}.pid')

        daemon_params = {}
        signature = inspect.signature(Daemon).parameters
        for param in kwargs.copy():
            if param in signature:
                daemon_params.update({param: kwargs.pop(param)})

        self.daemon = Daemon(pidfile=pidfile, **daemon_params)

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
        return ['start', 'stop', 'restart', 'status']

    def get_command(self, ctx, name):
        """Get a callable command object."""

        if name not in Daemon.list_actions():
            return None

        # Assign the daemon worker as the partial of the group callback
        # with the parameters received (these are the parameters of the
        # group, not of the command).
        self.daemon.worker = partial(self.group_cb, **ctx.params)

        return self.commands[name]
