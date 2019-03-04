""" Adapter for LINE """
from logging import Logger
import traceback
from threading import Thread
from queue import Queue
from minette import Minette
from minette.message import Message, Payload, Group, Response
from minette.channel import Adapter
from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    Event, BeaconEvent, FollowEvent, JoinEvent, LeaveEvent, MessageEvent,
    PostbackEvent, UnfollowEvent,
    TextMessage, ImageMessage, AudioMessage, VideoMessage, LocationMessage,
    StickerMessage, TextSendMessage, ImageSendMessage, AudioSendMessage,
    VideoSendMessage, LocationSendMessage, StickerSendMessage,
    ImagemapSendMessage, TemplateSendMessage, FlexSendMessage
)


class WorkerThread(Thread):
    """
    Worker for processing queued requests

    Attributes
    ----------
    adapter : LineAdapter
        Adapter for LINE Messaging API
    queue : Queue
        Request queue
    """

    def __init__(self, adapter):
        """
        Parameters
        ----------
        adapter : LineAdapter
            Adapter for LINE Messaging API
        """
        super().__init__()
        self.adapter = adapter
        self.queue = Queue()

    def run(self):
        """
        Run the loop for processing queued requests
        """
        while True:
            try:
                message = self.queue.get()
                response = self.adapter.minette.chat(message)
                self.adapter.send(self.adapter.format_response(response))
            except Exception as ex:
                self.minette.logger.error("Error occured in processing queue message: " + str(ex) + "\n" + traceback.format_exc())


class LineAdapter(Adapter):
    """
    Adapter for LINE Messaging API

    Attributes
    ----------
    minette : Minette
        Instance of Minette
    line_bot_api : LineBotApi
        LINE Messaging API
    worker : WorkerThread
        Worker for processing queued requests
    logger : Logger
        Logger
    debug : bool
        Debug mode
    """

    def __init__(self, minette, channel_secret=None, 
                 channel_access_token=None, logger=None, debug=False):
        """
        Parameters
        ----------
        minette : Minette
            Instance of Minette
        channel_secret : str or None, default None
            Channel Secret for your LINE Bot
        channel_access_token : str or None, default None
            Channel Access Token for your LINE Bot
        logger : Logger, default None
            Logger
        debug : bool, default False
            Debug mode
        """
        super().__init__(minette, logger, debug)
        self.parser = WebhookParser(
            channel_secret if channel_secret else minette.config.get(section="line_bot_api", key="channel_secret"))
        self.line_bot_api = LineBotApi(
            channel_access_token if channel_access_token else minette.config.get(section="line_bot_api", key="channel_access_token"))
        self.worker = WorkerThread(self)
        self.worker.start()

    def parse_request(self, event):
        """
        Parse event to Message object

        Parameters
        ----------
        event : Event
            Event from LINE Messaging API

        Returns
        -------
        message : Message
            Request converted into Message object
        """
        if self.debug:
            self.logger.info(event)
        msg = Message(
            type=event.type,
            token=event.reply_token,
            channel="LINE",
            channel_detail="Messaging",
            channel_user_id=event.source.user_id,
            channel_message=event)
        if event.source.type in ["group", "room"]:
            # group = Group(group_type=event.source.type)
            if event.source.type == "group":
                # group.id = event.source.group_id
                msg.group = Group(id=event.source.group_id, type="group")
            elif event.source.type == "room":
                # group.id = event.source.room_id
                msg.group = Group(id=event.source.room_id, type="room")
            # if group.id:
            #     msg.group = group
        if isinstance(event, MessageEvent):
            msg.id = event.message.id
            msg.type = event.message.type
            if isinstance(event.message, TextMessage):
                msg.text = event.message.text
            elif isinstance(event.message, (ImageMessage, VideoMessage, AudioMessage)):
                msg.payloads.append(
                    Payload(content_type=event.message.type,
                            url="https://api.line.me/v2/bot/message/%s/content" % event.message.id,
                            headers={
                                "Authorization": "Bearer {%s}" % self.channel_access_token
                            })
                )
            elif isinstance(event.message, LocationMessage):
                msg.payloads.append(
                    Payload(content_type=event.message.type, content={
                        "title": event.message.title,
                        "address": event.message.address,
                        "latitude": event.message.latitude,
                        "longitude": event.message.longitude
                    })
                )
            elif isinstance(event.message, StickerMessage):
                msg.payloads.append(
                    Payload(content_type=event.message.type, content={
                        "package_id": event.message.package_id,
                        "sticker_id": event.message.sticker_id,
                    })
                )
        elif isinstance(event, PostbackEvent):
            msg.payloads.append(
                Payload(content_type="postback", content={
                    "data": event.postback.data,
                    "params": event.postback.params
                })
            )
        elif isinstance(event, FollowEvent):
            pass
        elif isinstance(event, UnfollowEvent):
            pass
        elif isinstance(event, JoinEvent):
            pass
        elif isinstance(event, LeaveEvent):
            pass
        elif isinstance(event, BeaconEvent):
            pass
        else:
            pass
        return msg

    def format_response(self, response):
        """
        Set LINE Messaging API formatted response to `for_channel` attribute

        Parameters
        ----------
        response : Response
            Response from chatbot

        Returns
        -------
        response : Response
            Response with LINE Messaging API formatted response
        """
        send_messages = []
        for msg in response.messages:
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
        response.for_channel = send_messages
        response.headers = {"reply_token": response.messages[0].token if response.messages else ""}
        return response

    def chat(self, request_data_as_text, request_headers):
        """
        Interface to chat with LINE Bot

        Parameters
        ----------
        request_data_as_text : str
            Request from LINE Messaging API as string

        Returns
        -------
        response : Response
            Response that shows queued status. The response from chatbot will be sent by worker thread
        """
        try:
            messages = []
            signature = request_headers["X-Line-Signature"]
            events = self.parser.parse(request_data_as_text, signature)
            for ev in events:
                messages.append(self.parse_request(ev))
            for message in messages:
                self.worker.queue.put(message)
            return Response(messages=[Message(text="queued", type="system")], for_channel="queued")
        except InvalidSignatureError:
            self.logger.error("Request signiture is invalid: " + str(ex) + "\n" + traceback.format_exc())
            return Response(messages=[Message(text="invalid signiture", type="system")], for_channel="invalid signiture")
        except Exception as ex:
            self.logger.error("Request parsing error: " + str(ex) + "\n" + traceback.format_exc())
            return Response(messages=[Message(text="failure in parsing request", type="system")], for_channel="failure in parsing request")

    def send(self, response):
        """
        Send response from chatbot to Reply API

        Parameters
        ----------
        response : Response
            Response with LINE Messaging API formatted response
        """
        if response.messages:
            for msg in response.for_channel:
                if self.debug:
                    self.logger.info(msg)
                else:
                    self.logger.info("Minette> {}".format(msg.text if hasattr(msg, "text") else msg.alt_text if hasattr(msg, "alt_text") else msg.type)) 
            self.line_bot_api.reply_message(response.headers["reply_token"], response.for_channel)
