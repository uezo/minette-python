import sys
import os
sys.path.append(os.pardir)
import pytest
from pytz import timezone
from logging import Logger, FileHandler, getLogger
from datetime import datetime
from types import GeneratorType

from minette import (
    Minette, DialogService, SQLiteConnectionProvider,
    SQLiteContextStore, SQLiteUserStore, SQLiteMessageLogStore,
    Tagger, Config, DialogRouter, StoreSet, Message, User, Group,
    DependencyContainer, Payload
)
from minette.utils import date_to_unixtime
from minette.tagger.janometagger import JanomeTagger

now = datetime.now()
user_id = "user_id" + str(date_to_unixtime(now))
print("user_id: {}".format(user_id))


class CustomTagger(Tagger):
    pass


class CustomConnectionProvider(SQLiteConnectionProvider):
    pass


class CustomContextStore(SQLiteContextStore):
    pass


class CustomUserStore(SQLiteUserStore):
    pass


class CustomMessageLogStore(SQLiteMessageLogStore):
    pass


class CustomDataStores(StoreSet):
    connection_provider = CustomConnectionProvider
    context_store = CustomContextStore
    user_store = CustomUserStore
    messagelog_store = CustomMessageLogStore


class MyDialog(DialogService):
    def compose_response(self, request, context, connection):
        return "res:" + request.text


class ErrorDialog(DialogService):
    def compose_response(self, request, context, connection):
        1 / 0
        return "res:" + request.text


class MyDialogRouter(DialogRouter):
    def __init__(self, custom_router_arg=None, **kwargs):
        super().__init__(**kwargs)
        self.custom_attr = custom_router_arg


class TaggerDialog(DialogService):
    def compose_response(self, request, context, connection):
        return request.to_reply(
            text=request.text,
            payloads=[Payload(content_type="data", content=request.words)])


class TaggerManuallyParseDialog(DialogService):
    def compose_response(self, request, context, connection):
        assert request.words == []
        request.words = self.dependencies.tagger.parse(request.text, max_length=10)
        return request.to_reply(
            text=request.text,
            payloads=[Payload(content_type="data", content=request.words)])


class TaggerManuallyParseGeneratorDialog(DialogService):
    def compose_response(self, request, context, connection):
        assert request.words == []
        request.words = self.dependencies.tagger.parse_as_generator(request.text, max_length=10)
        return request.to_reply(
            text=request.text,
            payloads=[Payload(content_type="data", content=request.words)])


def test_init():
    # without config
    bot = Minette()
    assert bot.config.get("timezone") == "UTC"
    assert bot.timezone == timezone("UTC")
    assert isinstance(bot.logger, Logger)
    assert bot.logger.name == "minette"
    assert isinstance(bot.connection_provider, SQLiteConnectionProvider)
    assert isinstance(bot.context_store, SQLiteContextStore)
    assert isinstance(bot.user_store, SQLiteUserStore)
    assert isinstance(bot.messagelog_store, SQLiteMessageLogStore)
    assert bot.default_dialog_service is None
    assert isinstance(bot.tagger, Tagger)


def test_init_config():
    bot = Minette(config_file="./config/test_config.ini")
    assert bot.timezone == timezone("Asia/Tokyo")
    for handler in bot.logger.handlers:
        if isinstance(handler, FileHandler):
            assert handler.baseFilename == \
                os.path.join(os.path.dirname(os.path.abspath(__file__)),
                bot.config.get("log_file"))
    assert bot.connection_provider.connection_str != ""
    assert bot.connection_provider.connection_str == \
        bot.config.get("connection_str")
    assert bot.context_store.timeout == bot.config.get("context_timeout")
    assert bot.context_store.table_name == bot.config.get("context_table")
    assert bot.user_store.table_name == bot.config.get("user_table")
    assert bot.messagelog_store.table_name == \
        bot.config.get("messagelog_table")


