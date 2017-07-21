""" UserRepository using MySQL """
from minette.user import UserRepository

class MySQLUserRepository(UserRepository):
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
            "prepare_check_user": "select * from information_schema.TABLES where TABLE_NAME='{0}' and TABLE_SCHEMA=%s".format(table_user),
            "prepare_create_user": "create table {0} (user_id VARCHAR(100) primary key, timestamp DATETIME, name VARCHAR(100), nickname VARCHAR(100), data VARCHAR(4000))".format(table_user),
            "prepare_check_uidmap": "select * from information_schema.TABLES where TABLE_NAME='{0}' and TABLE_SCHEMA=%s".format(table_uidmap),
            "prepare_create_uidmap": "create table {0} (channel VARCHAR(20), channel_user VARCHAR(100), user_id VARCHAR(100), timestamp DATETIME, primary key(channel, channel_user))".format(table_uidmap),
            "get_user": "select * from {0} inner join {1} on ({0}.user_id = {1}.user_id) where {1}.channel=%s and {1}.channel_user=%s limit 1".format(table_user, table_uidmap),
            "add_user": "insert into {0} (user_id, timestamp, name, nickname, data) values (%s,%s,%s,%s,%s)".format(table_user),
            "add_uidmap": "insert into {0} (channel, channel_user, user_id, timestamp) values (%s,%s,%s,%s)".format(table_uidmap),
            "save_user": "update {0} set timestamp=%s, name=%s, nickname=%s, data=%s where user_id=%s".format(table_user),
        }
