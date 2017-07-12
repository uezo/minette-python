""" utilities functions for minette """
from datetime import datetime
import calendar
import json

class DateTimeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super(DateTimeJSONEncoder, self).default(obj)

def encode_json(obj):
    if obj is None:
        return ""
    return json.dumps(obj, cls=DateTimeJSONEncoder)

def decode_json(json_string):
    if json_string is None or json_string == "":
        return None
    return json.loads(json_string)

def date_to_str(dt:datetime):
    if dt.tzinfo:
        return dt.strftime("%Y-%m-%d %H:%M:%S %z")
    else:
        return dt.strftime("%Y-%m-%d %H:%M:%S +0000")

def str_to_date(dtstr) -> datetime:
    #to be modified to using regex
    if len(dtstr) > 19:
        return datetime.strptime(dtstr, "%Y-%m-%d %H:%M:%S %z")
    else:
        return datetime.strptime(dtstr + " +0000", "%Y-%m-%d %H:%M:%S %z")

def date_to_unixtime(dt:datetime):
    return calendar.timegm(dt.utctimetuple())

def unixtime_to_date(unixtime, tz=None) -> datetime:
    return datetime.fromtimestamp(unixtime, tz=tz)
