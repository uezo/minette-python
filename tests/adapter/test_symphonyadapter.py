"""
To run this test script, put symphony configuration file and private key here.

- config:       tests/config/private/symphony/symphony.json
- privatekey    tests/config/private/symphony/privatekey.pem

Then configure your symphony.json like below.

```
{
    "sessionAuthHost": "YOUR_POD.symphony.com",
    "sessionAuthPort": 443,
    "keyAuthHost": "YOUR_POD.symphony.com",
    "keyAuthPort": 443,
    "podHost": "YOUR_POD.symphony.com",
    "podPort": 443,
    "agentHost": "YOUR_POD.symphony.com",
    "agentPort": 443,
    "botRSAPath":"config/private/symphony/",
    "botRSAName": "privatekey.pem",
    "botUsername": "YOUR_BOT_NAME",
    "botEmailAddress": "your_bot@your_pod_domain.com",
    "appCertPath": "",
    "appCertName": "",
    "appCertPassword": "",
    "proxyURL": "",
    "proxyPort": "",
    "proxyUsername": "",
    "proxyPassword": "",
    "authTokenRefreshPeriod": "30",
    "truststorePath": ""
}
```
"""

import pytest
from pytz import timezone
from concurrent.futures import ThreadPoolExecutor

from sym_api_client_python.configure.configure import SymConfig
from sym_api_client_python.auth.rsa_auth import SymBotRSAAuth
from sym_api_client_python.clients.sym_bot_client import SymBotClient

from minette import DialogService, Message, Payload, Config
from minette.adapter.symphonyadapter import SymphonyAdapter


class MyDialog(DialogService):
    def compose_response(self, request, context, connection):
        return "res:" + request.text


def test_init():
    adapter = SymphonyAdapter(
        symphony_config="config/private/symphony/symphony.json",
        timezone=timezone("Asia/Tokyo"),
        prepare_table=True)
    assert adapter.timezone == timezone("Asia/Tokyo")
    assert isinstance(adapter.executor, ThreadPoolExecutor)
    assert isinstance(adapter.bot_client, SymBotClient)


