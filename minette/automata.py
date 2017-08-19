""" Core module of Minette """
from time import time
import logging
import traceback
from pytz import timezone
from minette.database import ConnectionProvider
from minette.session import SessionStore
from minette.user import UserRepository
from minette.tagger import Tagger
from minette.dialog import Message, DialogService, MessageLogger, Classifier
from minette.util import get_class
from minette.config import Config

class Automata:
    def __init__(self, connection_provider, session_store, user_repository, classifier, tagger, message_logger, logger, config, tzone):
        """
        :param connection_provider: ConnectionProvider
        :type connection_provider: ConnectionProvider
        :param session_store: SessionStore
        :type session_store: SessionStore
        :param user_repository: UserRepository
        :type user_repository: UserRepository
        :param classifier: Classifier
        :type classifier: Classifier
        :param tagger: Tagger
        :type tagger: Tagger
        :param message_logger: MessageLogger
        :type message_logger: MessageLogger
        :param logger: logging.Logger
        :type logger: logging.Logger
        :param config: Config
        :type config: Config
        :param tzone: timezone
        :type tzone: timezone
        """
        self.connection_provider = connection_provider
        self.session_store = session_store
        self.user_repository = user_repository
        self.classifier = classifier
        self.tagger = tagger
        self.message_logger = message_logger
        self.logger = logger
        self.config = config
        self.timezone = tzone

    def execute(self, request):
        """
        :param request: Request message
        :type request: Message
        :return: Response message
        :rtype: [Message]
        """
        start_time = time()
        ticks = []
        #processing dialog
        try:
            #initialize response message
            if not isinstance(request, Message):
                request = Message(text=str(request))
            response = [request.get_reply_message("?")]
            conn = self.connection_provider.get_connection()
            ticks.append(("get_connection", time() - start_time))
            request.words = self.tagger.parse(request.text)
            ticks.append(("tagger.parse", time() - start_time))
            request.user = self.user_repository.get_user(request.channel, request.channel_user, conn)
            ticks.append(("get_user", time() - start_time))
            session = self.session_store.get_session(request.channel, request.channel_user, conn)
            ticks.append(("get_session", time() - start_time))
            session.mode, session.data = self.classifier.detect_mode(request, session, conn)
            ticks.append(("classifier.detect_mode", time() - start_time))
            dialog_service = self.classifier.classify(request, session, conn)
            ticks.append(("classifier.classify", time() - start_time))
            if isinstance(dialog_service, type):
                dialog_service = dialog_service(logger=self.logger, config=self.config, tzone=self.timezone)
            elif dialog_service is None:
                self.logger.info("No dialog services")
                return []
            ticks.append(("dialog_service instancing", time() - start_time))
            dialog_service.prepare_data(request=request, session=session, connection=conn)
            ticks.append(("dialog_service.prepare_data", time() - start_time))
            dialog_service.process_request(request=request, session=session, connection=conn)
            ticks.append(("dialog_service.process_request", time() - start_time))
            response = dialog_service.compose_response(request=request, session=session, connection=conn)
            ticks.append(("dialog_service.compose_response", time() - start_time))
            dialog_service.serialize_data(request=request, session=session, connection=conn)
            ticks.append(("dialog_service.serialize_data", time() - start_time))
        except Exception as ex:
            self.logger.error("Error occured in processing dialog: " + str(ex) + "\n" + traceback.format_exc())
            session.keep_mode = False
        #session and user
        try:
            #clear session
            if session.keep_mode is False:
                session.mode = ""
                session.dialog_status = ""
                session.data = None
            self.session_store.save_session(session, conn)
            ticks.append(("save_session", time() - start_time))
            self.user_repository.save_user(request.user, conn)
            ticks.append(("save_user", time() - start_time))
        except Exception as ex:
            self.logger.error("Error occured in saving session/user: " + str(ex) + "\n" + traceback.format_exc())
        #message log
        try:
            if not isinstance(response, list):
                response = [response]
            total_ms = int((time() - start_time) * 1000)
            outtexts = [r.text for r in response]
            self.message_logger.write(request, " / ".join(outtexts), total_ms, conn)
            ticks.append(("message_logger.write", time() - start_time))
        except Exception as ex:
            self.logger.error("Error occured in logging message: " + str(ex) + "\n" + traceback.format_exc())
        finally:
            conn.close()
        #performance log
        ticks_sum = 0
        performance_info = "Performance info:\nuser> " + request.text + "\n"
        performance_info += "minette> " + response[0].text + "\n"
        for i, v in enumerate(ticks):
            performance_info += v[0] + ":" + str(int((v[1] - ticks_sum) * 1000)) + "\n"
            ticks_sum = v[1]
        self.logger.debug(performance_info)
        return response

