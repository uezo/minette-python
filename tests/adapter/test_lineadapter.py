import pytest
from pytz import timezone
from concurrent.futures import ThreadPoolExecutor

from linebot import LineBotApi, WebhookParser
from linebot.models import (
    Event, BeaconEvent, FollowEvent, JoinEvent, LeaveEvent, MessageEvent,
    PostbackEvent, UnfollowEvent, MemberJoinedEvent, MemberLeftEvent,
    AccountLinkEvent,
    TextMessage, ImageMessage, AudioMessage, VideoMessage, LocationMessage,
    StickerMessage, TextSendMessage, ImageSendMessage, AudioSendMessage,
    VideoSendMessage, LocationSendMessage, StickerSendMessage,
    ImagemapSendMessage, TemplateSendMessage, FlexSendMessage,
    ImagemapAction, ButtonsTemplate, FlexContainer,
)
from linebot.exceptions import LineBotApiError, InvalidSignatureError

from minette import DialogService, Message, Payload, Config
from minette.adapter.lineadapter import LineAdapter


lineconfig = Config("config/test_config_adapter.ini")

channel_secret = lineconfig.get("channel_secret", section="line_bot_api")
channel_access_token = lineconfig.get("channel_access_token", section="line_bot_api")


class MyDialog(DialogService):
    def compose_response(self, request, context, connection):
        return "res:" + request.text


def test_init():
    adapter = LineAdapter(
        channel_secret=channel_secret,
        channel_access_token=channel_access_token, prepare_table=True)
    assert isinstance(adapter.parser, WebhookParser)
    assert isinstance(adapter.api, LineBotApi)


def test_extract_token():
    adapter = LineAdapter(
        channel_secret=channel_secret,
        channel_access_token=channel_access_token, prepare_table=True)
    event = MessageEvent.new_from_json_dict({
        "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
        "type": "message",
        "timestamp": 1462629479859,
        "source": {
            "type": "user",
            "userId": "U4af4980629..."
        },
        "message": {
            "id": "325708",
            "type": "text",
            "text": "Hello, world!"
        }
    })
    token = adapter._extract_token(event)
    assert token == "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA"


