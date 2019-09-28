import MySQLdb
from MySQLdb.cursors import DictCursor
from MySQLdb.connections import Connection

from .connectionprovider import ConnectionProvider
from .contextstore import ContextStore
from .userstore import UserStore
from .messagelogstore import MessageLogStore
from .storeset import StoreSet


class MySQLConnection(Connection):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class MySQLConnectionProvider(ConnectionProvider):
    """
    Connection provider for MySQL

    Attributes
    ----------
    connection_str : str
        Connection string
    connection_params : dict
        Parameters for connection
    """
    def __init__(self, connection_str, **kwargs):
        """
        Parameters
        ----------
        connection_str : str
            Connection string
        """
        self.connection_str = connection_str
        self.connection_params = {"cursorclass": DictCursor, "charset": "utf8"}
        param_values = self.connection_str.split(";")
        for pv in param_values:
            if "=" in pv:
                p, v = list(map(str.strip, pv.split("=")))
                self.connection_params[p] = v

    def get_connection(self):
        """
        Get connection

        Returns
        -------
        connection : Connection
            Database connection
        """
        return MySQLConnection(**self.connection_params)

    def get_prepare_params(self):
        """
        Get parameters for preparing tables

        Returns
        -------
        prepare_params : tuple or None
            Parameters for preparing tables
        """
        return (self.connection_params["db"], )


class MySQLContextStore(ContextStore):
    def get_sqls(self):
        """
        Get SQLs used in ContextStore

        Returns
        -------
        sqls : dict
            SQLs used in SessionStore
        """
        return {
            "prepare_check": "select * from information_schema.TABLES where TABLE_NAME='{0}' and TABLE_SCHEMA=%s".format(self.table_name),
            "prepare_create": "create table {0} (channel VARCHAR(20), channel_user_id VARCHAR(100), timestamp DATETIME, topic_name VARCHAR(100), topic_status VARCHAR(100), topic_previous VARCHAR(500), topic_priority INT, data JSON, primary key(channel, channel_user_id))".format(self.table_name),
            "get_context": "select channel, channel_user_id, timestamp, topic_name, topic_status, topic_previous, topic_priority, data from {0} where channel=%s and channel_user_id=%s limit 1".format(self.table_name),
            "save_context": "replace into {0} (channel, channel_user_id, timestamp, topic_name, topic_status, topic_previous, topic_priority, data) values (%s,%s,%s,%s,%s,%s,%s,%s)".format(self.table_name),
        }


class MySQLUserStore(UserStore):
    def get_sqls(self):
        """
        Get SQLs used in UserStore

        Returns
        -------
        sqls : dict
            SQLs used in UserRepository
        """
        return {
            "prepare_check": "select * from information_schema.TABLES where TABLE_NAME='{0}' and TABLE_SCHEMA=%s".format(self.table_name),
            "prepare_create": "create table {0} (channel VARCHAR(20), channel_user_id VARCHAR(100), user_id VARCHAR(100), timestamp DATETIME, name VARCHAR(100), nickname VARCHAR(100), profile_image_url VARCHAR(500), data JSON, primary key(channel, channel_user_id))".format(self.table_name),
            "get_user": "select channel, channel_user_id, user_id, timestamp, name, nickname, profile_image_url, data from {0} where channel=%s and channel_user_id=%s limit 1".format(self.table_name),
            "add_user": "insert into {0} (channel, channel_user_id, user_id, timestamp, name, nickname, profile_image_url, data) values (%s,%s,%s,%s,%s,%s,%s,%s)".format(self.table_name),
            "save_user": "update {0} set timestamp=%s, name=%s, nickname=%s, profile_image_url=%s, data=%s where channel=%s and channel_user_id=%s".format(self.table_name),
        }


class MySQLMessageLogStore(MessageLogStore):
    def get_sqls(self):
        """
        Get SQLs used in MessageLogStore

        Returns
        -------
        sqls : dict
            SQLs used in MessageLogger
        """
        return {
            "prepare_check": "select * from information_schema.TABLES where TABLE_NAME='{0}' and TABLE_SCHEMA=%s".format(self.table_name),
            "prepare_create": """
                create table {0} (
                    id INT PRIMARY KEY AUTO_INCREMENT,
                    channel VARCHAR(20),
                    channel_detail VARCHAR(100),
                    channel_user_id VARCHAR(100),
                    request_timestamp DATETIME,
                    request_id VARCHAR(100),
                    request_type VARCHAR(100),
                    request_text VARCHAR(4000),
                    request_payloads JSON,
                    request_intent VARCHAR(100),
                    request_is_adhoc BOOLEAN,
                    response_type VARCHAR(100),
                    response_text VARCHAR(4000),
                    response_payloads JSON,
                    response_milliseconds INT,
                    context_is_new BOOLEAN,
                    context_topic_name TEXT,
                    context_topic_status TEXT,
                    context_topic_is_new BOOLEAN,
                    context_topic_keep_on BOOLEAN,
                    context_topic_priority INT,
                    context_error JSON,
                    request_json JSON,
                    response_json JSON,
                    context_json JSON)
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
                    %s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s,%s)
                """.format(self.table_name),
        }


class MySQLStores(StoreSet):
    connection_provider = MySQLConnectionProvider
    context_store = MySQLContextStore
    user_store = MySQLUserStore
    messagelog_store = MySQLMessageLogStore
