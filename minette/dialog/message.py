""" message datamodel and defalt message_logger using SQLite """
from datetime import datetime
from typing import List
import logging
import traceback
from configparser import ConfigParser
import sqlite3
from pytz import timezone
from minette.user.user_repository import User
from minette.taggers.tagger import WordNode
from minette.util import date_to_str, date_to_unixtime

class Payload:
    def __init__(self, content_type="image", url="", thumb="", headers=None, content=None):
        self.content_type = content_type
        self.url = url
        self.thumb = thumb if thumb != "" else url
        self.headers = headers if headers else {}
        self.content = content

class Message:
    def __init__(self, message_id="", message_type="message", timestamp=None, channel="", channel_user="", channel_message=None, token="", text="", words:List[WordNode]=None, payloads:List[Payload]=None, is_private=True, user:User=None):
        self.message_id = message_id
        self.type = message_type
        self.timestamp = timestamp if timestamp else datetime.now(timezone("UTC"))
        self.channel = channel
        self.channel_user = channel_user
        self.channel_message = channel_message
        self.token = token
        self.user = None
        self.text = text
        self.words = words if words else []
        self.payloads = payloads if payloads else []
        self.is_private = is_private

    def get_reply_message(self, text="", message_type="text", payloads:List[Payload]=None):
        import copy
        message = copy.copy(self)
        message.timestamp = datetime.now(message.timestamp.tzinfo)
        message.channel_message = None
        message.type = message_type
        message.text = text
        message.words = []
        message.payloads = payloads if payloads else []
        return message

class MessageLogger:
    def __init__(self, connection_str="minette.db", logger:logging.Logger=None, config:ConfigParser=None, tzone:timezone=None, prepare_database=True):
        self.connection_str = connection_str
        self.logger = logger if logger else logging.getLogger(__name__)
        self.config = config
        self.timezone = tzone
        if prepare_database:
            self.prepare_database(self.connection_str)

    def __get_connection(self):
        conn = sqlite3.connect(self.connection_str)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        return (conn, cur)

    def prepare_database(self, connection_str):
        self.logger.warn("DB preparation for MessageLogger is ON. Turn off if this bot is runnning in production environment.")
        try:
            self.connection_str = connection_str
            conn, cur = self.__get_connection()
            cur.execute("select * from sqlite_master where type='table' and name='messagelog'")
            if cur.fetchone() is None:
                cur.execute("create table messagelog(timestamp TEXT, unixtime INTEGER, channel TEXT, totaltick INTEGER, user_id TEXT, user_name TEXT, message_type TEXT, input_text TEXT, output_text TEXT)")
                conn.commit()
        finally:
            conn.close()

    def write(self, request:Message, output_text, total_ms):
        try:
            sql = "insert into messagelog (timestamp, unixtime, channel, totaltick, user_id, user_name, message_type, input_text, output_text) values (?,?,?,?,?,?,?,?,?)"
            conn, cur = self.__get_connection()
            now = datetime.now(self.timezone)
            cur.execute(sql, (date_to_str(now), date_to_unixtime(now), request.channel, total_ms, request.user.user_id, request.user.name, request.type, request.text, output_text))
            conn.commit()
        except Exception as ex:
            self.logger.error("Message log failed: " + str(ex) + "\n" + traceback.format_exc())
        finally:
            conn.close()
