import pytest

try:
    from cek import (
        Clova,
        URL
    )
    from minette.adapter.clovaadapter import ClovaAdapter
    import request_samples as rs
except Exception:
    # Skip if import dependencies not found
    pytestmark = pytest.mark.skip

from minette import (
    DialogService,
    Message,
    Config
)
from minette.serializer import loads

clovaconfig = Config("config/test_config_adapter.ini")
application_id = clovaconfig.get("application_id", section="clova_cek")
default_language = clovaconfig.get("default_language", section="clova_cek")

# Skip if application_id is not provided
if not application_id:
    pytestmark = pytest.mark.skip


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
        "Signaturecek": rs.REQUEST_SIGNATURE,
        "Content-Type": "application/json;charset=UTF-8",
        "Content-Length": 578,
        "Host": "host.name.local",
        "Accept": "*/*",
    }

    # launch request
    response = loads(adapter.handle_http_request(rs.LAUNCH_REQUEST_BODY, request_headers))
    assert response["response"]["outputSpeech"]["values"]["value"] == "Handled LaunchRequest"

    # intent request
    response = loads(adapter.handle_http_request(rs.INTENT_REQUEST_BODY, request_headers))
    assert response["response"]["outputSpeech"]["values"]["value"] == "Handled IntentRequest"

    # intent request (multiple response message)
    response = loads(adapter.handle_http_request(rs.INTENT_REQUEST_TURN_OFF, request_headers))
    assert response["response"]["outputSpeech"]["values"][0]["value"] == "Handled IntentRequest"
    assert response["response"]["outputSpeech"]["values"][1]["value"] == "Finish turning off"

    # end request
    response = loads(adapter.handle_http_request(rs.END_REQUEST_BODY, request_headers))
    assert response["response"]["outputSpeech"]["values"]["value"] == "Handled SessionEndedRequest"

    # event request
    response = loads(adapter.handle_http_request(rs.EVENT_REQUEST_BODY, request_headers))
    assert response["response"]["outputSpeech"]["values"]["value"] == "Handled EventRequest"

    # EventFromSkillStore request
    response = loads(adapter.handle_http_request(rs.EVENT_REQUEST_BODY_FROM_SKILL_STORE, request_headers))
    assert response["response"]["outputSpeech"]["values"]["value"] == "Handled EventRequest"
