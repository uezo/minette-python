import traceback
import logging
from concurrent.futures import ThreadPoolExecutor
import lxml.html
import xml.etree.ElementTree as ET

from sym_api_client_python.configure.configure import SymConfig
from sym_api_client_python.auth.rsa_auth import SymBotRSAAuth
from sym_api_client_python.clients.sym_bot_client import SymBotClient

from .base import Adapter
from ..models import (
    Message,
    Payload,
    Group,
    Response,
    Context
)


class SymphonyAdapter(Adapter):
    """
    Adapter for LINE Messaging API

    Attributes
    ----------
    bot : minette.Minette
        Instance of Minette
    bot_client : SymBotClient
        Symphony chatbot client
    datafeed_client : aaa
        Datafeed client using long polling
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
                 symphony_config="symphony.json", symphony_log="symphony.log",
                 **kwargs):
        """
        Parameters
        ----------
        bot : minette.Minette, default None
            Instance of Minette.
            If None, create new instance of Minette by using `**kwargs`
        symphony_config : str, default 'config.json'
            Config file for Symphony SDK
        symphony_log : str, defautl 'symphony.log'
            Log file of Symphony SDK
        threads : int, default None
            Max number of worker threads. If None, number of processors on the machine, multiplied by 5
        debug : bool, default False
            Debug mode
        """
        super().__init__(bot=bot, threads=threads, debug=debug, **kwargs)
        # setup root logger (used internally in symphony libraries)
        logging.basicConfig(
            filename=symphony_log,
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            filemode="w", level=logging.DEBUG)
        # set logging level for urllib3 used in symphony libraries
        logging.getLogger("urllib3").setLevel(logging.WARNING)
        # configure and authenticate
        config = SymConfig(symphony_config)
        config.load_config()
        auth = SymBotRSAAuth(config)
        auth.authenticate()
        # initialize SymBotClient with auth and configure objects
        self.bot_client = SymBotClient(auth, config)
        self.datafeed_client = self.bot_client.get_datafeed_client()

    def start_datafeed(self):
        """
        Start datafeed to read and process events from Symphony

        """
        # get datafeed id
        datafeed_id = self.datafeed_client.create_datafeed()
        self.logger.info("Datafeed client is ready")
        # datafeed loop forever
        while True:
            try:
                # read datafeed by datafeed_id (30 sec long polling)
                data = self.datafeed_client.read_datafeed(datafeed_id)
                if data:
                    # api returns list of events but SDK nest it to array.(I don't know why...)
                    events = data[0]
                    for event in events:
                        if event["initiator"]["user"]["userId"] != self.bot_client.get_bot_user_info()["id"]:
                            if self.executor:
                                self.executor.submit(self.handle_event, event)
                            else:
                                self.handle_event(event)
            except Exception as ex:
                self.logger.error("Error occured in datafeed loop: " + str(ex) + "\n" + traceback.format_exc())

    def handle_event(self, event):
        """
        Handle event and reply message

        Parameters
        ----------
        event : Event
            Event data from Symphony
        """
        channel_messages, stream_id = super().handle_event(event)
        if channel_messages:
            for msg in channel_messages:
                self.logger.info("Minette> {}".format(msg["message"] if "message" in msg else msg))
                self.bot_client.get_message_client().send_msg(stream_id, msg)

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
        return event["payload"]["messageSent"]["message"]["stream"]["streamId"]

    def _to_minette_message(self, event):
        """
        Convert Symphony Event object to Minette Message object

        Parameters
        ----------
        event : Event
            Event from Symphony. See the url below for information
            https://developers.symphony.com/restapi/docs/real-time-events

        Returns
        -------
        message : minette.Message
            Request message object
        """
        if self.debug:
            self.logger.info(event)
        msg = Message(
            type=event["type"],
            channel="Symphony",
            channel_detail="",
            channel_user_id=str(event["initiator"]["user"]["userId"]),
            channel_message=event)
        if msg.type == "MESSAGESENT":
            m = event["payload"]["messageSent"]["message"]
            msg.token = m["stream"]["streamId"]
            msg.text = lxml.html.fromstring(m["message"]).text_content()
            if m["stream"]["streamType"] == "ROOM":
                msg.group = Group(id=m["stream"]["streamId"], type="ROOM")
            if "attachments" in m:
                for a in m["attachments"]:
                    if len(a["images"]) > 0:
                        content_type = "image"
                    else:
                        content_type = "file"
                    msg.payloads.append(Payload(content_type=content_type, content=a))
        return msg

    @staticmethod
    def _to_channel_message(message):
        """
        Convert Minette Message object to Symphony message dict

        Parameters
        ----------
        message : Message
            Response message object

        Returns
        -------
        response : dict
            Message dict for Symphony
        """
        return {"message": "<messageML>{}</messageML>".format(message.text)}