def test_init_args():
    # initialize arguments
    config = Config("")
    config.confg_parser.add_section("test_section")
    config.confg_parser.set("test_section", "test_key", "test_value")
    tz = timezone("Asia/Tokyo")
    logger = getLogger("test_core_logger")
    print(logger.name)
    connection_provider = CustomConnectionProvider
    context_store = CustomContextStore
    user_store = CustomUserStore
    messagelog_store = CustomMessageLogStore
    data_stores = CustomDataStores
    default_dialog_service = MyDialog
    dialog_router = MyDialogRouter
    tagger = CustomTagger
    custom_router_arg = "router_value"

    # create bot
    bot = Minette(
        config=config, timezone=tz, logger=logger,
        connection_provider=connection_provider, context_store=context_store,
        user_store=user_store, messagelog_store=messagelog_store,
        default_dialog_service=default_dialog_service,
        dialog_router=dialog_router,
        custom_router_arg=custom_router_arg,
        tagger=tagger, prepare_table=True
    )
    assert bot.config.get("test_key", section="test_section") == "test_value"
    assert bot.timezone == timezone("Asia/Tokyo")
    assert bot.logger.name == "test_core_logger"
    assert isinstance(bot.connection_provider, CustomConnectionProvider)
    assert isinstance(bot.context_store, CustomContextStore)
    assert isinstance(bot.user_store, CustomUserStore)
    assert isinstance(bot.messagelog_store, CustomMessageLogStore)
    assert bot.default_dialog_service is MyDialog
    assert isinstance(bot.dialog_router, MyDialogRouter)
    assert bot.dialog_router.custom_attr == "router_value"
    assert isinstance(bot.tagger, CustomTagger)

    # create bot with data_stores
    bot = Minette(
        config=config, timezone=tz, logger=logger,
        data_stores=data_stores,
        default_dialog_service=default_dialog_service,
        dialog_router=dialog_router,
        custom_router_arg=custom_router_arg,
        tagger=tagger, prepare_table=True
    )
    assert bot.config.get("test_key", section="test_section") == "test_value"
    assert bot.timezone == timezone("Asia/Tokyo")
    assert bot.logger.name == "test_core_logger"
    assert isinstance(bot.connection_provider, CustomConnectionProvider)
    assert isinstance(bot.context_store, CustomContextStore)
    assert isinstance(bot.user_store, CustomUserStore)
    assert isinstance(bot.messagelog_store, CustomMessageLogStore)
    assert bot.default_dialog_service is MyDialog
    assert isinstance(bot.dialog_router, MyDialogRouter)
    assert bot.dialog_router.custom_attr == "router_value"
    assert isinstance(bot.tagger, CustomTagger)


def test_get_user():
    bot = Minette(prepare_table=True)
    with bot.connection_provider.get_connection() as connection:
        # register user for test
        u = bot.user_store.get(
            channel="get_user_test", channel_user_id=user_id,
            connection=connection)
        u.name = "user channel"
        bot.user_store.save(u, connection)
        u_detail = bot.user_store.get(
            channel="get_user_test_detail", channel_user_id=user_id,
            connection=connection)
        u_detail.name = "user detail"
        bot.user_store.save(u_detail, connection)

        # without detail
        request = Message(
            text="hello", channel="get_user_test", channel_user_id=user_id)
        user = bot._get_user(request, connection)
        assert user.channel == "get_user_test"
        assert user.channel_user_id == user_id
        assert user.name == "user channel"

        # with detail
        bot.config.confg_parser.set("minette", "user_scope", "channel_detail")
        request = Message(
            text="hello", channel="get_user_test", channel_detail="detail",
            channel_user_id=user_id)
        user = bot._get_user(request, connection)
        assert user.channel == "get_user_test_detail"
        assert user.channel_user_id == user_id
        assert user.name == "user detail"


def test_save_user():
    bot = Minette(prepare_table=True)
    with bot.connection_provider.get_connection() as connection:
        # register user for test
        u = bot.user_store.get(
            channel="save_user_test", channel_user_id=user_id,
            connection=connection)
        u.name = "Tomori Nao"

        # save
        bot._save_user(u, connection)

        # check
        request = Message(
            text="hello", channel="save_user_test", channel_user_id=user_id)
        user = bot._get_user(request, connection)
        assert user.channel == "save_user_test"
        assert user.channel_user_id == user_id
        assert user.name == "Tomori Nao"


def test_get_context():
    bot = Minette(prepare_table=True)
    with bot.connection_provider.get_connection() as connection:
        # register context for test
        ctx = bot.context_store.get(
            channel="get_context_test", channel_user_id=user_id,
            connection=connection)
        ctx.data["unixtime"] = date_to_unixtime(now)
        bot.context_store.save(ctx, connection)
        ctx_group = bot.context_store.get(
            channel="get_context_test", channel_user_id="group_" + user_id,
            connection=connection)
        ctx_group.data["unixtime"] = date_to_unixtime(now)
        bot.context_store.save(ctx_group, connection)
        ctx_detail = bot.context_store.get(
            channel="get_context_test_detail", channel_user_id=user_id,
            connection=connection)
        ctx_detail.data["unixtime"] = date_to_unixtime(now)
        bot.context_store.save(ctx_detail, connection)

        # without detail
        request = Message(
            text="hello", channel="get_context_test", channel_user_id=user_id)
        context = bot._get_context(request, connection)
        assert context.channel == "get_context_test"
        assert context.channel_user_id == user_id
        assert context.data["unixtime"] == date_to_unixtime(now)

        # group without group
        request = Message(
            text="hello", channel="get_context_test", channel_user_id=user_id)
        request.group = Group(id="group_" + user_id)
        context = bot._get_context(request, connection)
        assert context.channel == "get_context_test"
        assert context.channel_user_id == "group_" + user_id
        assert context.data["unixtime"] == date_to_unixtime(now)

        # with detail
        bot.config.confg_parser.set(
            "minette", "context_scope", "channel_detail")
        request = Message(
            text="hello", channel="get_context_test", channel_detail="detail",
            channel_user_id=user_id)
        context = bot._get_context(request, connection)
        assert context.channel == "get_context_test_detail"
        assert context.channel_user_id == user_id
        assert context.data["unixtime"] == date_to_unixtime(now)


