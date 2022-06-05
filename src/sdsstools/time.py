#!/usr/bin/env python
# -*- coding: utf-8 -*-
#
# @Author: José Sánchez-Gallego (gallegoj@uw.edu)
# @Date: 2022-04-25
# @Filename: time.py
# @License: BSD 3-clause (http://www.opensource.org/licenses/BSD-3-Clause)


import datetime
import os
import socket
import warnings

from typing import Optional


__all__ = ["SJD_OFFSET", "get_sjd"]


SJD_OFFSET = {"APO": 0.3, "LCO": 0.4}


def sex2dec(hour: int, minute: int, second: float, microsecond: float = 0.0):
    """Convert a sexagesimal time to decimal hours."""

    return float(hour) + minute / 60.0 + (second + microsecond / 1e6) / 3600.0


def datetime2decimalTime(
    datetime_obj: Optional[datetime.datetime] = None,
):  # pragma: nocover
    """Converts a Python ``datetime.datetime`` object into a decimal hour."""

    if datetime_obj is None:
        datetime_obj = datetime.datetime.now()

    return sex2dec(
        datetime_obj.hour,
        datetime_obj.minute,
        datetime_obj.second,
        datetime_obj.microsecond,
    )


def ymd2jd(year: int, month: int, day: int) -> float:  # pragma: nocover
    """Converts a year, month, and day to a Julian Date.

    This function uses an algorithm from the book "Practical Astronomy with your
    Calculator" by Peter Duffet-Smith (Page 7).

    Parameters
    ----------
    year
        A Gregorian year
    month
        A Gregorian month
    day
        A Gregorian day

    Returns
    -------
    jd
        A Julian Date computed from the input year, month, and day.

    """

    if month == 1 or month == 2:
        yprime = year - 1
        mprime = month + 12
    else:
        yprime = year
        mprime = month

    if year > 1582 or (year == 1582 and (month >= 10 and day >= 15)):
        A = int(yprime / 100)
        B = 2 - A + int(A / 4.0)
    else:
        B = 0

    if yprime < 0:
        C = int((365.25 * yprime) - 0.75)
    else:
        C = int(365.25 * yprime)

    D = int(30.6001 * (mprime + 1))

    return B + C + D + day + 1720994.5


def datetime2jd(datetime_obj: datetime.datetime) -> float:  # pragma: nocover
    """Converts a Python datetime object to a Julian Date.

    Parameters
    ----------
    datetime_obj
        A Python datetime.datetime object calculated using an algorithm from the book
        "Practical Astronomy with your Calculator" by Peter Duffet-Smith (Page 7)

    """

    A = ymd2jd(datetime_obj.year, datetime_obj.month, datetime_obj.day)
    B = datetime2decimalTime(datetime_obj) / 24.0

    return A + B


def get_sjd(
    observatory: Optional[str] = None,
    date: Optional[datetime.datetime] = None,
    raise_error: bool = True,
) -> int:
    """Returns the SDSS-modified MJD.

    At APO, ``SJD=MJD+0.3``. At LCO, ``SJD=MJD+0.4``.

    Parameters
    ----------
    observatory
        The observatory for which the SJD is requested. It must be ``'APO'`` or
        ``'LCO'``. If not provided, the code will use the ``$OBSERVATORY``
        environment variable first, if it exists, or the fully qualified domain
        name.
    date
        A `datetime.datetime` object with the date for which to calculate the SJD.
        If `None`, the current date will be used.
    raise_error
        If `True`, raises a `ValueError` if the observatory cannot be identified.
        If `False`, issues a warning and returns the current MJD without offset.

    Returns
    -------
    sjd
        The SJD as an integer.

    Raises
    ------
    ValueError
        When it is not possible to determine the current observatory and
        ``raise_error=True``.

    """

    if date is None:
        date = datetime.datetime.utcnow()

    jd = datetime2jd(date)

    if observatory is None:
        if "OBSERVATORY" in os.environ:
            observatory = os.environ["OBSERVATORY"]
        else:
            fqdn = socket.getfqdn()
            if fqdn.endswith("apo.nmsu.edu"):
                observatory = "APO"
            elif fqdn.endswith("lco.cl"):
                observatory = "LCO"
            else:
                if raise_error is True:
                    raise ValueError("Cannot determine the current observatory.")
                else:
                    warnings.warn(
                        "Cannot determine the current observatory. Returning MDJ.",
                        UserWarning,
                    )
                    return int(jd - 2400000.5)

    observatory = observatory.upper()

    if observatory not in ["APO", "LCO"]:
        raise ValueError(f"Invalid observatory {observatory!r}.")

    mjd = jd - 2400000.5

    return int(mjd + SJD_OFFSET[observatory])
