""" Utilities functions for minette """
from datetime import datetime
import calendar
import importlib
import sys


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
        return dt.strftime("%Y-%m-%d %H:%M:%S %z")
    else:
        return dt.strftime("%Y-%m-%d %H:%M:%S")


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
    if not isinstance(dtstr, str):
        return dtstr
    if len(dtstr) > 19:
        return datetime.strptime(dtstr, "%Y-%m-%d %H:%M:%S %z")
    else:
        return datetime.strptime(dtstr, "%Y-%m-%d %H:%M:%S")


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


def get_class(path_to_class):
    """
    Get class from path

    Parameters
    ----------
    path_to_class : str
        Namespace and class name like "name.space.and.Class"

    Returns
    -------
    class : type
        Class
    """
    namespaces = path_to_class.split(".")
    package_name = ".".join(namespaces[:-1])
    class_name = namespaces[-1]
    importlib.import_module(package_name)
    return getattr(sys.modules[package_name], class_name)
