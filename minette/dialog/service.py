""" Base class for DialogService for processing each dialogs """
import traceback
from logging import Logger, getLogger

from ..models import (
    Message,
    Response,
    Context,
    PerformanceInfo
)


class DialogService:
    """
    Base class for DialogService

    Attributes
    ----------
    config : minette.Config
        Configuration
    timezone : timezone
        Timezone
    logger : logging.Logger
        Logger
    dependencies : DependencyContainer
        Container to attach objects DialogRouter depends
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

    def __init__(self, config=None, timezone=None, logger=None):
        """
        Parameters
        ----------
        config : minette.Config, default None
            Configuration
        timezone : pytz.timezone, default None
            Timezone
        logger : logging.Logger, default None
            Logger
        """
        self.config = config
        self.timezone = timezone
        self.logger = logger or getLogger(__name__)
        self.dependencies = None

    def execute(self, request, context, connection, performance):
        """
        Main logic of DialogService

        Parameters
        ----------
        request : minette.Message
            Request message
        context : minette.Context
            Context
        connection : Connection
            Connection
        performance : minette.PerformanceInfo
            Performance information

        Returns
        -------
        response : minette.Response
            Response from chatbot
        """
        try:
            # extract entities
            for k, v in self.extract_entities(
                    request, context, connection).items():
                if not request.entities.get(k, ""):
                    request.entities[k] = v
            performance.append("dialog_service.extract_entities")

            # initialize context data
            if context.topic.is_new:
                context.data = self.get_slots(request, context, connection)
            performance.append("dialog_service.get_slots")

            # process request
            self.process_request(request, context, connection)
            performance.append("dialog_service.process_request")

            # compose response
            response_messages = \
                self.compose_response(request, context, connection)
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
                    response.messages.append(request.to_reply(text=rm))
            performance.append("dialog_service.compose_response")

        except Exception as ex:
            self.logger.error(
                "Error occured in dialog_service: "
                + str(ex) + "\n" + traceback.format_exc())
            response = Response(messages=[
                self.handle_exception(request, context, ex, connection)])

        return response

    def extract_entities(self, request, context, connection):
        """
        Extract entities from request message

        Parameters
        ----------
        request : minette.Message
            Request message
        context : minette.Context
            Context
        connection : Connection
            Connection

        Returns
        -------
        entities : dict
            Entities extracted from request message
        """
        return {}

    def get_slots(self, request, context, connection):
        """
        Get initial context.data at the start of this dialog

        Parameters
        ----------
        request : minette.Message
            Request message
        context : minette.Context
            Context
        connection : Connection
            Connection

        Returns
        -------
        slots : dict
            Initial context.data
        """
        return {}

    def process_request(self, request, context, connection):
        """
        Process your chatbot's functions/skills and setup context data

        Parameters
        ----------
        request : minette.Message
            Request message
        context : minette.Context
            Context
        connection : Connection
            Connection
        """
        pass

    def compose_response(self, request, context, connection):
        """
        Compose response messages using context data

        Parameters
        ----------
        request : minette.Message
            Request message
        context : minette.Context
            Context
        connection : Connection
            Connection

        Returns
        -------
        response : minette.Response
            Response from chatbot
        """
        return ""

    def handle_exception(self, request, context, exception, connection):
        """
        Handle exception and return error response message

        Parameters
        ----------
        request : minette.Message
            Request message
        context : minette.Context
            Context
        exception : Exception
            Exception
        connection : Connection
            Connection

        Returns
        -------
        response : minette.Response
            Error response from chatbot
        """
        context.set_error(exception)
        context.topic.keep_on = False
        return request.to_reply(text="?")


class EchoDialogService(DialogService):
    """
    Simple echo dialog service for tutorial

    """
    def compose_response(self, request, context, connection=None):
        return request.to_reply(text="You said: {}".format(request.text))


class ErrorDialogService(DialogService):
    """
    Dialog service for error in chatting

    """
    def compose_response(self, request, context, connection=None):
        return request.to_reply(text="?")
