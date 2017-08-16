""" user datamodel and defalt user_repository using SQLite """
from datetime import datetime
import traceback
import uuid
from minette.util import date_to_str
from minette.serializer import JsonSerializable, encode_json, decode_json

class User(JsonSerializable):
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
        self.data = {}
        self.__repository = repository
        self.__connection = connection

    def save(self):
        """ Save this user using UserRepository """
        if self.__repository:
            self.__repository.save_user(self, self.__connection)

class UserRepository:
    def __init__(self, logger=None, config=None, tzone=None, connection_provider_for_prepare=None, table_user="user", table_uidmap="user_id_mapper"):
        """
        :param logger: Logger
        :type logger: logging.Logger
        :param config: Config
        :type config: Config
        :param tzone: Timezone
        :type tzone: timezone
        :param connection_provider_for_prepare: ConnectionProvider to create table if not existing
        :type connection_provider_for_prepare: ConnectionProvider
        :param table_user: User table
        :type table_user: str
        :param table_uidmap: User-Channel mapping table
        :type table_uidmap: str
        """
        self.sqls = self.get_sqls(table_user, table_uidmap)
        self.logger = logger
        self.config = config
        self.timezone = tzone
        if connection_provider_for_prepare:
            self.logger.warn("DB preparation for UserRepository is ON. Turn off if this bot is runnning in production environment.")
            connection_provider_for_prepare.prepare_table(self.sqls["prepare_check_user"], self.sqls["prepare_create_user"])
            connection_provider_for_prepare.prepare_table(self.sqls["prepare_check_uidmap"], self.sqls["prepare_create_uidmap"])

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
            "prepare_check_user": "select * from sqlite_master where type='table' and name='{0}'".format(table_user),
            "prepare_create_user": "create table {0} (user_id TEXT primary key, timestamp TEXT, name TEXT, nickname TEXT, data TEXT)".format(table_user),
            "prepare_check_uidmap": "select * from sqlite_master where type='table' and name='{0}'".format(table_uidmap),
            "prepare_create_uidmap": "create table {0} (channel TEXT, channel_user TEXT, user_id TEXT, timestamp TEXT, primary key(channel, channel_user))".format(table_uidmap),
            "get_user": "select * from {0} inner join {1} on ({0}.user_id = {1}.user_id) where {1}.channel=? and {1}.channel_user=? limit 1".format(table_user, table_uidmap),
            "add_user": "insert into {0} (user_id, timestamp, name, nickname, data) values (?,?,?,?,?)".format(table_user),
            "add_uidmap": "insert into {0} (channel, channel_user, user_id, timestamp) values (?,?,?,?)".format(table_uidmap),
            "save_user": "update {0} set timestamp=?, name=?, nickname=?, data=? where user_id=?".format(table_user),
        }

    def map_record(self, row):
        """
        :param row: A row of record set
        :type row: sqlite3.Row
        :return: Record
        :rtype: dict
        """
        return {
            "user_id": str(row["user_id"]),
            "name": str(row["name"]),
            "nickname": str(row["nickname"]),
            "data": decode_json(row["data"])
        }

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
            cursor.execute(self.sqls["get_user"], (channel, channel_user))
            row = cursor.fetchone()
            if row is not None:
                record = self.map_record(row)
                user.user_id = record["user_id"]
                user.name = record["name"]
                user.nickname = record["nickname"]
                user.data = record["data"] if record["data"] else {}
            else:
                now = date_to_str(datetime.now(self.timezone))
                cursor.execute(self.sqls["add_user"], (user.user_id, now, user.name, user.nickname, None))
                cursor.execute(self.sqls["add_uidmap"], (channel, channel_user, user.user_id, now))
                connection.commit()
        except Exception as ex:
            self.logger.error("Error occured in restoring user from database: " + str(ex) + "\n" + traceback.format_exc())
        return user

    def save_user(self, user, connection):
        """
        :param user: User
        :type user: User
        :param connection: Connection
        :type connection: Connection
        """
        user_dict = user.to_dict()
        serialized_data = encode_json(user_dict["data"])
        cursor = connection.cursor()
        cursor.execute(self.sqls["save_user"], (date_to_str(datetime.now(self.timezone)), user.name, user.nickname, serialized_data, user.user_id))
        connection.commit()
