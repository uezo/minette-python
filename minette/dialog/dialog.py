""" Data models and default components for processing dialog using SQLite """
from datetime import datetime
import logging
from pytz import timezone
import requests
from minette.util import date_to_str, date_to_unixtime

class Payload:
    def __init__(self, content_type="image", url="", thumb="", headers=None, content=None):
        """
        :param content_type: Type of content like image, audio, video or file
        :type content_type: str
        :param url: URL to get content
        :type url: str
        :param thumb: URL to get thumbnail image
        :type thumb: str
        :param headers: HTTP Headers required for getting content
        :type headers: dict
        :param content: Content itself
        """
        self.content_type = content_type
        self.url = url
        self.thumb = thumb if thumb != "" else url
        self.headers = headers if headers else {}
        self.content = content
    
    def get(self, set_content=False):
        """
        :param set_content: Set content data to content property
        :type set_content: bool
        :return: Content
        """
        data = requests.get(self.url, headers=self.headers).content
        if set_content:
            self.content = data
        return data

    def save(self, filepath):
        """
        :param filepath: File path to save content
        :type filepath: str
        """
        data = self.get()
        with open(filepath, "wb") as f:
            f.write(data)

class Message:
    def __init__(self, message_id="", message_type="message", timestamp=None, channel="[NOT_SPECIFIED]", channel_user="[ANONYMOUS]", channel_message=None, token="", text="", words=None, payloads=None, is_private=True, user=None):
        """
        :param message_id: ID of message
        :type message_id: str
        :param message_type: Type of message
        :type message_type: str
        :param timestamp: Timestamp
        :type timestamp: datetime
        :param channel: Channel
        :type channel: str
        :param channel_user: User ID of channel
        :type channel_user: str
        :param channel_message: Original message from channel
        :param token: Token of message for reply or some actions
        :type token: str
        :param text: Body of message
        :type text: str
        :param words: Word nodes
        :type words: [WordNode]
        :param payloads: Payloads
        :type payloads: [Payload]
        :param is_private: Chatting in private space
        :type is_private: bool
        :param user: User
        :type user: User
        """
        self.message_id = message_id
        self.type = message_type
        self.timestamp = timestamp if timestamp else datetime.now(timezone("UTC"))
        self.channel = channel
        self.channel_user = channel_user
        self.channel_message = channel_message
        self.token = token
        self.user = user
        self.text = text
        self.words = words if words else []
        self.payloads = payloads if payloads else []
        self.is_private = is_private

    def get_reply_message(self, text="", message_type="text", payloads=None):
        """
        :param text: Body of reply message
        :type text: str
        :param message_type: Type of message
        :type message_type: str
        :param payloads: Payloads
        :type payloads: [Payload]
        :return: Reply message for this message
        :rtype: Message
        """
        import copy
        message = copy.copy(self)
        message.timestamp = datetime.now(message.timestamp.tzinfo)
        message.channel_message = None
        message.type = message_type
        message.text = text
        message.words = []
        message.payloads = payloads if payloads else []
        return message


class MessageLogger:
    def __init__(self, logger=None, config=None, tzone=None, connection_provider_for_prepare=None, table_name="messagelog"):
        """
        :param logger: Logger
        :type logger: logging.Logger
        :param config: ConfigParser
        :type config: ConfigParser
        :param tzone: Timezone
        :type tzone: timezone
        :param connection_provider_for_prepare: ConnectionProvider to create table if not existing
        :type connection_provider_for_prepare: ConnectionProvider
        :param table_name: Message log table
        :type table_name: str
        """
        self.sqls = self.get_sqls(table_name)
        self.logger = logger if logger else logging.getLogger(__name__)
        self.config = config
        self.timezone = tzone
        if connection_provider_for_prepare:
            self.logger.warn("DB preparation for MessageLogger is ON. Turn off if this bot is runnning in production environment.")
            connection_provider_for_prepare.prepare_table(self.sqls["prepare_check"], self.sqls["prepare_create"])

    def get_sqls(self, table_name):
        """
        :param table_name: Message log table
        :type table_name: str
        :return: Dictionary of SQL
        :rtype: dict
        """
        return {
            "prepare_check": "select * from sqlite_master where type='table' and name='{0}'".format(table_name),
            "prepare_create": "create table {0} (timestamp TEXT, unixtime INTEGER, channel TEXT, totaltick INTEGER, user_id TEXT, user_name TEXT, message_type TEXT, input_text TEXT, output_text TEXT)".format(table_name),
            "write": "insert into {0} (timestamp, unixtime, channel, totaltick, user_id, user_name, message_type, input_text, output_text) values (?,?,?,?,?,?,?,?,?)".format(table_name)
        }

    def write(self, request, output_text, total_ms, connection):
        """
        :param request: Request message
        :type request: Message
        :param output_text: Body of response message
        :type output_text: str
        :param total_ms: Response time (milliseconds)
        :type total_ms: int
        :param connection: Connection
        :type connection: Connection
        """
        now = datetime.now(self.timezone)
        cursor = connection.cursor()
        cursor.execute(self.sqls["write"], (date_to_str(now), date_to_unixtime(now), request.channel, total_ms, request.user.user_id, request.user.name, request.type, request.text, output_text))
        connection.commit()


class DialogService:
    def __init__(self, request, session, logger=None, config=None, tzone=None, connection=None):
        """
        :param request: Request message
        :type request: Message
        :param session: Session
        :type session: Session
        :param logger: Logger
        :type logger: logging.Logger
        :param config: ConfigParser
        :type config: ConfigParser
        :param tzone: Timezone
        :type tzone: timezone
        :param connection: Connection
        :type connection: Connection
        """
        self.request = request
        self.session = session
        self.logger = logger
        self.timezone = tzone
        self.config = config
        self.connection = connection

    def decode_data(self):
        """ Restore data from JSON to your own data objects """
        pass

    def encode_data(self):
        """ Serialize your own data objects to JSON """
        pass

    def process_request(self):
        """ Process your bot's functions/skills and setup session data """
        pass

    def compose_response(self):
        """ Compose the response messages using session data
        :return: Response message
        :rtype: Message
        """
        return self.request.get_reply_message("You said: " + self.request.text)


class Classifier:
    def __init__(self, logger=None, config=None, tzone=None):
        """
        :param logger: Logger
        :type logger: logging.Logger
        :param config: ConfigParser
        :type config: ConfigParser
        :param tzone: Timezone
        :type tzone: timezone
        """
        self.logger = logger if logger else logging.getLogger(__name__)
        self.config = config
        self.timezone = tzone

    def classify(self, request, session, connection=None):
        """ Detect the topic from what user is saying and return DialogService suitable for it
        :param request: Request message
        :type request: Message
        :param session: Session
        :type session: Session
        :param connection: Connection
        :type connection: Connection
        :return: DialogService
        :rtype: DialogService
        """
        return DialogService(request=request, session=session, logger=self.logger, config=self.config, tzone=self.timezone, connection=connection)
