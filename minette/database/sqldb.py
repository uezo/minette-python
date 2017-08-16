""" Components depend on SQLDatabase """
import pyodbc
from minette.database import ConnectionProvider
from minette.session import SessionStore
from minette.user import UserRepository
from minette.dialog import MessageLogger
from minette.serializer import decode_json

class SQLDBConnectionProvider(ConnectionProvider):
    def __init__(self, connection_str="", host="", port=1433, database="minette", user="", password="", driver="ODBC Driver 13 for SQL Server"):
        """
        :param connection_str: Connection string
        :type connection_str: str
        :param host: Hostname
        :type host: str
        :param port: Port
        :type port: int
        :param database: Database
        :type database: str
        :param user: User name
        :type user: str
        :param password: Password
        :type password: str
        :param driver: ODBC Driver name
        :type driver: str
        """
        self.connection_str = connection_str if connection_str else self.get_connection_str(host, port, database, user, password, driver)

    def get_connection(self):
        """
        :return: Database connection
        :rtype: Connection, Cursor
        """
        return pyodbc.connect(self.connection_str)

    @staticmethod
    def get_connection_str(host="", port=1433, database="minette", user="", password="", driver="ODBC Driver 13 for SQL Server"):
        """
        :param host: Hostname
        :type host: str
        :param port: Port
        :type port: int
        :param database: Database
        :type database: str
        :param user: User name
        :type user: str
        :param password: Password
        :type password: str
        :param driver: ODBC Driver name
        :type driver: str
        :return: Connection string
        :rtype: str
        """
        return "DRIVER={{{5}}};SERVER={0};PORT={1};DATABASE={2};UID={3};PWD={4}".format(host, port, database, user, password, driver)

class SQLDBSessionStore(SessionStore):
    def get_sqls(self, table_name):
        """
        :param table_name: Session table
        :type table_name: str
        :return: Dictionary of SQL
        :rtype: dict
        """
        return {
            "prepare_check": "select id from dbo.sysobjects where id = object_id('{0}')".format(table_name),
            "prepare_create": "create table {0} (channel NVARCHAR(20), channel_user NVARCHAR(100), timestamp DATETIME2, mode NVARCHAR(100), dialog_status NVARCHAR(100), chat_context NVARCHAR(100), data NVARCHAR(4000), primary key(channel, channel_user))".format(table_name),
            "get_session": "select top 1 * from {0} where channel=? and channel_user=?".format(table_name),
            # "save_session": "replace into {0} (channel, channel_user, timestamp, mode, dialog_status, chat_context, data) values (?,?,?,?,?,?,?)".format(table_name),
            "save_session": """
                            merge into {0} as A
                            using (select ? as channel, ? as channel_user, ? as timestamp, ? as mode, ? as dialog_status, ? as chat_context, ? as data) as B
                            on (A.channel = B.channel and A.channel_user = B.channel_user)
                            when matched then
                            update set timestamp=B.timestamp, mode=B.mode, dialog_status=B.dialog_status, chat_context=B.chat_context, data=B.data
                            when not matched then 
                            insert (channel, channel_user, timestamp, mode, dialog_status, chat_context, data) values (B.channel, B.channel_user, B.timestamp, B.mode, B.dialog_status, B.chat_context, B.data);
                            """.format(table_name)
        }

    def map_record(self, row):
        """
        :param row: A row of record set
        :return: Record
        :rtype: dict
        """
        return {
            "timestamp": row[2],
            "mode": str(row[3]),
            "dialog_status": str(row[4]),
            "chat_context": str(row[5]),
            "data": decode_json(row[6])
        }

class SQLDBUserRepository(UserRepository):
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
            "prepare_check_user": "select id from dbo.sysobjects where id = object_id('{0}')".format(table_user),
            "prepare_create_user": "create table {0} (user_id NVARCHAR(100) primary key, timestamp DATETIME2, name NVARCHAR(100), nickname NVARCHAR(100), data NVARCHAR(4000))".format(table_user),
            "prepare_check_uidmap": "select id from dbo.sysobjects where id = object_id('{0}')".format(table_uidmap),
            "prepare_create_uidmap": "create table {0} (channel NVARCHAR(20), channel_user NVARCHAR(100), user_id NVARCHAR(100), timestamp DATETIME2, primary key(channel, channel_user))".format(table_uidmap),
            "get_user": "select top 1 * from {0} inner join {1} on ({0}.user_id = {1}.user_id) where {1}.channel=? and {1}.channel_user=?".format(table_user, table_uidmap),
            "add_user": "insert into {0} (user_id, timestamp, name, nickname, data) values (?,?,?,?,?)".format(table_user),
            "add_uidmap": "insert into {0} (channel, channel_user, user_id, timestamp) values (?,?,?,?)".format(table_uidmap),
            "save_user": "update {0} set timestamp=?, name=?, nickname=?, data=? where user_id=?".format(table_user),
        }

    def map_record(self, row):
        """
        :param row: A row of record set
        :return: Record
        :rtype: dict
        """
        return {
            "user_id": str(row[0]),
            "name": str(row[2]),
            "nickname": str(row[3]),
            "data": decode_json(row[4])
        }

class SQLDBMessageLogger(MessageLogger):
    def get_sqls(self, table_name):
        """
        :param table_name: Message log table
        :type table_name: str
        :return: Dictionary of SQL
        :rtype: dict
        """
        return {
            "prepare_check": "select id from dbo.sysobjects where id = object_id('{0}')".format(table_name),
            "prepare_create": "create table {0} (timestamp DATETIME2, unixtime INT, channel NVARCHAR(20), totaltick INT, user_id NVARCHAR(100), user_name NVARCHAR(100), message_type NVARCHAR(100), input_text NVARCHAR(4000), output_text NVARCHAR(4000))".format(table_name),
            "write": "insert into {0} (timestamp, unixtime, channel, totaltick, user_id, user_name, message_type, input_text, output_text) values (?,?,?,?,?,?,?,?,?)".format(table_name)
        }
