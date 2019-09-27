import pytest
from pytz import timezone
from datetime import datetime

from minette import Context, Topic
from minette.utils import date_to_str, str_to_date


def test_init():
    context = Context(channel="TEST", channel_user_id="user_id")
    assert context.channel == "TEST"
    assert context.channel_user_id == "user_id"
    assert context.timestamp is None
    assert context.is_new is True
    assert isinstance(context.topic, Topic)
    assert context.data == {}
    assert context.error == {}


def test_reset():
    # setup context
    context = Context(channel="TEST", channel_user_id="user_id")
    context.data = {"fruit": "Apple"}
    context.topic.name = "favorite_fruit"
    context.topic.status = "continue"
    context.topic.keep_on = True
    # reset
    context.reset()
    assert context.topic.name == "favorite_fruit"
    assert context.topic.status == "continue"
    assert context.topic.previous.name == "favorite_fruit"
    assert context.topic.previous.status == "continue"
    assert context.data == {"fruit": "Apple"}
    # update
    context.topic.status = "finish"
    context.topic.keep_on = False
    # reset
    context.reset()
    assert context.topic.name == ""
    assert context.topic.status == ""
    assert context.topic.previous.name == "favorite_fruit"
    assert context.topic.previous.status == "finish"
    assert context.data == {}


def test_set_error():
    context = Context(channel="TEST", channel_user_id="user_id")
    try:
        1 / 0
    except Exception as ex:
        context.set_error(ex, info="this is test error")
    assert context.error["exception"] == "division by zero"
    assert "Traceback" in context.error["traceback"]
    assert context.error["info"] == "this is test error"


def test_from_dict():
    context_dict = {
        "channel": "TEST",
        "channel_user_id": "user_id",
        "data": {"fruit": "Apple"},
        "topic": {
            "name": "favorite_fruit",
            "status": "continue"
        }
    }
    context = Context.from_dict(context_dict)
    assert context.channel == "TEST"
    assert context.channel_user_id == "user_id"
    assert context.timestamp is None
    assert context.is_new is True
    assert context.topic.name == "favorite_fruit"
    assert context.topic.status == "continue"
    assert context.data == {"fruit": "Apple"}
    assert context.error == {}
