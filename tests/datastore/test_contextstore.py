import pytest
from datetime import datetime
from pytz import timezone
from time import sleep

from minette import (
    SQLiteStores,
    Context,
    Config
)

# SQLDatabase
SQLDBStores = None
try:
    from minette.datastore.sqldbstores import SQLDBStores
except Exception:
    pass

# AzureTableStorage
AzureTableStores = None
try:
    from minette.datastore.azurestoragestores import AzureTableStores
except Exception:
    pass

# MySQL
MySQLStores = None
try:
    from minette.datastore.mysqlstores import MySQLStores
except Exception:
    pass

# SQLAlchemy
SQLAlchemyStores = None
SQLAlchemyConnectionProvider = None
try:
    from minette.datastore.sqlalchemystores import (
        SQLAlchemyStores,
        SQLAlchemyConnectionProvider
    )
except Exception:
    pass

from minette.utils import date_to_unixtime

now = datetime.now(tz=timezone("Asia/Tokyo"))
table_name = "context" + str(date_to_unixtime(now))
user_id = "user_id" + str(date_to_unixtime(now))
print("context_table: {}".format(table_name))
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

    cs = datastore_class.context_store(
        table_name=table_name, timezone=timezone("Asia/Tokyo"))
    cp = datastore_class.connection_provider(connection_str)
    with cp.get_connection() as connection:
        prepare_params = cp.get_prepare_params()
        if SQLAlchemyConnectionProvider and isinstance(cp, SQLAlchemyConnectionProvider):
            assert cs.prepare_table(connection, prepare_params) is False
        else:
            assert cs.prepare_table(connection, prepare_params) is True
        assert cs.prepare_table(connection, prepare_params) is False


@pytest.mark.parametrize("datastore_class, connection_str", datastore_params)
def test_get(datastore_class, connection_str):
    if not datastore_class:
        pytest.skip("Unable to import DataStoreSet")
    if not connection_str:
        pytest.skip(
            "Connection string for {} is not provided"
            .format(datastore_class.connection_provider.__name__))

    cs = datastore_class.context_store(
        table_name=table_name, timezone=timezone("Asia/Tokyo"))
    with datastore_class.connection_provider(connection_str).get_connection() as connection:
        ctx = cs.get("TEST", user_id, connection)
        assert ctx.channel == "TEST"
        assert ctx.channel_user_id == user_id
        assert ctx.is_new is True
        assert ctx.data == {}

        # get without user_id
        ctx_without_user = cs.get("TEST", None, connection)
        assert ctx_without_user.channel == "TEST"
        assert ctx_without_user.channel_user_id == ""


@pytest.mark.parametrize("datastore_class,connection_str", datastore_params)
def test_get_error(datastore_class, connection_str):
    if not datastore_class:
        pytest.skip("Unable to import DataStoreSet")
    if not connection_str:
        pytest.skip(
            "Connection string for {} is not provided"
            .format(datastore_class.connection_provider.__name__))

    cs = datastore_class.context_store(
        table_name=table_name, timezone=timezone("Asia/Tokyo"))
    cs.sqls["get_context"] = ""
    with datastore_class.connection_provider(connection_str).get_connection() as connection:
        ctx = cs.get("TEST", user_id, connection)
        assert ctx.channel == "TEST"
        assert ctx.channel_user_id == user_id
        assert ctx.is_new is True
        assert ctx.data == {}


@pytest.mark.parametrize("datastore_class, connection_str", datastore_params)
def test_save(datastore_class, connection_str):
    if not datastore_class:
        pytest.skip("Unable to import DataStoreSet")
    if not connection_str:
        pytest.skip(
            "Connection string for {} is not provided"
            .format(datastore_class.connection_provider.__name__))

    cs = datastore_class.context_store(
        table_name=table_name, timezone=timezone("Asia/Tokyo"))
    with datastore_class.connection_provider(connection_str).get_connection() as connection:
        ctx = cs.get("TEST", user_id, connection)
        ctx.data["strvalue"] = "value1"
        ctx.data["intvalue"] = 2
        ctx.data["dtvalue"] = now
        ctx.data["dictvalue"] = {
            "k1": "v1",
            "k2": 2,
        }
        cs.save(ctx, connection)
        ctx = cs.get("TEST", user_id, connection)
        assert ctx.channel == "TEST"
        assert ctx.channel_user_id == user_id
        assert ctx.is_new is False
        assert ctx.data == {
            "strvalue": "value1",
            "intvalue": 2,
            "dtvalue": now,
            "dictvalue": {
                "k1": "v1",
                "k2": 2,
            }
        }

        # save (not saved)
        cs.save(Context(), connection)

    # timeout
    cs_timeout = datastore_class.context_store(
        table_name=table_name, timezone=timezone("Asia/Tokyo"), timeout=3)
    with datastore_class.connection_provider(connection_str).get_connection() as connection:
        ctx = cs_timeout.get("TEST", user_id + "_to", connection)
        assert ctx.is_new is True
        ctx.data["strvalue"] = "value1"
        cs.save(ctx, connection)
        sleep(1)    # shorter than timeout
        ctx = cs_timeout.get("TEST", user_id + "_to", connection)
        assert ctx.is_new is False
        assert ctx.data["strvalue"] == "value1"
        sleep(5)    # longer than timeout
        ctx = cs_timeout.get("TEST", user_id + "_to", connection)
        assert ctx.is_new is True
        assert ctx.data == {}