def get_default_logger():
    """
    :return: Default Logger
    :rtype: logging.Logger
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
    file_handler = logging.FileHandler(filename="./minette.log")
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    return logger

def create(connection_provider=None, session_store=None, user_repository=None, classifier=None, tagger=None, message_logger=None, logger=None, config_file="", prepare_table=True, default_dialog_service=None):
    """
    :param connection_provider: ConnectionProvider
    :type connection_provider: ConnectionProvider
    :param session_store: SessionStore
    :type session_store: SessionStore
    :param user_repository: UserRepository
    :type user_repository: UserRepository
    :param classifier: Classifier
    :type classifier: Classifier
    :param tagger: Tagger
    :type tagger: Tagger
    :param message_logger: MessageLogger
    :type message_logger: MessageLogger
    :param logger: logging.Logger
    :type logger: logging.Logger
    :param config_file: Path to configuration file
    :type config_file: str
    :param prepare_table: Check and create table if not existing
    :type prepare_table: bool
    :param default_dialog_service: Default dialog service
    :type default_dialog_service: DialogService
    """
    #initialize logger and config
    if logger is None:
        logger = get_default_logger()
    config = Config(config_file)
    #timezone
    tzone = timezone(config.get("timezone", default="UTC"))
    #initialize connection provider
    connection_str = config.get("connection_str")
    if not isinstance(connection_provider, ConnectionProvider):
        connection_provider_classname = config.get("connection_provider")
        if connection_provider_classname:
            connection_provider = get_class(connection_provider_classname)
        else:
            connection_provider = ConnectionProvider
        connection_provider = connection_provider(connection_str)
    #initialize default components
    args = {"logger":logger, "config":config, "tzone":tzone}
    #session store
    if session_store is None:
        session_store_classname = config.get("session_store")
        if session_store_classname:
            session_store = get_class(session_store_classname)
        else:
            session_store = SessionStore
    if isinstance(session_store, type):
        session_args = args.copy()
        session_args["connection_provider_for_prepare"] = connection_provider if prepare_table else None
        session_args["table_name"] = config.get("session_table", default="session")
        session_args["timeout"] = config.getint("session_timeout", default=300)
        session_store = session_store(**session_args)
    #user repository
    if user_repository is None:
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
    #classifier
    if classifier is None:
        classifier_classname = config.get("default_classifier")
        if classifier_classname:
            classifier = get_class(classifier_classname)
        else:
            classifier = Classifier
    if isinstance(classifier, type):
        classifier_args = args.copy()
        if default_dialog_service:
            classifier_args["default_dialog_service"] = default_dialog_service
        elif config.get("default_dialog_service", default=None):
            classifier_args["default_dialog_service"] = get_class(config.get("default_dialog_service", default=None))
        classifier = classifier(**classifier_args)
    #tagger
    if tagger is None:
        tagger_classname = config.get("tagger")
        if tagger_classname:
            tagger = get_class(tagger_classname)
        else:
            tagger = Tagger
    if isinstance(tagger, type):
        tagger = tagger(**args)
    #message logger
    if message_logger is None:
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
    #create automata
    return Automata(connection_provider, session_store, user_repository, classifier, tagger, message_logger, logger, config, tzone)
