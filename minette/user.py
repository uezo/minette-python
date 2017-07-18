""" user datamodel and defalt user_repository using SQLite """
from datetime import datetime
import traceback
import uuid
from minette.util import encode_json, decode_json, date_to_str

class User:
    def __init__(self, channel, channel_user, channel_user_data=None, repository=None, connection=None):
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
        self.__connection = connection

    def save(self):
        """ Save this user using UserRepository """
        if self.__repository:
            self.__repository.save_user(self, self.__connection)

class UserRepository:
    def __init__(self, logger=None, config=None, tzone=None, connection_provider_for_prepare=None):
        """
        :param logger: Logger
        :type logger: logging.Logger
        :param config: ConfigParser
        :type config: ConfigParser
        :param tzone: Timezone
        :type tzone: timezone
        :param connection_provider_for_prepare: ConnectionProvider to create table if not existing
        :type connection_provider_for_prepare: ConnectionProvider
        """
        self.logger = logger
        self.config = config
        self.timezone = tzone
        if connection_provider_for_prepare:
            self.prepare_table(connection_provider_for_prepare)

    def prepare_table(self, connection_provider):
        """
        :param connection_provider: ConnectionProvider to create table if not existing
        :type connection_provider: ConnectionProvider
        """
        self.logger.warn("DB preparation for UserRepository is ON. Turn off if this bot is runnning in production environment.")
        connection = connection_provider.get_connection()
        cursor = connection.cursor()
        cursor.execute("select * from sqlite_master where type='table' and name='user'")
        if cursor.fetchone() is None:
            cursor.execute("create table user(user_id TEXT primary key, timestamp TEXT, name TEXT, nickname TEXT, data TEXT)")
            connection.commit()
        cursor.execute("select * from sqlite_master where type='table' and name='user_id_mapper'")
        if cursor.fetchone() is None:
            cursor.execute("create table user_id_mapper(channel TEXT, channel_user TEXT, user_id TEXT, timestamp TEXT, primary key(channel, channel_user))")
            connection.commit()

    def get_user(self, channel, channel_user, connection):
        """
        :param channel: Channel
        :type channel: str
        :param channel_user: User ID of channel
        :type channel_user: str
        :param connection: Connection
        :type connection: Connection
        :return: User
        :rtype: User
        """
        user = User(channel=channel, channel_user=channel_user, repository=self, connection=connection)
        try:
            cursor = connection.cursor()
            sql = "select * from user inner join user_id_mapper on (user.user_id = user_id_mapper.user_id) where user_id_mapper.channel=? and user_id_mapper.channel_user=? limit 1"
            cursor.execute(sql, (channel, channel_user))
            row = cursor.fetchone()
            if row is not None:
                user.user_id = str(row["user_id"])
                user.name = str(row["name"])
                user.nickname = str(row["nickname"])
                user.data = decode_json(row["data"])
            else:
                now = date_to_str(datetime.now(self.timezone))
                sql_user = "insert into user (user_id, timestamp, name, nickname, data) values (?,?,?,?,?)"
                sql_uid = "insert into user_id_mapper (channel, channel_user, user_id, timestamp) values (?,?,?,?)"
                cursor.execute(sql_user, (user.user_id, now, user.name, user.nickname, None))
                cursor.execute(sql_uid, (channel, channel_user, user.user_id, now))
                connection.commit()
        except Exception as ex:
            self.logger.error("Error occured in restoring user from Sqlite: " + str(ex) + "\n" + traceback.format_exc())
        return user

    def save_user(self, user, connection):
        """
        :param user: User
        :type user: User
        :param connection: Connection
        :type connection: Connection
        """
        cursor = connection.cursor()
        sql = "update user set timestamp=?, name=?, nickname=?, data=? where user_id=?"
        cursor.execute(sql, (date_to_str(datetime.now(self.timezone)), user.name, user.nickname, encode_json(user.data), user.user_id))
        connection.commit()
