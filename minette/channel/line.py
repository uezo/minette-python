""" Adapter for LINE """
from threading import Thread
from queue import Queue
import traceback
from minette.dialog import Message, Payload, Group
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    BeaconEvent, FollowEvent, JoinEvent, LeaveEvent, MessageEvent, PostbackEvent, UnfollowEvent,
    TextMessage, ImageMessage, AudioMessage, VideoMessage, LocationMessage, StickerMessage,
    TextSendMessage, ImageSendMessage, AudioSendMessage, VideoSendMessage, LocationSendMessage, StickerSendMessage, ImagemapSendMessage, TemplateSendMessage, FlexSendMessage
)

class LineWorkerThread(Thread):
    def __init__(self, bot, channel_secret, channel_access_token):
        """
        :param bot: Bot
        :type bot: minette.Automata
        :param channel_secret: channel_secret
        :type channel_secret: str
        :param channel_access_token: channel_access_token
        :type channel_access_token: str
        """
        super(LineWorkerThread, self).__init__()
        self.bot = bot
        self.api = LineBotApi(channel_access_token)
        self.queue = Queue()
        self.channel_access_token = channel_access_token
        self.logger = bot.logger

    def run(self):
        """ Start worker thread """
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

    def map_request(self, ev):
        """
        :param ev: Event
        :type ev: Event
        :return: Message
        :rtype: Message
        """
        self.bot.logger.debug(ev)
        msg = Message(
            message_type=ev.type,
            token=ev.reply_token,
            channel="LINE",
            channel_user=ev.source.user_id,
            channel_message=ev)
        if ev.source.type in ["group", "room"]:
            group = Group(group_type=ev.source.type)
            if ev.source.type == "group":
                group.id = ev.source.group_id
            elif ev.source.type == "room":
                group.id = ev.source.room_id
            if group.id:
                msg.group = group
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
                    "data": ev.postback.data,
                    "params": ev.postback.params
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

    def map_response(self, messages):
        """
        :param messages: Messages
        :type messages: [Message]
        :return: SendMessages
        :rtype: [SendMessage]
        """
        send_messages = []
        for msg in messages:
            payload = next(iter([p for p in msg.payloads if p.content_type != "quick_reply"]), None)
            quick_reply = next(iter([p.content for p in msg.payloads if p.content_type == "quick_reply"]), None)
            if msg.type == "text":
                send_messages.append(TextSendMessage(text=msg.text, quick_reply=quick_reply))
            elif msg.type == "image":
                send_messages.append(ImageSendMessage(original_content_url=payload.url, preview_image_url=payload.thumb, quick_reply=quick_reply))
            elif msg.type == "audio":
                send_messages.append(AudioSendMessage(original_content_url=payload.url, duration=payload.content["duration"], quick_reply=quick_reply))
            elif msg.type == "video":
                send_messages.append(VideoSendMessage(original_content_url=payload.url, preview_image_url=payload.thumb, quick_reply=quick_reply))
            elif msg.type == "location":
                cont = payload.content
                send_messages.append(LocationSendMessage(title=cont["title"], address=cont["address"], latitude=cont["latitude"], longitude=cont["longitude"], quick_reply=quick_reply))
            elif msg.type == "sticker":
                send_messages.append(StickerSendMessage(package_id=payload.content["package_id"], sticker_id=payload.content["sticker_id"], quick_reply=quick_reply))
            elif msg.type == "imagemap":
                send_messages.append(ImagemapSendMessage(alt_text=msg.text, base_url=payload.url, base_size=payload.content["base_size"], actions=payload.content["actions"], quick_reply=quick_reply))
            elif msg.type == "template":
                send_messages.append(TemplateSendMessage(alt_text=msg.text, template=payload.content, quick_reply=quick_reply))
            elif msg.type == "flex":
                send_messages.append(FlexSendMessage(alt_text=msg.text, contents=payload.content, quick_reply=quick_reply))
        return send_messages

class LineAdapter:
    def __init__(self, worker, channel_secret):
        """
        :param worker: WorkerThread
        :type worker: WorkerThread
        :param channel_secret: channel_secret
        :type channel_secret: str
        """
        self.worker = worker
        self.parser = WebhookParser(channel_secret)

    def parse_request(self, request):
        """
        :param request: Flask HTTP Request
        :return: HTTP Status code
        :rtype: int
        """
        signature = request.headers["X-Line-Signature"]
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
