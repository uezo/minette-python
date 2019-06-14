""" Base components for route proper dialog for the intent """
from logging import Logger, getLogger
import traceback
from minette.message import Message
from minette.dialog import DialogService, ErrorDialogService


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

    def execute(self, request, session, connection, performance):
        # route dialog
        try:
            # extract intent and entities
            extracted = self.extract_intent(request=request, session=session, connection=connection)
            if isinstance(extracted, tuple):
                request.intent = extracted[0]
                request.entities = extracted[1]
                if len(extracted) > 2:
                    request.intent_priority = extracted[2]
            elif isinstance(extracted, str):
                request.intent = extracted
            performance.append("dialog_router.extract_intent")
            # preprocess before route
            self.before_route(request, session, connection)
            performance.append("dialog_router.before_route")
            # route dialog
            dialog_service = self.route(request, session, connection)
            if isinstance(dialog_service, type):
                dialog_service = dialog_service(self.logger, self.config, self.timezone)
            performance.append("dialog_router.route")
        except Exception as ex:
            self.logger.error("Error occured in dialog_router: " + str(ex) + "\n" + traceback.format_exc())
            dialog_service = self.handle_exception(request, session, ex, connection)

        return dialog_service

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
                session.topic.status = ""
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
            session.topic.status = ""
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
