""" Components depend on SQLDatabase """
import pyodbc
from pyodbc import Row
from minette.database import ConnectionProvider
from minette.session import SessionStore
from minette.user import UserRepository
from minette.message import MessageLogger
from minette.serializer import decode_json, encode_json
from minette.util import str_to_date


class SQLDBConnectionProvider(ConnectionProvider):
    """
    Connection provider for SQL Database

    Attributes
    ----------
    connection_str : str
        Connection string
    """
    def __init__(self, connection_str=None, host=None, port=1433,
                 database="minette", user=None, password=None,
                 driver="ODBC Driver 13 for SQL Server"):
        """
        Parameters
        ----------
        connection_str : str, default None
            Connection string
        host : str, default None
            Host name or IP address of server
        port : int, default 1433
            Port number of database server
        database : str, default "minette"
            Database name
        user : str, default None
            User for database
        password : str, default None
            Password for database
        driver : str, default "ODBC Driver 13 for SQL Server"
            ODBC driver name
        """
        self.connection_str = connection_str if connection_str else self.get_connection_str(host, port, database, user, password, driver)

    def get_connection(self):
        """
        Get connection

        Returns
        -------
        connection : Connection
            Database connection
        """
        return pyodbc.connect(self.connection_str)

    @staticmethod
    def get_connection_str(host, port, database, user, password, driver):
        """
        Get connection string

        Parameters
        ----------
        host : str
            Host name or IP address of server
        port : int
            Port number of database server
        database : str
            Database name
        user : str
            User for database
        password : str
            Password for database
        driver : str
            ODBC driver name

        Returns
        -------
        connection_str : str
            Connection string
        """
        return "DRIVER={{{5}}};SERVER={0};PORT={1};DATABASE={2};UID={3};PWD={4}".format(host, port, database, user, password, driver)


