import pytest
from pytz import timezone
from concurrent.futures import ThreadPoolExecutor
from copy import deepcopy

from cek import (
    Clova,
    URL,
    Request as ClovaRequest,
    Response as ClovaResponse,
    IntentRequest
)

from request_samples import *

from minette import (
    DialogService,
    Message,
    Payload,
    Config
)
from minette.utils import decode_json
from minette.adapter.clovaadapter import ClovaAdapter

clovaconfig = Config("config/test_config_adapter.ini")

application_id = clovaconfig.get("application_id", section="clova_cek")
default_language = clovaconfig.get("default_language", section="clova_cek")


class MyDialog(DialogService):
    def compose_response(self, request, context, connection):
        if request.intent == "TurnOff":
            return ["Handled {}".format(request.type), "Finish turning off"]
        else:
            return "Handled {}".format(request.type)


def test_init():
    adapter = ClovaAdapter(
        application_id=application_id,
        default_language=default_language, prepare_table=True)
    assert adapter.application_id is not None
    assert adapter.application_id == clovaconfig.get("application_id", section="clova_cek")
    assert adapter.default_language is not None
    assert adapter.default_language == clovaconfig.get("default_language", section="clova_cek")
    assert isinstance(adapter.clova, Clova)


def test_to_channel_message():
    # text messages
    message = ClovaAdapter._to_channel_message(
        Message(text="hello", entities={"end_session": True, "reprompt": None}))
    assert message["speech_value"] == "hello"
    assert message["end_session"] is True
    assert message["reprompt"] is None

    # url messages
    message = ClovaAdapter._to_channel_message(
        Message(text="http://uezo.net", type="url",
                entities={"end_session": True, "reprompt": None}))
    assert message["speech_value"].value == URL("http://uezo.net").value
    assert message["end_session"] is True
    assert message["reprompt"] is None

    # end_session and reprompt
    message = ClovaAdapter._to_channel_message(
        Message(text="hello", entities={"end_session": False, "reprompt": "are you okay?"}))
    assert message["speech_value"] == "hello"
    assert message["end_session"] is False
    assert message["reprompt"] == "are you okay?"


def test_handle_intent_request():
    adapter = ClovaAdapter(
        application_id="com.line.myApplication",
        default_dialog_service=MyDialog,
        debug=True,
        prepare_table=True)
    request_headers = {
        "Signaturecek": REQUEST_SIGNATURE,
        "Content-Type": "application/json;charset=UTF-8",
        "Content-Length": 578,
        "Host": "host.name.local",
        "Accept": "*/*",
    }

    # launch request
    response = decode_json(adapter.handle_http_request(LAUNCH_REQUEST_BODY, request_headers))
    assert response["response"]["outputSpeech"]["values"]["value"] == "Handled LaunchRequest"

    # intent request
    response = decode_json(adapter.handle_http_request(INTENT_REQUEST_BODY, request_headers))
    assert response["response"]["outputSpeech"]["values"]["value"] == "Handled IntentRequest"

    # intent request (multiple response message)
    response = decode_json(adapter.handle_http_request(INTENT_REQUEST_TURN_OFF, request_headers))
    assert response["response"]["outputSpeech"]["values"][0]["value"] == "Handled IntentRequest"
    assert response["response"]["outputSpeech"]["values"][1]["value"] == "Finish turning off"

    # end request
    response = decode_json(adapter.handle_http_request(END_REQUEST_BODY, request_headers))
    assert response["response"]["outputSpeech"]["values"]["value"] == "Handled SessionEndedRequest"

    # event request
    response = decode_json(adapter.handle_http_request(EVENT_REQUEST_BODY, request_headers))
    assert response["response"]["outputSpeech"]["values"]["value"] == "Handled EventRequest"

    # EventFromSkillStore request
    response = decode_json(adapter.handle_http_request(EVENT_REQUEST_BODY_FROM_SKILL_STORE, request_headers))
    assert response["response"]["outputSpeech"]["values"]["value"] == "Handled EventRequest"
