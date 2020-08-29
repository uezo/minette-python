""" Utilities functions for minette """
from datetime import datetime
import calendar


def date_to_str(dt, with_timezone=False):
    """
    Convert datetime to str

    Parameters
    ----------
    dt : datetime
        datetime to convert
    with_timezone : bool, default False
        Include timezone or not

    Returns
    -------
    datetime_str : str
        Datetime string
    """
    if with_timezone and dt.tzinfo:
        dtstr = dt.strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        return dtstr[:-2] + ":" + dtstr[-2:]
    else:
        return dt.strftime("%Y-%m-%dT%H:%M:%S.%f")


def str_to_date(dtstr):
    """
    Convert str to datetime

    Parameters
    ----------
    dtstr : str
        str to convert

    Returns
    -------
    datetime : datetime
        datetime
    """
    if len(dtstr) > 19 and dtstr[-3:-2] == ":":
        dtstr = dtstr[:-3] + dtstr[-2:]
    fmt = "%Y-%m-%dT%H:%M:%S"
    if "." in dtstr:
        fmt += ".%f"
    if dtstr[-5] == "+" or dtstr[-5] == "-":
        fmt += "%z"
    return datetime.strptime(dtstr, fmt)


def date_to_unixtime(dt):
    """
    Convert datetime to unixtime

    Parameters
    ----------
    dt : datetime
        datetime to convert

    Returns
    -------
    unixtime : int
        Unixtime
    """
    return calendar.timegm(dt.utctimetuple())


def unixtime_to_date(unixtime, tz=None):
    """
    Convert unixtime to datetime

    Parameters
    ----------
    unixtime : int
        unixtime to convert
    tz : timezone
        timezone to set

    Returns
    -------
    datetime : datetime
        datetime
    """
    return datetime.fromtimestamp(unixtime, tz=tz)
