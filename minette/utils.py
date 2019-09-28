""" Utilities functions for minette """
import sys
from datetime import datetime
import calendar
import json


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


class _DateTimeJSONEncoder(json.JSONEncoder):
    """
    JSON Encoder to serialize DateTime

    """
    def default(self, obj):
        if isinstance(obj, datetime):
            if obj.tzinfo:
                return obj.strftime("%Y-%m-%d %H:%M:%S %z")
            else:
                return obj.strftime("%Y-%m-%d %H:%M:%S")
        return super().default(obj)


def encode_json(obj):
    """
    Encode object to JSON

    Parameters
    ----------
    obj : object
        Object to encode

    Returns
    -------
    json_string : str
        JSON string
    """
    if obj is None:
        return ""
    return json.dumps(obj, cls=_DateTimeJSONEncoder)


def decode_json(json_string):
    """
    Decode JSON to dict

    Parameters
    ----------
    json_string : str
        JSON string to decode

    Returns
    -------
    json_dict : dict
        JSON dict
    """
    if json_string is None or json_string == "":
        return None
    return json.loads(json_string)
