#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2020-08-06
# @Filename: daemonizer.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import asyncio
import inspect
from functools import partial, wraps

import click
from click.decorators import pass_context
from daemonocle import Daemon


def cli_coro(f):
    """Decorator function that allows defining coroutines with click."""

    @wraps(f)
    def wrapper(*args, **kwargs):
        loop = asyncio.get_event_loop()
        return loop.run_until_complete(f(*args, **kwargs))

    return wrapper


@click.command()
@click.option('--debug', is_flag=True,
              help='Do NOT detach and run in the background.')
@pass_context
def start(ctx, debug):
    """Start the daemon."""

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
