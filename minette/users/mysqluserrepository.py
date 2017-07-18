""" UserRepository using MySQL """
from datetime import datetime
import traceback
import uuid
import MySQLdb
from minette.databases.mysql import MySQLConnectionProvider
from minette.util import encode_json, decode_json, date_to_str
from minette.user import User, UserRepository

class MySQLUserRepository(UserRepository):
    def prepare_table(self, connection_provider):
        """
        :param connection_provider: MySQLConnectionProvider to create table if not existing
        :type connection_provider: MySQLConnectionProvider
        """
        self.logger.warn("DB preparation for UserRepository is ON. Turn off if this bot is runnning in production environment.")
        connection = connection_provider.get_connection()
        cursor = connection.cursor()
        sql = "select * from information_schema.TABLES where TABLE_NAME='user' and TABLE_SCHEMA=%s"
        cursor.execute(sql, (connection_provider.connection_info["db"],))
        if cursor.fetchone() is None:
            cursor.execute("create table user(user_id VARCHAR(100) primary key, timestamp DATETIME, name VARCHAR(100), nickname VARCHAR(100), data VARCHAR(4000))")
            connection.commit()
        sql = "select * from information_schema.TABLES where TABLE_NAME='user_id_mapper' and TABLE_SCHEMA=%s"
        cursor.execute(sql, (connection_provider.connection_info["db"],))
        if cursor.fetchone() is None:
            cursor.execute("create table user_id_mapper(channel VARCHAR(20), channel_user VARCHAR(100), user_id VARCHAR(100), timestamp DATETIME, primary key(channel, channel_user))")
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
            sql = "select * from user inner join user_id_mapper on (user.user_id = user_id_mapper.user_id) where user_id_mapper.channel=%s and user_id_mapper.channel_user=%s limit 1"
            cursor.execute(sql, (channel, channel_user))
            row = cursor.fetchone()
            if row is not None:
                user.user_id = str(row["user_id"])
                user.name = str(row["name"])
                user.nickname = str(row["nickname"])
                user.data = decode_json(row["data"])
            else:
                now = date_to_str(datetime.now(self.timezone), True)
                sql_user = "insert into user (user_id, timestamp, name, nickname, data) values (%s,%s,%s,%s,%s)"
                sql_uid = "insert into user_id_mapper (channel, channel_user, user_id, timestamp) values (%s,%s,%s,%s)"
                cursor.execute(sql_user, (user.user_id, now, user.name, user.nickname, None))
                cursor.execute(sql_uid, (channel, channel_user, user.user_id, now))
                connection.commit()
        except Exception as ex:
            self.logger.error("Error occured in restoring user from MySQL: " + str(ex) + "\n" + traceback.format_exc())
        return user

    def save_user(self, user, connection):
        """
        :param user: User
        :type user: User
        :param connection: Connection
        :type connection: Connection
        """
        cursor = connection.cursor()
        sql = "update user set timestamp=%s, name=%s, nickname=%s, data=%s where user_id=%s"
        cursor.execute(sql, (date_to_str(datetime.now(self.timezone), True), user.name, user.nickname, encode_json(user.data), user.user_id))
        connection.commit()
