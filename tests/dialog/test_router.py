import sys
import os
sys.path.append(os.pardir)
import pytest
from pytz import timezone

from minette import DialogRouter, DialogService, EchoDialogService, ErrorDialogService
from minette import (
    Message,
    Context,
    PerformanceInfo,
    Priority
)


class PizzaDialogService(DialogService):
    pass


class SobaDialogService(DialogService):
    pass


class AdhocDialogService(DialogService):
    pass


class MyDialogRouter(DialogRouter):
    def register_intents(self):
        self.intent_resolver = {
            "PizzaIntent": PizzaDialogService,
            "SobaIntent": SobaDialogService,
            "AdhocIntent": AdhocDialogService,
            "NotRegisteredIntent": None,
        }

    def extract_intent(self, request, context, connection):
        if "pizza" in request.text:
            return "PizzaIntent"
        elif "lower" in request.text:
            return "SobaIntent", {"soba_name": "tanuki soba", "is_hot": True}, Priority.Low
        elif "soba" in request.text:
            return "SobaIntent", {"soba_name": "tanuki soba", "is_hot": True}, Priority.High
        elif "adhoc" in request.text:
            request.is_adhoc = True
            return "AdhocIntent", {}, Priority.Highest
        elif "not_registered" in request.text:
            return "NotRegisteredIntent"
        elif "unknown" in request.text:
            return "UnknownIntent"
        elif "error" in request.text:
            1 / 0


def test_init_base():
    dr = DialogRouter(timezone=timezone("Asia/Tokyo"))
    assert dr.timezone == timezone("Asia/Tokyo")
    assert dr.default_dialog_service is DialogService


def test_extract_intent():
    dr = DialogRouter(timezone=timezone("Asia/Tokyo"))
    context = Context("TEST", "test_user")
    request = Message(channel="TEST", channel_user_id="test_user", text="Hello")
    request.intent = "PizzaIntent"
    request.entities = {"key1": "value1"}
    intent, entities = dr.extract_intent(request, context, None)
    assert intent == "PizzaIntent"
    assert entities == {"key1": "value1"}


def test_init():
    dr = MyDialogRouter(timezone=timezone("Asia/Tokyo"), default_dialog_service=EchoDialogService)
    assert dr.timezone == timezone("Asia/Tokyo")
    assert dr.default_dialog_service is EchoDialogService


def test_route():
    # update topic
    dr = MyDialogRouter(timezone=timezone("Asia/Tokyo"), default_dialog_service=EchoDialogService)
    context = Context("TEST", "test_user")
    request = Message(channel="TEST", channel_user_id="test_user", text="Hello")
    request.intent = "PizzaIntent"
    ds = dr.route(request, context, None)
    assert ds is PizzaDialogService

    # adhoc topic
    context = Context("TEST", "test_user")
    request = Message(channel="TEST", channel_user_id="test_user", text="Hello")
    request.intent = "AdhocIntent"
    request.is_adhoc = True
    ds = dr.route(request, context, None)
    assert ds is AdhocDialogService
    assert context.topic.name == ""

    # adhoc topic (keep previous topic)
    context = Context("TEST", "test_user")
    context.topic.name = "pizza"
    request = Message(channel="TEST", channel_user_id="test_user", text="Hello")
    request.intent = "AdhocIntent"
    request.is_adhoc = True
    request.intent_priority = Priority.High
    ds = dr.route(request, context, None)
    assert ds is AdhocDialogService
    assert context.topic.name == "pizza"
    assert context.topic.keep_on is True

    # continue topic
    context = Context("TEST", "test_user")
    context.topic.name = "pizza"
    request = Message(channel="TEST", channel_user_id="test_user", text="Hello")
    ds = dr.route(request, context, None)
    assert ds is PizzaDialogService

    # no intent
    context = Context("TEST", "test_user")
    request = Message(channel="TEST", channel_user_id="test_user", text="Hello")
    ds = dr.route(request, context, None)
    assert ds is dr.default_dialog_service

    # unknown intent
    context = Context("TEST", "test_user")
    request = Message(channel="TEST", channel_user_id="test_user", text="Hello")
    request.intent = "UnknownIntent"
    ds = dr.route(request, context, None)
    assert ds is dr.default_dialog_service

    # dialog for intent not registered
    context = Context("TEST", "test_user")
    request = Message(channel="TEST", channel_user_id="test_user", text="Hello")
    request.intent = "NotRegisteredIntent"
    ds = dr.route(request, context, None)
    assert ds is DialogService

    # update topic by higher priority intent
    context = Context("TEST", "test_user")
    request = Message(channel="TEST", channel_user_id="test_user", text="Hello")
    request.intent = "PizzaIntent"
    ds = dr.route(request, context, None)
    assert ds is PizzaDialogService
    context.topic.keep_on = True
    # intent continue without intent
    request = Message(channel="TEST", channel_user_id="test_user", text="Hello")
    ds = dr.route(request, context, None)
    assert ds is PizzaDialogService
    context.topic.keep_on = True
    # soba intent with normal priority (not updated)
    request = Message(channel="TEST", channel_user_id="test_user", text="Hello")
    request.intent = "SobaIntent"
    ds = dr.route(request, context, None)
    assert ds is PizzaDialogService
    context.topic.keep_on = True
    # soba intent with higher priority (updated)
    request = Message(channel="TEST", channel_user_id="test_user", text="Hello")
    request.intent = "SobaIntent"
    request.intent_priority = Priority.High
    ds = dr.route(request, context, None)
    assert ds is SobaDialogService

    # update topic by normal priority intent
    context = Context("TEST", "test_user")
    request = Message(channel="TEST", channel_user_id="test_user", text="Hello")
    request.intent = "PizzaIntent"
    request.intent_priority = Priority.Low
    ds = dr.route(request, context, None)
    assert ds is PizzaDialogService
    context.topic.keep_on = True
    # intent continue without intent
    request = Message(channel="TEST", channel_user_id="test_user", text="Hello")
    ds = dr.route(request, context, None)
    assert ds is PizzaDialogService
    context.topic.keep_on = True
    # soba intent with normal priority (updated)
    request = Message(channel="TEST", channel_user_id="test_user", text="Hello")
    request.intent = "SobaIntent"
    ds = dr.route(request, context, None)
    assert ds is SobaDialogService


