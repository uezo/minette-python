""" Core module of Minette """
from time import time
import logging
import traceback
from copy import deepcopy
from pytz import timezone as tz
from minette.database import ConnectionProvider
from minette.session import SessionStore, Topic
from minette.user import UserRepository
from minette.dialog import DialogRouter, DialogService
from minette.tagger import Tagger
from minette.message import Message, MessageLogger, Response
from minette.task import Scheduler
from minette.util import get_class
from minette.config import Config


class Minette:
    """
    Chatbot

    Attributes
    ----------
    connection_provider : ConnectionProvider
        Connection provider
    session_store: SessionStore
        Session store
    user_repository: UserRepository
        User repository
    dialog_router: DialogRouter
        Dialog router
    default_dialog_service : DialogService, default None
        Default dialog service for unhandled request
    task_scheduler : Scheduler
        Task scheduler
    message_logger: MessageLogger
        Message logger
    tagger: Tagger
        Tagger
    logger : logging.Logger
        Logger
    config : Config
        Configuration
    timezone : timezone
        Timezone
    prepare_table : bool
        Create tables if not existing
    """

    def __init__(self, connection_provider, session_store, user_repository,
                 dialog_router, default_dialog_service, task_scheduler,
                 message_logger, tagger, logger, config, timezone, prepare_table):
        """
        Parameters
        ----------
        connection_provider : ConnectionProvider
            Connection provider
        session_store: SessionStore
            Session store
        user_repository: UserRepository
            User repository
        dialog_router: DialogRouter
            Dialog router
        default_dialog_service : DialogService, default None
            Default dialog service for unhandled request
        task_scheduler : Scheduler
            Task scheduler
        message_logger: MessageLogger
            Message logger
        tagger: Tagger
            Tagger
        logger : logging.Logger
            Logger
        config : Config
            Configuration
        timezone : timezone
            Timezone
        prepare_table : bool
            Create tables if not existing
        """
        self.connection_provider = connection_provider
        self.session_store = session_store
        self.user_repository = user_repository
        self.dialog_router = dialog_router
        self.default_dialog_service = default_dialog_service
        self.task_scheduler = task_scheduler
        self.message_logger = message_logger
        self.tagger = tagger
        self.logger = logger
        self.config = config
        self.timezone = timezone
        self.prepare_table = prepare_table

    @staticmethod
    def get_logger(logfile):
        """
        Get logger used in chatbot-wide

        Parameters
        ----------
        logfile : str
            Path of log file

        Returns
        -------
        logger : logging.Logger
            Logger
        """
        logger = logging.getLogger(__name__)
        if len(logger.handlers) > 0:
            return logger
        logger.setLevel(logging.DEBUG)
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)
        logger.addHandler(stream_handler)
        file_handler = logging.FileHandler(filename=logfile)
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
        return logger

    @classmethod
    def create(cls, connection_provider=None, session_store=None,
               user_repository=None, dialog_router=None,
               default_dialog_service=None, task_scheduler=None,
               message_logger=None, tagger=None, logger=None,
               config_file=None, timezone=None, prepare_table=True):
        """
        Create chatbot instance

        Parameters
        ----------
        connection_provider : ConnectionProvider, default None
            Connection provider
        session_store: SessionStore, default None
            Session store
        user_repository: UserRepository, default None
            User repository
        dialog_router: DialogRouter, default None
            Dialog router
        default_dialog_service : DialogService, default None
            Default dialog service for unhandled request
        task_scheduler : Scheduler, default None
            Task scheduler
        message_logger: MessageLogger, default None
            Message logger
        tagger: Tagger, default None
            Tagger
        logger : logging.Logger, default None
            Logger
        config_file : str, default "./minette.ini"
            Path to configuration file
        timezone : timezone, default None
            Timezone
        prepare_table : bool, default True
            Create tables if not existing

        Returns
        -------
        minette : Minette
            Fully configured chatbot instance
        """
        # initialize config and logger
        config = Config(config_file if config_file else "./minette.ini")
        if not logger:
            logger = Minette.get_logger(logfile=config.get("logfile", default="./minette.log"))
        # timezone
        timezone = tz(config.get("timezone", default="UTC"))
        # get database presets
        database_presets = config.get("database_presets")
        if database_presets:
            get_presets = get_class("{}.get_presets".format(database_presets))
            connection_provider, session_store, user_repository, message_logger = get_presets()
        # initialize connection provider
        connection_str = config.get("connection_str")
        if not connection_provider:
            connection_provider_classname = config.get("connection_provider")
            if connection_provider_classname:
                connection_provider = get_class(connection_provider_classname)
            else:
                connection_provider = ConnectionProvider
        if isinstance(connection_provider, type):
            connection_provider = connection_provider(connection_str if connection_str else "./minette.db")
        # initialize common arguments
        args = {"logger": logger, "config": config, "timezone": timezone}
        # session store
        if not session_store:
            session_store_classname = config.get("session_store")
            if session_store_classname:
                session_store = get_class(session_store_classname)
            else:
                session_store = SessionStore
        if isinstance(session_store, type):
            session_args = args.copy()
            session_args["connection_provider_for_prepare"] = connection_provider if prepare_table else None
            session_args["table_name"] = config.get("session_table", default="session")
            session_args["timeout"] = config.get("session_timeout", default=300)
            session_store = session_store(**session_args)
        # user repository
        if not user_repository:
            user_repository_classname = config.get("user_repository")
            if user_repository_classname:
                user_repository = get_class(user_repository_classname)
            else:
                user_repository = UserRepository
        if isinstance(user_repository, type):
            user_args = args.copy()
            user_args["connection_provider_for_prepare"] = connection_provider if prepare_table else None
            user_args["table_user"] = config.get("user_table", default="user")
            user_args["table_uidmap"] = config.get("uidmap_table", default="user_id_mapper")
            user_repository = user_repository(**user_args)
        # dialog router
        if not dialog_router:
            dialog_router_classname = config.get("default_dialog_router")
            if dialog_router_classname:
                dialog_router = get_class(dialog_router_classname)
            else:
                dialog_router = DialogRouter
        if isinstance(dialog_router, type):
            dialog_router_args = args.copy()
            if default_dialog_service:
                dialog_router_args["default_dialog_service"] = default_dialog_service
            elif config.get("default_dialog_service", default=None):
                dialog_router_args["default_dialog_service"] = get_class(config.get("default_dialog_service", default=None))
            dialog_router = dialog_router(**dialog_router_args)
        dialog_router.configure()
        dialog_router.init_resolvers()
        # task scheduler
        if not task_scheduler:
            task_scheduler_classname = config.get("task_scheduler")
            if task_scheduler_classname:
                task_scheduler = get_class(task_scheduler_classname)
        if isinstance(task_scheduler, type):
            scheduler_args = args.copy()
            scheduler_args["connection_provider"] = connection_provider
            task_scheduler = task_scheduler(**scheduler_args)
            task_scheduler.register_tasks()
            task_scheduler.start()
        # message logger
        if not message_logger:
            message_logger_classname = config.get("message_logger")
            if message_logger_classname:
                message_logger = get_class(message_logger_classname)
            else:
                message_logger = MessageLogger
        if isinstance(message_logger, type):
            message_args = args.copy()
            message_args["connection_provider_for_prepare"] = connection_provider if prepare_table else None
            message_args["table_name"] = config.get("messagelog_table", default="messagelog")
            message_logger = message_logger(**message_args)
        # tagger
        if not tagger:
            tagger_classname = config.get("tagger")
            if tagger_classname:
                tagger = get_class(tagger_classname)
            else:
                tagger = Tagger
        if isinstance(tagger, type):
            tagger = tagger(**args)
        # create and return instance of Minette
        return cls(connection_provider, session_store, user_repository,
                   dialog_router, default_dialog_service, task_scheduler,
                   message_logger, tagger, logger, config, timezone, prepare_table)

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
        response = Response()
        try:
            ticks = []
            start_time = time()
            conn = self.connection_provider.get_connection()
            ticks.append(("get_connection", time() - start_time))
            if isinstance(request, str):
                request = Message(text=request)
            # extract words with tagger
            request.words = self.tagger.parse(request.text)
            ticks.append(("tagger.parse", time() - start_time))
            # get user
            request.user = self.user_repository.get_user(request.channel, request.channel_user_id, conn)
            ticks.append(("user_repository.get_user", time() - start_time))
            # get session
            if request.group:
                session = self.session_store.get_session(request.channel, request.group.id, conn)
            else:
                session = self.session_store.get_session(request.channel, request.channel_user_id, conn)
            ticks.append(("session_store.get_session", time() - start_time))
            # route dialog
            try:
                # extract intent and entities
                extracted = self.dialog_router.extract_intent(request=request, session=session, connection=conn)
                if isinstance(extracted, tuple):
                    request.intent = extracted[0]
                    request.entities = extracted[1]
                    if len(extracted) > 2:
                        request.intent_priority = extracted[2]
                elif isinstance(extracted, str):
                    request.intent = extracted
                ticks.append(("dialog_router.extract_intent", time() - start_time))
                # preprocess before route
                self.dialog_router.before_route(request, session, conn)
                ticks.append(("dialog_router.before_route", time() - start_time))
                # route dialog
                dialog_service = self.dialog_router.route(request, session, conn)
                if isinstance(dialog_service, type):
                    dialog_service = dialog_service(self.logger, self.config, self.timezone)
                ticks.append(("dialog_router.route", time() - start_time))
            except Exception as ex:
                self.logger.error("Error occured in dialog_router: " + str(ex) + "\n" + traceback.format_exc())
                dialog_service = self.dialog_router.handle_exception(request, session, ex, conn)
            # process dialog
            try:
                # extract entities
                for k, v in dialog_service.extract_entities(request, session, conn).items():
                    if not request.entities.get(k, ""): request.entities[k] = v
                ticks.append(("dialog_service.extract_entities", time() - start_time))
                # initialize session data
                if session.topic.is_new:
                    session.data = dialog_service.get_slots(request, session, conn)
                ticks.append(("dialog_service.get_slots", time() - start_time))
                # process request
                dialog_service.process_request(request, session, conn)
                ticks.append(("dialog_service.process_request", time() - start_time))
                # compose response
                response_messages = dialog_service.compose_response(request, session, conn)
                if not response_messages:
                    self.logger.info("No response")
                    response_messages = []
                elif not isinstance(response_messages, list):
                    response_messages = [response_messages]
                for rm in response_messages:
                    if isinstance(rm, Message):
                        response.messages.append(rm)
                    elif isinstance(rm, str):
                        response.messages.append(request.reply(text=rm))
                ticks.append(("dialog_service.compose_response", time() - start_time))
            except Exception as ex:
                self.logger.error("Error occured in dialog_service: " + str(ex) + "\n" + traceback.format_exc())
                response.messages = [dialog_service.handle_exception(request, session, ex, conn)]
            # save session and user
            session_for_log = deepcopy(session)
            try:
                session.reset(self.config.get("keep_session_data", False))
                self.session_store.save_session(session, conn)
                ticks.append(("save_session", time() - start_time))
                self.user_repository.save_user(request.user, conn)
                ticks.append(("save_user", time() - start_time))
            except Exception as ex:
                self.logger.error("Error occured in saving session/user: " + str(ex) + "\n" + traceback.format_exc())
            # message log
            try:
                response.milliseconds = int(ticks[-1][1] * 1000)
                response.performance_info = ticks
                self.message_logger.write(request, response, session_for_log, conn)
            except Exception as ex:
                self.logger.error("Error occured in logging message: " + str(ex) + "\n" + traceback.format_exc())
        except Exception as ex:
            self.logger.error("Error occured in preparing or finalizing: " + str(ex) + "\n" + traceback.format_exc())
        finally:
            conn.close()
        return response

    def get_message_log(self, count=20, max_id=2147483647):
        """
        Get message logs in 24 hours

        Parameters
        ----------
        count : int
            Record count to get
        max_id : int
            Max value of id

        Returns
        -------
        message_logs : [dict]
            Message logs
        """
        message_logs = []
        connection = self.connection_provider.get_connection()
        try:
            message_logs = self.message_logger.get_recent_log(count, max_id, connection)
        except Exception as ex:
            self.logger.error("Error occured in getting message log: " + str(ex) + "\n" + traceback.format_exc())
        finally:
            connection.close()
        return message_logs
