""" Base components for processing dialog """
from logging import Logger, getLogger


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


class DialogRouter:
    """
    Base class of dialog router

    Attributes
    ----------
    logger : Logger
        Logger
    config : Config
        Configuration
    timezone : timezone
        Timezone
    default_dialog_service : DialogService
        Default dialog service for unhandled request
    helpers : dict
        Helper objects and functions
    intent_resolver : dict
        Resolver for intent to dialog
    topic_resolver : dict
        Resolver for topic to dialog
    """
    def __init__(self, logger=None, config=None, timezone=None, default_dialog_service=None, helpers=None):
        """
        Parameters
        ----------
        logger : Logger, default None
            Logger
        config : Config, default None
            Configuration
        timezone : timezone, default None
            Timezone
        default_dialog_service : DialogService, default None
            Default dialog service for unhandled request
        helpers : dict, default None
            Helper objects and functions
        """
        self.logger = logger if logger else logging.getLogger(__name__)
        self.config = config
        self.timezone = timezone
        self.default_dialog_service = default_dialog_service or DialogService
        self.helpers = helpers if helpers else {}
        self.intent_resolver = {}
        self.topic_resolver = {}

    def configure(self):
        """
        Configuration after instancing
        """
        pass

    def init_resolvers(self):
        """
        Initialize intent_resolver and topic_resolver
        """
        self.topic_resolver = {v.topic_name(): v for v in self.intent_resolver.values() if v}
        self.topic_resolver[self.default_dialog_service.topic_name()] = self.default_dialog_service

    def extract_intent(self, request, session, connection):
        """
        Extract intent and entities from request message

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
        response : (str, dict)
            Intent and entities
        """
        return request.intent, request.entities

    def before_route(self, request, session, connection):
        """
        Preprocessing for all requests before routing

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
        """
        pass

    def route(self, request, session, connection):
        """
        Return DialogService for the topic

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
        dialog_service : DialogService
            Dialog service proper for intent or topic
        """
        # update
        if request.intent in self.intent_resolver and (request.intent_priority > session.topic.priority or not session.topic.name):
            dialog_service = self.intent_resolver[request.intent]
            # update topic if request is not adhoc
            if dialog_service and not request.is_adhoc:
                session.topic.name = dialog_service.topic_name()
                session.topic.is_new = True
            # do not update topic when request is adhoc or dialog_service is not registered
            else:
                dialog_service = dialog_service or DialogService
                if session.topic.name:
                    session.topic.keep_on = True
        # continue
        elif session.topic.name:
            dialog_service = self.topic_resolver[session.topic.name]
        # default
        else:
            dialog_service = self.default_dialog_service
            session.topic.name = dialog_service.topic_name()
            session.topic.is_new = True
        return dialog_service

    def handle_exception(self, request, session, exception, connection):
        """
        Handle exception and return ErrorDialogService

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
        response : ErrorDialogService
            Dialog service for error occured in chatting
        """
        session.set_error(exception)
        return ErrorDialogService(logger=self.logger, config=self.config, timezone=self.timezone)
