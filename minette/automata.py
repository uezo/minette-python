""" Core module of Minette """
from time import time
from typing import List
import logging
import traceback
from configparser import ConfigParser
from pytz import timezone
from minette.session import SessionStore
from minette.user import UserRepository
from minette.tagger import Tagger
from minette.dialog import Message, MessageLogger, Classifier

class Automata:
    def __init__(self, session_store:SessionStore, user_repository:UserRepository, classifier:Classifier, tagger:Tagger, message_logger:MessageLogger, logger:logging.Logger, config:ConfigParser, tzone:timezone):
        self.session_store = session_store
        self.user_repository = user_repository
        self.classifier = classifier
        self.tagger = tagger
        self.message_logger = message_logger
        self.logger = logger
        self.config = config
        self.timezone = tzone

    def execute(self, request) -> List[Message]:
        start_time = time()
        #processing dialog
        try:
            if isinstance(request, str):
                request = Message(text=request)
            response = [request.get_reply_message("?")]
            request.words = self.tagger.parse(request.text)
            request.user = self.user_repository.get_user(request.channel, request.channel_user)
            session = self.session_store.get_session(request.channel, request.channel_user)
            dialog_service = self.classifier.classify(request, session)
            if isinstance(dialog_service, type):
                dialog_service = dialog_service(request=request, session=session, logger=self.logger, config=self.config, tzone=self.timezone)
            elif dialog_service is None:
                self.logger.info("No dialog services")
                return []
            dialog_service.decode_data()
            dialog_service.process_request()
            response = dialog_service.compose_response()
            dialog_service.encode_data()
            self.session_store.save_session(session)
            self.user_repository.save_user(request.user)
        except Exception as ex:
            self.logger.error("Error occured in processing dialog: " + str(ex) + "\n" + traceback.format_exc())
            session.keep_mode = False
        #clear session
        if session.keep_mode is False:
            session.mode = ""
            session.dialog_status = ""
            session.data = None
        #message log
        if not isinstance(response, list):
            response = [response]
        total_ms = int((time() - start_time) * 1000)
        outtexts = []
        for r in response:
            outtexts.append(r.text)
        self.message_logger.write(request, " / ".join(outtexts), total_ms)
        return response

def get_default_logger():
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.DEBUG)
    formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    stream_handler = logging.StreamHandler()
    stream_handler.setLevel(logging.DEBUG)
    stream_handler.setFormatter(formatter)
    logger.addHandler(stream_handler)
    file_handler = logging.FileHandler(filename="./minette.log")
    file_handler.setLevel(logging.ERROR)
    file_handler.setFormatter(logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s'))
    logger.addHandler(file_handler)
    return logger

def create(session_store:SessionStore=None, user_repository:UserRepository=None, classifier:Classifier=None, tagger:Tagger=None, message_logger:MessageLogger=None, logger:logging.Logger=None, config_file="", prepare_database=True):
    #initialize logger and config
    if logger is None: logger = get_default_logger()
    config = ConfigParser()
    config.read(config_file if config_file else "./minette.ini")
    tzone = timezone("UTC")
    try:
        tzone = timezone(config.get("minette", "timezone"))
    except Exception as ex:
        logger.warn("No timezone or invalid timezone: " + str(ex) + "\n" + traceback.format_exc())
    #initialize default components
    args = {"logger":logger, "config":config, "tzone":tzone}
    if session_store is None:
        session_store = SessionStore(**args, prepare_database=prepare_database)
    elif isinstance(session_store, type):
        session_store = session_store(**args, prepare_database=prepare_database)
    if user_repository is None:
        user_repository = UserRepository(**args, prepare_database=prepare_database)
    elif isinstance(user_repository, type):
        user_repository = user_repository(**args, prepare_database=prepare_database)
    if classifier is None:
        classifier = Classifier(**args)
    elif isinstance(classifier, type):
        classifier = classifier(**args)
    if tagger is None:
        tagger = Tagger(**args)
    elif isinstance(tagger, type):
        tagger = tagger(**args)
    if message_logger is None: message_logger = MessageLogger(**args, prepare_database=prepare_database)
    #create automata
    return Automata(session_store, user_repository, classifier, tagger, message_logger, logger, config, tzone)
