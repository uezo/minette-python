""" Adapter for Clova Extensions Kit """
from logging import Logger
from cek import Clova, URL
from minette import Minette
from minette.message import Message, Response
from minette.channel import Adapter


class ClovaAdapter(Adapter):
    """
    Adapter for Clova Extensions Kit

    Attributes
    ----------
    minette : Minette
        Instance of Minette
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
        self.clova = Clova(
            application_id=application_id if application_id else minette.config.get(section="clova_api", key="application_id"),
            default_language=default_language if default_language else minette.config.get(section="clova_api", key="default_language", default="ja"),
            debug_mode=debug)

    def parse_request(self, request_json):
        """
        Parse JSON from clova to Message object

        Parameters
        ----------
        request : dict
            Request from clova

        Returns
        -------
        message : Message
            Request converted into Message object
        """
        if self.debug:
            self.logger.info(request_json)
        msg = Message(
            type=request_json["request"]["type"],
            channel="LINE",
            channel_detail="Clova",
            channel_user_id=request_json["session"]["user"]["userId"],
            channel_message=request_json
        )
        if msg.type == "IntentRequest":
            msg.intent = request_json["request"]["intent"]["name"]
            if request_json["request"]["intent"]["slots"]:
                msg.entities = request_json["request"]["intent"]["slots"]
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

    def chat(self, request_json):
        """
        Interface to chat with Clova Skill

        Parameters
        ----------
        request_json : dict
            JSON(dict) formatted request from Clova

        Returns
        -------
        response : Response
            Response from chatbot. Send back `json` attribute to Clova API
        """
        return super().chat(request_json)
