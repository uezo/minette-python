""" MessageLogger using MySQL """
from datetime import datetime
import logging
import traceback
import MySQLdb
from minette.databases.mysql import MySQLConnectionProvider
from minette.util import date_to_str, date_to_unixtime
from minette.dialog import MessageLogger

class MySQLMessageLogger(MessageLogger):
    def prepare_table(self, connection_provider):
        """
        :param connection_provider: MySQLConnectionProvider to create table if not existing
        :type connection_provider: MySQLConnectionProvider
        """
        self.logger.warn("DB preparation for MessageLogger is ON. Turn off if this bot is runnning in production environment.")
        connection = connection_provider.get_connection()
        cursor = connection.cursor()
        sql = "select * from information_schema.TABLES where TABLE_NAME='messagelog' and TABLE_SCHEMA=%s"
        cursor.execute(sql, (connection_provider.connection_info["db"],))
        if cursor.fetchone() is None:
            cursor.execute("create table messagelog(timestamp DATETIME, unixtime INT, channel VARCHAR(20), totaltick INT, user_id VARCHAR(100), user_name VARCHAR(100), message_type VARCHAR(100), input_text VARCHAR(4000), output_text VARCHAR(4000))")
            connection.commit()

    def write(self, request, output_text, total_ms, connection):
        """
        :param request: Request message
        :type request: Message
        :param output_text: Body of response message
        :type output_text: str
        :param total_ms: Response time (milliseconds)
        :type total_ms: int
        :param connection: Connection string or file path to access the database
        :type connection: Connection
        """
        now = datetime.now(self.timezone)
        cursor = connection.cursor()
        sql = "insert into messagelog (timestamp, unixtime, channel, totaltick, user_id, user_name, message_type, input_text, output_text) values (%s,%s,%s,%s,%s,%s,%s,%s,%s)"
        cursor.execute(sql, (date_to_str(now, True), date_to_unixtime(now), request.channel, total_ms, request.user.user_id, request.user.name, request.type, request.text, output_text))
        connection.commit()
