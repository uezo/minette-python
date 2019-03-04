""" Connection provider using SQLite """
import sqlite3


class ConnectionProvider:
    """
    Connection provider for SQLite

    Attributes
    ----------
    connection_str : str
        Connection string
    """
    def __init__(self, connection_str):
        """
        Parameters
        ----------
        connection_str : str
            Connection string
        """
        self.connection_str = connection_str

    def get_connection(self):
        """
        Get connection

        Returns
        -------
        connection : Connection
            Database connection
        """
        connection = sqlite3.connect(self.connection_str)
        connection.row_factory = sqlite3.Row
        return connection

    def prepare_table(self, check_sql, create_sql, query_params=tuple()):
        """
        Check and create table if not exist

        Parameters
        ----------
        check_sql : str
            SQL to check the table is existing
        create_sql : str
            SQL to create the table
        query_params : tuple, default tuple()
            Query parameters for checking table
        """
        try:
            connection = self.get_connection()
            cursor = connection.cursor()
            cursor.execute(check_sql, query_params)
            if not cursor.fetchone():
                cursor.execute(create_sql)
                connection.commit()
        finally:
            connection.close()
