""" Models and MessageLogger """
from datetime import datetime, timedelta
from logging import Logger, getLogger
from pytz import timezone as tz
import requests
import copy
from minette.util import date_to_str, str_to_date, date_to_unixtime, get_class
from minette.serializer import JsonSerializable, encode_json
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
        self.id = id
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
        """
        self.messages = messages if messages else []
        self.headers = headers if headers else {}
        self.for_channel = for_channel

    @property
    def json(self):
        return encode_json(self.for_channel)


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
            "prepare_create": "create table {0} (timestamp TEXT, channel TEXT, channel_detail TEXT, channel_user_id TEXT, totaltick INTEGER, user_id TEXT, user_name TEXT, message_type TEXT, topic_name TEXT, topic_status TEXT, topic_is_new TEXT, topic_keep_on TEXT, topic_priority INTEGER, is_adhoc TEXT, input_text TEXT, intent TEXT, intent_priority INTEGER, entities TEXT, output_text TEXT, error_info Text)".format(table_name),
            "write": "insert into {0} (timestamp, channel, channel_detail, channel_user_id, totaltick, user_id, user_name, message_type, topic_name, topic_status, topic_is_new, topic_keep_on, topic_priority, is_adhoc, input_text, intent, intent_priority, entities, output_text, error_info) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)".format(table_name),
            "get_recent_log": "select timestamp, channel, channel_detail, channel_user_id, totaltick, user_id, user_name, message_type, topic_name, topic_status, topic_is_new, topic_keep_on, topic_priority, is_adhoc, input_text, intent, intent_priority, entities, output_text, error_info from {0} where timestamp > ? order by timestamp desc".format(table_name)
        }

    def write(self, request, response, session, total_ms, connection):
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
        res_texts = [res.text if res.text else "" for res in response.messages]
        if not res_texts:
            res_texts = [""]
        for res_text in res_texts:
            cursor.execute(self.sqls["write"], (date_to_str(now), request.channel, request.channel_detail, request.channel_user_id, total_ms, request.user.id, request.user.name, request.type, session.topic.name, session.topic.status, session.topic.is_new, session.topic.keep_on, session.topic.priority, request.is_adhoc, request.text, request.intent, request.intent_priority, encode_json(request.entities), res_text, encode_json(session.error)))
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
            "channel": str(row["channel"]),
            "channel_detail": str(row["channel_detail"]),
            "channel_user_id": str(row["channel_user_id"]),
            "totaltick": row["totaltick"],
            "user_id": str(row["user_id"]),
            "user_name": str(row["user_name"]),
            "message_type": str(row["message_type"]),
            "topic_name": str(row["topic_name"]),
            "topic_status": str(row["topic_status"]),
            "topic_is_new": row["topic_is_new"],
            "topic_keep_on": row["topic_keep_on"],
            "topic_priority": row["topic_priority"],
            "is_adhoc": row["is_adhoc"],
            "input_text": str(row["input_text"]),
            "intent": str(row["intent"]),
            "intent_priority": str(row["intent_priority"]),
            "entities": encode_json(str(row["entities"])),
            "output_text": str(row["output_text"]),
            "error_info": encode_json(str(row["error_info"])),
        }

    def get_recent_log(self, connection, with_column=False):
        """
        Get recent message log

        Parameters
        ----------
        connection : Connection
            Connection

        Returns
        -------
        logs : [dict]
            Recent message logs
        """
        now = datetime.now(self.timezone)
        dt = now + timedelta(days=-1)
        cursor = connection.cursor()
        cursor.execute(self.sqls["get_recent_log"], (dt, ))
        return [self.map_record(r) for r in cursor]
