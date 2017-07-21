""" MessageLogger using MySQL """
from minette.dialog import MessageLogger

class MySQLMessageLogger(MessageLogger):
    def get_sqls(self, table_name):
        """
        :param table_name: Message log table
        :type table_name: str
        :return: Dictionary of SQL
        :rtype: dict
        """
        return {
            "prepare_check": "select * from information_schema.TABLES where TABLE_NAME='{0}' and TABLE_SCHEMA=%s".format(table_name),
            "prepare_create": "create table {0} (timestamp DATETIME, unixtime INT, channel VARCHAR(20), totaltick INT, user_id VARCHAR(100), user_name VARCHAR(100), message_type VARCHAR(100), input_text VARCHAR(4000), output_text VARCHAR(4000))".format(table_name),
            "write": "insert into {0} (timestamp, unixtime, channel, totaltick, user_id, user_name, message_type, input_text, output_text) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)".format(table_name)
        }
