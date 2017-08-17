""" JSON serialization """
from datetime import datetime
import json

class DateTimeJSONEncoder(json.JSONEncoder):
    def default(self, obj):
        if isinstance(obj, datetime):
            if obj.tzinfo:
                return obj.strftime("%Y-%m-%d %H:%M:%S %z")
            else:
                return obj.strftime("%Y-%m-%d %H:%M:%S")
        return super().default(obj)

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

class JsonSerializable:
    def __init__(self, **kwargs):
        pass

    def to_dict(self):
        """
        :return: Object as dict
        :rtype: dict
        """
        data = {}
        for key in self.__dict__.keys():
            if not key.startswith("_"):
                if isinstance(getattr(self, key, None), (list, tuple, set)):
                    data[key] = []
                    for elm in getattr(self, key, None):
                        if isinstance(elm, JsonSerializable):
                            data[key].append(elm.to_dict())
                        else:
                            data[key].append(elm)
                elif isinstance(getattr(self, key, None), dict):
                    data[key] = {}
                    for k, v in getattr(self, key, None).items():
                        if isinstance(v, JsonSerializable):
                            data[key][k] = v.to_dict()
                        else:
                            data[key][k] = v
                elif isinstance(getattr(self, key, None), JsonSerializable):
                    data[key] = getattr(self, key).to_dict()
                else:
                    data[key] = getattr(self, key, None)
        return data

    def to_json(self):
        """
        :return: Object as Json string
        :rtype: str
        """
        return encode_json(self.to_dict())

    @classmethod
    def from_dict(cls, data, as_args=False):
        """
        :param data: JSON serializable dictionary of this object
        :type data: dict
        :param as_args: Set data to object as arguments of __init__()
        :type as_args: bool
        :return: Instance of this class
        :rtype: object
        """
        if as_args:
            return cls(**data)
        obj = cls()
        for k, v in data.items():
            setattr(obj, k, v)
        return obj

    @classmethod
    def from_dict_dict(cls, data, as_args=False):
        """
        :param data: Dictionary of JSON serializable dictionaries of this object
        :type data: dict
        :param as_args: Set data to object as arguments of __init__()
        :type as_args: bool
        :return: Instance of this class
        :rtype: object
        """
        ret = {k: cls.from_dict(v, as_args) for k, v in data.items()}
        return ret

    @classmethod
    def from_dict_list(cls, data, as_args=False):
        """
        :param data: List of JSON serializable dictionaries of this object
        :type data: dict
        :param as_args: Set data to object as arguments of __init__()
        :type as_args: bool
        :return: Instance of this class
        :rtype: object
        """
        ret = [cls.from_dict(v, as_args) for i, v in enumerate(data)]
        return ret

    @classmethod
    def from_json(cls, json_str, as_args=False):
        """
        :param json_str: JSON string of this object
        :type json_str: str
        :param as_args: Set data to object as arguments of __init__()
        :type as_args: bool
        :return: Instance of this class
        :rtype: object
        """
        data = decode_json(json_str)
        return cls.from_dict(data, as_args)