def test_to_minette_message():
    adapter = SymphonyAdapter(
        symphony_config="config/private/symphony/symphony.json",
        prepare_table=True)

    # IM Message
    im_message_event = {'id': 'J5uf7A', 'messageId': '3LxcjF9_c5V4KYMpO9RcTn___pKGq_chbQ', 'timestamp': 1569698613470, 'type': 'MESSAGESENT', 'initiator': {'user': {'userId': 349026222344129, 'firstName': 'Uezo', 'lastName': 'Chan', 'displayName': 'uezochan', 'email': 'minette@uezo.net', 'username': 'minette@uezo.net'}}, 'payload': {'messageSent': {'message': {'messageId': '3LxcjF9_c5V4KYMpO9RcTn___pKGq_chbQ', 'timestamp': 1569698613470, 'message': '<div data-format="PresentationML" data-version="2.0" class="wysiwyg"><p>hello</p></div>', 'data': '{}', 'user': {'userId': 349026222344129, 'firstName': 'Uezo', 'lastName': 'Chan', 'displayName': 'uezochan', 'email': 'minette@uezo.net', 'username': 'minette@uezo.net'}, 'stream': {'streamId': 'On45D2InfVgaI2vhrMgXRn___pW3fpQfdA', 'streamType': 'IM'}, 'externalRecipients': False, 'userAgent': 'DESKTOP-40.0.0-10665-MacOSX-10.14.6-Safari-12.1.2', 'originalFormat': 'com.symphony.messageml.v2'}}}}
    message = adapter._to_minette_message(im_message_event)
    assert isinstance(message, Message)
    assert message.text == "hello"
    assert message.channel == "Symphony"
    assert message.channel_user_id == "349026222344129"
    assert message.group is None

    # Room Message
    room_message_event = {'id': '09eNPj', 'messageId': 'OrKrfST5Tiy7iMWYdGz5ZH___pKGnfJPbQ', 'timestamp': 1569699532208, 'type': 'MESSAGESENT', 'initiator': {'user': {'userId': 349026222344129, 'firstName': 'Uezo', 'lastName': 'Chan', 'displayName': 'uezochan', 'email': 'minette@uezo.net', 'username': 'minette@uezo.net'}}, 'payload': {'messageSent': {'message': {'messageId': 'OrKrfST5Tiy7iMWYdGz5ZH___pKGnfJPbQ', 'timestamp': 1569699532208, 'message': '<div data-format="PresentationML" data-version="2.0" class="wysiwyg"><p>hello room</p></div>', 'data': '{}', 'user': {'userId': 349026222344129, 'firstName': 'Uezo', 'lastName': 'Chan', 'displayName': 'uezochan', 'email': 'minette@uezo.net', 'username': 'minette@uezo.net'}, 'stream': {'streamId': 'TnsHiQtZFKB3x5CpRsbxdn___pW3e4sgdA', 'streamType': 'ROOM'}, 'externalRecipients': False, 'userAgent': 'DESKTOP-40.0.0-10665-MacOSX-10.14.6-Safari-12.1.2', 'originalFormat': 'com.symphony.messageml.v2'}}}}
    message = adapter._to_minette_message(room_message_event)
    assert isinstance(message, Message)
    assert message.text == "hello room"
    assert message.channel == "Symphony"
    assert message.channel_user_id == "349026222344129"
    assert message.group.type == "ROOM"
    assert message.group.id == "TnsHiQtZFKB3x5CpRsbxdn___pW3e4sgdA"

    # Message with image attachments
    image_message_event = {'id': '2rtywY', 'messageId': 'gPbZ1q584zta5gkYK1uxnX___pKGl5sibQ', 'timestamp': 1569699947741, 'type': 'MESSAGESENT', 'initiator': {'user': {'userId': 349026222344129, 'firstName': 'Uezo', 'lastName': 'Chan', 'displayName': 'uezochan', 'email': 'minette@uezo.net', 'username': 'minette@uezo.net'}}, 'payload': {'messageSent': {'message': {'messageId': 'gPbZ1q584zta5gkYK1uxnX___pKGl5sibQ', 'timestamp': 1569699947741, 'message': '<div data-format="PresentationML" data-version="2.0" class="wysiwyg"><p>not okay</p></div>', 'data': '{}', 'attachments': [{'id': 'internal_349026222344129%2F57HU6TaEzV8uB83gKN6j3g%3D%3D', 'name': 'ダメだ.jpeg', 'size': 20342, 'images': [{'id': 'internal_349026222344129%2FY1a0PkG13uAI3vlJdDJjYA%3D%3D', 'dimension': '600'}]}], 'user': {'userId': 349026222344129, 'firstName': 'Uezo', 'lastName': 'Chan', 'displayName': 'uezochan', 'email': 'minette@uezo.net', 'username': 'minette@uezo.net'}, 'stream': {'streamId': 'On45D2InfVgaI2vhrMgXRn___pW3fpQfdA', 'streamType': 'IM'}, 'externalRecipients': False, 'userAgent': 'DESKTOP-40.0.0-10665-MacOSX-10.14.6-Safari-12.1.2', 'originalFormat': 'com.symphony.messageml.v2'}}}}
    message = adapter._to_minette_message(image_message_event)
    assert isinstance(message, Message)
    assert message.text == "not okay"
    assert message.channel == "Symphony"
    assert message.channel_user_id == "349026222344129"
    assert message.group is None
    assert len(message.payloads) == 1
    assert message.payloads[0].content_type == "image"
    assert message.payloads[0].content["id"] == "internal_349026222344129%2F57HU6TaEzV8uB83gKN6j3g%3D%3D"
    assert message.payloads[0].content["name"] == "ダメだ.jpeg"

    # Message with file attachments
    file_message_event = {'id': 'JcmfIY', 'messageId': 'eDXqRLWFgMuyYKwcw1m6qn___pKGjg18bQ', 'timestamp': 1569700573827, 'type': 'MESSAGESENT', 'initiator': {'user': {'userId': 349026222344129, 'firstName': 'Uezo', 'lastName': 'Chan', 'displayName': 'uezochan', 'email': 'minette@uezo.net', 'username': 'minette@uezo.net'}}, 'payload': {'messageSent': {'message': {'messageId': 'eDXqRLWFgMuyYKwcw1m6qn___pKGjg18bQ', 'timestamp': 1569700573827, 'message': '<div data-format="PresentationML" data-version="2.0" class="wysiwyg"><p>sample excel data</p></div>', 'data': '{}', 'attachments': [{'id': 'internal_349026222344129%2FlzurB8IGd9tw6IANSoa9xA%3D%3D', 'name': 'sample.xlsx', 'size': 8805, 'images': []}], 'user': {'userId': 349026222344129, 'firstName': 'Uezo', 'lastName': 'Chan', 'displayName': 'uezochan', 'email': 'minette@uezo.net', 'username': 'minette@uezo.net'}, 'stream': {'streamId': 'On45D2InfVgaI2vhrMgXRn___pW3fpQfdA', 'streamType': 'IM'}, 'externalRecipients': False, 'userAgent': 'DESKTOP-40.0.0-10665-MacOSX-10.14.6-Safari-12.1.2', 'originalFormat': 'com.symphony.messageml.v2'}}}}
    message = adapter._to_minette_message(file_message_event)
    assert isinstance(message, Message)
    assert message.text == "sample excel data"
    assert message.channel == "Symphony"
    assert message.channel_user_id == "349026222344129"
    assert message.group is None
    assert len(message.payloads) == 1
    assert message.payloads[0].content_type == "file"
    assert message.payloads[0].content["id"] == "internal_349026222344129%2FlzurB8IGd9tw6IANSoa9xA%3D%3D"
    assert message.payloads[0].content["name"] == "sample.xlsx"


