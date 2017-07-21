""" SessionStore using MySQL """
from minette.session import SessionStore

class MySQLSessionStore(SessionStore):
    def get_sqls(self, table_name):
        """
        :param table_name: Session table
        :type table_name: str
        :return: Dictionary of SQL
        :rtype: dict
        """
        return {
            "prepare_check": "select * from information_schema.TABLES where TABLE_NAME='{0}' and TABLE_SCHEMA=%s".format(table_name),
            "prepare_create": "create table {0} (channel VARCHAR(20), channel_user VARCHAR(100), timestamp DATETIME, mode VARCHAR(100), dialog_status VARCHAR(100), chat_context VARCHAR(100), data VARCHAR(4000), primary key(channel, channel_user))".format(table_name),
            "get_session": "select * from {0} where channel=%s and channel_user=%s limit 1".format(table_name),
            "save_session": "replace into {0} (channel, channel_user, timestamp, mode, dialog_status, chat_context, data) values (%s,%s,%s,%s,%s,%s,%s)".format(table_name),
        }
