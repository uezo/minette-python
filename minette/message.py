""" Models and MessageLogger """
from datetime import datetime, timedelta
from logging import Logger, getLogger
from pytz import timezone as tz
import requests
import copy
from minette.util import date_to_str, str_to_date, date_to_unixtime, get_class
from minette.serializer import JsonSerializable, encode_json, decode_json
from minette.session import Priority


class Group(JsonSerializable):
    """
    Group

    Attributes
    ----------
    id : str
        ID of group
    type : str
        Type of group
    """
    def __init__(self, id, type):
        """
        Parameters
        ----------
        id : str
            ID of group
        type : str
            Type of group
        """
        self.id = id
        self.type = type


class Payload(JsonSerializable):
    """
    Payload

    Attributes
    ----------
    content_type : str
        Content type of payload
    url : str
        Url to get content
    thumb : str
        URL to get thumbnail image
    headers : dict
        HTTP Headers required for getting content
    content : Any
        Content itself
    """
    def __init__(self, content_type="image", url=None, thumb=None, headers=None, content=None):
        """
        Parameters
        ----------
        content_type : str, default "image"
            Content type of payload
        url : str, default None
            Url to get content
        thumb : str, default None
            URL to get thumbnail image
        headers : dict, default None
            HTTP Headers required for getting content
        content : Any, default None
            Content itself
        """
        self.content_type = content_type
        self.url = url
        self.thumb = thumb if thumb else url
        self.headers = headers if headers else {}
        self.content = content

    def get(self, set_content=False):
        """
        Get content data from url

        Parameters
        ----------
        set_content : bool, default False
            Set content data to content property

        Returns
        -------
        content : Any
            Content
        """
        data = requests.get(self.url, headers=self.headers).content
        if set_content:
            self.content = data
        return data

    def save(self, filepath):
        """
        Save content data to file

        Parameters
        ----------
        filepath : str
            File path to save content
        """
        data = self.get()
        with open(filepath, "wb") as f:
            f.write(data)


class Message(JsonSerializable):
    """
    Message

    Attributes
    ----------
    id : str
        Message ID
    type : str
        Message type
    timestamp : datetime
        Timestamp
    channel : str
        Channel
    channel_detail : str
        Detail information of channel
    channel_user_id : str
        User ID of channel
    channel_message : Any
        Original message from channel
    token : Any
        Token to do actions to the channel
    user : User
        User
    group : Group
        Group
    text : str
        Body of message
    words : [WordNode]
        Word nodes parsed by tagger
    payloads : [Payload]
        Payloads
    intent : str
        Intent extracted from message
    intent_priority : int
        Priority for processing intent
    entities : dict
        Entities extracted from message
    is_adhoc : bool
        Process adhoc or not
    """
    def __init__(self, id=None, type="text", channel="console",
                 channel_detail=None, channel_user_id="anonymous",
                 channel_message=None, token=None, text=None, payloads=None):
        """
        Parameters
        ----------
        id : str, default None
            Message ID
        type : str default "text"
            Message type
        channel : str, default "console"
            Channel
        channel_detail : str, default None
            Detail information of channel
        channel_user_id : str, default "anonymous"
            User ID of channel
        channel_message : Any, default None
            Original message from channel
        token : Any, default None
            Token to do actions to the channel
        text : str, default None
            Body of message
        payloads : [Payload], default None
            Payloads
        """
        self.id = id if id else ""
        self.type = type
        self.timestamp = datetime.now(tz("UTC"))
        self.channel = channel
        self.channel_detail = channel_detail
        self.channel_user_id = channel_user_id
        self.channel_message = channel_message
        self.token = token
        self.user = None
        self.group = None
        self.text = text if text else ""
        self.words = []
        self.payloads = payloads if payloads else []
        self.intent = ""
        self.intent_priority = Priority.Normal
        self.entities = {}
        self.is_adhoc = False

    def reply(self, text=None, payloads=None, type="text"):
        """
        Get reply message for this message

        Parameters
        ----------
        text : str, default None
            Body of message
        payloads : [Payload], default None
            Payloads
        type : str default "text"
            Message type

        Returns
        -------
        reply_message : Message
            Reply message for this message
        """
        message = copy.copy(self)
        message.timestamp = datetime.now(message.timestamp.tzinfo)
        message.channel_message = None
        message.type = type
        message.text = text
        message.words = []
        message.payloads = payloads if payloads else []
        message.intent = ""
        message.entities = {}
        message.is_adhoc = False
        return message

    def to_dict(self):
        """
        Convert Message object to dict

        Returns
        -------
        message_dict : dict
            Message dictionary
        """
        message_dict = super().to_dict()
        # channel_message is not JSON serializable
        message_dict["channel_message"] = str(message_dict["channel_message"])
        return message_dict

    @classmethod
    def from_dict(cls, data):
        """
        Convert dict to Message object

        Parameters
        ----------
        data : dict
            Dictionary

        Returns
        -------
        message : Message
            Message object
        """
        message = super().from_dict(data, as_args=False)
        message.timestamp = str_to_date(message.timestamp)
        message.payloads = Payload.from_dict_list(message.payloads)
        return message


