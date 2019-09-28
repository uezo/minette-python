import pyodbc

from .connectionprovider import ConnectionProvider
from .contextstore import ContextStore
from .userstore import UserStore
from .messagelogstore import MessageLogStore
from .storeset import StoreSet


class SQLDBConnectionProvider(ConnectionProvider):
    """
    Connection provider for Azure SQL Database

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
        return pyodbc.connect(self.connection_str)


class SQLDBContextStore(ContextStore):
    """
    Session store for Azure SQL Database to enable successive conversation

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
            "prepare_check": "select id from dbo.sysobjects where id = object_id('{0}')".format(self.table_name),
            "prepare_create": "create table {0} (channel NVARCHAR(20), channel_user_id NVARCHAR(100), timestamp DATETIME2, topic_name NVARCHAR(100), topic_status NVARCHAR(100), topic_previous NVARCHAR(4000), topic_priority INT, data NVARCHAR(MAX), primary key(channel, channel_user_id))".format(self.table_name),
            "get_context": "select top 1 * from {0} where channel=? and channel_user_id=?".format(self.table_name),
            "save_context": """
                            merge into {0} as A
                            using (select ? as channel, ? as channel_user_id, ? as timestamp, ? as topic_name, ? as topic_status, ? as topic_previous, ? as topic_priority, ? as data) as B
                            on (A.channel = B.channel and A.channel_user_id = B.channel_user_id)
                            when matched then
                            update set timestamp=B.timestamp, topic_name=B.topic_name, topic_status=B.topic_status, topic_previous=B.topic_previous, topic_priority=B.topic_priority, data=B.data
                            when not matched then
                            insert (channel, channel_user_id, timestamp, topic_name, topic_status, topic_previous, topic_priority, data) values (B.channel, B.channel_user_id, B.timestamp, B.topic_name, B.topic_status, B.topic_previous, B.topic_priority, B.data);
                            """.format(self.table_name)
        }


class SQLDBUserStore(UserStore):
    """
    User store for Azure SQL Database

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
            "prepare_check": "select id from dbo.sysobjects where id = object_id('{0}')".format(self.table_name),
            "prepare_create": "create table {0} (channel NVARCHAR(20), channel_user_id NVARCHAR(100), user_id NVARCHAR(100), timestamp DATETIME2, name NVARCHAR(100), nickname NVARCHAR(100), profile_image_url NVARCHAR(500), data NVARCHAR(MAX), primary key(channel, channel_user_id))".format(self.table_name),
            "get_user": "select top 1 channel, channel_user_id, user_id, timestamp, name, nickname, profile_image_url, data from {0} where channel=? and channel_user_id=?".format(self.table_name),
            "add_user": "insert into {0} (channel, channel_user_id, user_id, timestamp, name, nickname, profile_image_url, data) values (?,?,?,?,?,?,?,?)".format(self.table_name),
            "save_user": "update {0} set timestamp=?, name=?, nickname=?, profile_image_url=?, data=? where channel=? and channel_user_id=?".format(self.table_name),
        }


class SQLDBMessageLogStore(MessageLogStore):
    """
    Message log store for Azure SQL Database

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
            "prepare_check": "select id from dbo.sysobjects where id = object_id('{0}')".format(self.table_name),
            "prepare_create": """
                create table {0} (
                    id INT primary key identity,
                    channel NVARCHAR(20),
                    channel_detail NVARCHAR(100),
                    channel_user_id NVARCHAR(100),
                    request_timestamp DATETIME2,
                    request_id NVARCHAR(100),
                    request_type NVARCHAR(100),
                    request_text NVARCHAR(MAX),
                    request_payloads NVARCHAR(MAX),
                    request_intent NVARCHAR(100),
                    request_is_adhoc BIT,
                    response_type NVARCHAR(100),
                    response_text NVARCHAR(MAX),
                    response_payloads NVARCHAR(MAX),
                    response_milliseconds INT,
                    context_is_new BIT,
                    context_topic_name TEXT,
                    context_topic_status TEXT,
                    context_topic_is_new BIT,
                    context_topic_keep_on BIT,
                    context_topic_priority INT,
                    context_error NVARCHAR(MAX),
                    request_json NVARCHAR(MAX),
                    response_json NVARCHAR(MAX),
                    context_json NVARCHAR(MAX))
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


class SQLDBStores(StoreSet):
    connection_provider = SQLDBConnectionProvider
    context_store = SQLDBContextStore
    user_store = SQLDBUserStore
    messagelog_store = SQLDBMessageLogStore