def test_save_context():
    bot = Minette(prepare_table=True)
    with bot.connection_provider.get_connection() as connection:
        # register context for test
        ctx = bot.context_store.get(
            channel="save_context_test", channel_user_id=user_id,
            connection=connection)
        ctx.data["unixtime"] = date_to_unixtime(now)

        # save
        ctx.topic.keep_on = True
        bot._save_context(ctx, connection)

        # check
        request = Message(
            text="hello", channel="save_context_test", channel_user_id=user_id)
        context = bot._get_context(request, connection)
        assert context.channel == "save_context_test"
        assert context.channel_user_id == user_id
        assert context.data["unixtime"] == date_to_unixtime(now)


def test_chat():
    bot = Minette(default_dialog_service=MyDialog)
    res = bot.chat("hello")
    assert res.messages[0].text == "res:hello"


def test_chat_error():
    bot = Minette(default_dialog_service=MyDialog)
    bot.connection_provider = None
    res = bot.chat("hello")
    assert res.messages == []


def test_chat_messagelog_error():
    bot = Minette(default_dialog_service=MyDialog)
    bot.messagelog_store = None
    res = bot.chat("hello")
    assert res.messages[0].text == "res:hello"


def test_chat_dialog_error():
    bot = Minette(default_dialog_service=ErrorDialog)
    res = bot.chat("hello")
    assert res.messages[0].text == "?"


def test_chat_timezone():
    bot = Minette(default_dialog_service=MyDialog, timezone=timezone("Asia/Tokyo"))
    res = bot.chat("hello")
    # bot.timezone itself is +9:19
    assert res.messages[0].timestamp.tzinfo == datetime.now(tz=bot.timezone).tzinfo


def test_chat_with_tagger():
    bot = Minette(
        default_dialog_service=TaggerDialog,
        tagger=JanomeTagger)
    res = bot.chat("今日はいい天気です。")
    assert res.messages[0].text == "今日はいい天気です。"
    words = res.messages[0].payloads[0].content
    assert words[0].surface == "今日"
    assert words[1].surface == "は"
    assert words[2].surface == "いい"
    assert words[3].surface == "天気"
    assert words[4].surface == "です"


def test_chat_with_tagger_no_parse():
    bot = Minette(
        default_dialog_service=TaggerDialog,
        tagger=JanomeTagger, tagger_max_length=0)
    assert bot.tagger.max_length == 0
    res = bot.chat("今日はいい天気です。")
    assert res.messages[0].text == "今日はいい天気です。"
    words = res.messages[0].payloads[0].content
    assert words == []


def test_chat_parse_morph_manually():
    bot = Minette(
        default_dialog_service=TaggerManuallyParseDialog,
        tagger=JanomeTagger, tagger_max_length=0)
    bot.dialog_uses(tagger=bot.tagger)
    res = bot.chat("今日はいい天気です。")
    assert res.messages[0].text == "今日はいい天気です。"
    words = res.messages[0].payloads[0].content
    assert words[0].surface == "今日"
    assert words[1].surface == "は"
    assert words[2].surface == "いい"
    assert words[3].surface == "天気"
    assert words[4].surface == "です"


def test_chat_parse_morph_manually_generator():
    bot = Minette(
        default_dialog_service=TaggerManuallyParseGeneratorDialog,
        tagger=JanomeTagger, tagger_max_length=0)
    bot.dialog_uses(tagger=bot.tagger)
    res = bot.chat("今日はいい天気です。")
    assert res.messages[0].text == "今日はいい天気です。"
    assert isinstance(res.messages[0].payloads[0].content, GeneratorType)
    words = [w for w in res.messages[0].payloads[0].content]
    assert words[0].surface == "今日"
    assert words[1].surface == "は"
    assert words[2].surface == "いい"
    assert words[3].surface == "天気"
    assert words[4].surface == "です"


def test_dialog_uses():
    class HighCostToCreate:
        pass

    class OnlyForFooDS:
        pass

    class FooFialog(DialogService):
        pass

    # run once when create bot
    hctc = HighCostToCreate()
    offds = OnlyForFooDS()

    # create bot
    bot = Minette()

    # set dependencies to dialogs
    bot.dialog_uses(
        {
            FooFialog: {"api": offds}
        },
        highcost=hctc
    )

    assert bot.dialog_router.dependencies.highcost == hctc
    assert hasattr(bot.dialog_router.dependencies, "api") is False
    assert bot.dialog_router.dependency_rules[FooFialog]["api"] == offds

    # create bot and not set dialog dependencies
    bot_no_dd = Minette()
    assert bot_no_dd.dialog_router.dependencies is None
    bot_no_dd.dialog_uses()
    assert isinstance(bot_no_dd.dialog_router.dependencies, DependencyContainer)
