""" Connection provider """
import sqlite3

class ConnectionProvider:
    def __init__(self, connection_str):
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
