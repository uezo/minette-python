""" base class of classifier """
import logging
from configparser import ConfigParser
from pytz import timezone
from minette.session.session_store import Session
from minette.dialog.dialog_service import DialogService
from minette.dialog.message import Message

class Classifier:
    def __init__(self, logger:logging.Logger=None, config:ConfigParser=None, tzone:timezone=None):
        self.logger = logger if logger else logging.getLogger(__name__)
        self.config = config
        self.timezone = tzone

    def classify(self, request:Message, session: Session) -> DialogService:
        """ Detect the topic from what user is saying and return DialogService suitable for it """
        return DialogService(request=request, session=session, logger=self.logger, config=self.config, tzone=self.timezone)
