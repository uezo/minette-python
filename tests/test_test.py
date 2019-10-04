import pytest
from pytz import timezone
from logging import Logger
from datetime import datetime

from minette import (
    DialogService, SQLiteConnectionProvider,
    SQLiteContextStore, SQLiteUserStore, SQLiteMessageLogStore,
    Tagger, Message
)
from minette.test.helper import MinetteForTest
from minette.utils import date_to_unixtime

now = datetime.now()
user_id = "user_id" + str(date_to_unixtime(now))
print("user_id: {}".format(user_id))


class FooDialog(DialogService):
    def compose_response(self, request, context, connetion):
        return "foo"


class BarDialog(DialogService):
    def compose_response(self, request, context, connetion):
        return "bar"


class MessageDialog(DialogService):
    def compose_response(self, request, context, connetion):
        return request.channel + "_" + request.channel_user_id


def test_init():
    # without config
    bot = MinetteForTest(
        default_channel="TEST",
        intent_resolver={
            "FooIntent": FooDialog,
            "BarIntent": BarDialog,
        },
    )
    assert bot.config.get("timezone") == "UTC"
    assert bot.timezone == timezone("UTC")
    assert isinstance(bot.logger, Logger)
    assert bot.logger.name == "minette"
    assert isinstance(bot.connection_provider, SQLiteConnectionProvider)
    assert isinstance(bot.context_store, SQLiteContextStore)
    assert isinstance(bot.user_store, SQLiteUserStore)
    assert isinstance(bot.messagelog_store, SQLiteMessageLogStore)
    assert bot.default_dialog_service is None
    assert isinstance(bot.tagger, Tagger)
    assert len(bot.case_id) > 10
    assert bot.default_channel == "TEST"
    assert bot.dialog_router.intent_resolver["FooIntent"] == FooDialog
    assert bot.dialog_router.intent_resolver["BarIntent"] == BarDialog


def test_chat():
    bot = MinetteForTest(
        default_channel="TEST",
        intent_resolver={
            "FooIntent": FooDialog,
            "BarIntent": BarDialog,
        },
    )
    assert bot.chat("hello", intent="FooIntent").messages[0].text == "foo"
    assert bot.chat("hello", intent="BarIntent").messages[0].text == "bar"
    assert bot.chat("hello").messages == []


def test_chat_message():
    bot = MinetteForTest(
        intent_resolver={
            "MessageIntent": MessageDialog,
        },
    )
    assert bot.chat(Message(
        intent="MessageIntent",
        channel="test_channel",
        channel_user_id="test_user"
    )).messages[0].text == "test_channel_test_user"