class Response(JsonSerializable):
    """
    Response from chatbot

    Attributes
    ----------
    messages : [Message]
        Response messages
    headers : dict
        Response header
    for_channel : Any
        Formetted response for channels
    milliseconds : int
        Total processing time in milliseconds
    performance_info : list
        Ticks of each steps in chat()
    json : str
        JSON encoded response for channels
    """
    def __init__(self, messages=None, headers=None, for_channel=None):
        """
        Parameters
        ----------
        messages : [Message], default None
            Response messages
        headers : dict, default None
            Response header
        for_channel : Any, default None
            Formetted response for channels
        milliseconds : int
            Total processing time in milliseconds
        """
        self.messages = messages if messages else []
        self.headers = headers if headers else {}
        self.for_channel = for_channel
        self.milliseconds = 0
        self.performance_info = []

    @property
    def json(self):
        return encode_json(self.for_channel)

    def to_dict(self):
        """
        Convert Response object to dict

        Returns
        -------
        response_dict : dict
            Response dictionary
        """
        response_dict = super().to_dict()
        # for_channel is not JSON serializable
        response_dict["for_channel"] = str(response_dict["for_channel"])
        return response_dict


class MessageLogger:
    """
    Message logger to analyze the communication

    Attributes
    ----------
    sqls : dict
        SQLs used in MessageLogger
    logger : Logger
        Logger
    config : Config
        Configuration
    timezone : timezone
        Timezone
    """
    def __init__(self, logger=None, config=None, timezone=None,
                 connection_provider_for_prepare=None, table_name="messagelog"):
        """
        Parameters
        ----------
        logger : Logger, default None
            Logger
        config : Config, default None
            Configuration
        timezone : timezone, default None
            Timezone
        connection_provider_for_prepare : ConnectionProvider
            Connection provider for preparing table if not exist
        table_name : str
            Table name for message log
        """
        self.sqls = self.get_sqls(table_name)
        self.logger = logger if logger else getLogger(__name__)
        self.config = config
        self.timezone = timezone
        if connection_provider_for_prepare:
            connection_provider_for_prepare.prepare_table(self.sqls["prepare_check"], self.sqls["prepare_create"])

    def get_sqls(self, table_name):
        """
        Get SQLs used in MessageLogger

        Parameters
        ----------
        table_name : str
            Table name for message log

        Returns
        -------
        sqls : dict
            SQLs used in MessageLogger
        """
        return {
            "prepare_check": "select * from sqlite_master where type='table' and name='{0}'".format(table_name),
            "prepare_create": "create table {0} (id INTEGER PRIMARY KEY, timestamp TEXT, request_id TEXT, channel TEXT, channel_detail TEXT, channel_user_id TEXT, request_json TEXT, response_json TEXT, session_json TEXT)".format(table_name),
            "write": "insert into {0} (timestamp, request_id, channel, channel_detail, channel_user_id, request_json, response_json, session_json) values (?,?,?,?,?,?,?,?)".format(table_name),
            "get_recent_log": "select timestamp, request_id, channel, channel_detail, channel_user_id, request_json, response_json, session_json from {0} where id <= ? order by id desc limit ?".format(table_name)
        }

    def write(self, request, response, session, connection):
        """
        Write message log

        Parameters
        ----------
        request : Message
            Request message
        response : Response
            Response from chatbot
        session : Session
            Session
        total_ms : int
            Response time (milliseconds)
        connection : Connection
            Connection
        """
        now = datetime.now(self.timezone)
        cursor = connection.cursor()
        cursor.execute(self.sqls["write"], (date_to_str(now), request.id, request.channel, request.channel_detail, request.channel_user_id, request.to_json(), response.to_json(), session.to_json()))
        connection.commit()

    def map_record(self, row):
        """
        Map database record to dictionary

        Parameters
        ----------
        row : Row
            A row of record set

        Returns
        -------
        mapped_record : dict
            Record as dict
        """
        return {
            "timestamp": str_to_date(str(row["timestamp"])),
            "request_id": str(row["request_id"]),
            "channel": str(row["channel"]),
            "channel_detail": str(row["channel_detail"]),
            "channel_user_id": str(row["channel_user_id"]),
            "request": decode_json(str(row["request_json"])),
            "response": decode_json(str(row["response_json"])),
            "session": decode_json(str(row["session_json"]))
        }

    def get_recent_log(self, count, max_id, connection):
        """
        Get recent message log

        Parameters
        ----------
        count : int
            Record count to get
        max_id : int
            Max value of id
        connection : Connection
            Connection

        Returns
        -------
        logs : [dict]
            Recent message logs
        """
        cursor = connection.cursor()
        cursor.execute(self.sqls["get_recent_log"], (max_id, count))
        return [self.map_record(r) for r in cursor]
