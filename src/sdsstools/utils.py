#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2020-09-17
# @Filename: utils.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio
import concurrent.futures
import pathlib
import sys
import tempfile
import time
from contextlib import suppress
from functools import partial


__all__ = [
    "Timer",
    "get_temporary_file_path",
    "run_in_executor",
    "cancel_task",
    "GatheringTaskGroup",
]


class Timer:
    """Convenience context manager to time events.

    Modified from https://bit.ly/3ebdp3y.
    """

    def __enter__(self):
        self.start = time.time()
        self.end = None
        return self

    def __exit__(self, *args):
        self.end = time.time()
        self.interval = self.end - self.start

    @property
    def elapsed(self):
        if self.end:
            return self.interval

        return time.time() - self.start


def get_temporary_file_path(*args, create_parents: bool = False, **kwargs):
    """Returns a valid path to a temporary file.

    `args` and `kwargs` are directly passed to `tempfile.NamedTemporaryFile`.
    If `create_parents`, the parent directories are created if they don't
    exist.

    """

    tmp_log_file = tempfile.NamedTemporaryFile(*args, **kwargs)
    tmp_log_file.close()

    tmp_path = pathlib.Path(tmp_log_file.name)
    if tmp_path.exists():
        tmp_path.unlink()
    elif create_parents:
        tmp_path.parent.mkdir(parents=True, exist_ok=True)

    return tmp_path


async def run_in_executor(fn, *args, executor="thread", **kwargs):
    """Runs a function in an executor.

    In addition to streamlining the use of the executor, this function
    catches any warning issued during the execution and reissues them
    after the executor is done. This is important when using the
    actor log handler since inside the executor there is no loop that
    CLU can use to output the warnings.

    In general, note that the function must not try to do anything with
    the actor since they run on different loops.

    """

    fn = partial(fn, *args, **kwargs)

    if executor == "thread":
        executor = concurrent.futures.ThreadPoolExecutor
    elif executor == "process":
        executor = concurrent.futures.ProcessPoolExecutor
    else:
        raise ValueError("Invalid executor name.")

    with executor() as pool:
        result = await asyncio.get_running_loop().run_in_executor(pool, fn)

    return result


async def cancel_task(task: asyncio.Future | None):
    """Safely cancels a task."""

    if task is None or task.done():
        return

    task.cancel()
    with suppress(asyncio.CancelledError):
        await task


if sys.version_info >= (3, 11):

    class GatheringTaskGroup(asyncio.TaskGroup):
        """An extension to ``asyncio.TaskGroup`` that keeps track of the tasks created.

        Adapted from https://stackoverflow.com/questions/75204560/consuming-taskgroup-response

        """

        def __init__(self):
            super().__init__()
            self.__tasks = []

        def create_task(self, coro, *, name=None, context=None):
            """Creates a task and appends it to the list of tasks."""

            task = super().create_task(coro, name=name, context=context)
            self.__tasks.append(task)

            return task

        def results(self):
            """Returns the results of the tasks in the same order they were created."""

            if len(self._tasks) > 0:
                raise RuntimeError("Not all tasks have completed yet.")

            return [task.result() for task in self.__tasks]

else:

    class GatheringTaskGroup:
        """Simple implementation of ``asyncio.TaskGroup`` for Python 3.10 and below.

        The behaviour of this class is not exactly the same as ``asyncio.TaskGroup``,
        especially when it comes to handling of exceptions during execution.

        """

        def __init__(self):
            self._tasks = []
            self._joined: bool = False

        def __repr__(self):
            return f"<GatheringTaskGroup tasks={len(self._tasks)}>"

        async def __aenter__(self):
            self._joined = False
            self._tasks = []

            return self

        async def __aexit__(self, exc_type, exc_value, traceback):
            if exc_type is not None:
                return False

            await asyncio.gather(*self._tasks)
            self._joined = True

        def create_task(self, coro):
            """Creates a task and appends it to the list of tasks."""

            task = asyncio.create_task(coro)
            self._tasks.append(task)

            return task

        def results(self):
            """Returns the results of the tasks in the same order they were created."""

            if not self._joined:
                raise RuntimeError("Tasks have not been gathered yet.")

            return [task.result() for task in self._tasks]

    __all__.append("GatheringTaskGroup")
