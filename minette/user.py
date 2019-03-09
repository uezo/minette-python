""" user datamodel and defalt user_repository using SQLite """
from logging import Logger, getLogger
import traceback
from datetime import datetime
from sqlite3 import Row
from uuid import uuid4
from minette.util import date_to_str
from minette.serializer import JsonSerializable, encode_json, decode_json


class User(JsonSerializable):
    """
    User

    Attributes
    ----------
    id : str
        User ID
    name : str
        User name
    nickname : str
        Nickname
    channel : str
        Channel
    channel_user_id : str
        Channel user ID
    data : dict
        User data
    """
    def __init__(self, channel, channel_user_id):
        """
        Parameters
        ----------
        channel : str
            Channel
        channel_user_id : str
            Channel user ID
        """
        self.id = str(uuid4())
        self.name = ""
        self.nickname = ""
        self.channel = channel
        self.channel_user_id = channel_user_id if isinstance(channel_user_id, str) else ""
        self.profile_image_url = ""
        self.data = {}


class UserRepository:
    """
    User repository

    Attributes
    ----------
    sqls : dict
        SQLs used in UserRepository
    logger : Logger
        Logger
    config : Config
        Configuration
    timezone : timezone
        Timezone
    """
    def __init__(self, logger=None, config=None, timezone=None,
                 connection_provider_for_prepare=None,
                 table_user="user", table_uidmap="uidmap"):
        """
        Parameters
        ----------
        logger : Logger, default None
            Logger
        config : Config, default None
            Configuration
        timezone : timezone, default None
            Timezone
        connection_provider_for_prepare : ConnectionProvider, default None
            Connection provider for preparing table if not exist
        table_user : str, default "user"
            Table name for user
        table_uidmap : str, default "uidmap"
            Table name for channel_user_id and user_id mapping
        """
        self.sqls = self.get_sqls(table_user, table_uidmap)
        self.logger = logger if logger else getLogger(__name__)
        self.config = config
        self.timezone = timezone
        if connection_provider_for_prepare:
            connection_provider_for_prepare.prepare_table(self.sqls["prepare_check_user"], self.sqls["prepare_create_user"])
            connection_provider_for_prepare.prepare_table(self.sqls["prepare_check_uidmap"], self.sqls["prepare_create_uidmap"])

    def get_sqls(self, table_user, table_uidmap):
        """
        Get SQLs used in UserRepository

        Parameters
        ----------
        table_user : str
            Table name for user
        table_uidmap : str
            Table name for channel_user_id and user_id mapping

        Returns
        -------
        sqls : dict
            SQLs used in UserRepository
        """
        return {
            "prepare_check_user": "select * from sqlite_master where type='table' and name='{0}'".format(table_user),
            "prepare_create_user": "create table {0} (user_id TEXT primary key, timestamp TEXT, name TEXT, nickname TEXT, profile_image_url TEXT, data TEXT)".format(table_user),
            "prepare_check_uidmap": "select * from sqlite_master where type='table' and name='{0}'".format(table_uidmap),
            "prepare_create_uidmap": "create table {0} (channel TEXT, channel_user_id TEXT, user_id TEXT, timestamp TEXT, primary key(channel, channel_user_id))".format(table_uidmap),
            "get_user": "select {0}.user_id, {0}.timestamp, {0}.name, {0}.nickname, {0}.profile_image_url, {0}.data from {0} inner join {1} on ({0}.user_id = {1}.user_id) where {1}.channel=? and {1}.channel_user_id=? limit 1".format(table_user, table_uidmap),
            "add_user": "insert into {0} (user_id, timestamp, name, nickname, profile_image_url, data) values (?,?,?,?,?,?)".format(table_user),
            "add_uidmap": "insert into {0} (channel, channel_user_id, user_id, timestamp) values (?,?,?,?)".format(table_uidmap),
            "save_user": "update {0} set timestamp=?, name=?, nickname=?, profile_image_url=?, data=? where user_id=?".format(table_user),
        }

    def map_record(self, row):
        """
        Map database record to dictionary

        Parameters
        ----------
        row : Row
            A row of record set

        Returns
        -------
        mapped_record : dict
            Record as dict
        """
        return {
            "user_id": str(row["user_id"]),
            "name": str(row["name"]),
            "nickname": str(row["nickname"]),
            "profile_image_url": str(row["profile_image_url"]),
            "data": decode_json(row["data"])
        }

    def get_user(self, channel, channel_user_id, connection):
        """
        Get user from repository by channel and channel_user_id

        Parameters
        ----------
        channel : str
            Channel
        channel_user_id : str
            Channel user ID
        connection : Connection
            Connection

        Returns
        -------
        user : User
            User
        """
        user = User(channel=channel, channel_user_id=channel_user_id)
        if not channel_user_id:
            return user
        try:
            cursor = connection.cursor()
            cursor.execute(self.sqls["get_user"], (channel, channel_user_id))
            row = cursor.fetchone()
            if row is not None:
                record = self.map_record(row)
                user.id = record["user_id"]
                user.name = record["name"]
                user.nickname = record["nickname"]
                user.profile_image_url = record["profile_image_url"]
                user.data = record["data"] if record["data"] else {}
            else:
                now = date_to_str(datetime.now(self.timezone))
                cursor.execute(self.sqls["add_user"], (user.id, now, user.name, user.nickname, user.profile_image_url, None))
                cursor.execute(self.sqls["add_uidmap"], (channel, channel_user_id, user.id, now))
                connection.commit()
        except Exception as ex:
            self.logger.error("Error occured in restoring user from database: " + str(ex) + "\n" + traceback.format_exc())
        return user

    def save_user(self, user, connection):
        """
        Save user

        Parameters
        ----------
        user : User
            User to save
        connection : Connection
            Connection
        """
        user_dict = user.to_dict()
        serialized_data = encode_json(user_dict["data"])
        cursor = connection.cursor()
        cursor.execute(self.sqls["save_user"], (date_to_str(datetime.now(self.timezone)), user.name, user.nickname, user.profile_image_url, serialized_data, user.id))
        connection.commit()
