""" base class of classifier """
import logging
from minette.session.session_store import Session
from minette.dialog.dialog_service import DialogService
from minette.dialog.message import Message

class Classifier:
    def __init__(self, logger:logging.Logger=None):
        self.logger = logger
        self.timezone = None

    def classify(self, request:Message, session: Session) -> DialogService:
        """ Detect the topic from what user is saying and return DialogService suitable for it """
        return DialogService(request, session, self.logger, self.timezone)
