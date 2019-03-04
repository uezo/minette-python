import sys
import os
sys.path.append(os.pardir)
import unittest
import logging
from datetime import datetime
from minette import Minette
from minette.database import ConnectionProvider
from minette.dialog import DialogRouter, DialogService, EchoDialogService, ErrorDialogService
from minette.session import Session, SessionStore
from minette.user import User, UserRepository
from minette.message import Message, MessageLogger
from minette.tagger import Tagger
from minette.tagger.mecab import MeCabTagger
from minette.tagger.google import GoogleTagger
from minette.database.mysql import MySQLConnectionProvider, MySQLSessionStore, MySQLUserRepository, MySQLMessageLogger
from minette.database.sqldb import SQLDBConnectionProvider, SQLDBSessionStore, SQLDBUserRepository, SQLDBMessageLogger
from minette.serializer import JsonSerializable
from minette.util import date_to_str, str_to_date


class MyDefaultRouter(DialogRouter):
    def __init__(self, logger=None, config=None, timezone=None, default_dialog_service=None):
        super().__init__(logger, config, timezone, default_dialog_service)
        self.my_value = "default_router_value"
        print(self.my_value)


class MyDefaultDialogService(DialogService):
    def compose_response(self, request, session, connection):
        return "default_dialog_value"


class TestAutomata(unittest.TestCase):
    def create_base(self, config_file, cp, ss, ur, ml):
        channel = "TEST"
        channel_user_id = "test_user"
        bot = Minette.create(config_file=config_file)
        # ConnectionProvider
        self.assertIsInstance(bot.connection_provider, cp)
        conn = bot.connection_provider.get_connection()
        # SessionStore
        self.assertIsInstance(bot.session_store, ss)
        sess = bot.session_store.get_session(channel, channel_user_id, conn)
        self.assertIsInstance(sess, Session)
        sess.data = {"key1": "val1", "key2": "val2"}
        bot.session_store.save_session(sess, conn)
        self.assertEqual("val2", bot.session_store.get_session(channel, channel_user_id, conn).data["key2"])
        # UserRepository
        self.assertIsInstance(bot.user_repository, ur)
        user = bot.user_repository.get_user(channel, channel_user_id, conn)
        self.assertIsInstance(user, User)
        user.data = {"ukey1": "udata1", "ukey2": "udata2", "ukey3": "udata3"}
        bot.user_repository.save_user(user, conn)
        self.assertEqual("udata2", bot.user_repository.get_user(channel, channel_user_id, conn).data["ukey2"])
        # DialogRouter
        self.assertIsInstance(bot.dialog_router, DialogRouter)
        self.assertIs(bot.dialog_router.route(request=Message(text="this is test"), session=sess, connection=conn), EchoDialogService)
        # Tagger
        self.assertIsInstance(bot.tagger, Tagger)
        # MessageLogger
        self.assertIsInstance(bot.message_logger, ml)
        # logger
        self.assertIsInstance(bot.logger, logging.Logger)
        self.assertEqual("minette.core", bot.logger.name)
        bot.logger.debug("test debug message")
        bot.logger.error("test error message")

    def test_create(self):
        self.create_base("config/minette_test_create.ini", ConnectionProvider, SessionStore, UserRepository, MessageLogger)

    def test_create_mysql(self):
        self.create_base("config/minette_test_create_mysql.ini", MySQLConnectionProvider, MySQLSessionStore, MySQLUserRepository, MySQLMessageLogger)

    def test_create_sqldb(self):
        self.create_base("config/minette_test_create_sqldb.ini", SQLDBConnectionProvider, SQLDBSessionStore, SQLDBUserRepository, SQLDBMessageLogger)

    def test_get_logger(self):
        logger = Minette.get_logger(logfile="./logger_test.log")
        self.assertEqual("minette.core", logger.name)
        logger.debug("test debug message")
        logger.error("test error message")

    def execute_base(self, config_file, message_sql, input_key, output_key):
        # custom dialogrouter
        class MyRouter(DialogRouter):
            def configure(self):
                self.intent_resolver = {
                    "GetTypeIntent": EchoDialogService,
                    "GetNoneIntent": None,
                    "GetNoResponseIntent": MyDialogService,
                    "RaiseDialogExceptionIntent": MyErrorDialogService,
                    "InstanceIntent": InstanceDialogService()
                }

            def extract_intent(self, request, session, connection=None):
                if request.text == "Get type":
                    return "GetTypeIntent"
                elif request.text == "Get None":
                    return "GetNoneIntent"
                elif request.text == "Get no response":
                    return "GetNoResponseIntent"
                elif request.text == "Raise exception":
                    return "RaiseExceptionIntent"
                elif request.text == "Raise dialog exception":
                    return "RaiseDialogExceptionIntent"
                elif request.text == "Get Instance":
                    return "InstanceIntent"

            def route(self, request, session, connection=None):
                if request.intent == "RaiseExceptionIntent":
                    return 1 / 0
                return super().route(request, session, connection)

        class MyDialogService(DialogService):
            def compose_response(self, request, session, connection):
                return

        class InstanceDialogService(DialogService):
            def compose_response(self, request, session, connection):
                return "Instance"

        class MyErrorDialogService(DialogService):
            def compose_response(self, request, session, connection):
                val = 1 / 0

        # default
        bot = Minette.create(config_file=config_file)
        if bot.dialog_router.default_dialog_service is DialogService:
            bot.dialog_router.default_dialog_service = EchoDialogService
        self.assertEqual("You said: Hello", bot.chat(Message(text="Hello")).messages[0].text)
        self.assertEqual("You said: Good Morning", bot.chat("Good Morning").messages[0].text)
        # check message logger is working
        message_str = "now: " + date_to_str(datetime.now())
        bot.chat(message_str)
        conn = bot.connection_provider.get_connection()
        cur = conn.cursor()
        cur.execute(message_sql, (message_str, ))
        row = cur.fetchone()
        self.assertEqual(message_str, row[input_key])
        self.assertEqual("You said: " + message_str, row[output_key])
        # using custom dialogrouter
        bot_clsfr = Minette.create(config_file=config_file, dialog_router=MyRouter)
        if bot_clsfr.dialog_router.default_dialog_service is DialogService:
            bot_clsfr.dialog_router.default_dialog_service = EchoDialogService
        self.assertEqual("You said: Hello", bot_clsfr.chat(Message(text="Hello")).messages[0].text)
        self.assertEqual("You said: Get type", bot_clsfr.chat(Message(text="Get type")).messages[0].text)
        self.assertEqual([], bot_clsfr.chat(Message(text="Get None")).messages)
        msg = bot_clsfr.chat(Message(text="Get no response"))
        self.assertListEqual([], bot_clsfr.chat(Message(text="Get no response")).messages)
        self.assertEqual("?", bot_clsfr.chat(Message(text="Raise exception")).messages[0].text)
        self.assertEqual("?", bot_clsfr.chat(Message(text="Raise dialog exception")).messages[0].text)
        self.assertEqual("Instance", bot_clsfr.chat(Message(text="Get Instance")).messages[0].text)
        bot_clsfr.message_logger = None
        self.assertEqual("You said: Hello", bot_clsfr.chat(Message(text="Hello")).messages[0].text)

    def test_execute(self):
        self.execute_base("config/minette_test_create.ini", "select * from messagelog where input_text=? limit 1", "input_text", "output_text")

    def test_execute_without_config(self):
        self.execute_base(None, "select * from messagelog where input_text=? limit 1", "input_text", "output_text")

    def test_execute_mysql(self):
        self.execute_base("config/minette_test_create_mysql.ini", "select * from messagelog where input_text=%s limit 1", "input_text", "output_text")

    def test_execute_mysql_preset(self):
        self.execute_base("config/minette_test_create_mysql_preset.ini", "select * from messagelog where input_text=%s limit 1", "input_text", "output_text")

    def test_execute_sqldb(self):
        self.execute_base("config/minette_test_create_sqldb.ini", "select top 1 * from minette.messagelog where input_text=?", 14, 18)

    def test_execute_sqldb_preset(self):
        self.execute_base("config/minette_test_create_sqldb_preset.ini", "select top 1 * from minette.messagelog where input_text=?", 14, 18)

    def test_execute_tagger(self):
        class MyDialog(DialogService):
            def compose_response(self, request, session, connection):
                words = []
                for w in request.words:
                    words.append(w.word)
                return [Message(text="/".join(words))]

        bot = Minette.create(config_file="config/minette_test_mecab.ini", default_dialog_service=MyDialog)
        self.assertIsInstance(bot.tagger, MeCabTagger)
        self.assertEqual("これ/は/テスト/です", bot.chat("これはテストです").messages[0].text)
        self.assertEqual("", bot.chat("").messages[0].text)

        bot = Minette.create(config_file="config/minette_test_googletagger.ini", default_dialog_service=MyDialog, tagger=GoogleTagger)
        self.assertIsInstance(bot.tagger, GoogleTagger)
        self.assertEqual("これ/は/テスト/です", bot.chat("これはテストです").messages[0].text)
        self.assertEqual("", bot.chat("").messages[0].text)

    def test_default_dialog(self):
        bot = Minette.create(config_file="config/minette_test_create_router_and_dialog.ini")
        self.assertEqual("default_router_value", bot.dialog_router.my_value)
        self.assertEqual("default_dialog_value", bot.chat("test").messages[0].text)

    def test_serializer(self):
        class TestSerializeMemberClass(JsonSerializable):
            def __init__(self, strvalue="no value"):
                self.strvalue = strvalue
                self.intvalue = 7890
                self.nullvalue = None

        class TestSerializeClass(JsonSerializable):
            def __init__(self):
                self.strvalue = "テスト"
                self.intvalue = 123456
                self.dtvalue = datetime.now()
                self.objvalue = TestSerializeMemberClass("objvalue")
                self.nullvalue = None
                self.listvalue = ["a", "b", "c"]
                self.dictvalue = {"k1":"v1", "k2":"v2", "k3":"v3", "k4":"v4"}
                self.obj_list = [TestSerializeMemberClass("obj_list1"), TestSerializeMemberClass("obj_list2"), TestSerializeMemberClass("obj_list3")]
                self.obj_dict = {"dict1": TestSerializeMemberClass("obj_dict1"), "dict2": TestSerializeMemberClass("obj_dict2"), "dict3": TestSerializeMemberClass("obj_dict3")}

            @classmethod
            def from_dict(cls, data, as_args=False):
                tsc = super().from_dict(data, as_args)
                tsc.objvalue = TestSerializeMemberClass.from_dict(tsc.objvalue)
                tsc.obj_list = TestSerializeMemberClass.from_dict_list(tsc.obj_list)
                tsc.obj_dict = TestSerializeMemberClass.from_dict_dict(tsc.obj_dict)
                return tsc

        tsc = TestSerializeClass()
        tsc_dict = tsc.to_dict()
        tsc_json = tsc.to_json()
        tsc_restore = TestSerializeClass.from_json(tsc_json)

        self.assertIsInstance(tsc_dict, dict)
        self.assertIsInstance(tsc_json, str)
        self.assertIsInstance(tsc_restore, TestSerializeClass)
        self.assertIsInstance(tsc_restore.objvalue, TestSerializeMemberClass)
        self.assertEqual(123456, tsc_dict["intvalue"])
        self.assertEqual("obj_list2", tsc_dict["obj_list"][1]["strvalue"])
        self.assertEqual("テスト", tsc_restore.strvalue)
        self.assertEqual("obj_dict1", tsc_restore.obj_dict["dict1"].strvalue)

    def test_messagelog(self):
        bot = Minette.create(config_file="config/minette_test_create.ini")
        messagelogs = bot.get_message_log()
        self.assertIsInstance(messagelogs[0]["timestamp"], datetime)

    def test_messagelog_mysql(self):
        bot = Minette.create(config_file="config/minette_test_create_mysql.ini")
        messagelogs = bot.get_message_log()
        self.assertIsInstance(messagelogs[0]["timestamp"], datetime)

    def test_messagelog_sqldb(self):
        bot = Minette.create(config_file="config/minette_test_create_sqldb.ini")
        messagelogs = bot.get_message_log()
        self.assertIsInstance(messagelogs[0]["timestamp"], datetime)


if __name__ == "__main__":
    from minette.config import Config
    # prepare mysql
    conf = Config(config_file="config/minette_test_create_mysql.ini")
    cp = MySQLConnectionProvider(conf.get("connection_str"))
    con = cp.get_connection()
    cur = con.cursor()
    try:
        cur.execute("drop table session")
        cur.execute("drop table user")
        cur.execute("drop table user_id_mapper")
        cur.execute("drop table messagelog")
    except Exception as ex:
        print(ex)
    finally:
        con.close()
    # prepare sqldb
    conf = Config(config_file="config/minette_test_create_sqldb.ini")
    cp = SQLDBConnectionProvider(conf.get("connection_str"))
    con = cp.get_connection()
    cur = con.cursor()
    try:
        cur.execute("drop table minette.session")
        cur.execute("drop table minette.users")
        cur.execute("drop table minette.uidmap")
        cur.execute("drop table minette.messagelog")
    except Exception as ex:
        print(ex)
    finally:
        con.close()
    # test
    unittest.main()
