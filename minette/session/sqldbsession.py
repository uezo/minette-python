""" SessionStore using Azure SQL Database """
import MySQLdb
from minette.session import SessionStore
from minette.util import decode_json

class SQLDBSessionStore(SessionStore):
    def get_sqls(self, table_name):
        """
        :param table_name: Session table
        :type table_name: str
        :return: Dictionary of SQL
        :rtype: dict
        """
        return {
            "prepare_check": "select id from dbo.sysobjects where id = object_id('{0}')".format(table_name),
            "prepare_create": "create table {0} (channel NVARCHAR(20), channel_user NVARCHAR(100), timestamp DATETIME2, mode NVARCHAR(100), dialog_status NVARCHAR(100), chat_context NVARCHAR(100), data NVARCHAR(4000), primary key(channel, channel_user))".format(table_name),
            "get_session": "select top 1 * from {0} where channel=? and channel_user=?".format(table_name),
            # "save_session": "replace into {0} (channel, channel_user, timestamp, mode, dialog_status, chat_context, data) values (?,?,?,?,?,?,?)".format(table_name),
            "save_session": """
                            merge into {0} as A
                            using (select ? as channel, ? as channel_user, ? as timestamp, ? as mode, ? as dialog_status, ? as chat_context, ? as data) as B
                            on (A.channel = B.channel and A.channel_user = B.channel_user)
                            when matched then
                            update set timestamp=B.timestamp, mode=B.mode, dialog_status=B.dialog_status, chat_context=B.chat_context, data=B.data
                            when not matched then 
                            insert (channel, channel_user, timestamp, mode, dialog_status, chat_context, data) values (B.channel, B.channel_user, B.timestamp, B.mode, B.dialog_status, B.chat_context, B.data);
                            """.format(table_name)
        }

    def map_record(self, row):
        """
        :param row: A row of record set
        :return: Record
        :rtype: dict
        """
        return {
            "timestamp": row[2],
            "mode": str(row[3]),
            "dialog_status": str(row[4]),
            "chat_context": str(row[5]),
            "data": decode_json(row[6])
        }
