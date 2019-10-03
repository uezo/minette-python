import pytest
from pytz import timezone
from datetime import datetime

from minette import Message, Group, Payload, Priority


def test_init():
    now = datetime.now(timezone("Asia/Tokyo"))
    message = Message(
        id="mid123456789",
        type="hogehoge",
        timestamp=now,
        channel="TEST",
        channel_detail="messaging",
        channel_user_id="user_id",
        channel_message={
            "text": "hello"
        },
        text="hello",
        token="token123456789",
        payloads=[Payload(content_type="image", url="https://image")],
        intent="OrderPan",
        intent_priority=Priority.High,
        entities={"menu": "Yakisoba Pan", "count": 20},
        is_adhoc=True
    )
    assert message.id == "mid123456789"
    assert message.type == "hogehoge"
    assert message.timestamp == now
    assert message.channel == "TEST"
    assert message.channel_detail == "messaging"
    assert message.channel_user_id == "user_id"
    assert message.channel_message == {"text": "hello"}
    assert message.text == "hello"
    assert message.token == "token123456789"
    assert message.payloads[0].url == "https://image"
    assert message.intent == "OrderPan"
    assert message.intent_priority == Priority.High
    assert message.entities == {"menu": "Yakisoba Pan", "count": 20}
    assert message.is_adhoc is True


def test_init_default():
    message = Message()
    assert message.id == ""
    assert message.type == "text"
    assert isinstance(message.timestamp, datetime)
    assert message.channel == "console"
    assert message.channel_detail == ""
    assert message.channel_user_id == "anonymous"
    assert message.text == ""
    assert message.token == ""
    assert message.payloads == []
    assert message.channel_message is None


def test_to_reply():
    now = datetime.now(timezone("Asia/Tokyo"))
    message = Message(
        id="mid123456789",
        type="hogehoge",
        timestamp=now,
        channel="TEST",
        channel_detail="messaging",
        channel_user_id="user_id",
        text="hello",
        token="token123456789",
        channel_message={
            "text": "hello"
        }
    ).to_reply(text="nice talking to you", payloads=[Payload(content_type="image", url="https://image")], type="image")
    assert message.id == "mid123456789"
    assert message.type == "image"
    assert isinstance(message.timestamp, datetime)
    assert str(message.timestamp.tzinfo) == "Asia/Tokyo"
    assert message.channel == "TEST"
    assert message.channel_detail == "messaging"
    assert message.channel_user_id == "user_id"
    assert message.text == "nice talking to you"
    assert message.token == "token123456789"
    assert message.payloads[0].url == "https://image"
    assert message.channel_message is None


def test_to_dict():
    now = datetime.now(timezone("Asia/Tokyo"))
    message = Message(
        id="mid123456789",
        type="hogehoge",
        timestamp=now,
        channel="TEST",
        channel_detail="messaging",
        channel_user_id="user_id",
        text="hello",
        token="token123456789",
        payloads=[Payload(content_type="image", url="https://image")],
        channel_message={
            "text": "hello"
        }
    )
    msg_dict = message.to_dict()
    assert msg_dict["id"] == "mid123456789"
    assert msg_dict["timestamp"] == now


def test_from_dict():
    now = datetime.now(timezone("Asia/Tokyo"))
    message = Message(
        id="mid123456789",
        type="hogehoge",
        timestamp=now,
        channel="TEST",
        channel_detail="messaging",
        channel_user_id="user_id",
        text="hello",
        token="token123456789",
        payloads=[Payload(content_type="image", url="https://image")],
        channel_message={
            "text": "hello"
        }
    )
    msg_dict = message.to_dict()
    message = Message.from_dict(msg_dict)
    assert message.id == "mid123456789"
    assert message.type == "hogehoge"
    assert message.timestamp == now
    assert message.channel == "TEST"
    assert message.channel_detail == "messaging"
    assert message.channel_user_id == "user_id"
    assert message.text == "hello"
    assert message.token == "token123456789"
    assert message.payloads[0].url == "https://image"
    assert message.channel_message == str({"text": "hello"})