class SQLDBSessionStore(SessionStore):
    """
    Session store to enable successive conversation for SQL Database

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
            "prepare_check": "select id from dbo.sysobjects where id = object_id('{0}')".format(table_name),
            "prepare_create": "create table {0} (channel NVARCHAR(20), channel_user_id NVARCHAR(100), timestamp DATETIME2, topic_name NVARCHAR(100), topic_status NVARCHAR(100), topic_previous NVARCHAR(4000), topic_priority INT, data NVARCHAR(MAX), primary key(channel, channel_user_id))".format(table_name),
            "get_session": "select top 1 * from {0} where channel=? and channel_user_id=?".format(table_name),
            "save_session": """
                            merge into {0} as A
                            using (select ? as channel, ? as channel_user_id, ? as timestamp, ? as topic_name, ? as topic_status, ? as topic_previous, ? as topic_priority, ? as data) as B
                            on (A.channel = B.channel and A.channel_user_id = B.channel_user_id)
                            when matched then
                            update set timestamp=B.timestamp, topic_name=B.topic_name, topic_status=B.topic_status, topic_previous=B.topic_previous, topic_priority=B.topic_priority, data=B.data
                            when not matched then 
                            insert (channel, channel_user_id, timestamp, topic_name, topic_status, topic_previous, topic_priority, data) values (B.channel, B.channel_user_id, B.timestamp, B.topic_name, B.topic_status, B.topic_previous, B.topic_priority, B.data);
                            """.format(table_name)
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
            "channel": str(row[0]),
            "channel_user_id": str(row[1]),
            "timestamp": row[2],
            "topic_name": str(row[3]),
            "topic_status": str(row[4]),
            "topic_previous": decode_json(str(row[5])),
            "topic_priority": int(row[6]),
            "data": decode_json(row[7])
        }


class SQLDBUserRepository(UserRepository):
    """
    User repository for SQL Database

    Attributes
    ----------
    sqls : dict
        SQLs used in UserRepository
    logger : Logger
        Logger
    config : Config
        Configuration
    timezone : timezone
        Timezone
    """
    def get_sqls(self, table_user, table_uidmap):
        """
        Get SQLs used in UserRepository

        Parameters
        ----------
        table_user : str
            Table name for user
        table_uidmap : str
            Table name for channel_user_id and user_id mapping

        Returns
        -------
        sqls : dict
            SQLs used in UserRepository
        """
        return {
            "prepare_check_user": "select id from dbo.sysobjects where id = object_id('{0}')".format(table_user),
            "prepare_create_user": "create table {0} (user_id NVARCHAR(100) primary key, timestamp DATETIME2, name NVARCHAR(100), nickname NVARCHAR(100), profile_image_url NVARCHAR(500), data NVARCHAR(4000))".format(table_user),
            "prepare_check_uidmap": "select id from dbo.sysobjects where id = object_id('{0}')".format(table_uidmap),
            "prepare_create_uidmap": "create table {0} (channel NVARCHAR(20), channel_user_id NVARCHAR(100), user_id NVARCHAR(100), timestamp DATETIME2, primary key(channel, channel_user_id))".format(table_uidmap),
            "get_user": "select top 1 {0}.user_id, {0}.timestamp, {0}.name, {0}.nickname, {0}.profile_image_url, {0}.data from {0} inner join {1} on ({0}.user_id = {1}.user_id) where {1}.channel=? and {1}.channel_user_id=?".format(table_user, table_uidmap),
            "add_user": "insert into {0} (user_id, timestamp, name, nickname, profile_image_url, data) values (?,?,?,?,?,?)".format(table_user),
            "add_uidmap": "insert into {0} (channel, channel_user_id, user_id, timestamp) values (?,?,?,?)".format(table_uidmap),
            "save_user": "update {0} set timestamp=?, name=?, nickname=?, profile_image_url=?, data=? where user_id=?".format(table_user),
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
            "user_id": str(row[0]),
            "name": str(row[2]),
            "nickname": str(row[3]),
            "profile_image_url": str(row[4]),
            "data": decode_json(row[5])
        }


class SQLDBMessageLogger(MessageLogger):
    """
    Message logger to analyze the communication for SQL Database

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
            "prepare_check": "select id from dbo.sysobjects where id = object_id('{0}')".format(table_name),
            "prepare_create": "create table {0} (timestamp DATETIME2, channel NVARCHAR(20), channel_detail NVARCHAR(100), channel_user_id NVARCHAR(100), totaltick INT, user_id NVARCHAR(100), user_name NVARCHAR(100), message_type NVARCHAR(100), topic_name NVARCHAR(100), topic_status NVARCHAR(100), topic_is_new NVARCHAR(10), topic_keep_on NVARCHAR(10), topic_priority INT, is_adhoc NVARCHAR(10), input_text NVARCHAR(4000), intent NVARCHAR(100), intent_priority INT, entities NVARCHAR(4000), output_text NVARCHAR(4000), error_info NVARCHAR(4000))".format(table_name),
            "write": "insert into {0} (timestamp, channel, channel_detail, channel_user_id, totaltick, user_id, user_name, message_type, topic_name, topic_status, topic_is_new, topic_keep_on, topic_priority, is_adhoc, input_text, intent, intent_priority, entities, output_text, error_info) values (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)".format(table_name),
            "get_recent_log": "select timestamp, channel, channel_detail, channel_user_id, totaltick, user_id, user_name, message_type, topic_name, topic_status, topic_is_new, topic_keep_on, topic_priority, is_adhoc, input_text, intent, intent_priority, entities, output_text, error_info from {0} where timestamp > ? order by timestamp desc".format(table_name)
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
            "timestamp": str_to_date(row[0]),
            "channel": str(row[1]),
            "channel_detail": str(row[2]),
            "channel_user_id": str(row[3]),
            "totaltick": row[4],
            "user_id": str(row[5]),
            "user_name": str(row[6]),
            "message_type": str(row[7]),
            "topic_name": str(row[8]),
            "topic_status": str(row[9]),
            "topic_is_new": row[10],
            "topic_keep_on": row[11],
            "topic_priority": row[12],
            "is_adhoc": row[13],
            "input_text": str(row[14]),
            "intent": str(row[15]),
            "intent_priority": str(row[16]),
            "entities": encode_json(str(row[17])),
            "output_text": str(row[18]),
            "error_info": encode_json(str(row[19])),
        }


def get_presets():
    """
    Get database components for SQL Database

    Returns
    -------
    database_presets : (SQLDBConnectionProvider, SQLDBSessionStore, SQLDBUserRepository, SQLDBMessageLogger)
        Database presets
    """
    return SQLDBConnectionProvider, SQLDBSessionStore, SQLDBUserRepository, SQLDBMessageLogger
