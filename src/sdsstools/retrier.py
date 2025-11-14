#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2024-01-02
# @Filename: retrier.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio
import inspect
import time
import warnings
from dataclasses import dataclass, field
from functools import wraps

from typing import (
    Any,
    Awaitable,
    Callable,
    TypeVar,
    overload,
)

from typing_extensions import ParamSpec, Self


__all__ = ["Retrier"]


T = TypeVar("T", bound=Any)
P = ParamSpec("P")


@dataclass
class Retrier:
    """A class that implements a retry mechanism.

    The object returned by this class can be used to wrap a function that
    will be retried ``max_attempts`` times if it fails::

        def test_function():
            ...

        retrier = Retrier(max_attempts=5)
        retrier(test_function)()

    where the wrapped function can be a coroutine, in which case the wrapped function
    will also be a coroutine.

    Most frequently this class will be used as a decorator::

        @Retrier(max_attempts=4, delay=0.1)
        async def test_function(x, y):
            ...

        await test_function(1, 2)

    Parameters
    ----------
    max_attempts
        The maximum number of attempts before giving up.
    delay
        The delay between attempts, in seconds.
    use_exponential_backoff
        Whether to use exponential backoff for the delay between attempts. If
        :obj:`True`, the delay will be
        ``delay * exponential_backoff_base ** (attempt - 1) + random_ms`` where
        ``random_ms`` is a random number between 0 and 100 ms used to avoid
        synchronisation issues.
    exponential_backoff_base
        The base for the exponential backoff.
    max_delay
        The maximum delay between attempts when using exponential backoff.
    on_retry
        A function that will be called when a retry is attempted. The function
        should accept an exception as its only argument.
    raise_on_exception_class
        A list of exception classes that will cause an exception to be raised
        without retrying.
    timeout
        If defined, each attempt can take at most this amount of time. If the
        attempt times out, an :obj:`asyncio.TimeoutError` will be raised.
        This only works if the wrapped function is a coroutine.

    """

    max_attempts: int = 3
    delay: float = 1
    use_exponential_backoff: bool = True
    exponential_backoff_base: float = 2
    max_delay: float = 32.0
    on_retry: Callable[[Exception], None] | None = None
    raise_on_exception_class: list[type[Exception]] = field(default_factory=list)
    timeout: float | None = None

    def calculate_delay(self, attempt: int) -> float:
        """Calculates the delay for a given attempt."""

        # Random number between 0 and 100 ms to avoid synchronisation issues.
        random_ms = 0.1 * (time.time() % 1)

        if self.use_exponential_backoff:
            return min(
                self.delay * self.exponential_backoff_base ** (attempt - 1) + random_ms,
                self.max_delay,
            )
        else:
            return self.delay

    @overload
    def __call__(
        self: Self,
        func: Callable[P, T],
    ) -> Callable[P, T]: ...

    @overload
    def __call__(
        self: Self,
        func: Callable[P, Awaitable[T]],
    ) -> Callable[P, Awaitable[T]]: ...

    def __call__(
        self,
        func: Callable[P, T] | Callable[P, Awaitable[T]],
    ) -> Callable[P, T] | Callable[P, Awaitable[T]]:
        """Wraps a function to retry it if it fails."""

        if inspect.iscoroutinefunction(func):

            @wraps(func)
            async def async_wrapper(*args: P.args, **kwargs: P.kwargs):
                attempt = 0
                while True:
                    try:
                        return await asyncio.wait_for(
                            func(*args, **kwargs),
                            timeout=self.timeout,
                        )
                    except Exception as ee:
                        attempt += 1
                        if attempt >= self.max_attempts:
                            raise ee
                        elif isinstance(ee, tuple(self.raise_on_exception_class)):
                            raise ee
                        else:
                            if self.on_retry:
                                self.on_retry(ee)
                            await asyncio.sleep(self.calculate_delay(attempt))

            return async_wrapper

        else:

            @wraps(func)
            def wrapper(*args: P.args, **kwargs: P.kwargs):
                attempt = 0
                while True:
                    try:
                        if self.timeout is not None:
                            warnings.warn(
                                "The wrapped function is not a coroutine. "
                                "The timeout parameter will be ignored.",
                                RuntimeWarning,
                            )
                        return func(*args, **kwargs)
                    except Exception as ee:
                        attempt += 1
                        if attempt >= self.max_attempts:
                            raise ee
                        elif isinstance(ee, tuple(self.raise_on_exception_class)):
                            raise ee
                        else:
                            if self.on_retry:
                                self.on_retry(ee)
                            time.sleep(self.calculate_delay(attempt))

            return wrapper
