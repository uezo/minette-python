import json
from datetime import datetime
import re
from .utils import date_to_str, str_to_date


def _is_datestring(s):
    return isinstance(s, str) and \
        re.match(r"(\d{4})-(\d{2})-(\d{2})T(\d{2})\:(\d{2})\:(\d{2})", s)


def _encode_datetime(obj):
    if isinstance(obj, datetime):
        return date_to_str(obj, obj.tzinfo is not None)


def _decode_datetime(d):
    for k in d:
        if _is_datestring(d[k]):
            d[k] = str_to_date(d[k])
        if isinstance(d[k], list):
            for i, v in enumerate(d[k]):
                if _is_datestring(v):
                    d[k][i] = str_to_date(v)
    return d


def dumpd(obj):
    """
    Convert object to dict

    Parameters
    ----------
    obj : object
        Object to convert

    Returns
    -------
    d : dict
        Object as dict
    """
    # return input directly if it is already dict
    if isinstance(obj, dict):
        return obj
    # return list of dict
    elif isinstance(obj, (list, tuple, set)):
        return [dumpd(o) for o in obj]
    # convert to dict
    data = {}
    for key in obj.__dict__.keys():
        if not key.startswith("_"):
            # convert each items in list-like object
            if isinstance(getattr(obj, key, None), (list, tuple, set)):
                data[key] = []
                for v in getattr(obj, key, None):
                    if hasattr(v, "to_dict"):
                        data[key].append(v.to_dict())
                    elif hasattr(v, "__dict__"):
                        data[key].append(dumpd(v))
                    else:
                        data[key].append(v)
            # convert each items in dict
            elif isinstance(getattr(obj, key, None), dict):
                data[key] = {}
                for k, v in getattr(obj, key, None).items():
                    if hasattr(v, "to_dict"):
                        data[key][k] = v.to_dict()
                    elif hasattr(v, "__dict__"):
                        data[key][k] = dumpd(v)
                    else:
                        data[key][k] = v
            # convert object with `to_dict`
            elif hasattr(getattr(obj, key, None), "to_dict"):
                data[key] = getattr(obj, key).to_dict()
            # convert plain object
            elif hasattr(getattr(obj, key, None), "__dict__"):
                data[key] = dumpd(getattr(obj, key))
            else:
                data[key] = getattr(obj, key, None)
    return data


def loadd(d, obj_cls):
    """
    Convert dict to object

    Parameters
    ----------
    d : dict
        Dictionary to convert
    obj_cls : type
        Class of object to convert

    Returns
    -------
    obj : object
        Instance of obj_cls
    """
    # return None when input is None
    if d is None:
        return None
    # return the list of objects when input is list
    if isinstance(d, list):
        return [loadd(di, obj_cls) for di in d]
    # use `create_object` instead of its constructor
    if hasattr(obj_cls, "create_object"):
        obj = obj_cls.create_object(d)
    else:
        obj = obj_cls()
    # get member's type info
    types = obj_cls._types() if getattr(obj_cls, "_types", None) else {}
    # set values to object
    for k, v in d.items():
        if k in types:
            if hasattr(types[k], "from_dict"):
                setattr(obj, k, types[k].from_dict(v))
            else:
                setattr(obj, k, loadd(v, types[k]))
        else:
            setattr(obj, k, v)
    return obj


def dumps(obj, **kwargs):
    """
    Encode object/dict to JSON

    Parameters
    ----------
    obj : object
        Object to encode

    Returns
    -------
    s : str
        JSON string
    """
    if obj is None:
        return ""
    d = dumpd(obj)
    return json.dumps(d, default=_encode_datetime, **kwargs)


def loads(s, obj_cls=None, **kwargs):
    """
    Decode JSON to dict/object

    Parameters
    ----------
    s : str
        JSON string to decode
    obj_cls : type, default None
        Class of object to convert. If None, convert to dict

    Returns
    -------
    obj : object
        Instance of obj_cls
    """
    if s is None or s == "":
        return None
    d = json.loads(s, object_hook=_decode_datetime, **kwargs)
    if obj_cls is None:
        return d
    else:
        return loadd(d, obj_cls)


class Serializable:
    """
    Base class for serializable object

    """

    @classmethod
    def _types(cls):
        """
        Override this method to create instance of specific class for members.
        Configure like below then instance of `Foo` will be set to `self.foo`
        and `Bar` to `self.bar`
        ```
        return {
            "foo": Foo,
            "bar": Bar
        }
        ```
        """
        return {}

    def __repr__(self):
        return "<{} at {}>\n{}".format(
            self.__class__.__name__,
            hex(id(self)),
            self.to_json(indent=2, ensure_ascii=False))

    @classmethod
    def create_object(obj_cls, d):
        return obj_cls()

    def to_dict(self):
        """
        Convert this object to dict

        Returns
        -------
        d : dict
            Object as dict
        """
        return dumpd(self)

    def to_json(self, **kwargs):
        """
        Convert this object to JSON

        Returns
        -------
        s : str
            Object as JSON string
        """
        return dumps(self, **kwargs)

    @classmethod
    def from_dict(cls, d):
        """
        Create object from dict

        Parameters
        ----------
        d : dict
            Dictionary of this object

        Returns
        -------
        obj : Serializable
            Instance of this class
        """
        return loadd(d, cls)

    @classmethod
    def from_dict_dict(cls, dict_dict):
        """
        Create dictionary of this objects from dictionaries of dictionaries

        Parameters
        ----------
        dict_dict : dict
            Dictionary of dictionaries

        Returns
        -------
        dict_of_this_obj : dict
            Dictionary of this objects
        """
        return {k: cls.from_dict(v) for k, v in dict_dict.items()}

    @classmethod
    def from_json(cls, s, **kwargs):
        """
        Create this object from JSON string

        Parameters
        ----------
        s : str
            JSON string of this object

        Returns
        -------
        obj : Serializable
            Instance of this class
        """
        return loads(s, cls, **kwargs)
