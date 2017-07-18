

import MySQLdb
from MySQLdb.cursors import DictCursor
from minette.database import ConnectionProvider

class MySQLConnectionProvider(ConnectionProvider):
    def __init__(self, connection_str):
        """
        :param connection_str: Connection string
        :type connection_str: str
        """
        self.connection_str = connection_str if connection_str else "host=localhost;user=root;passwd=;db=minette;charset=utf8;"
        self.connection_info = {"cursorclass": DictCursor, "charset": "utf8"}
        param_values = self.connection_str.split(";")
        for pv in param_values:
            if "=" in pv:
                p, v = list(map(str.strip, pv.split("=")))
                self.connection_info[p] = v

    def get_connection(self):
        """
        :return: Database connection
        :rtype: Connection, Cursor
        """
        return MySQLdb.connect(**self.connection_info)
