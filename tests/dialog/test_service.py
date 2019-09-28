import pytest
from pytz import timezone

from minette import DialogService, EchoDialogService, ErrorDialogService
from minette import (
    Message,
    Response,
    Context,
    PerformanceInfo
)


class MyDialog(DialogService):
    pass


class PizzaDialogService(DialogService):
    def extract_entities(self, request, context, connection):
        if "seafood" in request.text:
            return {"pizza_name": "Seafood Pizza"}
        else:
            return {"pizza_name": ""}

    def get_slots(self, request, context, connection):
        return {
            "pizza_name": "",
            "pizza_count": 0
        }

    def process_request(self, request, context, connection):
        if request.text == "error":
            # raise runtime error
            1 / 0

        if request.text == "no message":
            context.topic.status = "no_message"
            return

        # confirmation
        if context.topic.status == "confirmation":
            if request.text == "yes":
                context.topic.status = "confirmed"
                return

        # get order
        context.data["pizza_name"] = context.data["pizza_name"] or request.entities.get("pizza_name", "")
        if context.data["pizza_name"]:
            context.topic.status = "confirmation"
        else:
            context.topic.status = "requireorder"

    def compose_response(self, request, context, connection):
        if context.topic.status == "no_message":
            return

        elif context.topic.status == "requireorder":
            context.topic.keep_on = True
            return "Which pizza?"

        elif context.topic.status == "confirmation":
            context.topic.keep_on = True
            return "Your order is {}?".format(context.data["pizza_name"])

        elif context.topic.status == "confirmed":
            messages = [
                request.to_reply(text="Thank you!"),
                "We will deliver {} in 30min.".format(context.data["pizza_name"])
            ]
            return messages


def test_init_base():
    ds = DialogService(timezone=timezone("Asia/Tokyo"))
    assert ds.timezone == timezone("Asia/Tokyo")


def test_topic_name():
    my_ds = MyDialog()
    assert my_ds.topic_name() == "my"
    pizza_ds = PizzaDialogService()
    assert pizza_ds.topic_name() == "pizza"


def test_handle_exception():
    ds = MyDialog()
    context = Context("TEST", "test_user")
    request = Message(channel="TEST", channel_user_id="test_user", text="Hello")
    message = ds.handle_exception(request, context, ValueError("test error"), None)
    assert message.text == "?"
    assert context.error["exception"] == "test error"


def test_execute():
    ds = PizzaDialogService(timezone=timezone("Asia/Tokyo"))
    performance = PerformanceInfo()

    # first contact
    context = Context("TEST", "test_user")
    context.topic.is_new = True
    request = Message(channel="TEST", channel_user_id="test_user", text="Give me pizza")
    response = ds.execute(request, context, None, performance)
    assert response.messages[0].text == "Which pizza?"
    assert request.entities == {"pizza_name": ""}
    assert context.data == {
        "pizza_name": "",
        "pizza_count": 0
    }
    # say pizza name
    context.is_new = False
    context.topic.is_new = False
    request = Message(channel="TEST", channel_user_id="test_user", text="seafood pizza")
    response = ds.execute(request, context, None, performance)
    assert response.messages[0].text == "Your order is Seafood Pizza?"

    # confirmation
    request = Message(channel="TEST", channel_user_id="test_user", text="yes")
    response = ds.execute(request, context, None, performance)
    assert response.messages[0].text == "Thank you!"
    assert response.messages[1].text == "We will deliver Seafood Pizza in 30min."

    # raise error
    request = Message(channel="TEST", channel_user_id="test_user", text="error")
    response = ds.execute(request, context, None, performance)
    assert response.messages[0].text == "?"
    assert context.error["exception"] == "division by zero"

    # no response messages
    request = Message(channel="TEST", channel_user_id="test_user", text="no message")
    response = ds.execute(request, context, None, performance)
    assert response.messages == []


def test_execute_default():
    ds = MyDialog()
    performance = PerformanceInfo()
    context = Context("TEST", "test_user")
    context.topic.is_new = True
    request = Message(channel="TEST", channel_user_id="test_user", text="hello")
    response = ds.execute(request, context, None, performance)
    assert response.messages == []
    assert request.entities == {}
    assert context.data == {}


def test_execute_echo():
    ds = EchoDialogService(timezone=timezone("Asia/Tokyo"))
    performance = PerformanceInfo()
    context = Context("TEST", "test_user")
    context.topic.is_new = True
    request = Message(channel="TEST", channel_user_id="test_user", text="hello")
    response = ds.execute(request, context, None, performance)
    assert response.messages[0].text == "You said: hello"


def test_execute_error():
    ds = ErrorDialogService(timezone=timezone("Asia/Tokyo"))
    performance = PerformanceInfo()
    context = Context("TEST", "test_user")
    context.topic.is_new = True
    request = Message(channel="TEST", channel_user_id="test_user", text="hello")
    response = ds.execute(request, context, None, performance)
    assert response.messages[0].text == "?"