def test_to_minette_message():
    # setup adapter
    adapter = LineAdapter(
        channel_secret=channel_secret,
        channel_access_token=channel_access_token, prepare_table=True)

    # text
    event = MessageEvent.new_from_json_dict({
        "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
        "type": "message",
        "timestamp": 1462629479859,
        "source": {
            "type": "user",
            "userId": "U4af4980629..."
        },
        "message": {
            "id": "325708",
            "type": "text",
            "text": "Hello, world!"
        }
    })
    message = adapter._to_minette_message(event)
    assert message.id == "325708"
    assert message.type == "text"
    assert message.text == "Hello, world!"
    assert message.channel_user_id == "U4af4980629..."

    # image
    event = MessageEvent.new_from_json_dict({
        "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
        "type": "message",
        "timestamp": 1462629479859,
        "source": {
            "type": "user",
            "userId": "U4af4980629..."
        },
        "message": {
            "id": "325708",
            "type": "image",
            "contentProvider": {
                "type": "line"
            }
        }
    })
    message = adapter._to_minette_message(event)
    assert message.type == "image"
    assert message.payloads[0].url == \
        "https://api.line.me/v2/bot/message/325708/content"
    assert message.payloads[0].thumb == \
        "https://api.line.me/v2/bot/message/325708/content"

    # video
    event = MessageEvent.new_from_json_dict({
        "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
        "type": "message",
        "timestamp": 1462629479859,
        "source": {
            "type": "user",
            "userId": "U4af4980629..."
        },
        "message": {
            "id": "325708",
            "type": "video",
            "duration": 60000,
            "contentProvider": {
                "type": "external",
                "originalContentUrl": "https://example.com/original.mp4",
                "previewImageUrl": "https://example.com/preview.jpg"
            }
        }
    })
    message = adapter._to_minette_message(event)
    assert message.type == "video"
    assert message.payloads[0].url == \
        "https://api.line.me/v2/bot/message/325708/content"
    assert message.payloads[0].thumb == \
        "https://api.line.me/v2/bot/message/325708/content"

    # audio
    event = MessageEvent.new_from_json_dict({
        "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
        "type": "message",
        "timestamp": 1462629479859,
        "source": {
            "type": "user",
            "userId": "U4af4980629..."
        },
        "message": {
            "id": "325708",
            "type": "audio",
            "duration": 60000,
            "contentProvider": {
                "type": "line"
            }
        }
    })
    message = adapter._to_minette_message(event)
    assert message.type == "audio"
    assert message.payloads[0].url == \
        "https://api.line.me/v2/bot/message/325708/content"

    # location
    event = MessageEvent.new_from_json_dict({
        "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
        "type": "message",
        "timestamp": 1462629479859,
        "source": {
            "type": "user",
            "userId": "U4af4980629..."
        },
        "message": {
            "id": "325708",
            "type": "location",
            "title": "my location",
            "address": "〒150-0002 東京都渋谷区渋谷２丁目２１−１",
            "latitude": 35.65910807942215,
            "longitude": 139.70372892916203
        }
    })
    message = adapter._to_minette_message(event)
    assert message.type == "location"
    assert message.payloads[0].content["title"] == "my location"
    assert message.payloads[0].content["address"] == \
        "〒150-0002 東京都渋谷区渋谷２丁目２１−１"
    assert message.payloads[0].content["latitude"] == 35.65910807942215
    assert message.payloads[0].content["longitude"] == 139.70372892916203

    # sticker
    event = MessageEvent.new_from_json_dict({
        "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
        "type": "message",
        "timestamp": 1462629479859,
        "source": {
            "type": "user",
            "userId": "U4af4980629..."
        },
        "message": {
            "id": "325708",
            "type": "sticker",
            "packageId": "1",
            "stickerId": "2"
        }
    })
    message = adapter._to_minette_message(event)
    assert message.type == "sticker"
    assert message.payloads[0].content["package_id"] == "1"
    assert message.payloads[0].content["sticker_id"] == "2"

    # postback
    event = PostbackEvent.new_from_json_dict({
        "type": "postback",
        "replyToken": "b60d432864f44d079f6d8efe86cf404b",
        "source": {
            "userId": "U91eeaf62d...",
            "type": "user"
        },
        "timestamp": 1513669370317,
        "postback": {
            "data": "storeId=12345",
            "params": {
                "datetime": "2017-12-25T01:00"
            }
        }
    })
    message = adapter._to_minette_message(event)
    assert message.type == "postback"
    assert message.payloads[0].content["data"] == "storeId=12345"
    assert message.payloads[0].content["params"] == \
        {"datetime": "2017-12-25T01:00"}

    # follow
    event = FollowEvent.new_from_json_dict({
        "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
        "type": "follow",
        "timestamp": 1462629479859,
        "source": {
            "type": "user",
            "userId": "U4af4980629..."
        }
    })
    message = adapter._to_minette_message(event)
    assert message.type == "follow"

    # unfollow
    event = UnfollowEvent.new_from_json_dict({
        "type": "unfollow",
        "timestamp": 1462629479859,
        "source": {
            "type": "user",
            "userId": "U4af4980629..."
        }
    })
    message = adapter._to_minette_message(event)
    assert message.type == "unfollow"

    # join
    event = JoinEvent.new_from_json_dict({
        "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
        "type": "join",
        "timestamp": 1462629479859,
        "source": {
            "type": "group",
            "groupId": "C4af4980629..."
        }
    })
    message = adapter._to_minette_message(event)
    assert message.type == "join"

    # leave
    event = LeaveEvent.new_from_json_dict({
        "type": "leave",
        "timestamp": 1462629479859,
        "source": {
            "type": "group",
            "groupId": "C4af4980629..."
        }
    })
    message = adapter._to_minette_message(event)
    assert message.type == "leave"

    # member join
    event = MemberJoinedEvent.new_from_json_dict({
        "replyToken": "0f3779fba3b349968c5d07db31eabf65",
        "type": "memberJoined",
        "timestamp": 1462629479859,
        "source": {
            "type": "room",
            "roomId": "C4af4980629..."
        },
        "joined": {
            "members": [
                {
                    "type": "user",
                    "userId": "U4af4980629..."
                },
                {
                    "type": "user",
                    "userId": "U91eeaf62d9..."
                }
            ]
        }
    })
    message = adapter._to_minette_message(event)
    assert message.type == "memberJoined"
    assert message.group.type == "room"

    # member leave
    event = MemberLeftEvent.new_from_json_dict({
        "type": "memberLeft",
        "timestamp": 1462629479960,
        "source": {
            "type": "room",
            "roomId": "C4af4980629..."
        },
        "left": {
            "members": [
                {
                    "type": "user",
                    "userId": "U4af4980629..."
                },
                {
                    "type": "user",
                    "userId": "U91eeaf62d9..."
                }
            ]
        }
    })
    message = adapter._to_minette_message(event)
    assert message.type == "memberLeft"
    assert message.group.type == "room"

    # beacon
    event = BeaconEvent.new_from_json_dict({
        "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
        "type": "beacon",
        "timestamp": 1462629479859,
        "source": {
            "type": "user",
            "userId": "U4af4980629..."
        },
        "beacon": {
            "hwid": "d41d8cd98f",
            "type": "enter"
        }
    })
    message = adapter._to_minette_message(event)
    assert message.type == "beacon"

    # other(account link)
    event = AccountLinkEvent.new_from_json_dict({
        "type": "accountLink",
        "replyToken": "b60d432864f44d079f6d8efe86cf404b",
        "source": {
            "userId": "U91eeaf62d...",
            "type": "user"
        },
        "timestamp": 1513669370317,
        "link": {
            "result": "ok",
            "nonce": "xxxxxxxxxxxxxxx"
        }
    })
    message = adapter._to_minette_message(event)
    assert message.type == "accountLink"


