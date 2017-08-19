""" Session datamodel and defalt SessionStore using SQLite """
from datetime import datetime
import logging
import traceback
import sqlite3
from minette.util import date_to_str, str_to_date
from minette.serializer import JsonSerializable, encode_json, decode_json

class ModeStatus:
    Start = 1
    Continue = 2
    End = 3

class Session(JsonSerializable):
    def __init__(self, channel, channel_user):
        """
        :param channel: Channel
        :type channel: str
        :param channel_user: User ID of channel
        :type channel_user: str
        """
        self.channel = channel
        self.channel_user = channel_user
        self.timestamp = None
        self.is_new = True
        self.mode = ""
        self.mode_status = ModeStatus.Start
        self.keep_mode = False
        self.dialog_status = ""
        self.chat_context = ""
        self.data = {}

class SessionStore:
    def __init__(self, timeout=300, logger=None, config=None, tzone=None, connection_provider_for_prepare=None, table_name="session"):
        """
        :param timeout: Session timeout (seconds)
        :type timeout: int
        :param logger: Logger
        :type logger: logging.Logger
        :param config: Config
        :type config: Config
        :param tzone: Timezone
        :type tzone: timezone
        :param connection_provider_for_prepare: ConnectionProvider to create table if not existing
        :type connection_provider_for_prepare: ConnectionProvider
        :param table_name: Session table
        :type table_name: str
        """
        self.sqls = self.get_sqls(table_name)
        self.timeout = timeout if timeout else 300
        self.logger = logger if logger else logging.getLogger(__name__)
        self.config = config
        self.timezone = tzone
        if connection_provider_for_prepare:
            self.logger.warn("DB preparation for SessionStore is ON. Turn off if this bot is runnning in production environment.")
            connection_provider_for_prepare.prepare_table(self.sqls["prepare_check"], self.sqls["prepare_create"])

    def get_sqls(self, table_name):
        """
        :param table_name: Session table
        :type table_name: str
        :return: Dictionary of SQL
        :rtype: dict
        """
        return {
            "prepare_check": "select * from sqlite_master where type='table' and name='{0}'".format(table_name),
            "prepare_create": "create table {0} (channel TEXT, channel_user TEXT, timestamp TEXT, mode TEXT, dialog_status TEXT, chat_context TEXT, data TEXT, primary key(channel, channel_user))".format(table_name),
            "get_session": "select * from {0} where channel=? and channel_user=? limit 1".format(table_name),
            "save_session": "replace into {0} (channel, channel_user, timestamp, mode, dialog_status, chat_context, data) values (?,?,?,?,?,?,?)".format(table_name),
        }

    def map_record(self, row):
        """
        :param row: A row of record set
        :type row: sqlite3.Row
        :return: Record
        :rtype: dict
        """
        return {
            "timestamp": str_to_date(str(row["timestamp"])),
            "mode": str(row["mode"]),
            "dialog_status": str(row["dialog_status"]),
            "chat_context": str(row["chat_context"]),
            "data": decode_json(row["data"])
        }

    def get_session(self, channel, channel_user, connection):
        """
        :param channel: Channel
        :type channel: str
        :param channel_user: User ID of channel
        :type channel_user: str
        :param connection: Connection
        :type connection: Connection
        :return: Session
        :rtype: Session
        """
        sess = Session(channel, channel_user)
        sess.timestamp = datetime.now(self.timezone)
        try:
            cursor = connection.cursor()
            cursor.execute(self.sqls["get_session"], (channel, channel_user))
            row = cursor.fetchone()
            if row is not None:
                record = self.map_record(row)
                last_access = record["timestamp"]
                last_access = self.timezone.localize(last_access)
                if (datetime.now(self.timezone) - last_access).total_seconds() <= self.timeout:
                    sess.mode = record["mode"]
                    sess.dialog_status = record["dialog_status"]
                    sess.chat_context = record["chat_context"]
                    sess.data = record["data"] if record["data"] else {}
                    sess.is_new = False
                    sess.mode_status = ModeStatus.Continue if sess.mode != "" else ModeStatus.Start
        except Exception as ex:
            self.logger.error("Error occured in restoring session from database: " + str(ex) + "\n" + traceback.format_exc())
        return sess

    def save_session(self, session, connection):
        """
        :param session: Session
        :type session: Session
        :param connection: Connection
        :type connection: Connection
        """
        if session.data:
            session_dict = session.to_dict()
            serialized_data = encode_json(session_dict["data"])
        else:
            serialized_data = None
        cursor = connection.cursor()
        cursor.execute(self.sqls["save_session"], (session.channel, session.channel_user, date_to_str(session.timestamp), session.mode, session.dialog_status, session.chat_context, serialized_data))
        connection.commit()
