""" Base class of adapters for each channels """
from logging import Logger
import traceback
from minette import Minette
from minette.message import Message, Response


class Adapter:
    """
    Base class of adapters for each channels

    Attributes
    ----------
    minette : Minette
        Instance of Minette
    logger : Logger
        Logger
    debug : bool
        Debug mode
    """

    def __init__(self, minette, logger=None, debug=False):
        """
        Parameters
        ----------
        minette : Minette
            Instance of Minette
        logger : Logger, default None
            Logger
        debug : bool, default False
            Debug mode
        """
        self.minette = minette
        self.logger = logger if logger else minette.logger
        self.debug = debug

    def parse_request(self, request):
        """
        Parse channel-specific formatted request to Message object

        Parameters
        ----------
        request : Any
            Request from channel

        Returns
        -------
        message : Message
            Request converted into Message object
        """
        return Message(text=str(request))

    def format_response(self, response):
        """
        Set channel-specific formatted response to `for_channel` attribute

        Parameters
        ----------
        response : Response
            Response from chatbot

        Returns
        -------
        response : Response
            Response from chatbot with channel-specific formatted response
        """
        return response

    def chat(self, request):
        """
        Interface to chat with your bot

        Parameters
        ----------
        request : Message
            Message to chatbot

        Returns
        -------
        response : Response
            Response from chatbot
        """
        try:
            message = self.parse_request(request)
            response = self.minette.chat(message)
            return self.format_response(response)
        except Exception as ex:
            self.logger.error("Error occured in chatting: " + str(ex) + "\n" + traceback.format_exc())
            return Response(messages=[Message(text="Error occured in chatting", type="system")], for_channel="Error occured in chatting")
