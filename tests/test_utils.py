import pytest
from datetime import datetime
from pytz import timezone

from minette.serializer import dumps, loads
import minette.utils as u

naive_dt = datetime(2019, 1, 2, 3, 4, 5)
aware_dt = timezone("Asia/Tokyo").localize(naive_dt)


def test_date_to_str():
    assert u.date_to_str(naive_dt) == "2019-01-02T03:04:05.000000"
    assert u.date_to_str(aware_dt) == "2019-01-02T03:04:05.000000"
    assert u.date_to_str(aware_dt, with_timezone=True) == "2019-01-02T03:04:05.000000+09:00"


def test_str_to_date():
    assert u.str_to_date("2019-01-02T03:04:05") == naive_dt
    assert u.str_to_date("2019-01-02T03:04:05+09:00") == aware_dt


def test_date_to_unixtime():
    assert u.date_to_unixtime(aware_dt) == 1546365845


def test_unixtime_to_date():
    assert u.unixtime_to_date(1546365845) == naive_dt


def test_encode_json():
    obj = {
        "key1": "value1",
        "key2": 2,
        "key3": naive_dt,
        "key4": aware_dt
    }
    assert dumps(obj) == '{"key1": "value1", "key2": 2, "key3": "2019-01-02T03:04:05.000000", "key4": "2019-01-02T03:04:05.000000+09:00"}'
    assert dumps(None) == ""
    with pytest.raises(AttributeError):
        dumps(object())


def test_decode_json():
    obj = loads('{"key1": "value1", "key2": 2, "key3": "2019-01-02T03:04:05+09:00"}')
    assert obj["key1"] == "value1"
    assert obj["key2"] == 2
    assert obj["key3"] == aware_dt
    assert loads("") is None
