import pytest
import sqlite3

# SQLite
from minette import (
    SQLiteConnectionProvider,
    Config
)

# SQLDatabase
SQLDBConnection = None
SQLDBConnectionProvider = None
try:
    import pyodbc
    SQLDBConnection = pyodbc.Connection
    from minette.datastore.sqldbstores import SQLDBConnectionProvider
except Exception:
    pass

# AzureTableStorage
AzureTableConnection = None
AzureTableConnectionProvider = None
try:
    from minette.datastore.azurestoragestores import (
        AzureTableConnection,
        AzureTableConnectionProvider
    )
except Exception:
    pass

# MySQL
MySQLConnection = None
MySQLConnectionProvider = None
try:
    from minette.datastore.mysqlstores import (
        MySQLConnection,
        MySQLConnectionProvider
    )
except Exception:
    pass

# SQLAlchemy
SQLAlchemyConnection = None
SQLAlchemyConnectionProvider = None
try:
    from minette.datastore.sqlalchemystores import (
        SQLAlchemyConnection,
        SQLAlchemyConnectionProvider
    )
except Exception:
    pass

dbconfig = Config("config/test_config_datastores.ini")

datastore_params = [
    (sqlite3.Connection, SQLiteConnectionProvider, "test.db"),
    (SQLDBConnection, SQLDBConnectionProvider, dbconfig.get("sqldb_connection_str")),
    (AzureTableConnection, AzureTableConnectionProvider, dbconfig.get("table_connection_str")),
    (MySQLConnection, MySQLConnectionProvider, dbconfig.get("mysql_connection_str")),
    (SQLAlchemyConnection, SQLAlchemyConnectionProvider, dbconfig.get("sqlalchemy_sqlite_connection_str")),
    (SQLAlchemyConnection, SQLAlchemyConnectionProvider, dbconfig.get("sqlalchemy_sqldb_connection_str")),
    (SQLAlchemyConnection, SQLAlchemyConnectionProvider, dbconfig.get("sqlalchemy_mysql_connection_str")),
]


@pytest.mark.parametrize("connection_class, connection_provider_class, connection_str", datastore_params)
def test_get_connection(connection_class, connection_provider_class, connection_str):
    if not connection_class or not connection_provider_class:
        pytest.skip("Dependencies are not found")
    if not connection_str:
        pytest.skip(
            "Connection string for {} is not provided"
            .format(connection_provider_class.__name__))

    cp = connection_provider_class(connection_str)
    with cp.get_connection() as connection:
        connection = cp.get_connection()
        assert isinstance(connection, connection_class)
