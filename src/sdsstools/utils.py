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
import tempfile
import time
from contextlib import suppress
from functools import partial


__all__ = ["Timer", "get_temporary_file_path", "run_in_executor", "cancel_task"]


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