def test_to_channel_message():
    #     payload = next(iter([p for p in message.payloads if p.content_type != "quick_reply"]), None)
    #     quick_reply = next(iter([p.content for p in message.payloads if p.content_type == "quick_reply"]), None)

    message = LineAdapter._to_channel_message(Message(text="hello"))
    assert isinstance(message, TextSendMessage)
    assert message.text == "hello"

    message = LineAdapter._to_channel_message(Message(type="image",
        payloads=[Payload(url="https://image", thumb="https://thumb")]))
    assert isinstance(message, ImageSendMessage)
    assert message.original_content_url == "https://image"
    assert message.preview_image_url == "https://thumb"

    message = LineAdapter._to_channel_message(Message(type="audio",
        payloads=[Payload(url="https://audio", content={"duration": 1.2})]))
    assert isinstance(message, AudioSendMessage)
    assert message.original_content_url == "https://audio"
    assert message.duration == 1.2

    message = LineAdapter._to_channel_message(Message(type="video",
        payloads=[Payload(url="https://video", thumb="https://thumb")]))
    assert isinstance(message, VideoSendMessage)
    assert message.original_content_url == "https://video"
    assert message.preview_image_url == "https://thumb"

    message = LineAdapter._to_channel_message(
        Message(type="location", payloads=[Payload(content={
            "title": "Jiyugaoka",
            "address": "1-2-3 Jiyugaoka, Meguro-ku, Tokyo",
            "latitude": 35.607757, "longitude": 139.668411
        })])
    )
    assert isinstance(message, LocationSendMessage)
    assert message.title == "Jiyugaoka"
    assert message.address == "1-2-3 Jiyugaoka, Meguro-ku, Tokyo"
    assert message.latitude == 35.607757
    assert message.longitude == 139.668411

    message = LineAdapter._to_channel_message(Message(type="sticker",
        payloads=[Payload(content={
            "package_id": "11537", "sticker_id": "52002734"})]))
    assert isinstance(message, StickerSendMessage)
    assert message.package_id == "11537"
    assert message.sticker_id == "52002734"

    imagemap_action = {
        "type": "uri",
        "label": "https://example.com/",
        "linkUri": "https://example.com/",
        "area": {
            "x": 0,
            "y": 0,
            "width": 520,
            "height": 1040
        }
    }
    message = LineAdapter._to_channel_message(Message(type="imagemap",
        text="imagemap message",
        payloads=[Payload(
            url="https://imagemap",
            content={
                "base_size": {"width": 1040, "height": 585},
                "actions": [imagemap_action]})]))
    assert isinstance(message, ImagemapSendMessage)
    assert message.alt_text == "imagemap message"
    assert message.base_url == "https://imagemap"
    assert message.base_size.width == 1040
    assert message.base_size.height == 585
    assert message.actions[0].type == "uri"
    assert message.actions[0].link_uri == "https://example.com/"
    assert message.actions[0].area.width == 520

    template = {
        "type": "buttons",
        "thumbnailImageUrl": "https://example.com/bot/images/image.jpg",
        "imageAspectRatio": "rectangle",
        "imageSize": "cover",
        "imageBackgroundColor": "#FFFFFF",
        "title": "Menu",
        "text": "Please select",
        "defaultAction": {
            "type": "uri",
            "label": "View detail",
            "uri": "http://example.com/page/123"
        },
        "actions": [
            {
                "type": "postback",
                "label": "Buy",
                "data": "action=buy&itemid=123"
            },
            {
                "type": "postback",
                "label": "Add to cart",
                "data": "action=add&itemid=123"
            },
            {
                "type": "uri",
                "label": "View detail",
                "uri": "http://example.com/page/123"
            }
        ]
    }
    message = LineAdapter._to_channel_message(Message(type="template",
        text="template message", payloads=[Payload(content=template)]))
    assert isinstance(message, TemplateSendMessage)
    assert message.alt_text == "template message"
    assert isinstance(message.template, ButtonsTemplate)

    flex = {
        "type": "bubble",
        "body": {
            "type": "box",
            "layout": "vertical",
            "contents": [
                {
                    "type": "text",
                    "text": "hello"
                },
                {
                    "type": "text",
                    "text": "world"
                }
            ]
        }
    }
    message = LineAdapter._to_channel_message(Message(type="flex",
        text="flex message", payloads=[Payload(content=flex)]))
    assert isinstance(message, FlexSendMessage)
    assert message.alt_text == "flex message"
    assert isinstance(message.contents, FlexContainer)

    message = LineAdapter._to_channel_message(Message(type="unknown"))
    assert message is None


