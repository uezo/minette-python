""" Adapter for Clova Extensions Kit """
from logging import Logger
from cek import Clova, URL, Request
from minette import Minette
from minette.message import Message, Response
from minette.channel import Adapter
from minette.serializer import encode_json


class ClovaAdapter(Adapter):
    """
    Adapter for Clova Extensions Kit

    Attributes
    ----------
    minette : Minette
        Instance of Minette
    application_id : str
        Application ID of Clova Skill
    default_language : str
        Default language of Clova Skill
    clova : Clova
        Clova Extensions Kit API
    logger : Logger
        Logger
    debug : bool
        Debug mode
    """

    def __init__(self, minette, application_id=None,
                 default_language=None, logger=None, debug=False):
        """
        Parameters
        ----------
        minette : Minette
            Instance of Minette
        application_id : str or None, default None
            Application ID for your Clova Skill
        default_language : str or None, default None
            Default language
        logger : Logger, default None
            Logger
        debug : bool, default False
            Debug mode
        """
        super().__init__(minette, logger, debug)
        self.application_id = application_id if application_id else minette.config.get(section="clova_api", key="application_id")
        self.default_language = default_language if default_language else minette.config.get(section="clova_api", key="default_language", default="ja")
        self.clova = Clova(application_id=self.application_id, default_language=self.default_language, debug_mode=debug)

        # handler for all types of request
        @self.clova.handle.default
        def default(clova_request):
            return clova_request

    def parse_request(self, clova_request):
        """
        Parse request from clova to Message object

        Parameters
        ----------
        clova_request : Request
            Request from clova

        Returns
        -------
        message : Message
            Request converted into Message object
        """
        if self.debug:
            self.logger.info(clova_request.__dict__)
        msg = Message(
            type=clova_request.request_type,
            channel="LINE",
            channel_detail="Clova",
            channel_user_id=clova_request.user_id,
            channel_message=clova_request
        )
        if clova_request.is_intent:
            msg.intent = clova_request.intent_name
            # if clova_request.slots_dict: <- Error occures when no slot values
            if clova_request._request["intent"]["slots"]:
                msg.entities = clova_request.slots_dict
        return msg

    def format_response(self, response):
        """
        Set Clova formatted response to `for_channel` attribute

        Parameters
        ----------
        response : Response
            Response from chatbot

        Returns
        -------
        response : Response
            Response with Clova formatted response
        """
        if not response.messages:
            response.for_channel = self.clova.response("")
            return response
        res = response.messages[0]
        end_session = res.entities.get("end_session", True)
        if res.type == "url":
            clova_res = self.clova.response(URL(res.text), end_session=end_session)
        else:
            clova_res = self.clova.response(res.text, end_session=end_session)
        response.for_channel = clova_res
        return response

    def chat(self, request_data, request_headers):
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
        return super().chat(clova_request)
