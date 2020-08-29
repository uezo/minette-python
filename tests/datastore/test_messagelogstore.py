import pytest
from datetime import datetime
from pytz import timezone

from minette import (
    SQLiteStores,
    Message,
    Response,
    Context,
    Config
)
from minette.serializer import dumpd

SQLDBStores = None
try:
    from minette.datastore.sqldbstores import SQLDBStores
except Exception:
    pass

AzureTableStores = None
AzureTableConnection = None
try:
    from minette.datastore.azurestoragestores import (
        AzureTableStores,
        AzureTableConnection,
    )
except Exception:
    pass

MySQLStores = None
MySQLConnection = None
try:
    from minette.datastore.mysqlstores import (
        MySQLStores,
        MySQLConnection,
    )
except Exception:
    pass

SQLAlchemyStores = None
SQLAlchemyConnection = None
SQLAlchemyMessageLog = None
SQLAlchemyMessageLogStore = None
try:
    from minette.datastore.sqlalchemystores import (
        SQLAlchemyStores,
        SQLAlchemyConnection,
        SQLAlchemyMessageLog,
        SQLAlchemyMessageLogStore
    )
except Exception:
    pass

from minette.utils import date_to_unixtime, date_to_str

now = datetime.now()
table_name = "messagelog" + str(date_to_unixtime(now))
user_id = "user_id" + str(date_to_unixtime(now))
print("messagelog_table: {}".format(table_name))
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

    ms = datastore_class.messagelog_store(
        table_name=table_name, timezone=timezone("Asia/Tokyo"))
    cp = datastore_class.connection_provider(connection_str)
    with cp.get_connection() as connection:
        prepare_params = cp.get_prepare_params()
        if SQLAlchemyMessageLogStore and isinstance(ms, SQLAlchemyMessageLogStore):
            assert ms.prepare_table(connection, prepare_params) is False
        else:
            assert ms.prepare_table(connection, prepare_params) is True
        assert ms.prepare_table(connection, prepare_params) is False


@pytest.mark.parametrize("datastore_class, connection_str", datastore_params)
def test_save(datastore_class, connection_str):
    if not datastore_class:
        pytest.skip("Unable to import DataStoreSet")
    if not connection_str:
        pytest.skip(
            "Connection string for {} is not provided"
            .format(datastore_class.connection_provider.__name__))

    ms = datastore_class.messagelog_store(
        table_name=table_name, timezone=timezone("Asia/Tokyo"))
    with datastore_class.connection_provider(connection_str).get_connection() as connection:
        # request
        request = Message(
            id=str(date_to_unixtime(now)),
            channel="TEST", channel_user_id=user_id,
            text="request message {}".format(str(date_to_unixtime(now))))
        # response
        response = Response(messages=[Message(channel="TEST", channel_user_id=user_id, text="response message {}".format(str(date_to_unixtime(now))))])
        # context
        context = Context("TEST", user_id)
        context.data = {
            "strvalue": "value1",
            "intvalue": 2,
            "dtvalue": date_to_str(now),
            "dictvalue": {
                "k1": "v1",
                "k2": 2,
            }
        }

        # save
        save_res = ms.save(request, response, context, connection)

        # check
        if AzureTableConnection and isinstance(connection, AzureTableConnection):
            record = connection.get_entity(table_name, user_id, save_res)
        elif SQLAlchemyConnection and isinstance(connection, SQLAlchemyConnection):
            record = connection.query(SQLAlchemyMessageLog).filter(
                SQLAlchemyMessageLog.request_id == str(date_to_unixtime(now))
            ).first()
            record = dumpd(record)
        else:
            cursor = connection.cursor()
            if MySQLConnection and isinstance(connection, MySQLConnection):
                sql = "select * from {} where request_id = %s"
            else:
                sql = "select * from {} where request_id = ?"
            cursor.execute(sql.format(table_name), (str(date_to_unixtime(now)), ))
            row = cursor.fetchone()
            if isinstance(row, dict):
                record = row
            else:
                record = dict(zip([column[0] for column in cursor.description], row))

        assert record["request_text"] == "request message {}".format(str(date_to_unixtime(now)))
        assert record["response_text"] == "response message {}".format(str(date_to_unixtime(now)))
