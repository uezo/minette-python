""" Base components for processing each dialogs """
from logging import Logger, getLogger
import traceback
import requests
from minette.message import Message, Response
from minette.session import Session
from minette.performance import PerformanceInfo
from minette.serializer import encode_json


class DialogService:
    """
    Base class of dialog services

    Attributes
    ----------
    logger : Logger
        Logger
    config : Config
        Configuration
    timezone : timezone
        Timezone
    """

    @classmethod
    def topic_name(cls):
        """
        Topic name of this dialog service

        Returns
        -------
        topic_name : str
            Topic name of this dialog service
        """
        cls_name = cls.__name__.lower()
        if cls_name.endswith("dialogservice"):
            cls_name = cls_name[:-13]
        elif cls_name.endswith("dialog"):
            cls_name = cls_name[:-6]
        return cls_name

    def __init__(self, logger=None, config=None, timezone=None):
        """
        Parameters
        ----------
        logger : Logger, default None
            Logger
        config : Config, default None
            Configuration
        timezone : timezone, default None
            Timezone
        """
        self.logger = logger
        self.config = config
        self.timezone = timezone

    def execute(self, request, session, connection, performance):
        """
        Main logic of DialogService

        Parameters
        ----------
        request : Message
            Request message
        session : Session
            Session
        exception : Exception
            Exception
        connection : Connection
            Connection
        performance : PerformanceInfo
            Performance information

        Returns
        -------
        response : Response
            Response from chatbot
        """
        try:
            # extract entities
            for k, v in self.extract_entities(request, session, connection).items():
                if not request.entities.get(k, ""):
                    request.entities[k] = v
            performance.append("dialog_service.extract_entities")

            # initialize session data
            if session.topic.is_new:
                session.data = self.get_slots(request, session, connection)
            performance.append("dialog_service.get_slots")

            # process request
            self.process_request(request, session, connection)
            performance.append("dialog_service.get_slots")

            # compose response
            response_messages = self.compose_response(request, session, connection)
            if not response_messages:
                self.logger.info("No response")
                response_messages = []
            elif not isinstance(response_messages, list):
                response_messages = [response_messages]
            response = Response()
            for rm in response_messages:
                if isinstance(rm, Message):
                    response.messages.append(rm)
                elif isinstance(rm, str):
                    response.messages.append(request.reply(text=rm))
            performance.append("dialog_service.compose_response")

        except Exception as ex:
            self.logger.error("Error occured in dialog_service: " + str(ex) + "\n" + traceback.format_exc())
            response = Response(messages=[self.handle_exception(request, session, ex, connection)])

        return response

    def extract_entities(self, request, session, connection):
        """
        Extract entities from request message

        Parameters
        ----------
        request : Message
            Request message
        session : Session
            Session
        connection : Connection
            Connection

        Returns
        -------
        entities : dict
            Entities extracted from request message
        """
        return {}

    def get_slots(self, request, session, connection):
        """
        Get initial slot data in session

        Parameters
        ----------
        request : Message
            Request message
        session : Session
            Session
        connection : Connection
            Connection

        Returns
        -------
        slots : dict
            Initial slots in session.data
        """
        return {}

    def process_request(self, request, session, connection):
        """
        Process your chatbot's functions/skills and setup session data

        Parameters
        ----------
        request : Message
            Request message
        session : Session
            Session
        connection : Connection
            Connection
        """
        pass

    def compose_response(self, request, session, connection):
        """
        Compose response messages using session data

        Parameters
        ----------
        request : Message
            Request message
        session : Session
            Session
        connection : Connection
            Connection

        Returns
        -------
        response : Response
            Response from chatbot
        """
        return ""

    def handle_exception(self, request, session, exception, connection):
        """
        Handle exception and return error response message

        Parameters
        ----------
        request : Message
            Request message
        session : Session
            Session
        exception : Exception
            Exception
        connection : Connection
            Connection

        Returns
        -------
        response : Response
            Error response from chatbot
        """
        session.set_error(exception)
        session.topic.keep_on = False
        return request.reply(text="?")


class EchoDialogService(DialogService):
    """
    Simple echo dialog service for tutorial

    Attributes
    ----------
    logger : Logger
        Logger
    config : Config
        Configuration
    timezone : timezone
        Timezone
    """
    def compose_response(self, request, session, connection=None):
        return request.reply(text="You said: {}".format(request.text))


class ErrorDialogService(DialogService):
    """
    Dialog service for error occured in chatting

    Attributes
    ----------
    logger : Logger
        Logger
    config : Config
        Configuration
    timezone : timezone
        Timezone
    """
    def compose_response(self, request, session, connection=None):
        return request.reply(text="?")


class HttpDialogServiceClient(DialogService):
    """
    Base class of client for DialogService provided as WebService

    Attributes
    ----------
    logger : Logger
        Logger
    config : Config
        Configuration
    timezone : timezone
        Timezone
    endpoint_uri : str
        Endpoint URI of WebService
    """

    def __init__(self, logger=None, config=None, timezone=None):
        """
        Parameters
        ----------
        logger : Logger, default None
            Logger
        config : Config, default None
            Configuration
        timezone : timezone, default None
            Timezone
        """
        super().__init__(logger, config, timezone)
        self.endpoint_uri = ""

    def execute(self, request, session, connection, performance):
        try:
            service_response = self.fetch(request, session, performance)
            response = self.handle_service_response(service_response, request, session, connection, performance)
        except Exception as ex:
            self.logger.error(f"Error occured in dialog_service(client): {str(ex)} \n{traceback.format_exc()}")
            response = Response(messages=[self.handle_exception(request, session, ex, connection)])
        return response

    def fetch(self, request, session, performance):
        """
        Call and fetch data from WebService

        Parameters
        ----------
        request : Message
            Request message
        session : Session
            Session
        performance : PerformanceInfo
            Performance information

        Returns
        -------
        http_response_json : dict
            HTTP Response parsed into dict
        """
        data = encode_json({"request": request.to_dict(), "session": session.to_dict(), "performance": performance.to_dict()})
        return requests.post(self.endpoint_uri, data=data, headers={"Content-Type": "application/json"}, timeout=60).json()

    def handle_service_response(self, service_response, request, session, connection, performance):
        """
        Update session and request and make response

        Parameters
        ----------
        request : Message
            Request message
        session : Session
            Session
        connection : Connection
            Connection

        Returns
        -------
        response : Response
            Response from remote DialogService
        """
        if service_response.get("error", ""):
            error = service_response["error"]
            self.logger.error(f"Error occured in dialog_service(remote): {error}")
            return Response(messages=[self.handle_exception(request, session, None, connection)])
        else:
            # update request, session and performance
            res_request = Message.from_dict(service_response["request"])
            request.entities = res_request.entities
            res_session = Session.from_dict(service_response["session"])
            session.topic = res_session.topic
            session.data = res_session.data
            session.error = res_session.error
            res_performance = PerformanceInfo.from_dict(service_response["performance"])
            performance.ticks = res_performance.ticks
            # make response data
            return Response.from_dict(service_response["response"])
