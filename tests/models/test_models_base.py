import pytest
from pytz import timezone
from datetime import datetime

from minette.serializer import Serializable
from minette.utils import date_to_str


class CustomClass(Serializable):
    def __init__(self, strvalue=None, intvalue=None, dtvalue=None, listvalue=None, dictvalue=None, objvalue=None):
        super().__init__()
        self.strvalue = strvalue
        self.intvalue = intvalue
        self.dtvalue = dtvalue
        self.listvalue = listvalue
        self.dictvalue = dictvalue
        self.objvalue = objvalue


class SubClass(CustomClass):
    pass


def test_init():
    now = datetime.now(timezone("Asia/Tokyo"))
    cc = CustomClass(strvalue="str", intvalue=1, dtvalue=now, listvalue=[1, 2, 3], dictvalue={"key1": "value1", "key2": 2})
    assert cc.strvalue == "str"
    assert cc.intvalue == 1
    assert cc.dtvalue == now
    assert cc.listvalue == [1, 2, 3]
    assert cc.dictvalue == {"key1": "value1", "key2": 2}


def test_to_dict():
    now = datetime.now(timezone("Asia/Tokyo"))
    sc1 = SubClass(strvalue="sub_str_1")
    sc2 = SubClass(strvalue="sub_str_2")
    sc3 = SubClass(strvalue="sub_str_3")
    sc4 = SubClass(strvalue="sub_str_4")
    cc = CustomClass(strvalue="str", intvalue=1, dtvalue=now, listvalue=[sc1, sc2, "list_str_1"], dictvalue={"key1": "value1", "key2": 1, "key3": sc3}, objvalue=sc4)
    cc_dict = cc.to_dict()
    # CustomClass
    assert cc_dict["strvalue"] == "str"
    assert cc_dict["intvalue"] == 1
    assert cc_dict["dtvalue"] == now
    assert cc_dict["listvalue"] == [sc1.to_dict(), sc2.to_dict(), "list_str_1"]
    assert cc_dict["dictvalue"]["key1"] == "value1"
    assert cc_dict["dictvalue"]["key2"] == 1
    assert cc_dict["dictvalue"]["key3"] == sc3.to_dict()
    assert cc_dict["objvalue"] == sc4.to_dict()


def test_to_json():
    now = datetime.now(timezone("Asia/Tokyo"))
    cc = CustomClass(strvalue="str", intvalue=1, dtvalue=now, dictvalue={"key1": "value1", "key2": 2})
    cc_json = cc.to_json()
    assert cc_json == '{"strvalue": "str", "intvalue": 1, "dtvalue": "' + date_to_str(now, with_timezone=True) + '", "listvalue": null, "dictvalue": {"key1": "value1", "key2": 2}, "objvalue": null}'


def test_from_dict():
    now = datetime.now(timezone("Asia/Tokyo"))
    cc_dict = {
        "strvalue": "str",
        "intvalue": 1,
        "dtvalue": now,
        "listvalue": [1, 2, 3],
        "dictvalue": {"key1": "value1", "key2": 2},
    }
    cc = CustomClass.from_dict(cc_dict)
    assert cc.strvalue == "str"
    assert cc.intvalue == 1
    assert cc.dtvalue == now
    assert cc.listvalue == [1, 2, 3]
    assert cc.dictvalue == {"key1": "value1", "key2": 2}


def test_from_dict_dict():
    cc_dict_dict = {
        "cc1": {
            "strvalue": "str_1",
        },
        "cc2": {
            "strvalue": "str_2",
        },
    }
    cc = CustomClass.from_dict_dict(cc_dict_dict)
    assert cc["cc1"].strvalue == "str_1"
    assert cc["cc1"].to_dict() == CustomClass.from_dict({"strvalue": "str_1"}).to_dict()
    assert cc["cc2"].strvalue == "str_2"
    assert cc["cc2"].to_dict() == CustomClass.from_dict({"strvalue": "str_2"}).to_dict()


def test_from_dict_list():
    cc_dict_list = [
        {
            "strvalue": "str_1",
        },
        {
            "strvalue": "str_2",
        },
    ]
    cc = CustomClass.from_dict(cc_dict_list)
    assert cc[0].strvalue == "str_1"
    assert cc[0].to_dict() == CustomClass.from_dict({"strvalue": "str_1"}).to_dict()
    assert cc[1].strvalue == "str_2"
    assert cc[1].to_dict() == CustomClass.from_dict({"strvalue": "str_2"}).to_dict()


def test_from_json():
    now = datetime.now(timezone("Asia/Tokyo"))
    cc_json = '{"strvalue": "str", "intvalue": 1, "dtvalue": "' + date_to_str(now, with_timezone=True) + '", "listvalue": [1, 2, 3], "dictvalue": {"key1": "value1", "key2": 2}, "objvalue": null}'
    cc = CustomClass.from_json(cc_json)
    assert cc.strvalue == "str"
    assert cc.intvalue == 1
    assert cc.dtvalue == now
    assert cc.listvalue == [1, 2, 3]
    assert cc.dictvalue == {"key1": "value1", "key2": 2}
    assert cc.objvalue is None
