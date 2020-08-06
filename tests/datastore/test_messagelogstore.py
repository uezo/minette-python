import pytest
from datetime import datetime
from pytz import timezone

import objson

from minette import (
    SQLiteConnectionProvider,
    SQLiteMessageLogStore,
    Message,
    Response,
    Context,
    Config
)
from minette.datastore.sqldbstores import (
    SQLDBConnectionProvider,
    SQLDBMessageLogStore
)
from minette.datastore.azurestoragestores import (
    AzureTableConnectionProvider,
    AzureTableMessageLogStore,
    AzureTableConnection
)
from minette.datastore.mysqlstores import (
    MySQLConnection,
    MySQLConnectionProvider,
    MySQLMessageLogStore
)
from minette.datastore.sqlalchemystores import (
    SQLAlchemyConnection,
    SQLAlchemyConnectionProvider,
    SQLAlchemyMessageLogStore,
    SQLAlchemyMessageLog
)
from minette.utils import date_to_unixtime, date_to_str

now = datetime.now()
table_name = "messagelog" + str(date_to_unixtime(now))
user_id = "user_id" + str(date_to_unixtime(now))
print("messagelog_table: {}".format(table_name))
print("user_id: {}".format(user_id))

dbconfig = Config("config/test_config_datastores.ini")

datastore_params = [
    (
        SQLiteConnectionProvider,
        "test.db",
        SQLiteMessageLogStore
    ),
    (
        SQLDBConnectionProvider,
        dbconfig.get("sqldb_connection_str"),
        SQLDBMessageLogStore
    ),
    (
        AzureTableConnectionProvider,
        dbconfig.get("table_connection_str"),
        AzureTableMessageLogStore
    ),
    (
        MySQLConnectionProvider,
        dbconfig.get("mysql_connection_str"),
        MySQLMessageLogStore
    ),
    (
        SQLAlchemyConnectionProvider,
        dbconfig.get("sqlalchemy_sqlite_connection_str"),
        SQLAlchemyMessageLogStore
    ),
    (
        SQLAlchemyConnectionProvider,
        dbconfig.get("sqlalchemy_sqldb_connection_str"),
        SQLAlchemyMessageLogStore
    ),
    (
        SQLAlchemyConnectionProvider,
        dbconfig.get("sqlalchemy_mysql_connection_str"),
        SQLAlchemyMessageLogStore
    ),
]


@pytest.mark.parametrize("connection_provider_class,connection_str,messagelog_store_class", datastore_params)
def test_prepare(connection_provider_class, connection_str, messagelog_store_class):
    ms = messagelog_store_class(table_name=table_name, timezone=timezone("Asia/Tokyo"))
    cp = connection_provider_class(connection_str)
    with cp.get_connection() as connection:
        prepare_params = cp.get_prepare_params()
        if not isinstance(ms, SQLAlchemyMessageLogStore):
            assert ms.prepare_table(connection, prepare_params) is True
        else:
            assert ms.prepare_table(connection, prepare_params) is False
        assert ms.prepare_table(connection, prepare_params) is False


@pytest.mark.parametrize("connection_provider_class,connection_str,messagelog_store_class", datastore_params)
def test_save(connection_provider_class, connection_str, messagelog_store_class):
    ms = messagelog_store_class(table_name=table_name, timezone=timezone("Asia/Tokyo"))
    with connection_provider_class(connection_str).get_connection() as connection:
        # request
        request = Message(id=str(date_to_unixtime(now)), channel="TEST", channel_user_id=user_id, text="request message {}".format(str(date_to_unixtime(now))))
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
        if isinstance(connection, AzureTableConnection):
            record = connection.get_entity(table_name, user_id, save_res)
        elif isinstance(connection, SQLAlchemyConnection):
            record = connection.query(SQLAlchemyMessageLog).filter(SQLAlchemyMessageLog.request_id==str(date_to_unixtime(now))).first()
            record = objson.dumpd(record)
        else:
            cursor = connection.cursor()
            if isinstance(connection, MySQLConnection):
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
