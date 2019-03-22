""" Adapter for LINE """
from logging import Logger
import traceback
from time import time
import random
from threading import Thread
from queue import Queue
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
        self.processing = ""

    def run(self):
        """
        Run the loop for processing queued requests
        """
        while True:
            try:
                message, self.processing = self.queue.get()
                response = self.adapter.minette.chat(message)
                self.adapter.send(self.adapter.format_response(response))
            except Exception as ex:
                self.adapter.logger.error("{}: Error occured in processing queue message: {}: ".format(self.name, message.id) + str(ex) + "\n" + traceback.format_exc())
            finally:
                self.processing = ""


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
    line_bot_api : LineBotApi
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

    def __init__(self, minette, channel_secret=None,
                 channel_access_token=None, threads=16, logger=None, debug=False):
        """
        Parameters
        ----------
        minette : Minette
            Instance of Minette
        channel_secret : str or None, default None
            Channel Secret for your LINE Bot
        channel_access_token : str or None, default None
            Channel Access Token for your LINE Bot
        threads : int, default 16
            Number of worker thread
        logger : Logger, default None
            Logger
        debug : bool, default False
            Debug mode
        """
        super().__init__(minette, logger, debug)
        self.channel_secret = channel_secret if channel_secret else minette.config.get(section="line_bot_api", key="channel_secret")
        self.channel_access_token = channel_access_token if channel_access_token else minette.config.get(section="line_bot_api", key="channel_access_token")
        self.parser = WebhookParser(self.channel_secret)
        self.line_bot_api = LineBotApi(self.channel_access_token)
        self.threads = threads
        self.thread_pool = []
        self.prepare_thread_pool()
        self.minette.dialog_router.helpers["line_adapter"] = self
        if self.minette.task_scheduler:
            self.minette.task_scheduler.helpers["line_adapter"] = self

    def prepare_thread_pool(self):
        """
        Create worker threads and put into thread pool
        """
        # remove dead worker threads
        for t in self.thread_pool[:]:
            if not t.is_alive():
                self.thread_pool.remove(t)
                self.logger.warn("Remove: {} is not alive".format(t.name))
        # create new worker threads
        if len(self.thread_pool) < self.threads:
            self.logger.info("Create {} worker thread(s)".format(str(self.threads - len(self.thread_pool))))
            for i in range(self.threads - len(self.thread_pool)):
                worker = WorkerThread(self)
                worker.start()
                self.thread_pool.append(worker)

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

    def assign_worker(self, message):
        """
        Put message into worker thread's queue

        Parameters
        ----------
        message : Message
            Message to process

        Returns
        -------
        worker : WorkerThread
            Worker thread to process the user's request
        """
        # determine processing key
        processing_key = message.group.id if message.group else message.channel_user_id
        # remove dead workers
        self.prepare_thread_pool()
        # get worker that is processing current user's / group's request
        user_workers = [t for t in self.thread_pool if t.processing == processing_key]
        if user_workers:
            worker = user_workers[0]
            self.logger.info("Use {} that is now processing {}'s request".format(worker.name, processing_key))
        else:
            # use free worker
            free_workers = [t for t in self.thread_pool if not t.processing]
            if free_workers:
                worker = random.choice(free_workers)
            # choice worker randomly if all workers are busy
            else:
                worker = random.choice(self.thread_pool)
                self.logger.warn("All threads are busy. Use {} to process {}'s request later".format(worker.name, processing_key))
        # put message into worker's queue
        worker.queue.put((message, processing_key))

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
            Response that shows queued status. The response from chatbot will be sent by worker thread
        """
        try:
            signature = request_headers["X-Line-Signature"]
            events = self.parser.parse(request_data_as_text, signature)
            for ev in events:
                message = self.parse_request(ev)
                self.assign_worker(message)
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
            self.line_bot_api.push_message(to=channel_user_id, messages=response.for_channel)
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
            profile = self.line_bot_api.get_profile(user.channel_user_id)
            user.name = profile.display_name
            user.profile_image_url = profile.picture_url
        except Exception as ex:
            self.logger.error("Error occured in updating profile: " + str(ex) + "\n" + traceback.format_exc())
