""" Set of data stores and connection provider using SQLite """
import sqlite3

from .connectionprovider import ConnectionProvider
from .contextstore import ContextStore
from .userstore import UserStore
from .messagelogstore import MessageLogStore
from .storeset import StoreSet


class SQLiteConnectionProvider(ConnectionProvider):
    """
    Connection provider for SQLite

    Attributes
    ----------
    connection_str : str
        Connection string
    """
    def get_connection(self):
        """
        Get connection

        Returns
        -------
        connection : Connection
            Database connection
        """
        connection = sqlite3.connect(
            self.connection_str, detect_types=sqlite3.PARSE_DECLTYPES)
        connection.row_factory = sqlite3.Row
        return connection


class SQLiteContextStore(ContextStore):
    """
    ContextStore using SQLite

    """
    def get_sqls(self):
        """
        Get SQLs used in ContextStore

        Returns
        -------
        sqls : dict
            SQLs used in ContextStore
        """
        return {
            "prepare_check": """
                select * from sqlite_master where type='table' and name='{0}'
                """.format(self.table_name),
            "prepare_create": """
                create table {0} (
                    channel TEXT, channel_user_id TEXT, timestamp TIMESTAMP,
                    topic_name TEXT, topic_status TEXT, topic_previous TEXT,
                    topic_priority INTEGER, data TEXT, primary key(channel,
                    channel_user_id))""".format(self.table_name),
            "get_context": """
                select
                    channel, channel_user_id, timestamp, topic_name,
                    topic_status, topic_previous, topic_priority, data
                from {0}
                where
                    channel=? and channel_user_id=? limit 1
                """.format(self.table_name),
            "save_context": """
                replace into {0} (
                    channel, channel_user_id, timestamp, topic_name,
                    topic_status, topic_previous, topic_priority, data)
                values (
                    ?,?,?,?,?,?,?,?)
                """.format(self.table_name),
        }


class SQLiteUserStore(UserStore):
    """
    UserStore using SQLite

    """
    def get_sqls(self):
        """
        Get SQLs used in UserStore

        Returns
        -------
        sqls : dict
            SQLs used in UserStore
        """
        return {
            "prepare_check": """
                select * from sqlite_master where type='table' and name='{0}'
                """.format(self.table_name),
            "prepare_create": """
                create table {0} (
                    channel TEXT, channel_user_id TEXT, user_id TEXT,
                    timestamp TIMESTAMP, name TEXT, nickname TEXT,
                    profile_image_url TEXT, data TEXT,
                    primary key(channel, channel_user_id))
                """.format(self.table_name),
            "get_user": """
                select
                    channel, channel_user_id, user_id,timestamp, name,
                    nickname, profile_image_url, data
                from {0}
                where
                    channel=? and channel_user_id=? limit 1
                """.format(self.table_name),
            "add_user": """
                insert into {0} (
                    channel, channel_user_id, user_id, timestamp, name,
                    nickname, profile_image_url, data)
                values (
                    ?,?,?,?,?,?,?,?)
                """.format(self.table_name),
            "save_user": """
                update {0}
                set
                    timestamp=?, name=?, nickname=?, profile_image_url=?,
                    data=?
                where
                    channel=? and channel_user_id=?
                """.format(self.table_name),
        }


class SQLiteMessageLogStore(MessageLogStore):
    """
    MessageLogStore using SQLite

    """
    def get_sqls(self):
        """
        Get SQLs used in MessageLogStore

        Returns
        -------
        sqls : dict
            SQLs used in MessageLogStore
        """
        return {
            "prepare_check": """
                select * from sqlite_master where type='table' and name='{0}'
                """.format(self.table_name),
            "prepare_create": """
                create table {0} (
                    id INTEGER PRIMARY KEY,
                    channel TEXT,
                    channel_detail TEXT,
                    channel_user_id TEXT,
                    request_timestamp TIMESTAMP,
                    request_id TEXT,
                    request_type TEXT,
                    request_text TEXT,
                    request_payloads TEXT,
                    request_intent TEXT,
                    request_is_adhoc BOOLEAN,
                    response_type TEXT,
                    response_text TEXT,
                    response_payloads TEXT,
                    response_milliseconds INT,
                    context_is_new BOOLEAN,
                    context_topic_name TEXT,
                    context_topic_status TEXT,
                    context_topic_is_new BOOLEAN,
                    context_topic_keep_on BOOLEAN,
                    context_topic_priority INTEGER,
                    context_error TEXT,
                    request_json TEXT,
                    response_json TEXT,
                    context_json TEXT)
                """.format(self.table_name),
            "write": """
                insert into {0} (
                    channel,
                    channel_detail,
                    channel_user_id,
                    request_timestamp,
                    request_id,
                    request_type,
                    request_text,
                    request_payloads,
                    request_intent,
                    request_is_adhoc,
                    response_type,
                    response_text,
                    response_payloads,
                    response_milliseconds,
                    context_is_new,
                    context_topic_name,
                    context_topic_status,
                    context_topic_is_new,
                    context_topic_keep_on,
                    context_topic_priority,
                    context_error,
                    request_json, response_json, context_json)
                values (
                    ?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                """.format(self.table_name),
        }


class SQLiteStores(StoreSet):
    """
    Set of data stores and connection provider using SQLite

    """
    connection_provider = SQLiteConnectionProvider
    context_store = SQLiteContextStore
    user_store = SQLiteUserStore
    messagelog_store = SQLiteMessageLogStore
