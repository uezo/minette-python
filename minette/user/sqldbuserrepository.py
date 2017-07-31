""" UserRepository using Azure SQL Database """
import pyodbc
from minette.user import UserRepository
from minette.util import decode_json

class SQLDBUserRepository(UserRepository):
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
            "prepare_check_user": "select id from dbo.sysobjects where id = object_id('{0}')".format(table_user),
            "prepare_create_user": "create table {0} (user_id NVARCHAR(100) primary key, timestamp DATETIME2, name NVARCHAR(100), nickname NVARCHAR(100), data NVARCHAR(4000))".format(table_user),
            "prepare_check_uidmap": "select id from dbo.sysobjects where id = object_id('{0}')".format(table_uidmap),
            "prepare_create_uidmap": "create table {0} (channel NVARCHAR(20), channel_user NVARCHAR(100), user_id NVARCHAR(100), timestamp DATETIME2, primary key(channel, channel_user))".format(table_uidmap),
            "get_user": "select top 1 * from {0} inner join {1} on ({0}.user_id = {1}.user_id) where {1}.channel=? and {1}.channel_user=?".format(table_user, table_uidmap),
            "add_user": "insert into {0} (user_id, timestamp, name, nickname, data) values (?,?,?,?,?)".format(table_user),
            "add_uidmap": "insert into {0} (channel, channel_user, user_id, timestamp) values (?,?,?,?)".format(table_uidmap),
            "save_user": "update {0} set timestamp=?, name=?, nickname=?, data=? where user_id=?".format(table_user),
        }

    def map_record(self, row):
        """
        :param row: A row of record set
        :return: Record
        :rtype: dict
        """
        return {
            "user_id": str(row[0]),
            "name": str(row[2]),
            "nickname": str(row[3]),
            "data": decode_json(row[4])
        }
