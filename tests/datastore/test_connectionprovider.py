import pytest
import sqlite3
import pyodbc


from minette import SQLiteConnectionProvider, Config
from minette.datastore.sqldbstores import SQLDBConnectionProvider
from minette.datastore.azurestoragestores import (
    AzureTableConnection,
    AzureTableConnectionProvider
)
from minette.datastore.mysqlstores import (
    MySQLConnection,
    MySQLConnectionProvider
)
from minette.datastore.sqlalchemystores import (
    SQLAlchemyConnection,
    SQLAlchemyConnectionProvider
)

dbconfig = Config("config/test_config_datastores.ini")

datastore_params = [
    (sqlite3.Connection, SQLiteConnectionProvider, "test.db"),
    (pyodbc.Connection, SQLDBConnectionProvider, dbconfig.get("sqldb_connection_str")),
    (AzureTableConnection, AzureTableConnectionProvider, dbconfig.get("table_connection_str")),
    (MySQLConnection, MySQLConnectionProvider, dbconfig.get("mysql_connection_str")),
    (SQLAlchemyConnection, SQLAlchemyConnectionProvider, dbconfig.get("sqlalchemy_sqlite_connection_str")),
    (SQLAlchemyConnection, SQLAlchemyConnectionProvider, dbconfig.get("sqlalchemy_sqldb_connection_str")),
    (SQLAlchemyConnection, SQLAlchemyConnectionProvider, dbconfig.get("sqlalchemy_mysql_connection_str")),
]


@pytest.mark.parametrize("connection_class,connection_provider_class,connection_str", datastore_params)
def test_get_connection(connection_class, connection_provider_class, connection_str):
    cp = connection_provider_class(connection_str)
    with cp.get_connection() as connection:
        connection = cp.get_connection()
        assert isinstance(connection, connection_class)