def test_to_channel_message():
    message = SymphonyAdapter._to_channel_message(Message(text="hello"))
    assert message == {"message": "<messageML>hello</messageML>"}


def test_handle_event():
    adapter = SymphonyAdapter(
        symphony_config="config/private/symphony/symphony.json",
        default_dialog_service=MyDialog,
        prepare_table=True)

    im_message_event = {'id': 'J5uf7A', 'messageId': '3LxcjF9_c5V4KYMpO9RcTn___pKGq_chbQ', 'timestamp': 1569698613470, 'type': 'MESSAGESENT', 'initiator': {'user': {'userId': 349026222344129, 'firstName': 'Uezo', 'lastName': 'Chan', 'displayName': 'uezochan', 'email': 'minette@uezo.net', 'username': 'minette@uezo.net'}}, 'payload': {'messageSent': {'message': {'messageId': '3LxcjF9_c5V4KYMpO9RcTn___pKGq_chbQ', 'timestamp': 1569698613470, 'message': '<div data-format="PresentationML" data-version="2.0" class="wysiwyg"><p>hello</p></div>', 'data': '{}', 'user': {'userId': 349026222344129, 'firstName': 'Uezo', 'lastName': 'Chan', 'displayName': 'uezochan', 'email': 'minette@uezo.net', 'username': 'minette@uezo.net'}, 'stream': {'streamId': 'On45D2InfVgaI2vhrMgXRn___pW3fpQfdA', 'streamType': 'IM'}, 'externalRecipients': False, 'userAgent': 'DESKTOP-40.0.0-10665-MacOSX-10.14.6-Safari-12.1.2', 'originalFormat': 'com.symphony.messageml.v2'}}}}
    adapter.handle_event(im_message_event)
