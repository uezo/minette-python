""" Session datamodel and defalt SessionStore """
from datetime import datetime
from logging import Logger, getLogger
import traceback
from copy import deepcopy
from sqlite3 import Row
from minette.util import date_to_str, str_to_date
from minette.serializer import JsonSerializable, encode_json, decode_json


class Priority:
    """
    Priority of topic

    Attributes
    ----------
    Highest : int
        Highest (100)
    High : int
        High (75)
    Normal : int
        Normal (50)
    Low : int
        Low (25)
    Ignore : int
        Ignore (0)
    """
    Highest = 100
    High = 75
    Normal = 50
    Low = 25
    Ignore = 0


class Topic(JsonSerializable):
    """
    Topic

    Attributes
    ----------
    name : str
        Name of topic
    status : str
        Status of topic
    is_new : bool
        Topic starts at this trun or not
    keep_on : bool
        Keep this topic at next turn or not
    previous : Topic
        Previous topic object
    priority : int
        Priority of topic
    is_changed : bool
        Topic changed at this turn or not
    """
    def __init__(self):
        self.name = ""
        self.status = ""
        self.is_new = False
        self.keep_on = False
        self.previous = None
        self.priority = Priority.Normal

    @property
    def is_changed(self):
        return False if self.previous and self.previous.name == self.name else True


class Session(JsonSerializable):
    """
    Session

    Attributes
    ----------
    channel : str
        Channel
    channel_user_id : str
        Channel user ID
    timestamp : datetime
        Timestamp
    is_new : bool
        New created session or not
    topic : Topic
        Current topic
    data : dict
        Data slots
    error : dict
        Error info
    """
    def __init__(self, channel, channel_user_id):
        """
        Parameters
        ----------
        channel : str
            Channel
        channel_user_id : str
            Channel user ID
        """
        self.channel = channel
        self.channel_user_id = channel_user_id
        self.timestamp = None
        self.is_new = True
        self.topic = Topic()
        self.data = {}
        self.error = {}

    def reset(self, keep_data=False):
        """
        Backup to previous topic and remove data

        Parameters
        ----------
        keep_data : bool, default False
            Keep session data to next turn
        """
        # backup previous topic
        self.topic.previous = None
        self.topic.previous = deepcopy(self.topic)
        # remove data if topic not keep_on
        if not self.topic.keep_on:
            self.topic.name = ""
            self.topic.status = ""
            self.topic.priority = Priority.Normal
            self.data = self.data if keep_data else {}
            self.error = {}

    def previous_data(self, key, default):
        """
        Get previous session data of given key

        Parameters
        ----------
        key : str
            Key for data
        default : Any
            Default value of data

        Returns
        -------
        data : Any
            Value of previous data
        """
        return self.data.get(key, default) if self.topic.is_changed else default

    def set_error(self, ex, info=None):
        """
        Set error info

        Parameters
        ----------
        ex : Exception
            Exception
        info : dict
            More information for debugging
        """
        self.error = {"exception": str(ex), "traceback": traceback.format_exc(), "info": info if info else {}}


class SessionStore:
    """
    Session store to enable successive conversation

    Attributes
    ----------
    sqls : dict
        SQLs used in SessionStore
    timeout : int
        Session timeout (Seconds)
    logger : Logger
        Logger
    config : Config
        Configuration
    timezone : timezone
        Timezone
    """
    def __init__(self, timeout=300, logger=None, config=None, timezone=None,
                 connection_provider_for_prepare=None, table_name="session"):
        """
        Parameters
        ----------
        timeout : int, default 300
            Session timeout (Seconds)
        logger : Logger, default None
            Logger
        config : Config, default None
            Configuration
        timezone : timezone, default None
            Timezone
        connection_provider_for_prepare : ConnectionProvider, default None
            Connection provider for preparing table if not exist
        table_name : str, default "session"
            Table name for session store
        """
        self.sqls = self.get_sqls(table_name)
        self.timeout = timeout if timeout else 300
        self.logger = logger if logger else getLogger(__name__)
        self.config = config
        self.timezone = timezone
        if connection_provider_for_prepare:
            connection_provider_for_prepare.prepare_table(self.sqls["prepare_check"], self.sqls["prepare_create"])

    def get_sqls(self, table_name):
        """
        Get SQLs used in SessionStore

        Parameters
        ----------
        table_name : str
            Table name for SessionStore

        Returns
        -------
        sqls : dict
            SQLs used in SessionStore
        """
        return {
            "prepare_check": "select * from sqlite_master where type='table' and name='{0}'".format(table_name),
            "prepare_create": "create table {0} (channel TEXT, channel_user_id TEXT, timestamp TEXT, topic_name TEXT, topic_status TEXT, topic_previous TEXT, topic_priority INTEGER, data TEXT, primary key(channel, channel_user_id))".format(table_name),
            "get_session": "select channel, channel_user_id, timestamp, topic_name, topic_status, topic_previous, topic_priority, data from {0} where channel=? and channel_user_id=? limit 1".format(table_name),
            "save_session": "replace into {0} (channel, channel_user_id, timestamp, topic_name, topic_status, topic_previous, topic_priority, data) values (?,?,?,?,?,?,?,?)".format(table_name),
        }

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
            "channel": str(row["channel"]),
            "channel_user_id": str(row["channel_user_id"]),
            "timestamp": str_to_date(str(row["timestamp"])),
            "topic_name": str(row["topic_name"]),
            "topic_status": str(row["topic_status"]),
            "topic_priority": int(row["topic_priority"]),
            "topic_previous": decode_json(row["topic_previous"]),
            "data": decode_json(row["data"])
        }

    def get_session(self, channel, channel_user_id, connection):
        """
        Get session for channel and channel_user_id

        Parameters
        ----------
        channel : str
            Channel
        channel_user_id : str
            Channel user ID
        connection : Connection
            Connection

        Returns
        -------
        session : Session
            Session for channel and channel_user_id
        """
        session = Session(channel, channel_user_id)
        session.timestamp = datetime.now(self.timezone)
        if not channel_user_id:
            return session
        try:
            cursor = connection.cursor()
            cursor.execute(self.sqls["get_session"], (channel, channel_user_id))
            row = cursor.fetchone()
            if row is not None:
                record = self.map_record(row)
                last_access = record["timestamp"]
                last_access = self.timezone.localize(last_access)
                if (datetime.now(self.timezone) - last_access).total_seconds() <= self.timeout:
                    session.topic.name = record["topic_name"]
                    session.topic.status = record["topic_status"]
                    session.topic.priority = record["topic_priority"]
                    session.topic.previous = Topic.from_dict(record["topic_previous"]) if record["topic_previous"] else None
                    session.data = record["data"] if record["data"] else {}
                    session.is_new = False
        except Exception as ex:
            self.logger.error("Error occured in restoring session from database: " + str(ex) + "\n" + traceback.format_exc())
        return session

    def save_session(self, session, connection):
        """
        Save session

        Parameters
        ----------
        session : Session
            Session to save
        connection : Connection
            Connection
        """
        if not session.channel_user_id:
            return
        session_dict = session.to_dict()
        serialized_topic = encode_json(session_dict["topic"]["previous"])
        serialized_data = encode_json(session_dict["data"])
        cursor = connection.cursor()
        cursor.execute(self.sqls["save_session"], (session.channel, session.channel_user_id, date_to_str(session.timestamp), session.topic.name, session.topic.status, serialized_topic, session.topic.priority, serialized_data))
        connection.commit()
