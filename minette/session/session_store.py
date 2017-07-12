""" session datamodel and defalt session_store using SQLite """
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
    def __init__(self, timeout=300, connection_str="minette.db", logger:logging.Logger=None):
        self.logger = logger
        self.timezone = None
        self.timeout = timeout
        self.connection_str = connection_str
        conn, cur = self.__get_connection()
        cur.execute("select * from sqlite_master where type='table' and name='session'")
        if cur.fetchone() is None:
            cur.execute("create table session(channel TEXT, channel_user TEXT, timestamp TEXT, mode TEXT, dialog_status TEXT, chat_context TEXT, data TEXT, primary key(channel, channel_user))")
            conn.commit()
        conn.close()

    def __get_connection(self):
        conn = sqlite3.connect(self.connection_str)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        return (conn, cur)

    def get_session(self, channel, channel_user) -> Session:
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

    def save_session(self, sess:Session):
        try:
            conn, cur = self.__get_connection()
            sql = "replace into session (channel, channel_user, timestamp, mode, dialog_status, chat_context, data) values (?,?,?,?,?,?,?)"
            cur.execute(sql, (sess.channel, sess.channel_user, date_to_str(sess.timestamp), sess.mode, sess.dialog_status, sess.chat_context, encode_json(sess.data)))
            conn.commit()
        finally:
            conn.close()