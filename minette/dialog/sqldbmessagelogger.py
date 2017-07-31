""" MessageLogger using Azure SQL Database """
from minette.dialog import MessageLogger

class SQLDBMessageLogger(MessageLogger):
    def get_sqls(self, table_name):
        """
        :param table_name: Message log table
        :type table_name: str
        :return: Dictionary of SQL
        :rtype: dict
        """
        return {
            "prepare_check": "select id from dbo.sysobjects where id = object_id('{0}')".format(table_name),
            "prepare_create": "create table {0} (timestamp DATETIME2, unixtime INT, channel NVARCHAR(20), totaltick INT, user_id NVARCHAR(100), user_name NVARCHAR(100), message_type NVARCHAR(100), input_text NVARCHAR(4000), output_text NVARCHAR(4000))".format(table_name),
            "write": "insert into {0} (timestamp, unixtime, channel, totaltick, user_id, user_name, message_type, input_text, output_text) values (?,?,?,?,?,?,?,?,?)".format(table_name)
        }
