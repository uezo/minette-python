import pytest
from pytz import timezone
from concurrent.futures import ThreadPoolExecutor

from minette import Adapter, Message, DialogService


class ChannelEvent:
    def __init__(self, text):
        self.text = text


class CustomAdapter(Adapter):
    @staticmethod
    def _to_minette_message(event):
        return Message(text=event.text)

    @staticmethod
    def _to_channel_message(message):
        return message.text


class MyDialog(DialogService):
    def compose_response(self, request, context, connection):
        return "res:" + request.text


def test_init():
    adapter = CustomAdapter(
        timezone=timezone("Asia/Tokyo"), prepare_table=True)
    assert adapter.timezone == timezone("Asia/Tokyo")
    assert adapter.bot.timezone == timezone("Asia/Tokyo")
    assert isinstance(adapter.executor, ThreadPoolExecutor)
    # run in main thread
    adapter = CustomAdapter(
        timezone=timezone("Asia/Tokyo"), prepare_table=True, threads=0)
    assert adapter.executor is None


def test_extract_token():
    adapter = CustomAdapter(prepare_table=True)
    token = adapter._extract_token(ChannelEvent("hello"))
    assert token == ""


def test_handle_event():
    adapter = CustomAdapter(
        default_dialog_service=MyDialog, debug=True, prepare_table=True)
    channel_messages, token = adapter.handle_event(ChannelEvent("hello"))
    assert channel_messages[0] == "res:hello"
    assert token == ""
