""" Base class for DialogRouter that routes proper dialog for the intent """
from abc import ABC, abstractmethod
import traceback
from logging import Logger, getLogger

from ..models import Message, Priority
from .service import DialogService, ErrorDialogService
from .dependency import DependencyContainer


class DialogRouter:
    """
    Base class for DialogRouter

    Attributes
    ----------
    config : minette.Config
        Configuration
    timezone : timezone
        Timezone
    logger : logging.Logger
        Logger
    default_dialog_service : DialogService
        Dialog service used when intent is not clear
    dependency_rules : dict
        Rules that defines on which components each DialogService/Router depends
    default_dependencies : dict
        Dependency components for all DialogServices/Router
    dependencies : DependencyContainer
        Container to attach objects DialogRouter depends
    intent_resolver : dict
        Resolver for intent to dialog
    topic_resolver : dict
        Resolver for topic to dialog for successive chatting
    """

    def __init__(self, config=None, timezone=None, logger=None,
                 default_dialog_service=None, intent_resolver=None, **kwargs):
        """
        Parameters
        ----------
        config : minette.Config, default None
            Configuration
        timezone : pytz.timezone, default None
            Timezone
        logger : logging.Logger, default None
            Logger
        default_dialog_service : minette.DialogService or type, default None
            Dialog service used when intent is not clear.
        """
        self.config = config
        self.timezone = timezone
        self.logger = logger or getLogger(__name__)
        self.default_dialog_service = default_dialog_service or DialogService
        self.dependency_rules = None
        self.default_dependencies = None or {}  # empty dict is required to unpack
        self.dependencies = None
        # set up intent_resolver
        self.intent_resolver = intent_resolver or {}
        self.register_intents()
        # set up topic_resolver
        self.topic_resolver = {
            v.topic_name(): v for v in self.intent_resolver.values() if v}
        self.topic_resolver[self.default_dialog_service.topic_name()] = \
            self.default_dialog_service

    def register_intents(self):
        """
        Register intents and the dialog services to process the intents

        >>> self.intent_resolver = {
            "PizzaOrderIntent": PizzaDialogService,
            "ChangeAddressIntent": ChangeAddressDialogService,
        }
        """
        pass

    def execute(self, request, context, connection, performance):
        """
        Main logic of DialogRouter

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
        dialog_service : minette.DialogService
            DialogService to process request message
        """
        try:
            # extract intent and entities
            extracted = self.extract_intent(
                request=request, context=context, connection=connection)
            if isinstance(extracted, tuple):
                request.intent = extracted[0]
                request.entities = extracted[1]
                if len(extracted) > 2:
                    request.intent_priority = extracted[2]
            elif isinstance(extracted, str):
                request.intent = extracted
            performance.append("dialog_router.extract_intent")
            # preprocess before route
            self.before_route(request, context, connection)
            performance.append("dialog_router.before_route")
            # route dialog
            dialog_service = self.route(request, context, connection)
            if issubclass(dialog_service, DialogService):
                dialog_service = dialog_service(
                    config=self.config, timezone=self.timezone,
                    logger=self.logger
                )
            dialog_service.dependencies = DependencyContainer(
                dialog_service,
                self.dependency_rules,
                **self.default_dependencies)
            performance.append("dialog_router.route")
        except Exception as ex:
            self.logger.error(
                "Error occured in dialog_router: "
                + str(ex) + "\n" + traceback.format_exc())
            dialog_service = \
                self.handle_exception(request, context, ex, connection)

        return dialog_service

    def extract_intent(self, request, context, connection):
        """
        Extract intent and entities from request message

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
        response : tuple of (str, dict)
            Intent and entities
        """
        return request.intent, request.entities

    def before_route(self, request, context, connection):
        """
        Preprocessing for all requests before routing

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

    def route(self, request, context, connection):
        """
        Return proper DialogService for intent or topic

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
        dialog_service : minette.DialogService
            Dialog service proper for intent or topic
        """
        # update
        if request.intent in self.intent_resolver and (
                request.intent_priority > context.topic.priority or
                not context.topic.name):
            dialog_service = self.intent_resolver[request.intent]
            # update topic if request is not adhoc
            if dialog_service and not request.is_adhoc:
                context.topic.name = dialog_service.topic_name()
                context.topic.status = ""
                if request.intent_priority >= Priority.Highest:
                    # set slightly lower priority to enable to update Highest priority intent
                    context.topic.priority = Priority.Highest - 1
                else:
                    context.topic.priority = request.intent_priority
                context.topic.is_new = True
            # do not update topic when request is adhoc or ds is None
            else:
                dialog_service = dialog_service or DialogService
                if context.topic.name:
                    context.topic.keep_on = True

        # continue
        elif context.topic.name:
            dialog_service = self.topic_resolver[context.topic.name]

        # default (intent not extracted or unknown)
        else:
            dialog_service = self.default_dialog_service
            context.topic.name = dialog_service.topic_name()
            context.topic.status = ""
            context.topic.is_new = True
        return dialog_service

    def handle_exception(self, request, context, exception, connection):
        """
        Handle exception and return ErrorDialogService

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
        response : minette.ErrorDialogService
            Dialog service for error occured in chatting
        """
        context.set_error(exception)
        return ErrorDialogService(
            config=self.config, timezone=self.timezone, logger=self.logger)
