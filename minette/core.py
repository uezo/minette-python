""" Core module of minette """
import traceback
import logging
from datetime import datetime
from pytz import timezone as tz
from copy import deepcopy

from .models import (
    Topic,
    Message,
    PerformanceInfo,
    Response
)
from .datastore import (
    ConnectionProvider,
    ContextStore,
    UserStore,
    MessageLogStore,
    SQLiteConnectionProvider,
    SQLiteContextStore,
    SQLiteUserStore,
    SQLiteMessageLogStore
)
from .config import Config
from .dialog import (
    DialogService,
    DialogRouter,
    DependencyContainer
)
from .tagger import Tagger


class Minette:
    """
    Minette

    Attributes
    ----------
    config : minette.Config
        Configuration
    timezone : timezone
        Timezone
    logger : logging.Logger
        Logger
    connection_provider : ConnectionProvider
        Connection provider
    context_store: ContextStore
        Context store
    user_store: UserStore
        User store
    messagelog_store: MessageLogStore
        Message store
    default_dialog_service : DialogService
        Dialog service used when intent is not clear
    dialog_router: DialogRouter
        Dialog router to extract intent and entities,
        then returns proper DialogService for intent
    tagger: Tagger
        Morphological analysis engine
    """

    def __init__(self, *, config=None, config_file=None, timezone=None,
                 logger=None, log_file=None, logger_name=None,
                 data_stores=None,
                 connection_provider=None, connection_str=None,
                 context_store=None, context_table=None, context_timeout=None,
                 user_store=None, user_table=None,
                 messagelog_store=None, messagelog_table=None,
                 default_dialog_service=None, dialog_router=None,
                 tagger=None, tagger_max_length=None, prepare_table=True, **kwargs):
        """
        Parameters
        ----------
        config : minette.Config, default None
            Configuration
        config_file : str, default None
            Path to configuration file. Use `minette.ini` by default.
            config is used when both `config` and `config_file` are passed.
        timezone : pytz.timezone, default None
            Timezone
        logger : logging.Logger, default None
            Logger. All configuration including filters and handlers
            should be setup before instancing minette.
        log_file : str, default None
            Path to log file. Use `minette.log` by default.
            This is ignored when `logger` is passed.
        logger_name : str, default None
            Name for Logger to separate loggers between bot instances.
            Use `minette` by default.
            This is ignored when `logger` is passed.
        connection_provider : minette.ConnectionProvider or type, default None
            Fully setup instance of `ConnectionProvider` or its class.
            Use `SQLiteConnectionProvider` by default.
        connection_str : str, default None
            Connection string to create instance of ConnectionProvider.
            This is used when the class of ConnectionProvider
            passed for `connection_provider`.
        context_store: minette.ContextStore or type, default None
            Fully setup instance of `ContextStore` or its class.
            Use `SQLiteContextStore` by default.
        context_table: str, default None
            Database table name for ContextStore. Use `context` by default.
            This is ignored when instance of `ContextStore` is passed as
            `context_store`.
        context_timeout: int, default None
            Timeout of context(seconds, default 300).
        user_store: minette.UserStore or type, default None
            Fully setup instance of `UserStore` or its class.
            Use `SQLiteUserStore` by default.
        user_table: str, default None
            Database table name for UserStore. Use `user` by default.
            This is ignored when instance of `UserStore` is passed as
            `user_store`.
        messagelog_store: minette.MessageLogStore or type, default None
            Fully setup instance of `MessageLogStore` or its class.
            Use `SQLiteMessageLogStore` by default.
        messagelog_table: str, default None
            Database table name for MessageLogStore. Use `messegelog`
            by default.
            This is ignored when instance of `MessageLogStore` is passed as
            `messagelog_store`.
        default_dialog_service : minette.DialogService or type, default None
            Dialog service used when intent is not clear.
        dialog_router: minette.DialogRouter or type, default None
            Dialog router to extract intent and entities,
            and return proper DialogService for intent
        tagger: minette.Tagger or type, default None
            Morphological analysis engine
        tagger_max_length: Max length of the text to parse morph, default None
            Morphological analysis engine
        prepare_table: bool, default True
            Create tables for data stores if they don't exist.
        """
        # setup essensial members for other members
        if config:
            self.config = config
        else:
            self.config = Config(config_file or "minette.ini")
        self.timezone = timezone or tz(self.config.get("timezone") or "UTC")
        self.logger = self._get_logger(
            logger, log_file=log_file, logger_name=logger_name)
        self.connection_provider = self._get_connection_provider(
            connection_provider or (
                data_stores.connection_provider if data_stores else None),
            connection_str=connection_str, **kwargs)

        # make arguments dict
        setter_args = {
            "config": self.config,
            "timezone": self.timezone,
            "logger": self.logger,
            "connection_provider": self.connection_provider,
            "context_store": context_store or (
                data_stores.context_store if data_stores else None),
            "context_table": context_table,
            "context_timeout": context_timeout,
            "user_store": user_store or (
                data_stores.user_store if data_stores else None),
            "user_table": user_table,
            "messagelog_store": messagelog_store or (
                data_stores.messagelog_store if data_stores else None),
            "messagelog_table": messagelog_table,
            "dialog_router": dialog_router,
            "default_dialog_service": default_dialog_service,
            "tagger": tagger,
            "tagger_max_length": tagger_max_length,
        }
        setter_args.update({k: v for k, v in kwargs.items() if k not in setter_args})

        # setup members
        self.context_store = self._get_context_store(**setter_args)
        self.user_store = self._get_user_store(**setter_args)
        self.messagelog_store = self._get_messagelog_store(**setter_args)
        self.default_dialog_service = default_dialog_service
        self.dialog_router = self._get_dialog_router(**setter_args)
        self.tagger = self._get_tagger(**setter_args)

        # prepare tables
        if prepare_table is True:
            connection = self.connection_provider.get_connection()
            prepare_params = self.connection_provider.get_prepare_params()
            self.context_store.prepare_table(connection, prepare_params)
            self.user_store.prepare_table(connection, prepare_params)
            self.messagelog_store.prepare_table(connection, prepare_params)
            if hasattr(connection, "close"):
                connection.close()

    def _get_logger(self, logger, log_file=None, logger_name=None):
        lg = logger
        # use passed logger if already setup
        if lg:
            return lg
        lg = logging.getLogger(
            logger_name or self.config.get("logger_name") or "minette")
        # use logger if handlers are already setup
        # evaluate len() because lg.hasHandlers() returns True
        # even when lg.handlers == [] in some cases(e.g. pytest)
        if len(lg.handlers) > 0:
            return lg
        # setup logger
        lg.setLevel(logging.DEBUG)
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        stream_handler = logging.StreamHandler()
        stream_handler.setLevel(logging.INFO)
        stream_handler.setFormatter(formatter)
        lg.addHandler(stream_handler)
        file_handler = logging.FileHandler(
            filename=log_file or
            self.config.get("log_file") or "minette.log"
        )
        file_handler.setLevel(logging.ERROR)
        file_handler.setFormatter(formatter)
        lg.addHandler(file_handler)
        return lg

    def _get_connection_provider(self, connection_provider,
                                 connection_str=None, **kwargs):
        cp = connection_provider or SQLiteConnectionProvider
        if issubclass(cp, ConnectionProvider):
            cp = cp(
                connection_str=connection_str or
                self.config.get("connection_str") or "minette.db",
                **kwargs
            )
        return cp

    def _get_context_store(self, context_store, context_table=None,
                           context_timeout=None, **kwargs):
        ss = context_store or SQLiteContextStore
        if issubclass(ss, ContextStore):
            ss = ss(
                table_name=context_table or
                self.config.get("context_table") or "context",
                timeout=context_timeout or
                self.config.get("context_timeout") or 300,
                **kwargs
            )
        return ss

    def _get_user_store(self, user_store, user_table=None, **kwargs):
        us = user_store or SQLiteUserStore
        if issubclass(us, UserStore):
            us = us(
                table_name=user_table or
                self.config.get("user_table") or "user",
                **kwargs
            )
        return us

    def _get_messagelog_store(self, messagelog_store, messagelog_table=None,
                              **kwargs):
        ms = messagelog_store or SQLiteMessageLogStore
        if issubclass(ms, MessageLogStore):
            ms = ms(
                table_name=messagelog_table or
                self.config.get("messagelog_table") or "messagelog",
                **kwargs
            )
        return ms

    def _get_dialog_router(self, dialog_router, default_dialog_service=None,
                           **kwargs):
        dr = dialog_router or DialogRouter
        if issubclass(dr, DialogRouter):
            dr = dr(default_dialog_service=default_dialog_service, **kwargs)
        return dr

    def _get_tagger(self, tagger, tagger_max_length, **kwargs):
        tg = tagger or Tagger
        if issubclass(tg, Tagger):
            if tagger_max_length is not None:
                tg = tg(max_length=tagger_max_length, **kwargs)
            else:
                tg = tg(**kwargs)
        return tg

    def chat(self, request):
        """
        Get response from chatbot

        Examples
        --------
        >>> from minette import *
        >>> bot = Minette(defautl_dialog_service=EchoDialogService)
        >>> response = bot.chat("hello")
        >>> response.messages[0].text
        "You said: hello"

        Parameters
        ----------
        request : minette.Message or str
            Message to chatbot

        Returns
        -------
        response : minette.Response
            Response from chatbot
        """
        connection = None
        try:
            performance = PerformanceInfo()
            if isinstance(request, str):
                request = Message(text=request, timestamp=datetime.now(self.timezone))
            # connection
            connection = self.connection_provider.get_connection()
            performance.append("connection_provider.get_connection")
            # tagger
            request.words = self.tagger.parse(request.text)
            performance.append("tagger.parse")
            # user
            request.user = self._get_user(request, connection)
            performance.append("get_user")
            # context
            context = self._get_context(request, connection)
            performance.append("get_context")
            # route dialog
            dialog_service = self.dialog_router.execute(
                request=request, context=context,
                connection=connection, performance=performance)
            performance.append("dialog_router.execute")
            # process dialog
            response = dialog_service.execute(
                request=request, context=context,
                connection=connection, performance=performance)
            performance.append("dialog_service.execute")
            # save context
            context = self._save_context(context, connection)
            performance.append("save_context")
            # save user
            self._save_user(request.user, connection)
            performance.append("save_user")
        except Exception as ex:
            self.logger.error(
                "Error occured in chat: "
                + str(ex) + "\n" + traceback.format_exc())
            response = Response()
        finally:
            # set performance info to response
            response.performance = performance
            if connection:
                # message log
                try:
                    self.messagelog_store.save(
                        request, response, context, connection)
                except Exception as ex:
                    self.logger.error(
                        "Error occured in logging message: "
                        + str(ex) + "\n" + traceback.format_exc())
                # close connection
                if hasattr(connection, "close"):
                    connection.close()
        return response

    def _get_user(self, request, connection):
        user_scope = request.channel
        if self.config.get("user_scope") == "channel_detail":
            user_scope += "_" + request.channel_detail
        return self.user_store.get(
            user_scope, request.channel_user_id, connection)

    def _save_user(self, user, connection):
        self.user_store.save(user, connection)

    def _get_context(self, request, connection):
        context_scope = request.channel
        if self.config.get("context_scope") == "channel_detail":
            context_scope += "_" + request.channel_detail
        if request.group:
            context = self.context_store.get(
                context_scope, request.group.id, connection)
        else:
            context = self.context_store.get(
                context_scope, request.channel_user_id, connection)
        return context

    def _save_context(self, context, connection):
        context_for_log = deepcopy(context)
        context.reset(self.config.get("keep_context_data", False))
        self.context_store.save(context, connection)
        return context_for_log

    def dialog_uses(self, dependency_rules=None, **defaults):
        """
        Set dependency components for DialogServices/Router

        Examples
        --------
        >>> bot = Minette(defautl_dialog_service=EchoDialogService)
        >>> bot.dialog_uses(apiclient=apiclient, tagger=bot.tagger)

        You can use `apiclient` and `tagger` like below in your code of DialogService/Router.

        >>> self.dependencies.apiclient.get_profile(user.id)
        >>> self.dependencies.tagger.parse(request.text)

        Or, you can set dialog specific dependencies.

        >>> bot = Minette(defautl_dialog_service=EchoDialogService)
        >>> bot.dialog_uses({EchoDialogService: {"echo_engine": echo_engine}}, apiclient=apiclient, tagger=bot.tagger)

        Then, `echo_engine` can be used only in `EchoDialogService`, `apiclient` and `tagger` can be used any dialogs/router.

        Parameters
        ----------
        dependency_rules : dict
            Rules that defines on which components each DialogService/Router depends.
            Key is DialogService/Router class, value is dict of dependencies (name: value).

        defaults : dict
            Dependencies for all DialogServices/Router (name: value)
        """
        self.dialog_router.dependency_rules = dependency_rules
        self.dialog_router.default_dependencies = defaults
        self.dialog_router.dependencies = DependencyContainer(
            self.dialog_router, dependency_rules, **defaults)
