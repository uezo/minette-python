""" Connection provider using SQLite """
import sqlite3

class ConnectionProvider:
    def __init__(self, connection_str=""):
        """
        :param connection_str: Connection string
        :type connection_str: str
        """
        self.connection_str = connection_str if connection_str else "./minette.db"

    def get_connection(self):
        """
        :return: Database connection
        :rtype: (Connection, Cursor)
        """
        connection = sqlite3.connect(self.connection_str)
        connection.row_factory = sqlite3.Row
        return connection

    def prepare_table(self, check_sql, create_sql, query_params=tuple()):
        """
        :param check_sql: SQL to check the table is existing
        :type check_sql: str
        :param create_sql: SQL to create the table
        :type create_sql: str
        :param query_params: Query parameters for checking table
        :type query_params: tuple
        """
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute(check_sql, query_params)
            if cursor.fetchone() is None:
                cursor.execute(create_sql)
                connection.commit()
        finally:
            connection.close()
