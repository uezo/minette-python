import sys, os
sys.path.append(os.pardir)
import unittest
import logging
from datetime import datetime
import minette
from minette.database import ConnectionProvider, MySQLConnectionProvider, SQLDBConnectionProvider
from minette.dialog import Classifier, DialogService, Message, MessageLogger, MySQLMessageLogger, SQLDBMessageLogger
from minette.session import Session, SessionStore, MySQLSessionStore, SQLDBSessionStore
from minette.user import User, UserRepository, MySQLUserRepository, SQLDBUserRepository
from minette.tagger import MeCabTagger, GoogleTagger

class TestAutomata(unittest.TestCase):
    def create_base(self, config_file, cp, ss, ur, ml):
        channel = "TEST"
        channel_user = "test_user"
        bot = minette.create(config_file=config_file)
        # ConnectionProvider
        self.assertIsInstance(bot.connection_provider, cp)
        conn = bot.connection_provider.get_connection()
        # SessionStore
        self.assertIsInstance(bot.session_store, ss)
        sess = bot.session_store.get_session(channel, channel_user, conn)
        self.assertIsInstance(sess, Session)
        sess.data = {"key1": "val1", "key2": "val2"}
        bot.session_store.save_session(sess, conn)
        self.assertEqual("val2", bot.session_store.get_session(channel, channel_user, conn).data["key2"])
        # UserRepository
        self.assertIsInstance(bot.user_repository, ur)
        user = bot.user_repository.get_user(channel, channel_user, conn)
        self.assertIsInstance(user, User)
        user.data = {"ukey1": "udata1", "ukey2": "udata2", "ukey3": "udata3"}
        bot.user_repository.save_user(user, conn)
        self.assertEqual("udata2", bot.user_repository.get_user(channel, channel_user, conn).data["ukey2"])
        # Classifier
        self.assertIsInstance(bot.classifier, Classifier)
        self.assertIsInstance(bot.classifier.classify(request=Message(text="this is test"), session=sess, connection=conn), DialogService)
        # Tagger
        self.assertIsInstance(bot.tagger, minette.tagger.Tagger)
        # MessageLogger
        self.assertIsInstance(bot.message_logger, ml)
        # logger
        self.assertIsInstance(bot.logger, logging.Logger)
        self.assertEqual("minette.automata", bot.logger.name)
        bot.logger.debug("test debug message")
        bot.logger.error("test error message")

    def test_create(self):
        self.create_base("config/minette_test_create.ini", ConnectionProvider, SessionStore, UserRepository, MessageLogger)

    def test_create_mysql(self):
        self.create_base("config/minette_test_create_mysql.ini", MySQLConnectionProvider, MySQLSessionStore, MySQLUserRepository, MySQLMessageLogger)

    def test_create_sqldb(self):
        self.create_base("config/minette_test_create_sqldb.ini", SQLDBConnectionProvider, SQLDBSessionStore, SQLDBUserRepository, SQLDBMessageLogger)

    def test_get_default_logger(self):
        logger = minette.get_default_logger()
        self.assertEqual("minette.automata", logger.name)
        logger.debug("test debug message")
        logger.error("test error message")

    def execute_base(self, config_file, message_sql, input_key, output_key):
        # custom classifier
        class MyClassifier(Classifier):
            def classify(self, request, session, connection=None):
                if request.text == "Get type":
                    return DialogService
                if request.text == "Get None":
                    return None
                if request.text == "Raise exception":
                    return 1 / 0
                return super().classify(request, session, connection)

        # default
        bot = minette.create(config_file=config_file)
        self.assertEqual("You said: Hello", bot.execute(Message(text="Hello"))[0].text)
        self.assertEqual("You said: Good Morning", bot.execute("Good Morning")[0].text)
        # check message logger is working
        message_str = "now: " + minette.util.date_to_str(datetime.now())
        bot.execute(message_str)
        conn = bot.connection_provider.get_connection()
        cur = conn.cursor()
        cur.execute(message_sql, (message_str, ))
        row = cur.fetchone()
        self.assertEqual(message_str, row[input_key])
        self.assertEqual("You said: " + message_str, row[output_key])
        # using custom classifier
        bot_clsfr = minette.create(config_file="config/minette_test_create.ini", classifier=MyClassifier)
        self.assertEqual("You said: Hello", bot_clsfr.execute(Message(text="Hello"))[0].text)
        self.assertEqual("You said: Get type", bot_clsfr.execute(Message(text="Get type"))[0].text)
        self.assertListEqual([], bot_clsfr.execute(Message(text="Get None")))
        self.assertEqual("?", bot_clsfr.execute(Message(text="Raise exception"))[0].text)
        bot_clsfr.message_logger = None
        self.assertEqual("You said: Hello", bot_clsfr.execute(Message(text="Hello"))[0].text)

    def test_execute(self):
        self.execute_base("config/minette_test_create.ini", "select * from messagelog where input_text=? limit 1", "input_text", "output_text")

    def test_execute_mysql(self):
        self.execute_base("config/minette_test_create_mysql.ini", "select * from messagelog where input_text=%s limit 1", "input_text", "output_text")

    def test_execute_sqldb(self):
        self.execute_base("config/minette_test_create_sqldb.ini", "select top 1 * from minette_messagelog where input_text=?", 7, 8)

    def test_execute_tagger(self):
        class MyDialog(DialogService):
            def compose_response(self, request, session, connection):
                words = []
                for w in request.words:
                    words.append(w.word)
                return [Message(text="/".join(words))]

        bot = minette.create(config_file="config/minette_test_mecab.ini", default_dialog_service=MyDialog)
        self.assertIsInstance(bot.tagger, MeCabTagger)
        self.assertEqual("これ/は/テスト/です", bot.execute("これはテストです")[0].text)
        self.assertEqual("", bot.execute("")[0].text)

        bot = minette.create(config_file="config/minette_test_googletagger.ini", default_dialog_service=MyDialog, tagger=GoogleTagger)
        self.assertIsInstance(bot.tagger, GoogleTagger)
        self.assertEqual("これ/は/テスト/です", bot.execute("これはテストです")[0].text)
        self.assertEqual("", bot.execute("")[0].text)

if __name__ == '__main__':
    #prepare mysql
    from minette.config import Config
    conf = Config(config_file="config/minette_test_create_mysql.ini")
    cp = minette.database.MySQLConnectionProvider(conf.get("connection_str"))
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
    #prepare sqldb
    conf = Config(config_file="config/minette_test_create_sqldb.ini")
    cp = minette.database.SQLDBConnectionProvider(conf.get("connection_str"))
    con = cp.get_connection()
    cur = con.cursor()
    try:
        cur.execute("drop table minette_session")
        cur.execute("drop table minette_user")
        cur.execute("drop table minette_uidmap")
        cur.execute("drop table minette_messagelog")
    except Exception as ex:
        print(ex)
    finally:
        con.close()
    #test
    unittest.main()
