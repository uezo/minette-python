""" Components depend on MySQL """
import MySQLdb
from MySQLdb.cursors import DictCursor
from minette.database import ConnectionProvider
from minette.user import UserRepository
from minette.session import SessionStore
from minette.dialog import MessageLogger

class MySQLConnectionProvider(ConnectionProvider):
    def __init__(self, connection_str=""):
        """
        :param connection_str: Connection string
        :type connection_str: str
        """
        self.connection_str = connection_str if connection_str else "host=localhost;user=root;passwd=;db=minette;charset=utf8;"
        self.connection_info = {"cursorclass": DictCursor, "charset": "utf8"}
        param_values = self.connection_str.split(";")
        for pv in param_values:
            if "=" in pv:
                p, v = list(map(str.strip, pv.split("=")))
                self.connection_info[p] = v

    def get_connection(self):
        """
        :return: Database connection
        :rtype: Connection, Cursor
        """
        return MySQLdb.connect(**self.connection_info)

    def prepare_table(self, check_sql, create_sql, query_params=tuple()):
        """
        :param check_sql: SQL to check the table is existing
        :type check_sql: str
        :param create_sql: SQL to create the table
        :type create_sql: str
        :param query_params: Query parameters for checking table
        :type query_params: tuple
        """
        super().prepare_table(check_sql, create_sql, (self.connection_info["db"],))

class MySQLSessionStore(SessionStore):
    def get_sqls(self, table_name):
        """
        :param table_name: Session table
        :type table_name: str
        :return: Dictionary of SQL
        :rtype: dict
        """
        return {
            "prepare_check": "select * from information_schema.TABLES where TABLE_NAME='{0}' and TABLE_SCHEMA=%s".format(table_name),
            "prepare_create": "create table {0} (channel VARCHAR(20), channel_user VARCHAR(100), timestamp DATETIME, mode VARCHAR(100), dialog_status VARCHAR(100), chat_context VARCHAR(100), data VARCHAR(4000), primary key(channel, channel_user))".format(table_name),
            "get_session": "select * from {0} where channel=%s and channel_user=%s limit 1".format(table_name),
            "save_session": "replace into {0} (channel, channel_user, timestamp, mode, dialog_status, chat_context, data) values (%s,%s,%s,%s,%s,%s,%s)".format(table_name),
        }

class MySQLUserRepository(UserRepository):
    def get_sqls(self, table_user, table_uidmap):
        """
        :param table_user: User table
        :type table_user: str
        :param table_uidmap: UserId-Channel mapping table
        :type table_uidmap: str
        :return: Dictionary of SQL
        :rtype: dict
        """
        return {
            "prepare_check_user": "select * from information_schema.TABLES where TABLE_NAME='{0}' and TABLE_SCHEMA=%s".format(table_user),
            "prepare_create_user": "create table {0} (user_id VARCHAR(100) primary key, timestamp DATETIME, name VARCHAR(100), nickname VARCHAR(100), data VARCHAR(4000))".format(table_user),
            "prepare_check_uidmap": "select * from information_schema.TABLES where TABLE_NAME='{0}' and TABLE_SCHEMA=%s".format(table_uidmap),
            "prepare_create_uidmap": "create table {0} (channel VARCHAR(20), channel_user VARCHAR(100), user_id VARCHAR(100), timestamp DATETIME, primary key(channel, channel_user))".format(table_uidmap),
            "get_user": "select * from {0} inner join {1} on ({0}.user_id = {1}.user_id) where {1}.channel=%s and {1}.channel_user=%s limit 1".format(table_user, table_uidmap),
            "add_user": "insert into {0} (user_id, timestamp, name, nickname, data) values (%s,%s,%s,%s,%s)".format(table_user),
            "add_uidmap": "insert into {0} (channel, channel_user, user_id, timestamp) values (%s,%s,%s,%s)".format(table_uidmap),
            "save_user": "update {0} set timestamp=%s, name=%s, nickname=%s, data=%s where user_id=%s".format(table_user),
        }

class MySQLMessageLogger(MessageLogger):
    def get_sqls(self, table_name):
        """
        :param table_name: Message log table
        :type table_name: str
        :return: Dictionary of SQL
        :rtype: dict
        """
        return {
            "prepare_check": "select * from information_schema.TABLES where TABLE_NAME='{0}' and TABLE_SCHEMA=%s".format(table_name),
            "prepare_create": "create table {0} (timestamp DATETIME, unixtime INT, channel VARCHAR(20), totaltick INT, user_id VARCHAR(100), user_name VARCHAR(100), message_type VARCHAR(100), input_text VARCHAR(4000), output_text VARCHAR(4000))".format(table_name),
            "write": "insert into {0} (timestamp, unixtime, channel, totaltick, user_id, user_name, message_type, input_text, output_text) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(table_name)
        }
