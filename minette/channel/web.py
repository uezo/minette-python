""" Adapter for WebAPI """
from logging import Logger
import traceback
from flask import request
from minette import Minette
from minette.message import Message, Payload, Response
from minette.channel import Adapter


class WebAdapter(Adapter):
    """
    Adapter for Flask-based simple Web API

    Attributes
    ----------
    minette : Minette
        Instance of Minette
    logger : Logger
        Logger
    debug : bool
        Debug mode
    """

    def parse_request(self, request):
        """
        Parse request to Message object

        Parameters
        ----------
        request : request
            Request from web client as flask.request

        Returns
        -------
        message : Message
            Request converted into Message object
        """
        json = request.json
        if json:
            msg = Message.from_dict(json)
            msg.channel = "web" if msg.channel == "console" else msg.channel
        else:
            msg = Message(channel="web")
            msg.text = request.args.get("text")
            if request.args.get("media"):
                p = Payload()
                p.url = request.args.get("media")
                p.content_type = request.args.get("media_type") if request.args.get("media_type") else p.content_type
                msg.payloads.append(p)
        return msg

    def format_response(self, response):
        """
        Set dict formatted response to `for_channel` attribute

        Parameters
        ----------
        response : Response
            Response from chatbot

        Returns
        -------
        response : Response
            Response from chatbot with dict formatted response
        """
        response.for_channel = [res.to_dict() for res in response.messages]
        return response
