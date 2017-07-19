""" utilities functions for minette """
from datetime import datetime
import calendar
import json
import importlib
import sys

class DateTimeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DateTimeJSONEncoder, self).default(obj)

def encode_json(obj):
    """
    :param obj: Object to encode
    :return: JSON string
    :rtype: str
    """
    if obj is None:
        return ""
    return json.dumps(obj, cls=DateTimeJSONEncoder)

def decode_json(json_string):
    """
    :param obj: JSON string to decode
    :return: JSON dict
    """
    if json_string is None or json_string == "":
        return None
    return json.loads(json_string)

def date_to_str(dt, without_timezone=False):
    """
    :param dt: Datetime
    :type dt: datetime
    :param without_timezone: Return string without timezone
    :type without_timezone: bool
    :return: Datetime string
    :rtype: str
    """
    if without_timezone:
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    if dt.tzinfo:
        return dt.strftime("%Y-%m-%d %H:%M:%S %z")
    else:
        return dt.strftime("%Y-%m-%d %H:%M:%S +0000")

def str_to_date(dtstr):
    """
    :param dtstr: Datetime string
    :type dtstr: str
    :return: Datetime
    :rtype: datetime
    """
    #to be modified to using regex
    if len(dtstr) > 19:
        return datetime.strptime(dtstr, "%Y-%m-%d %H:%M:%S %z")
    else:
        return datetime.strptime(dtstr + " +0000", "%Y-%m-%d %H:%M:%S %z")

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
