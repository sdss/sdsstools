#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2020-08-06
# @Filename: test_daemonizer.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

import click
import pytest
from daemonocle import Daemon

from sdsstools.daemonizer import DaemonGroup, cli_coro


# These test don't spin any daemon. That seem to be difficult because the
# daemon process messes up with pytest and coverage. Ultimate what we care
# is that the callback function in the CLI is being called and we asume
# that daemonocle works well.


@click.group(cls=DaemonGroup, prog='test', workdir='./', pidfile='./test.pid')
@click.argument('name')
@click.option('--option', type=str)
def daemon_grp(name, option):

    print(f'Hello {name}!\n')
    print(f'Option: {option}\n')


def test_debug(cli_runner):

    result = cli_runner.invoke(daemon_grp, ['--option', 'AnOption',
                                            'Jose', 'start', '--debug'])

    assert result.exit_code == 0
    assert 'Hello Jose' in result.output
    assert 'Option: AnOption' in result.output

    ctx = daemon_grp.make_context('test', ['Jose', 'start', '--debug'])
    assert daemon_grp.list_commands(ctx) == ['start', 'stop',
                                             'restart', 'status']


def test_bad_command(cli_runner):

    result = cli_runner.invoke(daemon_grp, ['Jose', 'bad_command'])
    assert result.exit_code != 0


def test_start_stop_restart_status(mocker, cli_runner):

    mocker.patch.object(Daemon, 'do_action')

    cli_runner.invoke(daemon_grp, ['--option', 'AnOption', 'Jose', 'start'])
    Daemon.do_action.assert_called_once_with('start')
    Daemon.do_action.reset_mock()

    cli_runner.invoke(daemon_grp, ['--option', 'AnOption', 'Jose', 'stop'])
    Daemon.do_action.assert_called_once_with('stop')
    Daemon.do_action.reset_mock()

    cli_runner.invoke(daemon_grp, ['--option', 'AnOption', 'Jose', 'restart'])
    Daemon.do_action.assert_called_once_with('restart')
    Daemon.do_action.reset_mock()

    cli_runner.invoke(daemon_grp, ['--option', 'AnOption', 'Jose', 'status'])
    Daemon.do_action.assert_called_once_with('status')


def test_no_prog():

    with pytest.raises(RuntimeError):
        @click.group(cls=DaemonGroup, pidfile='./test.pid')
        @click.argument('name')
        @click.option('--option', type=str)
        def daemon_grp(name, option):
            pass


def test_daemon_coro(cli_runner):

    @click.group(cls=DaemonGroup, prog='test_async', pidfile='./test.pid')
    @click.argument('name')
    @cli_coro()
    async def daemon_grp_async(name):
        print(f'Hello {name}!\n')

    result = cli_runner.invoke(daemon_grp_async, ['Jose', 'start', '--debug'])

    # print(result.)
    assert result.exit_code == 0
    assert 'Hello Jose' in result.output


def test_coro_signal_handling(cli_runner):

    def dummy_handler(signal):
        pass

    @click.group(cls=DaemonGroup, prog='test_async')
    @click.argument('name')
    @cli_coro(shutdown_func=dummy_handler)
    async def daemon_grp_async(name):
        print(f'Hello {name}!\n')

    result = cli_runner.invoke(daemon_grp_async, ['Jose', 'start', '--debug'])

    # print(result.)
    assert result.exit_code == 0
    assert 'Hello Jose' in result.output
