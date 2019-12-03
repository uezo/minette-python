""" Utilities functions for minette """
from datetime import datetime
import calendar
import objson


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
    return objson.date_to_str(dt, with_timezone)


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
    return objson.str_to_date(dtstr)


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


def encode_json(obj, **kwargs):
    return objson.dumps(obj, **kwargs)


def decode_json(json_string, **kwargs):
    return objson.loads(json_string, **kwargs)
