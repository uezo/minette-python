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
    return json.dumps(obj, cls=DateTimeJSONEncoder)


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


class JsonSerializable:
    """
    Base class of JSON Serializable object
    """
    def __init__(self, **kwargs):
        pass

    def to_dict(self):
        """
        Convert this object to dict

        Returns
        -------
        object_dict : dict
            Object as dict
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
        Convert this object to JSON

        Returns
        -------
        object_json : str
            Object as JSON string
        """
        return encode_json(self.to_dict())

    @classmethod
    def from_dict(cls, data, as_args=False):
        """
        Create object from dict

        Parameters
        ----------
        data : dict
            JSON serializable dictionary of this object
        as_args : bool, default False
            Set data to object as arguments of __init__()

        Returns
        -------
        object : JsonSerializable
            Instance of JsonSerializable
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
        Create dictionary from dictionaries of JSON serializable object

        Parameters
        ----------
        data : dict
            JSON serializable dictionary of this object
        as_args : bool, default False
            Set data to object as arguments of __init__()

        Returns
        -------
        dict_of_jsonserializable : dict
            Dictionary of JSON serializable objects
        """
        ret = {k: cls.from_dict(v, as_args) for k, v in data.items()}
        return ret

    @classmethod
    def from_dict_list(cls, data, as_args=False):
        """
        Create list from dictionaries of JSON serializable object

        Parameters
        ----------
        data : dict
            JSON serializable dictionary of this object
        as_args : bool, default False
            Set data to object as arguments of __init__()

        Returns
        -------
        list_of_jsonserializable : list
            List of JSON serializable objects
        """
        ret = [cls.from_dict(v, as_args) for i, v in enumerate(data)]
        return ret

    @classmethod
    def from_json(cls, json_str, as_args=False):
        """
        Create object from JSON

        Parameters
        ----------
        json_str : str
            JSON string of this object
        as_args : bool, default False
            Set data to object as arguments of __init__()

        Returns
        -------
        object : JsonSerializable
            Instance of JsonSerializable
        """
        data = decode_json(json_str)
        return cls.from_dict(data, as_args)
