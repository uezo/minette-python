""" Adapter for LINE """
from threading import Thread
from typing import List
from queue import Queue
import traceback
from minette import automata
from minette.dialog.message import Message, Payload
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    Event, BeaconEvent, FollowEvent, JoinEvent, LeaveEvent, MessageEvent, PostbackEvent, UnfollowEvent,
    TextMessage, ImageMessage, AudioMessage, VideoMessage, LocationMessage, StickerMessage,
    SendMessage, TextSendMessage, ImageSendMessage, AudioSendMessage, VideoSendMessage, LocationSendMessage, StickerSendMessage, ImagemapSendMessage, TemplateSendMessage
)

class WorkerThread(Thread):
    def __init__(self, bot:automata.Automata, channel_secret, channel_access_token):
        super(WorkerThread, self).__init__()
        # self.daemon = True
        self.bot = bot
        self.api = LineBotApi(channel_access_token)
        self.queue = Queue()
        self.channel_access_token = channel_access_token
        self.logger = bot.logger

    def run(self):
        while True:
            try:
                event = self.queue.get()
                req = self.map_request(event)
                res = self.bot.execute(req)
                for message in res:
                    print("minette> " + message.text)
                send_messages = self.map_response(res)
                if send_messages:
                    self.api.reply_message(event.reply_token, send_messages)
            except Exception as ex:
                self.logger.error("Error occured in replying message: " + str(ex) + "\n" + traceback.format_exc())

    def map_request(self, ev:Event) -> Message:
        print(ev)
        msg = Message(
            message_type=ev.type,
            token=ev.reply_token,
            channel="LINE",
            channel_user=ev.source.user_id,
            channel_message=ev)
        if isinstance(ev, MessageEvent):
            msg.message_id = ev.message.id
            msg.type = ev.message.type
            if isinstance(ev.message, TextMessage):
                msg.text = ev.message.text
            elif isinstance(ev.message, (ImageMessage, VideoMessage, AudioMessage)):
                msg.payloads.append(
                    Payload(content_type=ev.message.type,
                            url="https://api.line.me/v2/bot/message/%s/content" % ev.message.id,
                            headers={
                                "Authorization": "Bearer {%s}" % self.channel_access_token
                            })
                )
            elif isinstance(ev.message, LocationMessage):
                msg.payloads.append(
                    Payload(content_type=ev.message.type, content={
                        "title": ev.message.title,
                        "address": ev.message.address,
                        "latitude": ev.message.latitude,
                        "longitude": ev.message.longitude
                    })
                )
            elif isinstance(ev.message, StickerMessage):
                msg.payloads.append(
                    Payload(content_type=ev.message.type, content={
                        "package_id": ev.message.package_id,
                        "sticker_id": ev.message.sticker_id,
                    })
                )
        elif isinstance(ev, PostbackEvent):
            msg.payloads.append(
                Payload(content_type="postback", content={
                    "data": ev.postback.data
                })
            )
        elif isinstance(ev, FollowEvent):
            pass
        elif isinstance(ev, UnfollowEvent):
            pass
        elif isinstance(ev, JoinEvent):
            pass
        elif isinstance(ev, LeaveEvent):
            pass
        elif isinstance(ev, BeaconEvent):
            pass
        else:
            pass
        return msg

    def map_response(self, messages:List[Message]) -> List[SendMessage]:
        send_messages = []
        for msg in messages:
            if msg.type == "text":
                send_messages.append(TextSendMessage(text=msg.text))
            elif msg.type == "image":
                send_messages.append(ImageSendMessage(original_content_url=msg.payloads[0].url, preview_image_url=msg.payloads[0].thumb))
            elif msg.type == "audio":
                send_messages.append(AudioSendMessage(original_content_url=msg.payloads[0].url, duration=msg.payloads[0].content["duration"]))
            elif msg.type == "video":
                send_messages.append(VideoSendMessage(original_content_url=msg.payloads[0].url, preview_image_url=msg.payloads[0].thumb))
            elif msg.type == "location":
                cont = msg.payloads[0].content
                send_messages.append(LocationSendMessage(title=cont["title"], address=cont["address"], latitude=cont["latitude"], longitude=cont["longitude"]))
            elif msg.type == "sticker":
                send_messages.append(StickerSendMessage(package_id=msg.payloads[0].content["package_id"], sticker_id=msg.payloads[0].content["sticker_id"]))
            elif msg.type == "imagemap":
                send_messages.append(ImagemapSendMessage(alt_text=msg.text, base_url=msg.payloads[0].url, base_size=msg.payloads[0].content["base_size"], actions=msg.payloads[0].content["actions"]))
            elif msg.type == "template":
                send_messages.append(TemplateSendMessage(alt_text=msg.text, template=msg.payloads[0].content))
        return send_messages

class RequestParser:
    def __init__(self, worker:WorkerThread, channel_secret):
        self.worker = worker
        self.parser = WebhookParser(channel_secret)

    def parse_request(self, request):
        signature = request.headers['X-Line-Signature']
        body = request.get_data(as_text=True)
        try:
            events = self.parser.parse(body, signature)
            for event in events:
                self.worker.queue.put(event)
        except InvalidSignatureError:
            return 400
        except Exception as ex:
            self.worker.logger.error("Request parsing error: " + str(ex) + "\n" + traceback.format_exc())
            return 500
        return 200
