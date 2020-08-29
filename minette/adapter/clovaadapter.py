""" Adapter for Clova Extensions Kit """
import traceback

from cek import (
    Clova,
    URL,
    IntentRequest
)

from ..serializer import dumps
from .base import Adapter
from ..models import Message


class ClovaAdapter(Adapter):
    """
    Adapter for Clova Extensions Kit

    Attributes
    ----------
    bot : minette.Minette
        Instance of Minette
    application_id : str
        Application ID of Clova Skill
    default_language : str
        Default language of Clova Skill
    clova : Clova
        Clova Extensions Kit API
    config : minette.Config
        Configuration
    timezone : pytz.timezone
        Timezone
    logger : logging.Logger
        Logger
    debug : bool
        Debug mode
    """

    def __init__(self, bot=None, *, debug=False,
                 application_id=None, default_language=None, **kwargs):
        """
        Parameters
        ----------
        bot : minette.Minette, default None
            Instance of Minette.
            If None, create new instance of Minette by using `**kwargs`
        application_id : str or None, default None
            Application ID for your Clova Skill
        default_language : str or None, default None
            Default language. ("en" / "ja" / "ko")
            If None, "ja" is set to Clova Extensions Kit API object
        debug : bool, default False
            Debug mode
        """
        super().__init__(bot=bot, threads=0, debug=debug, **kwargs)
        self.application_id = application_id or \
            self.config.get(section="clova_cek", key="application_id")
        self.default_language = default_language or \
            self.config.get(section="clova_cek", key="default_language") or "ja"
        self.clova = Clova(application_id=self.application_id,
                           default_language=self.default_language,
                           debug_mode=debug)

        # handler for all types of request
        @self.clova.handle.default
        def default(clova_request):
            return clova_request

    def handle_http_request(self, request_data, request_headers):
        """
        Interface to chat with Clova Skill

        Parameters
        ----------
        request_data : bytes
            Request data from Clova as bytes
        request_headers : dict
            Request headers from Clova as dict

        Returns
        -------
        response : Response
            Response from chatbot. Send back `json` attribute to Clova API
        """
        clova_request = self.clova.route(request_data, request_headers)
        return self.handle_event(clova_request)

    def handle_event(self, clova_request):
        # execute bot
        channel_messages, _ = super().handle_event(clova_request)

        # print response for debug
        for msg in channel_messages:
            if self.debug:
                self.logger.info(msg)
            else:
                self.logger.info("Minette> {}".format(msg["speech_value"]))

        # build response message
        speech_values = [msg["speech_value"] for msg in channel_messages]
        end_session = channel_messages[-1]["end_session"]
        reprompt = channel_messages[-1]["reprompt"]
        if len(speech_values) == 1:
            return dumps(self.clova.response(
                speech_values[0], end_session=end_session, reprompt=reprompt))
        else:
            return dumps(self.clova.response(
                speech_values, end_session=end_session, reprompt=reprompt))

    @staticmethod
    def _to_minette_message(clova_request):
        """
        Convert ClovaRequest object to Minette Message object

        Parameters
        ----------
        clova_request : cek.Request
            Request from clova

        Returns
        -------
        message : minette.Message
            Request converted into Message object
        """
        msg = Message(
            type=clova_request.type,
            channel="LINE",
            channel_detail="Clova",
            channel_user_id=clova_request.session.user.id if clova_request.session._session else "",
            channel_message=clova_request
        )

        # Set intent and entities when IntentRequest
        if isinstance(clova_request, IntentRequest):
            msg.intent = clova_request.name
            # if clova_request.slots: <- Error occures when no slot values
            if clova_request._request["intent"]["slots"]:
                msg.entities = clova_request.slots
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
        return {
            "speech_value": URL(message.text) if message.type == "url" else message.text,
            "end_session": message.entities.get("end_session", True),
            "reprompt": message.entities.get("reprompt", None)
        }