def test_handle_exception():
    dr = MyDialogRouter(timezone=timezone("Asia/Tokyo"), default_dialog_service=EchoDialogService)
    context = Context("TEST", "test_user")
    request = Message(channel="TEST", channel_user_id="test_user", text="Hello")
    ds = dr.handle_exception(request, context, ValueError("test error"), None)
    assert isinstance(ds, ErrorDialogService)
    assert context.error["exception"] == "test error"


def test_execute():
    dr = MyDialogRouter(timezone=timezone("Asia/Tokyo"), default_dialog_service=EchoDialogService)
    performance = PerformanceInfo()

    # default
    context = Context("TEST", "test_user")
    context.topic.is_new = True
    request = Message(channel="TEST", channel_user_id="test_user", text="Hello")
    ds = dr.execute(request, context, None, performance)
    assert isinstance(ds, dr.default_dialog_service)

    # pizza
    context = Context("TEST", "test_user")
    context.topic.is_new = True
    request = Message(channel="TEST", channel_user_id="test_user", text="give me pizza")
    ds = dr.execute(request, context, None, performance)
    assert isinstance(ds, PizzaDialogService)

    # continue pizza
    request = Message(channel="TEST", channel_user_id="test_user", text="seafood")
    ds = dr.execute(request, context, None, performance)
    assert isinstance(ds, PizzaDialogService)

    # soba lower priority (continume pizza)
    request = Message(channel="TEST", channel_user_id="test_user", text="lower")
    ds = dr.execute(request, context, None, performance)
    assert isinstance(ds, PizzaDialogService)

    # soba
    request = Message(channel="TEST", channel_user_id="test_user", text="give me soba")
    ds = dr.execute(request, context, None, performance)
    assert isinstance(ds, SobaDialogService)

    # adhoc
    context = Context("TEST", "test_user")
    context.topic.is_new = True
    request = Message(channel="TEST", channel_user_id="test_user", text="pizza")
    # start pizza
    ds = dr.execute(request, context, None, performance)
    assert isinstance(ds, PizzaDialogService)
    request = Message(channel="TEST", channel_user_id="test_user", text="adhoc")
    # adhoc
    ds = dr.execute(request, context, None, performance)
    assert isinstance(ds, AdhocDialogService)
    request = Message(channel="TEST", channel_user_id="test_user", text="seafood")
    # continue pizza
    ds = dr.execute(request, context, None, performance)
    assert isinstance(ds, PizzaDialogService)

    # no intent
    context = Context("TEST", "test_user")
    context.topic.is_new = True
    request = Message(channel="TEST", channel_user_id="test_user", text="_")
    ds = dr.execute(request, context, None, performance)
    assert isinstance(ds, dr.default_dialog_service)

    # unknown
    context = Context("TEST", "test_user")
    context.topic.is_new = True
    request = Message(channel="TEST", channel_user_id="test_user", text="unknown")
    ds = dr.execute(request, context, None, performance)
    assert isinstance(ds, dr.default_dialog_service)

    # dialog for intent not registered
    context = Context("TEST", "test_user")
    context.topic.is_new = True
    request = Message(channel="TEST", channel_user_id="test_user", text="not_registered")
    ds = dr.execute(request, context, None, performance)
    assert isinstance(ds, DialogService)

    # error
    context = Context("TEST", "test_user")
    context.topic.is_new = True
    request = Message(channel="TEST", channel_user_id="test_user", text="error")
    ds = dr.execute(request, context, None, performance)
    assert isinstance(ds, ErrorDialogService)
