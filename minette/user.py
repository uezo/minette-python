""" user datamodel and defalt user_repository using SQLite """
from datetime import datetime
import traceback
import uuid
import sqlite3
from minette.util import encode_json, decode_json, date_to_str

class User:
    def __init__(self, channel, channel_user, channel_user_data=None, repository=None):
        """
        :param channel: Channel
        :type channel: str
        :param channel_user: User ID of channel
        :type channel_user: str
        :param channel_user_data: User information from channel
        :param repository: UserRepository
        :type repository: UserRepository
        """
        self.user_id = str(uuid.uuid4())
        self.name = ""
        self.nickname = ""
        self.channel = channel
        self.channel_user = channel_user
        self.channel_user_data = channel_user_data
        self.data = None
        self.__repository = repository

    def save(self):
        """ Save this user using UserRepository """
        if self.__repository:
            self.__repository.save_user(self)

class UserRepository:
    def __init__(self, connection_str="", logger=None, config=None, tzone=None, prepare_database=True):
        """
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
        self.connection_str = connection_str if connection_str else "./minette.db"
        self.logger = logger
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
        self.logger.warn("DB preparation for UserRepository is ON. Turn off if this bot is runnning in production environment.")
        try:
            self.connection_str = connection_str
            conn, cur = self.__get_connection()
            cur.execute("select * from sqlite_master where type='table' and name='user'")
            if cur.fetchone() is None:
                cur.execute("create table user(user_id TEXT primary key, timestamp TEXT, name TEXT, nickname TEXT, data TEXT)")
                conn.commit()
            cur.execute("select * from sqlite_master where type='table' and name='user_id_mapper'")
            if cur.fetchone() is None:
                cur.execute("create table user_id_mapper(channel TEXT, channel_user TEXT, user_id TEXT, timestamp TEXT, primary key(channel, channel_user))")
                conn.commit()
        finally:
            conn.close()

    def get_user(self, channel, channel_user):
        """
        :param channel: Channel
        :type channel: str
        :param channel_user: User ID of channel
        :type channel_user: str
        :return: User
        :rtype: User
        """
        user = User(channel=channel, channel_user=channel_user, repository=self)
        try:
            conn, cur = self.__get_connection()
            sql = "select * from user inner join user_id_mapper on (user.user_id = user_id_mapper.user_id) where user_id_mapper.channel=? and user_id_mapper.channel_user=? limit 1"
            cur.execute(sql, (channel, channel_user))
            row = cur.fetchone()
        finally:
            conn.close()
        if row is not None:
            try:
                user.user_id = str(row["user_id"])
                user.name = str(row["name"])
                user.nickname = str(row["nickname"])
                user.data = decode_json(row["data"])
            except Exception as ex:
                self.logger.error("Error occured in restoring user from Sqlite: " + str(ex) + "\n" + traceback.format_exc())
        else:
            self.add_user(user, channel, channel_user)
        return user

    def add_user(self, user, channel, channel_user):
        """
        :param user: User
        :type user: User
        :param channel: Channel
        :type channel: str
        :param channel_user: User ID of channel
        :type channel_user: str
        """
        now = date_to_str(datetime.now(self.timezone))
        try:
            conn, cur = self.__get_connection()
            sql_user = "insert into user (user_id, timestamp, name, nickname, data) values (?,?,?,?,?)"
            sql_uid = "insert into user_id_mapper (channel, channel_user, user_id, timestamp) values (?,?,?,?)"
            cur.execute(sql_user, (user.user_id, now, user.name, user.nickname, None))
            cur.execute(sql_uid, (channel, channel_user, user.user_id, now))
            conn.commit()
        finally:
            conn.close()

    def save_user(self, user):
        """
        :param user: User
        :type user: User
        """
        try:
            conn, cur = self.__get_connection()
            sql = "update user set timestamp=?, name=?, nickname=?, data=? where user_id=?"
            cur.execute(sql, (date_to_str(datetime.now(self.timezone)), user.name, user.nickname, encode_json(user.data), user.user_id))
            conn.commit()
            conn.close()
        finally:
            conn.close()
