import traceback
from datetime import datetime

from linebot import LineBotApi, WebhookParser
from linebot.exceptions import InvalidSignatureError
from linebot.models import (
    Event, BeaconEvent, FollowEvent, JoinEvent, LeaveEvent, MessageEvent,
    PostbackEvent, UnfollowEvent, MemberJoinedEvent, MemberLeftEvent,
    TextMessage, ImageMessage, AudioMessage, VideoMessage, LocationMessage,
    StickerMessage, TextSendMessage, ImageSendMessage, AudioSendMessage,
    VideoSendMessage, LocationSendMessage, StickerSendMessage,
    ImagemapSendMessage, TemplateSendMessage, FlexSendMessage
)

from .base import Adapter
from ..models import (
    Message,
    Payload,
    Group,
    Response,
    Context
)


class LineAdapter(Adapter):
    """
    Adapter for LINE Messaging API

    Attributes
    ----------
    bot : minette.Minette
        Instance of Minette
    channel_secret : str
        Channel Secret
    channel_access_token : str
        Channel Access Token
    parser : WebhookParser
        WebhookParser
    api : LineBotApi
        LineBotApi
    config : minette.Config
        Configuration
    timezone : pytz.timezone
        Timezone
    logger : logging.Logger
        Logger
    threads : int
        Number of worker threads to process requests
    executor : ThreadPoolExecutor
        Thread pool of workers
    debug : bool
        Debug mode
    """

    def __init__(self, bot=None, *, threads=None, debug=False,
                 channel_secret=None, channel_access_token=None, **kwargs):
        """
        Parameters
        ----------
        bot : minette.Minette, default None
            Instance of Minette.
            If None, create new instance of Minette by using `**kwargs`
        channel_secret : str, default None
            Channel Secret
        channel_access_token : str, default None
            Channel Access Token
        threads : int, default None
            Number of worker threads to process requests
        debug : bool, default None
            Debug mode
        """
        super().__init__(bot=bot, threads=threads, debug=debug, **kwargs)
        self.channel_secret = channel_secret or \
            self.config.get(section="line_bot_api", key="channel_secret")
        self.channel_access_token = channel_access_token or \
            self.config.get(section="line_bot_api", key="channel_access_token")
        self.parser = WebhookParser(self.channel_secret)
        self.api = LineBotApi(self.channel_access_token)

    def handle_http_request(self, request_data, request_headers):
        """
        Interface to chat with LINE Bot

        Parameters
        ----------
        request_data : list of byte
            Request data from LINE Messaging API as string
        request_headers : dict
            Request headers from LINE Messaging API as dict

        Returns
        -------
        response : Response
            Response that shows queued status
        """
        try:
            events = self.parser.parse(
                request_data.decode("utf-8"),
                request_headers.get("X-Line-Signature", ""))
            for ev in events:
                if self.executor:
                    self.executor.submit(self.handle_event, ev)
                else:
                    self.handle_event(ev)
            return Response(messages=[Message(text="done", type="system")])
        except InvalidSignatureError as ise:
            self.logger.error(
                "Request signiture is invalid: "
                + str(ise) + "\n" + traceback.format_exc())
            return Response(
                messages=[Message(text="invalid signiture", type="system")])
        except Exception as ex:
            self.logger.error(
                "Request parsing error: "
                + str(ex) + "\n" + traceback.format_exc())
            return Response(
                messages=[Message(text="failure in parsing request",
                                  type="system")])

    def handle_event(self, event):
        channel_messages, token = super().handle_event(event)
        for msg in channel_messages:
            if self.debug:
                self.logger.info(msg)
            else:
                self.logger.info("Minette> {}".format(
                    msg.text if hasattr(msg, "text") else msg.alt_text
                    if hasattr(msg, "alt_text") else msg.type))
        self.api.reply_message(token, channel_messages)

    def _extract_token(self, event):
        """
        Extract token from event

        Parameters
        ----------
        event : Event
            Event from LINE Messaging API

        Returns
        -------
        message : Message
            Request message object
        """
        return event.reply_token if hasattr(event, "reply_token") else ""

    def _to_minette_message(self, event):
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
        msg = Message(
            type=event.type,
            token=event.reply_token if hasattr(event, "reply_token") else None,
            channel="LINE",
            channel_detail="Messaging",
            channel_user_id=event.source.user_id,
            channel_message=event,
            timestamp=datetime.now(self.timezone))
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
            elif isinstance(event.message, (
                    ImageMessage, VideoMessage, AudioMessage)):
                msg.payloads.append(
                    Payload(
                        content_type=event.message.type,
                        url="https://api.line.me/v2/bot/message/%s/content" %
                            event.message.id,
                        headers={
                            "Authorization": "Bearer {%s}" %
                            self.channel_access_token
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
        elif isinstance(event, MemberJoinedEvent):
            pass
        elif isinstance(event, MemberLeftEvent):
            pass
        elif isinstance(event, BeaconEvent):
            pass
        else:
            pass
        return msg

    @staticmethod
    def _to_channel_message(message):
        """
        Convert Minette Message object to LINE SendMessage object

        Parameters
        ----------
        response : Message
            Response message object

        Returns
        -------
        response : SendMessage
            SendMessage object for LINE Messaging API
        """
        payload = next(iter([p for p in message.payloads
            if p.content_type != "quick_reply"]), None)
        quick_reply = next(iter([p.content for p in message.payloads
            if p.content_type == "quick_reply"]), None)
        if message.type == "text":
            return TextSendMessage(text=message.text,
                                   quick_reply=quick_reply)
        elif message.type == "image":
            return ImageSendMessage(original_content_url=payload.url,
                                    preview_image_url=payload.thumb,
                                    quick_reply=quick_reply)
        elif message.type == "audio":
            return AudioSendMessage(original_content_url=payload.url,
                                    duration=payload.content["duration"],
                                    quick_reply=quick_reply)
        elif message.type == "video":
            return VideoSendMessage(original_content_url=payload.url,
                                    preview_image_url=payload.thumb,
                                    quick_reply=quick_reply)
        elif message.type == "location":
            cont = payload.content
            return LocationSendMessage(title=cont["title"],
                                       address=cont["address"],
                                       latitude=cont["latitude"],
                                       longitude=cont["longitude"],
                                       quick_reply=quick_reply)
        elif message.type == "sticker":
            return StickerSendMessage(package_id=payload.content["package_id"],
                                      sticker_id=payload.content["sticker_id"],
                                      quick_reply=quick_reply)
        elif message.type == "imagemap":
            return ImagemapSendMessage(alt_text=message.text,
                                       base_url=payload.url,
                                       base_size=payload.content["base_size"],
                                       actions=payload.content["actions"],
                                       quick_reply=quick_reply)
        elif message.type == "template":
            return TemplateSendMessage(alt_text=message.text,
                                       template=payload.content,
                                       quick_reply=quick_reply)
        elif message.type == "flex":
            return FlexSendMessage(alt_text=message.text,
                                   contents=payload.content,
                                   quick_reply=quick_reply)
        else:
            return None
