#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2023-12-13
# @Filename: test_utils.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio
import sys
import warnings
from time import sleep

import pytest

from sdsstools.utils import (
    Timer,
    cancel_task,
    get_temporary_file_path,
    run_in_executor,
)


if sys.version_info >= (3, 11):
    from sdsstools.utils import GatheringTaskGroup


def test_timer():
    with Timer() as timer:
        sleep(0.1)

    assert timer.elapsed > 0


def test_timer_no_end():
    with Timer() as timer:
        sleep(0.1)

    timer.end = None
    assert timer.elapsed > 0


@pytest.mark.parametrize("create_parents", [True, False])
def test_create_temp_file(create_parents: bool):
    tmp_path = get_temporary_file_path(create_parents=create_parents)

    assert not tmp_path.exists()

    if create_parents:
        assert tmp_path.parent.exists()

    tmp_path.unlink(missing_ok=True)


def _executor_test_function():
    warnings.warn("A warning", UserWarning)
    sleep(0.5)
    return True


@pytest.mark.parametrize("executor", ["thread", "process"])
async def test_run_in_executor(executor: str):
    result = await run_in_executor(_executor_test_function, executor=executor)

    assert result


async def test_run_in_executor_bad_executor():
    with pytest.raises(ValueError):
        await run_in_executor(_executor_test_function, executor="blah")


async def _task():
    await asyncio.sleep(0.5)
    return True


async def test_cancel_task():
    task = asyncio.create_task(_task())

    await cancel_task(task)

    assert task.cancelled()
    assert task.done()


async def test_cancel_task_done():
    task = asyncio.create_task(_task())
    await task

    await cancel_task(task)

    assert not task.cancelled()
    assert task.done()


async def test_cancel_task_None():
    task = None
    await cancel_task(task)


@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires python3.11 or higher")
async def test_gathering_task_group():
    async def _task(i):
        await asyncio.sleep(0.1)
        return i

    async with GatheringTaskGroup() as group:
        for i in range(10):
            group.create_task(_task(i))

    assert group.results() == list(range(10))


@pytest.mark.skipif(sys.version_info < (3, 11), reason="requires python3.11 or higher")
async def test_gathering_task_group_results_fails():
    async def _task(i):
        await asyncio.sleep(0.1)
        return i

    async with GatheringTaskGroup() as group:
        for i in range(10):
            group.create_task(_task(i))

        with pytest.raises(RuntimeError):
            group.results()
