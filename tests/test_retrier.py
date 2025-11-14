#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2024-01-02
# @Filename: test_retrier.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)

from __future__ import annotations

import asyncio
from unittest.mock import MagicMock

from typing import TYPE_CHECKING, Any, Awaitable, Callable, Literal, overload

import pytest

from sdsstools.retrier import Retrier


if TYPE_CHECKING:
    from pytest_mock import MockFixture


@overload
def get_test_function(
    fail: bool = False,
    succeed_on: int = 2,
    async_: Literal[False] = False,
) -> Callable[..., Any]: ...


@overload
def get_test_function(
    fail: bool = False,
    succeed_on: int = 2,
    async_: Literal[True] = True,
) -> Callable[..., Awaitable[Any]]: ...


def get_test_function(
    fail: bool = False,
    succeed_on: int = 2,
    async_: bool = False,
) -> Callable[..., Any] | Callable[..., Awaitable[Any]]:
    global n_attempts

    n_attempts = 0

    def _inner():
        global n_attempts

        if fail:
            raise ValueError()

        n_attempts += 1
        if n_attempts == succeed_on:
            return True
        else:
            raise ValueError()

    def test_function():
        return _inner()

    async def test_function_async():
        return _inner()

    return test_function_async if async_ else test_function


on_retry_mock = MagicMock()


def _get_retrier(
    exponential_backoff: bool,
    on_retry: Callable[[Exception], None] | None = None,
):
    if exponential_backoff:
        base = 1.1
    else:
        base = 2

    return Retrier(
        use_exponential_backoff=exponential_backoff,
        exponential_backoff_base=base,
        on_retry=on_retry,
    )


@pytest.mark.parametrize("fail", [False, True])
@pytest.mark.parametrize("exponential_backoff", [False, True])
@pytest.mark.parametrize("on_retry", [None, on_retry_mock])
def test_retrier(
    fail: bool,
    exponential_backoff: bool,
    on_retry: Callable[[Exception], None] | None,
):
    on_retry_mock.reset_mock()
    retrier = _get_retrier(exponential_backoff, on_retry=on_retry)
    test_function = retrier(get_test_function(async_=False, fail=fail))

    if fail:
        with pytest.raises(ValueError):
            test_function()
    else:
        assert test_function() is True
        if on_retry:
            assert on_retry_mock.call_count == 1
        else:
            assert on_retry_mock.call_count == 0


@pytest.mark.parametrize("fail", [False, True])
@pytest.mark.parametrize("exponential_backoff", [False, True])
@pytest.mark.parametrize("on_retry", [None, on_retry_mock])
async def test_retrier_async(
    fail: bool,
    exponential_backoff: bool,
    on_retry: Callable[[Exception], None] | None,
):
    on_retry_mock.reset_mock()
    retrier = _get_retrier(exponential_backoff, on_retry=on_retry)
    test_function = retrier(get_test_function(async_=True, fail=fail))

    if fail:
        with pytest.raises(ValueError):
            await test_function()
    else:
        assert (await test_function()) is True
        if on_retry:
            assert on_retry_mock.call_count == 1
        else:
            assert on_retry_mock.call_count == 0


def test_retier_raise_on_exception_class():
    def raise_runtime_error():
        raise RuntimeError()

    on_retry_mock.reset_mock()
    retrier = Retrier(raise_on_exception_class=[RuntimeError], on_retry=on_retry_mock)
    test_function = retrier(raise_runtime_error)

    with pytest.raises(RuntimeError):
        test_function()

    on_retry_mock.assert_not_called()


async def test_retier_raise_on_exception_class_async():
    async def raise_runtime_error():
        raise RuntimeError()

    on_retry_mock.reset_mock()
    retrier = Retrier(raise_on_exception_class=[RuntimeError], on_retry=on_retry_mock)
    test_function = retrier(raise_runtime_error)

    with pytest.raises(RuntimeError):
        await test_function()

    on_retry_mock.assert_not_called()


async def test_retrier_with_timeout():
    async def waiter():
        await asyncio.sleep(0.2)

    retrier = Retrier(timeout=0.1, delay=0.1, max_attempts=2)
    test_function = retrier(waiter)

    with pytest.raises(asyncio.TimeoutError):
        await test_function()


async def test_retrier_with_timeout_function_warns(mocker: MockFixture):
    retrier = Retrier(timeout=0.1, delay=0.1, max_attempts=2)
    test_function = retrier(mocker.MagicMock())

    with pytest.warns(RuntimeWarning) as record:
        test_function()

    assert "The timeout parameter will be ignored." in str(record.list[-1].message)
