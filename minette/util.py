""" utilities functions for minette """
from datetime import datetime
import calendar
import importlib
import sys

def date_to_str(dt, with_timezone=False):
    """
    :param dt: Datetime
    :type dt: datetime
    :param with_timezone: Return string with timezone
    :type with_timezone: bool
    :return: Datetime string
    :rtype: str
    """
    if with_timezone and dt.tzinfo:
        return dt.strftime("%Y-%m-%d %H:%M:%S %z")
    else:
        return dt.strftime("%Y-%m-%d %H:%M:%S")

def str_to_date(dtstr):
    """
    :param dtstr: Datetime string
    :type dtstr: str
    :return: Datetime
    :rtype: datetime
    """
    if isinstance(dtstr, str) is False:
        return dtstr
    if len(dtstr) > 19:
        return datetime.strptime(dtstr, "%Y-%m-%d %H:%M:%S %z")
    else:
        return datetime.strptime(dtstr, "%Y-%m-%d %H:%M:%S")

def date_to_unixtime(dt):
    """
    :param dt: Datetime
    :type dt: datetime
    :return: Unixtime
    :rtype: int
    """
    return calendar.timegm(dt.utctimetuple())

def unixtime_to_date(unixtime, tz=None):
    """
    :param unixtime: Unixtime
    :type unixtime: int
    :param tz: Timezone
    :type tz: timezone
    :return: Datetime
    :rtype: datetime
    """
    return datetime.fromtimestamp(unixtime, tz=tz)

def get_class(path_to_class):
    """
    :param path_to_class: Namespace and class name like "name.space.and.Class"
    :type path_to_class: str
    :return: Class
    """
    namespaces = path_to_class.split(".")
    package_name = ".".join(namespaces[:-1])
    class_name = namespaces[-1]
    importlib.import_module(package_name)
    return getattr(sys.modules[package_name], class_name)
