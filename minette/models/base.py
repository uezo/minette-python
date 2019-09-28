""" JSON serialization """
from datetime import datetime

from ..utils import encode_json, decode_json


class JsonSerializable:
    """
    Base class for JSON Serializable object

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

    @staticmethod
    def _class_from_dict(cls, data):
        """
        Create instance of specific class from dictionary.
        To override `from_dict` method, call this method to create
        the instance of subclass explicitly instead of super()

        """
        obj = cls()
        for k, v in data.items():
            setattr(obj, k, v)
        return obj

    @classmethod
    def from_dict(cls, data):
        """
        Create object from dict

        Parameters
        ----------
        data : dict
            JSON serializable dictionary of this object

        Returns
        -------
        object : JsonSerializable
            Instance of JsonSerializable
        """
        return cls._class_from_dict(cls, data)

    @classmethod
    def from_dict_dict(cls, data):
        """
        Create dictionary from dictionaries of JSON serializable object

        Parameters
        ----------
        data : dict
            Dictionary of dictionary

        Returns
        -------
        dict_of_jsonserializable : dict
            Dictionary of JSON serializable objects
        """
        ret = {k: cls.from_dict(v) for k, v in data.items()}
        return ret

    @classmethod
    def from_dict_list(cls, data):
        """
        Create list from dictionaries of JSON serializable object

        Parameters
        ----------
        data : list
            List of dictionary

        Returns
        -------
        list_of_jsonserializable : list
            List of JSON serializable objects
        """
        ret = [cls.from_dict(v) for v in data]
        return ret

    @classmethod
    def from_json(cls, json_str):
        """
        Create object from JSON string

        Parameters
        ----------
        json_str : str
            JSON string of this object

        Returns
        -------
        object : JsonSerializable
            Instance of JsonSerializable
        """
        data = decode_json(json_str)
        return cls.from_dict(data)
