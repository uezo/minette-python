""" Connection provider using Azure SQL Database """
import pyodbc
from minette.database import ConnectionProvider

class SQLDBConnectionProvider(ConnectionProvider):
    def __init__(self, connection_str="", host="", port=1433, database="minette", user="", password="", driver="ODBC Driver 13 for SQL Server"):
        """
        :param connection_str: Connection string
        :type connection_str: str
        :param host: Hostname
        :type host: str
        :param port: Port
        :type port: int
        :param database: Database
        :type database: str
        :param user: User name
        :type user: str
        :param password: Password
        :type password: str
        :param driver: ODBC Driver name
        :type driver: str
        """
        self.connection_str = connection_str if connection_str else self.get_connection_str(host, port, database, user, password, driver)

    def get_connection(self):
        """
        :return: Database connection
        :rtype: Connection, Cursor
        """
        return pyodbc.connect(self.connection_str)

    @staticmethod
    def get_connection_str(host="", port=1433, database="minette", user="", password="", driver="ODBC Driver 13 for SQL Server"):
        """
        :param host: Hostname
        :type host: str
        :param port: Port
        :type port: int
        :param database: Database
        :type database: str
        :param user: User name
        :type user: str
        :param password: Password
        :type password: str
        :param driver: ODBC Driver name
        :type driver: str
        :return: Connection string
        :rtype: str
        """
        return "DRIVER={{{5}}};SERVER={0};PORT={1};DATABASE={2};UID={3};PWD={4}".format(host, port, database, user, password, driver)
