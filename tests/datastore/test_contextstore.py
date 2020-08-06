import pytest
from datetime import datetime
from pytz import timezone
from time import sleep

from minette import (
    SQLiteConnectionProvider,
    SQLiteContextStore,
    Context,
    Config
)
from minette.datastore.sqldbstores import (
    SQLDBConnectionProvider,
    SQLDBContextStore
)
from minette.datastore.azurestoragestores import (
    AzureTableConnectionProvider,
    AzureTableContextStore
)
from minette.datastore.mysqlstores import (
    MySQLConnectionProvider,
    MySQLContextStore
)
from minette.datastore.sqlalchemystores import (
    SQLAlchemyConnectionProvider,
    SQLAlchemyContextStore
)

from minette.utils import date_to_unixtime, date_to_str

now = datetime.now(tz=timezone("Asia/Tokyo"))
table_name = "context" + str(date_to_unixtime(now))
user_id = "user_id" + str(date_to_unixtime(now))
print("context_table: {}".format(table_name))
print("user_id: {}".format(user_id))

dbconfig = Config("config/test_config_datastores.ini")

datastore_params = [
    (
        SQLiteConnectionProvider,
        "test.db",
        SQLiteContextStore
    ),
    (
        SQLDBConnectionProvider,
        dbconfig.get("sqldb_connection_str"),
        SQLDBContextStore
    ),
    (
        AzureTableConnectionProvider,
        dbconfig.get("table_connection_str"),
        AzureTableContextStore
    ),
    (
        MySQLConnectionProvider,
        dbconfig.get("mysql_connection_str"),
        MySQLContextStore
    ),
    (
        SQLAlchemyConnectionProvider,
        dbconfig.get("sqlalchemy_sqlite_connection_str"),
        SQLAlchemyContextStore
    ),
    (
        SQLAlchemyConnectionProvider,
        dbconfig.get("sqlalchemy_sqldb_connection_str"),
        SQLAlchemyContextStore
    ),
    (
        SQLAlchemyConnectionProvider,
        dbconfig.get("sqlalchemy_mysql_connection_str"),
        SQLAlchemyContextStore
    ),
]


@pytest.mark.parametrize("connection_provider_class,connection_str,context_store_class", datastore_params)
def test_prepare(connection_provider_class, connection_str, context_store_class):
    cs = context_store_class(table_name=table_name, timezone=timezone("Asia/Tokyo"))
    cp = connection_provider_class(connection_str)
    with cp.get_connection() as connection:
        prepare_params = cp.get_prepare_params()
        if not isinstance(cp, SQLAlchemyConnectionProvider):
            assert cs.prepare_table(connection, prepare_params) is True
        else:
            assert cs.prepare_table(connection, prepare_params) is False
        assert cs.prepare_table(connection, prepare_params) is False


@pytest.mark.parametrize("connection_provider_class,connection_str,context_store_class", datastore_params)
def test_get(connection_provider_class, connection_str, context_store_class):
    cs = context_store_class(table_name=table_name, timezone=timezone("Asia/Tokyo"))
    with connection_provider_class(connection_str).get_connection() as connection:
        ctx = cs.get("TEST", user_id, connection)
        assert ctx.channel == "TEST"
        assert ctx.channel_user_id == user_id
        assert ctx.is_new is True
        assert ctx.data == {}

        # get without user_id
        ctx_without_user = cs.get("TEST", None, connection)
        assert ctx_without_user.channel == "TEST"
        assert ctx_without_user.channel_user_id == ""


@pytest.mark.parametrize("connection_provider_class,connection_str,context_store_class", datastore_params)
def test_get_error(connection_provider_class, connection_str, context_store_class):
    cs = context_store_class(table_name=table_name, timezone=timezone("Asia/Tokyo"))
    cs.sqls["get_context"] = ""
    with connection_provider_class(connection_str).get_connection() as connection:
        ctx = cs.get("TEST", user_id, connection)
        assert ctx.channel == "TEST"
        assert ctx.channel_user_id == user_id
        assert ctx.is_new is True
        assert ctx.data == {}


@pytest.mark.parametrize("connection_provider_class,connection_str,context_store_class", datastore_params)
def test_save(connection_provider_class, connection_str, context_store_class):
    cs = context_store_class(table_name=table_name, timezone=timezone("Asia/Tokyo"))
    with connection_provider_class(connection_str).get_connection() as connection:
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
    cs_timeout = context_store_class(table_name=table_name, timezone=timezone("Asia/Tokyo"), timeout=3)
    with connection_provider_class(connection_str).get_connection() as connection:
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
