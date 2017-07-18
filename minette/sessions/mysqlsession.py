""" SessionStore using MySQL """
from datetime import datetime
import logging
import traceback
import MySQLdb
from minette.databases.mysql import MySQLConnectionProvider
from minette.session import Session, SessionStore, ModeStatus
from minette.util import encode_json, decode_json, date_to_str

class MySQLSessionStore(SessionStore):
    def prepare_table(self, connection_provider):
        """
        :param connection_provider: MySQLConnectionProvider to create table if not existing
        :type connection_provider: MySQLConnectionProvider
        """
        self.logger.warn("DB preparation for SessionStore is ON. Turn off if this bot is runnning in production environment.")
        connection = connection_provider.get_connection()
        cursor = connection.cursor()
        sql = "select * from information_schema.TABLES where TABLE_NAME='session' and TABLE_SCHEMA=%s"
        cursor.execute(sql, (connection_provider.connection_info["db"],))
        if cursor.fetchone() is None:
            cursor.execute("create table session(channel VARCHAR(20), channel_user VARCHAR(100), timestamp DATETIME, mode VARCHAR(100), dialog_status VARCHAR(100), chat_context VARCHAR(100), data VARCHAR(4000), primary key(channel, channel_user))")
            connection.commit()

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
            sql = "select * from session where channel=%s and channel_user=%s limit 1"
            cursor.execute(sql, (channel, channel_user))
            row = cursor.fetchone()
            if row is not None:
                last_access = row["timestamp"]
                last_access = last_access.replace(tzinfo=self.timezone)
                if (datetime.now(self.timezone) - last_access).total_seconds() <= self.timeout:
                    sess.mode = str(row["mode"])
                    sess.dialog_status = str(row["dialog_status"])
                    sess.chat_context = str(row["chat_context"])
                    sess.data = decode_json(row["data"])
                    sess.is_new = False
                    sess.mode_status = ModeStatus.Continue if sess.mode != "" else ModeStatus.Start
        except Exception as ex:
            self.logger.error("Error occured in restoring session from MySQL: " + str(ex) + "\n" + traceback.format_exc())
        return sess

    def save_session(self, session, connection):
        """
        :param session: Session
        :type session: Session
        :param connection: Connection
        :type connection: Connection
        """
        cursor = connection.cursor()
        sql = "replace into session (channel, channel_user, timestamp, mode, dialog_status, chat_context, data) values (%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(sql, (session.channel, session.channel_user, date_to_str(session.timestamp, True), session.mode, session.dialog_status, session.chat_context, encode_json(session.data)))
        connection.commit()