def test_handle_event():
    adapter = LineAdapter(
        channel_secret=channel_secret,
        channel_access_token=channel_access_token,
        default_dialog_service=MyDialog, debug=True, prepare_table=True
    )
    with pytest.raises(LineBotApiError):
        adapter.handle_event(MessageEvent.new_from_json_dict({
            "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
            "type": "message",
            "timestamp": 1462629479859,
            "source": {
                "type": "user",
                "userId": "U4af4980629..."
            },
            "message": {
                "id": "325708",
                "type": "text",
                "text": "Hello, world!"
            }
        }))
    adapter.debug = False
    with pytest.raises(LineBotApiError):
        adapter.handle_event(MessageEvent.new_from_json_dict({
            "replyToken": "nHuyWiB7yP5Zw52FIkcQobQuGDXCTA",
            "type": "message",
            "timestamp": 1462629479859,
            "source": {
                "type": "user",
                "userId": "U4af4980629..."
            },
            "message": {
                "id": "325708",
                "type": "text",
                "text": "Hello, world!"
            }
        }))


def test_handle_http_request():
    request_data = '{"events":[{"type":"message","replyToken":"e60740718df849e396e93600254b28b5","source":{"userId":"U4bb389af09ad694ace414ce22d57ac0f","type":"user"},"timestamp":1569657170129,"message":{"type":"text","id":"10646756260763","text":"hello"}}],"destination":"U9e20741b688ed93c536adbe97acee31d"}'.encode(encoding="utf-8")
    request_headers = {
        "X-Line-Signature": "Kj+MIQWKb6gE/IO8c9+TydGF3o9qx8sjC1qiqiTfDao=",
        "Content-Type": "application/json;charset=UTF-8",
        "Content-Length": 288,
        "Host": "host.name.local",
        "Accept": "*/*",
        "User-Agent": "LineBotWebhook/1.0",
        "X-Forwarded-Proto": "https",
        "X-Forwarded-For": "1.2.3.4"
    }
    # multi thread
    adapter = LineAdapter(
        channel_secret=channel_secret,
        channel_access_token=channel_access_token,
        default_dialog_service=MyDialog, prepare_table=True
    )
    response = adapter.handle_http_request(request_data, request_headers)
    # error will not be handled because error occures in worker thread
    assert response.messages[0].text == "done"

    # main thread
    adapter = LineAdapter(
        channel_secret=channel_secret,
        channel_access_token=channel_access_token,
        threads=0,
        default_dialog_service=MyDialog, prepare_table=True
    )
    response = adapter.handle_http_request(request_data, request_headers)
    assert response.messages[0].text == "failure in parsing request"

    # common error
    adapter.parser = None
    response = adapter.handle_http_request(request_data, request_headers)
    assert response.messages[0].text == "failure in parsing request"

    # signiture error
    request_headers = {
        "X-Line-Signature": "invalid_signiture",
        "Content-Type": "application/json;charset=UTF-8",
        "Content-Length": 288,
        "Host": "host.name.local",
        "Accept": "*/*",
        "User-Agent": "LineBotWebhook/1.0",
        "X-Forwarded-Proto": "https",
        "X-Forwarded-For": "1.2.3.4"
    }
    adapter = LineAdapter(
        channel_secret=channel_secret,
        channel_access_token=channel_access_token,
        default_dialog_service=MyDialog, prepare_table=True
    )
    response = adapter.handle_http_request(request_data, request_headers)
    assert response.messages[0].text == "invalid signiture"
