""" Session datamodel and defalt SessionStore using SQLite """
from datetime import datetime
import logging
import traceback
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
    def __init__(self, timeout=300, logger=None, config=None, tzone=None, connection_provider_for_prepare=None):
        """
        :param timeout: Session timeout (seconds)
        :type timeout: int
        :param logger: Logger
        :type logger: logging.Logger
        :param config: ConfigParser
        :type config: ConfigParser
        :param tzone: Timezone
        :type tzone: timezone
        :param connection_provider_for_prepare: ConnectionProvider to create table if not existing
        :type connection_provider_for_prepare: ConnectionProvider
        """
        self.timeout = timeout if timeout else 300
        self.logger = logger if logger else logging.getLogger(__name__)
        self.config = config
        self.timezone = tzone
        if connection_provider_for_prepare:
            self.prepare_table(connection_provider_for_prepare)

    def prepare_table(self, connection_provider):
        """
        :param connection_provider: ConnectionProvider to create table if not existing
        :type connection_provider: ConnectionProvider
        """
        self.logger.warn("DB preparation for SessionStore is ON. Turn off if this bot is runnning in production environment.")
        connection = connection_provider.get_connection()
        cursor = connection.cursor()
        cursor.execute("select * from sqlite_master where type='table' and name='session'")
        if cursor.fetchone() is None:
            cursor.execute("create table session(channel TEXT, channel_user TEXT, timestamp TEXT, mode TEXT, dialog_status TEXT, chat_context TEXT, data TEXT, primary key(channel, channel_user))")
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
            sql = "select * from session where channel=? and channel_user=? limit 1"
            cursor.execute(sql, (channel, channel_user))
            row = cursor.fetchone()
            if row is not None:
                last_access = str_to_date(str(row["timestamp"]))
                if (datetime.now(self.timezone) - last_access).total_seconds() <= self.timeout:
                    sess.mode = str(row["mode"])
                    sess.dialog_status = str(row["dialog_status"])
                    sess.chat_context = str(row["chat_context"])
                    sess.data = decode_json(row["data"])
                    sess.is_new = False
                    sess.mode_status = ModeStatus.Continue if sess.mode != "" else ModeStatus.Start
        except Exception as ex:
            self.logger.error("Error occured in restoring session from Sqlite: " + str(ex) + "\n" + traceback.format_exc())
        return sess

    def save_session(self, session, connection):
        """
        :param session: Session
        :type session: Session
        :param connection: Connection
        :type connection: Connection
        """
        cursor = connection.cursor()
        sql = "replace into session (channel, channel_user, timestamp, mode, dialog_status, chat_context, data) values (?,?,?,?,?,?,?)"
        cursor.execute(sql, (session.channel, session.channel_user, date_to_str(session.timestamp), session.mode, session.dialog_status, session.chat_context, encode_json(session.data)))
        connection.commit()
