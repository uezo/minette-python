""" base class of dialog service """
import logging
from configparser import ConfigParser
from pytz import timezone
from minette.session.session_store import Session
from minette.dialog.message import Message

class DialogService:
    def __init__(self, request:Message, session:Session, logger:logging.Logger=None, config:ConfigParser=None, tzone:timezone=None):
        self.request = request
        self.session = session
        self.logger = logger
        self.timezone = tzone
        self.config = config

    def decode_data(self):
        """ Restore data from JSON to your own data objects """
        pass

    def encode_data(self):
        """ Serialize your own data objects to JSON """
        pass

    def process_request(self):
        """ Process your bot's functions/skills and setup session data """
        pass

    def compose_response(self) -> Message:
        """ Compose the response messages using session data """
        return self.request.get_reply_message("You said: " + self.request.text)
