import pytest
from datetime import datetime
from pytz import timezone

from minette import (
    SQLiteConnectionProvider,
    SQLiteUserStore,
    User,
    Config
)
from minette.datastore.sqldbstores import (
    SQLDBConnectionProvider,
    SQLDBUserStore
)
from minette.datastore.azurestoragestores import (
    AzureTableConnectionProvider,
    AzureTableUserStore
)
from minette.datastore.mysqlstores import (
    MySQLConnectionProvider,
    MySQLUserStore
)
from minette.utils import date_to_unixtime, date_to_str

now = datetime.now()
table_name = "user" + str(date_to_unixtime(now))
user_id = "user_id" + str(date_to_unixtime(now))
print("user_table: {}".format(table_name))
print("user_id: {}".format(user_id))

dbconfig = Config("config/test_config_datastores.ini")

datastore_params = [
    (
        SQLiteConnectionProvider,
        "test.db",
        SQLiteUserStore
    ),
    (
        SQLDBConnectionProvider,
        dbconfig.get("sqldb_connection_str"),
        SQLDBUserStore
    ),
    (
        AzureTableConnectionProvider,
        dbconfig.get("table_connection_str"),
        AzureTableUserStore
    ),
    (
        MySQLConnectionProvider,
        dbconfig.get("mysql_connection_str"),
        MySQLUserStore
    )
]


@pytest.mark.parametrize("connection_provider_class,connection_str,user_store_class", datastore_params)
def test_prepare(connection_provider_class, connection_str, user_store_class):
    us = user_store_class(table_name=table_name, timezone=timezone("Asia/Tokyo"))
    cp = connection_provider_class(connection_str)
    with cp.get_connection() as connection:
        prepare_params = cp.get_prepare_params()
        assert us.prepare_table(connection, prepare_params) is True
        assert us.prepare_table(connection, prepare_params) is False


@pytest.mark.parametrize("connection_provider_class,connection_str,user_store_class", datastore_params)
def test_get(connection_provider_class, connection_str, user_store_class):
    us = user_store_class(table_name=table_name, timezone=timezone("Asia/Tokyo"))
    with connection_provider_class(connection_str).get_connection() as connection:
        user = us.get("TEST", user_id, connection)
        assert user.channel == "TEST"
        assert user.channel_user_id == user_id
        assert user.data == {}
        # get(without user_id)
        user_without_user_id = us.get("TEST", None, connection)
        assert user_without_user_id.channel == "TEST"
        assert user_without_user_id.channel_user_id == ""


@pytest.mark.parametrize("connection_provider_class,connection_str,user_store_class", datastore_params)
def test_get_error(connection_provider_class, connection_str, user_store_class):
    us = user_store_class(table_name=table_name, timezone=timezone("Asia/Tokyo"))
    us.sqls["get_user"] = ""
    with connection_provider_class(connection_str).get_connection() as connection:
        user = us.get("TEST", user_id, connection)
        assert user.channel == "TEST"
        assert user.channel_user_id == user_id
        assert user.data == {}
    # table doesn't exist
    us.table_name = "notexisttable"
    with connection_provider_class(connection_str).get_connection() as connection:
        user = us.get("TEST", user_id, connection)
        assert user.channel == "TEST"
        assert user.channel_user_id == user_id
        assert user.data == {}
    # invalid table name
    us.table_name = "_#_#_"
    with connection_provider_class(connection_str).get_connection() as connection:
        user = us.get("TEST", user_id, connection)
        assert user.channel == "TEST"
        assert user.channel_user_id == user_id
        assert user.data == {}


@pytest.mark.parametrize("connection_provider_class,connection_str,user_store_class", datastore_params)
def test_save(connection_provider_class, connection_str, user_store_class):
    us = user_store_class(table_name=table_name, timezone=timezone("Asia/Tokyo"))
    with connection_provider_class(connection_str).get_connection() as connection:
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
