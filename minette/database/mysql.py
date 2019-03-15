""" Components depend on MySQL """
import MySQLdb
from MySQLdb.cursors import DictCursor
from minette.database import ConnectionProvider
from minette.user import UserRepository
from minette.session import SessionStore
from minette.message import MessageLogger


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
    def __init__(self, connection_str):
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
        return MySQLdb.connect(**self.connection_params)

    def prepare_table(self, check_sql, create_sql, query_params=tuple()):
        """
        Check and create table if not exist

        Parameters
        ----------
        check_sql : str
            SQL to check the table is existing
        create_sql : str
            SQL to create the table
        query_params : tuple, default tuple()
            Query parameters for checking table
        """
        super().prepare_table(check_sql, create_sql, (self.connection_params["db"],))


class MySQLSessionStore(SessionStore):
    """
    Session store to enable successive conversation for MySQL

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
            "prepare_check": "select * from information_schema.TABLES where TABLE_NAME='{0}' and TABLE_SCHEMA=%s".format(table_name),
            "prepare_create": "create table {0} (channel VARCHAR(20), channel_user_id VARCHAR(100), timestamp DATETIME, topic_name VARCHAR(100), topic_status VARCHAR(100), topic_previous VARCHAR(4000), topic_priority INT, data VARCHAR(4000), primary key(channel, channel_user_id))".format(table_name),
            "get_session": "select channel, channel_user_id, timestamp, topic_name, topic_status, topic_previous, topic_priority, data from {0} where channel=%s and channel_user_id=%s limit 1".format(table_name),
            "save_session": "replace into {0} (channel, channel_user_id, timestamp, topic_name, topic_status, topic_previous, topic_priority, data) values (%s,%s,%s,%s,%s,%s,%s,%s)".format(table_name),
        }


class MySQLUserRepository(UserRepository):
    """
    User repository for MySQL

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
            "prepare_check_user": "select * from information_schema.TABLES where TABLE_NAME='{0}' and TABLE_SCHEMA=%s".format(table_user),
            "prepare_create_user": "create table {0} (user_id VARCHAR(100) primary key, timestamp DATETIME, name VARCHAR(100), nickname VARCHAR(100), profile_image_url VARCHAR(500), data VARCHAR(4000))".format(table_user),
            "prepare_check_uidmap": "select * from information_schema.TABLES where TABLE_NAME='{0}' and TABLE_SCHEMA=%s".format(table_uidmap),
            "prepare_create_uidmap": "create table {0} (channel VARCHAR(20), channel_user_id VARCHAR(100), user_id VARCHAR(100), timestamp DATETIME, primary key(channel, channel_user_id))".format(table_uidmap),
            "get_user": "select {0}.user_id, {0}.timestamp, {0}.name, {0}.nickname, {0}.profile_image_url, {0}.data from {0} inner join {1} on ({0}.user_id = {1}.user_id) where {1}.channel=%s and {1}.channel_user_id=%s limit 1".format(table_user, table_uidmap),
            "add_user": "insert into {0} (user_id, timestamp, name, nickname, profile_image_url, data) values (%s,%s,%s,%s,%s,%s)".format(table_user),
            "add_uidmap": "insert into {0} (channel, channel_user_id, user_id, timestamp) values (%s,%s,%s,%s)".format(table_uidmap),
            "save_user": "update {0} set timestamp=%s, name=%s, nickname=%s, profile_image_url=%s, data=%s where user_id=%s".format(table_user),
        }


class MySQLMessageLogger(MessageLogger):
    """
    Message logger to analyze the communication for MySQL

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
            "prepare_check": "select * from information_schema.TABLES where TABLE_NAME='{0}' and TABLE_SCHEMA=%s".format(table_name),
            "prepare_create": "create table {0} (id INT PRIMARY KEY AUTO_INCREMENT, timestamp DATETIME, request_id VARCHAR(100), channel VARCHAR(20), channel_detail VARCHAR(100), channel_user_id VARCHAR(100), request_json JSON, response_json JSON, session_json JSON)".format(table_name),
            "write": "insert into {0} (timestamp, request_id, channel, channel_detail, channel_user_id, request_json, response_json, session_json) values (%s,%s,%s,%s,%s,%s,%s,%s)".format(table_name),
            "get_recent_log": "select timestamp, request_id, channel, channel_detail, channel_user_id, request_json, response_json, session_json from {0} where id <= %s order by id desc limit %s".format(table_name)
        }


def get_presets():
    """
    Get database components for MySQL

    Returns
    -------
    database_presets : (MySQLConnectionProvider, MySQLSessionStore, MySQLUserRepository, MySQLMessageLogger)
        Database presets
    """
    return MySQLConnectionProvider, MySQLSessionStore, MySQLUserRepository, MySQLMessageLogger
