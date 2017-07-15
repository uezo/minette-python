""" Session datamodel and defalt SessionStore using SQLite """
from datetime import datetime
import logging
import traceback
import sqlite3
from minette.util import encode_json, decode_json, date_to_str, str_to_date

class ModeStatus:
    Start = 1
    Continue = 2
    End = 3

class Session:
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
        self.dialog_service = None
        self.data = None

class SessionStore:
    def __init__(self, timeout=300, connection_str="minette.db", logger=None, config=None, tzone=None, prepare_database=True):
        """
        :param timeout: Session timeout (seconds)
        :type timeout: int
        :param connection_str: Connection string or file path to access the database
        :type connection_str: str
        :param logger: Logger
        :type logger: logging.Logger
        :param config: ConfigParser
        :type config: ConfigParser
        :param tzone: Timezone
        :type tzone: timezone
        :param prepare_database: Check and create table if not existing
        :type prepare_database: bool
        """
        self.timeout = timeout
        self.connection_str = connection_str
        self.logger = logger if logger else logging.getLogger(__name__)
        self.config = config
        self.timezone = tzone
        if prepare_database:
            self.prepare_database(self.connection_str)

    def __get_connection(self):
        """
        :return: Database connection
        :rtype: (Connection, cur)
        """
        conn = sqlite3.connect(self.connection_str)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        return (conn, cur)

    def prepare_database(self, connection_str):
        """
        :param connection_str: Connection string or file path to access the database
        :type connection_str: str
        """
        self.logger.warn("DB preparation for SessionStore is ON. Turn off if this bot is runnning in production environment.")
        try:
            self.connection_str = connection_str
            conn, cur = self.__get_connection()
            cur.execute("select * from sqlite_master where type='table' and name='session'")
            if cur.fetchone() is None:
                cur.execute("create table session(channel TEXT, channel_user TEXT, timestamp TEXT, mode TEXT, dialog_status TEXT, chat_context TEXT, data TEXT, primary key(channel, channel_user))")
                conn.commit()
        finally:
            conn.close()

    def get_session(self, channel, channel_user):
        """
        :param channel: Channel
        :type channel: str
        :param channel_user: User ID of channel
        :type channel_user: str
        :return: Session
        :rtype: Session
        """
        sess = Session(channel, channel_user)
        sess.timestamp = datetime.now(self.timezone)
        try:
            sql = "select * from session where channel=? and channel_user=? limit 1"
            conn, cur = self.__get_connection()
            cur.execute(sql, (channel, channel_user))
            row = cur.fetchone()
        finally:
            conn.close()
        if row is not None:
            try:
                last_access = str_to_date(str(row["timestamp"]))
                if (datetime.now(self.timezone) - last_access).total_seconds() <= self.timeout:
                    sess.mode = str(row["mode"])
                    sess.dialog_status = str(row["dialog_status"])
                    sess.chat_context = str(row["chat_context"])
                    sess.data = decode_json(row["data"])
                    sess.is_new = False
                    sess.mode_status = ModeStatus.Continue if sess.mode != "" else ModeStatus.Start
                    return sess
            except Exception as ex:
                self.logger.error("Error occured in restoring session from Sqlite: " + str(ex) + "\n" + traceback.format_exc())
        return sess

    def save_session(self, session):
        """
        :param session: Session
        :type session: Session
        """
        try:
            conn, cur = self.__get_connection()
            sql = "replace into session (channel, channel_user, timestamp, mode, dialog_status, chat_context, data) values (?,?,?,?,?,?,?)"
            cur.execute(sql, (session.channel, session.channel_user, date_to_str(session.timestamp), session.mode, session.dialog_status, session.chat_context, encode_json(session.data)))
            conn.commit()
        finally:
            conn.close()
