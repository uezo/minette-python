""" Adapter for LINE """
from logging import Logger
import traceback
from time import time
from concurrent.futures import ThreadPoolExecutor
from minette import Minette
from minette.message import Message, Payload, Group, Response
from minette.channel import Adapter
from minette.session import Session
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


class LineAdapter(Adapter):
    """
    Adapter for LINE Messaging API

    Attributes
    ----------
    minette : Minette
        Instance of Minette
    channel_secret : str
        Channel Secret for your LINE Bot
    channel_access_token : str
        Channel Access Token for your LINE Bot
    api : LineBotApi
        LINE Messaging API
    threads : int
        Number of worker thread
    thread_pool : [WorkerThread]
        Pool of worker threads for processing queued requests
    logger : Logger
        Logger
    debug : bool
        Debug mode
    """

    def __init__(self, minette, channel_secret,
                 channel_access_token, *, api=None, threads=None, logger=None, debug=False):
        """
        Parameters
        ----------
        minette : Minette
            Instance of Minette
        channel_secret : str or None, default None
            Channel Secret for your LINE Bot
        channel_access_token : str or None, default None
            Channel Access Token for your LINE Bot
        api : LineBotApi, default None
            Messaging API interface
        threads : int, default 16
            Number of worker thread
        logger : Logger, default None
            Logger
        debug : bool, default False
            Debug mode
        """
        super().__init__(minette, logger, debug)
        self.channel_secret = channel_secret
        self.channel_access_token = channel_access_token
        self.parser = WebhookParser(self.channel_secret)
        self.api = api or LineBotApi(self.channel_access_token)
        self.threads = threads
        if self.threads != 0:
            self.logger.info("Using worker threads to handle events")
            self.executor = ThreadPoolExecutor(max_workers=self.threads, thread_name_prefix="Thread")
        else:
            self.logger.info(f"Using main thread to handle events")
            self.executor = None
        self.minette.dialog_router.helpers["line_adapter"] = self
        if self.minette.task_scheduler:
            self.minette.task_scheduler.helpers["line_adapter"] = self

    def chat(self, request_data_as_text, request_headers):
        """
        Interface to chat with LINE Bot

        Parameters
        ----------
        request_data_as_text : str
            Request data from LINE Messaging API as string
        request_headers : dict
            Request headers from LINE Messaging API as dict

        Returns
        -------
        response : Response
            Response that shows queued status
        """
        try:
            events = self.parser.parse(request_data_as_text, request_headers.get("X-Line-Signature", ""))
            for ev in events:
                if self.executor:
                    self.executor.submit(self.handle_event, ev)
                else:
                    self.handle_event(ev)
            return Response(messages=[Message(text="done", type="system")])
        except InvalidSignatureError as ise:
            self.logger.error("Request signiture is invalid: " + str(ise) + "\n" + traceback.format_exc())
            return Response(messages=[Message(text="invalid signiture", type="system")])
        except Exception as ex:
            self.logger.error("Request parsing error: " + str(ex) + "\n" + traceback.format_exc())
            return Response(messages=[Message(text="failure in parsing request", type="system")])

    def handle_event(self, event):
        """
        Handle event and reply message

        Parameters
        ----------
        event : Event
            Event data from LINE Messaging API
        """
        message = self.to_minette_message(event)
        reply_token = event.reply_token if hasattr(event, "reply_token") else ""
        response = self.minette.chat(message)
        line_messages = [self.to_line_message(m) for m in response.messages]
        if line_messages:
            self.reply(line_messages, reply_token)

    def to_minette_message(self, event):
        """
        Convert LINE Event object to Minette Message object

        Parameters
        ----------
        event : Event
            Event from LINE Messaging API

        Returns
        -------
        message : Message
            Request message object
        """
        if self.debug:
            self.logger.info(event)
        msg = Message(
            type=event.type,
            token=event.reply_token if hasattr(event, "reply_token") else None,
            channel="LINE",
            channel_detail="Messaging",
            channel_user_id=event.source.user_id,
            channel_message=event)
        if event.source.type in ["group", "room"]:
            if event.source.type == "group":
                msg.group = Group(id=event.source.group_id, type="group")
            elif event.source.type == "room":
                msg.group = Group(id=event.source.room_id, type="room")
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

    def to_line_message(self, message):
        """
        Convert Minette Message object to LINE SendMessage object

        Parameters
        ----------
        response : Message
            Response message object

        Returns
        -------
        response : Response
            SendMessage object for LINE Messaging API
        """
        payload = next(iter([p for p in message.payloads if p.content_type != "quick_reply"]), None)
        quick_reply = next(iter([p.content for p in message.payloads if p.content_type == "quick_reply"]), None)
        if message.type == "text":
            return TextSendMessage(text=message.text, quick_reply=quick_reply)
        elif message.type == "image":
            return ImageSendMessage(original_content_url=payload.url, preview_image_url=payload.thumb, quick_reply=quick_reply)
        elif message.type == "audio":
            return AudioSendMessage(original_content_url=payload.url, duration=payload.content["duration"], quick_reply=quick_reply)
        elif message.type == "video":
            return VideoSendMessage(original_content_url=payload.url, preview_image_url=payload.thumb, quick_reply=quick_reply)
        elif message.type == "location":
            cont = payload.content
            return LocationSendMessage(title=cont["title"], address=cont["address"], latitude=cont["latitude"], longitude=cont["longitude"], quick_reply=quick_reply)
        elif message.type == "sticker":
            return StickerSendMessage(package_id=payload.content["package_id"], sticker_id=payload.content["sticker_id"], quick_reply=quick_reply)
        elif message.type == "imagemap":
            return ImagemapSendMessage(alt_text=message.text, base_url=payload.url, base_size=payload.content["base_size"], actions=payload.content["actions"], quick_reply=quick_reply)
        elif message.type == "template":
            return TemplateSendMessage(alt_text=message.text, template=payload.content, quick_reply=quick_reply)
        elif message.type == "flex":
            return FlexSendMessage(alt_text=message.text, contents=payload.content, quick_reply=quick_reply)
        else:
            return None

    def reply(self, line_messages, reply_token):
        """
        Send reply messages to LINE Messaging API

        Parameters
        ----------
        line_messages : list
            List of SendMessage objects
        reply_token : str
            ReplyToken for LINE Messaging API
        """
        for msg in line_messages:
            if self.debug:
                self.logger.info(msg)
            else:
                self.logger.info("Minette> {}".format(msg.text if hasattr(msg, "text") else msg.alt_text if hasattr(msg, "alt_text") else msg.type))
        self.api.reply_message(reply_token, line_messages)

    def push(self, channel_user_id, messages, formatted=False):
        """
        Interface to push messages to user

        Parameters
        ----------
        channel_user_id : str
            Destination user
        messages : Message
            Message to user
        formatted : bool, default False
            Messages are already formatted for LINE Messaging API

        Returns
        -------
        success : bool
            Message pushed successfully or not
        """
        success = False
        try:
            start_time = time()
            connection = self.minette.connection_provider.get_connection()
            push_request = Message(type="push", text="", channel="LINE", channel_detail="Messaging", channel_user_id=channel_user_id)
            push_request.user = self.minette.user_repository.get_user(channel="LINE", channel_user_id=channel_user_id, connection=connection)
            session = Session(channel="LINE", channel_user_id=channel_user_id)
            if formatted:
                texts = [msg.text if hasattr(msg, "text") else msg.alt_text if hasattr(msg, "alt_text") else msg.type for msg in messages]
                response = Response(messages=[Message(text=text) for text in texts])
                response.for_channel = messages
            else:
                response = Response(messages=[Message(text=messages)] if isinstance(messages, str) else [messages] if isinstance(messages, Message) else messages)
                response = self.format_response(response)
            self.api.push_message(to=channel_user_id, messages=response.for_channel)
            response.milliseconds = int((time() - start_time) * 1000)
            success = True
            self.minette.message_logger.write(push_request, response, session, connection)
        except Exception as ex:
            self.logger.error("Error occured in pushing message: " + str(ex) + "\n" + traceback.format_exc())
        return success

    def update_profile(self, user):
        """
        Update user profile by LINE Messaging API

        Parameters
        ----------
        user : User
            User to update
        """
        if not user.channel_user_id:
            return
        try:
            profile = self.api.get_profile(user.channel_user_id)
            user.name = profile.display_name
            user.profile_image_url = profile.picture_url
        except Exception as ex:
            self.logger.error("Error occured in updating profile: " + str(ex) + "\n" + traceback.format_exc())
