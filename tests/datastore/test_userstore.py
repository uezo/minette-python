import pytest
from datetime import datetime
from pytz import timezone

from minette import (
    SQLiteStores,
    Config
)

SQLDBStores = None
try:
    from minette.datastore.sqldbstores import SQLDBStores
except Exception:
    pass

AzureTableStores = None
try:
    from minette.datastore.azurestoragestores import AzureTableStores
except Exception:
    pass

MySQLStores = None
try:
    from minette.datastore.mysqlstores import MySQLStores
except Exception:
    pass

SQLAlchemyStores = None
SQLAlchemyUserStore = None
try:
    from minette.datastore.sqlalchemystores import (
        SQLAlchemyStores,
        SQLAlchemyUserStore
    )
except Exception:
    pass

from minette.utils import date_to_unixtime

now = datetime.now()
table_name = "user" + str(date_to_unixtime(now))
user_id = "user_id" + str(date_to_unixtime(now))
print("user_table: {}".format(table_name))
print("user_id: {}".format(user_id))

dbconfig = Config("config/test_config_datastores.ini")

datastore_params = [
    (
        SQLiteStores,
        "test.db",
    ),
    (
        SQLDBStores,
        dbconfig.get("sqldb_connection_str"),
    ),
    (
        AzureTableStores,
        dbconfig.get("table_connection_str"),
    ),
    (
        MySQLStores,
        dbconfig.get("mysql_connection_str"),
    ),
    (
        SQLAlchemyStores,
        dbconfig.get("sqlalchemy_sqlite_connection_str"),
    ),
    (
        SQLAlchemyStores,
        dbconfig.get("sqlalchemy_sqldb_connection_str"),
    ),
    (
        SQLAlchemyStores,
        dbconfig.get("sqlalchemy_mysql_connection_str"),
    ),
]


@pytest.mark.parametrize("datastore_class, connection_str", datastore_params)
def test_prepare(datastore_class, connection_str):
    if not datastore_class:
        pytest.skip("Unable to import DataStoreSet")
    if not connection_str:
        pytest.skip(
            "Connection string for {} is not provided"
            .format(datastore_class.connection_provider.__name__))

    us = datastore_class.user_store(
        table_name=table_name, timezone=timezone("Asia/Tokyo"))
    cp = datastore_class.connection_provider(connection_str)
    with cp.get_connection() as connection:
        prepare_params = cp.get_prepare_params()
        if SQLAlchemyUserStore and isinstance(us, SQLAlchemyUserStore):
            assert us.prepare_table(connection, prepare_params) is False
        else:
            assert us.prepare_table(connection, prepare_params) is True
        assert us.prepare_table(connection, prepare_params) is False


@pytest.mark.parametrize("datastore_class, connection_str", datastore_params)
def test_get(datastore_class, connection_str):
    if not datastore_class:
        pytest.skip("Unable to import DataStoreSet")
    if not connection_str:
        pytest.skip(
            "Connection string for {} is not provided"
            .format(datastore_class.connection_provider.__name__))

    us = datastore_class.user_store(
        table_name=table_name, timezone=timezone("Asia/Tokyo"))
    with datastore_class.connection_provider(connection_str).get_connection() as connection:
        user = us.get("TEST", user_id, connection)
        assert user.channel == "TEST"
        assert user.channel_user_id == user_id
        assert user.data == {}
        # get(without user_id)
        user_without_user_id = us.get("TEST", None, connection)
        assert user_without_user_id.channel == "TEST"
        assert user_without_user_id.channel_user_id == ""


@pytest.mark.parametrize("datastore_class, connection_str", datastore_params)
def test_get_error(datastore_class, connection_str):
    if not datastore_class:
        pytest.skip("Unable to import DataStoreSet")
    if not connection_str:
        pytest.skip(
            "Connection string for {} is not provided"
            .format(datastore_class.connection_provider.__name__))

    us = datastore_class.user_store(
        table_name=table_name, timezone=timezone("Asia/Tokyo"))
    us.sqls["get_user"] = ""
    with datastore_class.connection_provider(connection_str).get_connection() as connection:
        user = us.get("TEST", user_id, connection)
        assert user.channel == "TEST"
        assert user.channel_user_id == user_id
        assert user.data == {}
    # table doesn't exist
    us.table_name = "notexisttable"
    with datastore_class.connection_provider(connection_str).get_connection() as connection:
        user = us.get("TEST", user_id, connection)
        assert user.channel == "TEST"
        assert user.channel_user_id == user_id
        assert user.data == {}
    # invalid table name
    us.table_name = "_#_#_"
    with datastore_class.connection_provider(connection_str).get_connection() as connection:
        user = us.get("TEST", user_id, connection)
        assert user.channel == "TEST"
        assert user.channel_user_id == user_id
        assert user.data == {}


@pytest.mark.parametrize("datastore_class, connection_str", datastore_params)
def test_save(datastore_class, connection_str):
    if not datastore_class:
        pytest.skip("Unable to import DataStoreSet")
    if not connection_str:
        pytest.skip(
            "Connection string for {} is not provided"
            .format(datastore_class.connection_provider.__name__))

    us = datastore_class.user_store(
        table_name=table_name, timezone=timezone("Asia/Tokyo"))
    with datastore_class.connection_provider(connection_str).get_connection() as connection:
        # save
        user = us.get("TEST", user_id, connection)
        user.data["strvalue"] = "value1"
        user.data["intvalue"] = 2
        user.data["dtvalue"] = now
        user.data["dictvalue"] = {
            "k1": "v1",
            "k2": 2,
        }
        us.save(user, connection)

        # check
        user = us.get("TEST", user_id, connection)
        assert user.channel == "TEST"
        assert user.channel_user_id == user_id
        assert user.data == {
            "strvalue": "value1",
            "intvalue": 2,
            "dtvalue": now,
            "dictvalue": {
                "k1": "v1",
                "k2": 2,
            }
        }
