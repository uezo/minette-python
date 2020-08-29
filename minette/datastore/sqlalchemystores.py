import traceback
from datetime import datetime
from copy import deepcopy

from sqlalchemy import (
    create_engine,
    Column,
    Integer,
    String,
    DateTime,
    Boolean,
    TEXT
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import Session

from .connectionprovider import ConnectionProvider
from .contextstore import ContextStore
from .userstore import UserStore
from .messagelogstore import MessageLogStore
from .storeset import StoreSet

from ..serializer import dumps, loads, Serializable
from ..models import (
    Context,
    Topic,
    User
)

# Base of models
Base = declarative_base()


# Models

class SQLAlchemyContext(Context, Base):
    __tablename__ = "context"
    channel = Column("channel", String(length=20), primary_key=True)
    channel_user_id = Column("channel_user_id", String(length=100), primary_key=True)
    timestamp = Column("timestamp", DateTime)
    topic_name = Column("topic_name", String(length=100))
    topic_status = Column("topic_status", String(length=100))
    topic_previous = Column("topic_previous", String(length=4000))
    topic_priority = Column("topic_priority", Integer)
    data = Column("data", TEXT)


class SQLAlchemyUser(User, Base):
    __tablename__ = "user"
    channel = Column("channel", String(length=20), primary_key=True)
    channel_user_id = Column("channel_user_id", String(length=100), primary_key=True)
    id = Column("user_id", String(length=100))
    timestamp = Column("timestamp", DateTime)
    name = Column("name", String(length=100))
    nickname = Column("nickname", String(length=100))
    profile_image_url = Column("profile_image_url", String(length=500))
    data = Column("data", TEXT)


class SQLAlchemyMessageLog(Serializable, Base):
    __tablename__ = "messagelog"
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    channel = Column("channel", String(length=20))
    channel_detail = Column("channel_detail", String(length=100))
    channel_user_id = Column("channel_user_id", String(length=100))
    request_timestamp = Column("request_timestamp", DateTime)
    request_id = Column("request_id", String(length=100))
    request_type = Column("request_type", String(length=100))
    request_text = Column("request_text", String(length=4000))
    request_payloads = Column("request_payloads", TEXT)
    request_intent = Column("request_intent", String(length=100))
    request_is_adhoc = Column("request_is_adhoc", Boolean)
    response_type = Column("response_type", String(length=100))
    response_text = Column("response_text", String(length=4000))
    response_payloads = Column("response_payloads", TEXT)
    response_milliseconds = Column("response_milliseconds", Integer)
    context_is_new = Column("context_is_new", Boolean)
    context_topic_name = Column("context_topic_name", String(length=100))
    context_topic_status = Column("context_topic_status", String(length=100))
    context_topic_is_new = Column("context_topic_is_new", Boolean)
    context_topic_keep_on = Column("context_topic_keep_on", Boolean)
    context_topic_priority = Column("context_topic_priority", Integer)
    context_error = Column("context_error", TEXT)
    request_json = Column("request_json", TEXT)
    response_json = Column("response_json", TEXT)
    context_json = Column("context_json", TEXT)


# DataStores

class SQLAlchemyConnection(Session):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        self.close()


class SQLAlchemyConnectionProvider(ConnectionProvider):
    def __init__(self, connection_str, db_engine=None, db_echo=True, **kwargs):
        """
        Parameters
        ----------
        connection_str : str
            Connection string
        """
        super().__init__(connection_str)
        self.engine = db_engine or create_engine(self.connection_str, echo=db_echo)

    def get_connection(self):
        """
        Get connection

        Returns
        -------
        connection : Connection
            Database connection
        """
        return SQLAlchemyConnection(
            autocommit=False,
            autoflush=True,
            bind=self.engine)


class SQLAlchemyContextStore(ContextStore):
    """
    Context store for SQLAlchemy to enable successive conversation

    """
    def __init__(self, config=None, timezone=None, logger=None,
                 table_name="context", *, timeout=300, **kwargs):
        super().__init__(config, timezone, logger, table_name,
                 timeout=timeout, **kwargs)
        SQLAlchemyContext.__table__.name = self.table_name

    def get_sqls(self):
        """
        Use api instead.

        """
        return {}

    def prepare_table(self, connection, prepare_params=None):
        """
        Check and create table if not exist

        Parameters
        ----------
        connection : Connection
            Connection for prepare

        query_params : tuple, default tuple()
            Query parameters for checking table

        Returns
        -------
        created : bool
            Return True when created new table
        """
        Base.metadata.create_all(bind=connection.bind, tables=[SQLAlchemyContext.__table__])
        # Always return `False` because the result can't be handled
        return False

    def get(self, channel, channel_user_id, connection):
        """
        Get context by channel and channel_user_id

        Parameters
        ----------
        channel : str
            Channel
        channel_user_id : str
            Channel user ID
        connection : Connection
            Connection

        Returns
        -------
        context : minette.Context
            Context for channel and channel_user_id
        """

        # Create new instance and map stored values to assure that constructor is always called

        context = SQLAlchemyContext(channel, channel_user_id)
        context.timestamp = datetime.now(self.timezone)

        if not channel_user_id:
            return context

        try:
            stored_context = connection.query(SQLAlchemyContext).filter(SQLAlchemyContext.channel==channel, SQLAlchemyContext.channel_user_id==channel_user_id).first()
            if stored_context is not None:
                # check context timeout
                if stored_context.timestamp.tzinfo:
                    last_access = stored_context.timestamp.astimezone(self.timezone)
                else:
                    last_access = self.timezone.localize(stored_context.timestamp)

                gap = datetime.now(self.timezone) - last_access
                if gap.total_seconds() <= self.timeout:
                    # restore context if not timeout
                    context.topic.name = stored_context.topic_name
                    context.topic.status = stored_context.topic_status
                    context.topic.priority = stored_context.topic_priority
                    context.topic.previous = Topic.from_json(
                        stored_context.topic_previous) \
                        if stored_context.topic_previous else None
                    context.data = loads(stored_context.data) \
                        if stored_context.data else {}
                    context.is_new = False

        except Exception as ex:
            self.logger.error(
                "Error occured in restoring context from database: "
                + str(ex) + "\n" + traceback.format_exc())

        return context

    def save(self, context, connection):
        """
        Save context

        Parameters
        ----------
        context : SQLAlchemyContext
            Context to save
        connection : Session
            Connection
        """
        if not context.channel_user_id:
            return

        # copy and serialize values to store
        context_to_store = deepcopy(context)
        context_to_store.topic_name = context_to_store.topic.name
        context_to_store.topic_status = context_to_store.topic.status
        context_to_store.topic_previous = dumps(context_to_store.topic.previous)
        context_to_store.topic_priority = context_to_store.topic.priority
        context_to_store.data = dumps(context_to_store.data)

        # save
        connection.merge(instance=context_to_store)
        connection.commit()


class SQLAlchemyUserStore(UserStore):
    """
    User store for SQLAlchemy

    """
    def __init__(self, config=None, timezone=None, logger=None,
                 table_name="user", **kwargs):
        super().__init__(config, timezone, logger, table_name, **kwargs)
        SQLAlchemyUser.__table__.name = self.table_name

    def get_sqls(self):
        """
        Use api instead.

        """
        return {}

    def prepare_table(self, connection, query_params=None):
        """
        Check and create table if not exist

        Parameters
        ----------
        connection : Connection
            Connection for prepare

        query_params : tuple, default None
            Query parameters for checking table

        Returns
        -------
        created : bool
            Return True when created new table
        """
        Base.metadata.create_all(bind=connection.bind, tables=[SQLAlchemyUser.__table__])
        # Always return `False` because the result can't be handled
        return False

    def get(self, channel, channel_user_id, connection):
        """
        Get user from repository by channel and channel_user_id

        Parameters
        ----------
        channel : str
            Channel
        channel_user_id : str
            Channel user ID
        connection : Connection
            Connection

        Returns
        -------
        user : User
            User
        """

        # Create new instance and map stored values to assure that constructor is always called

        user = SQLAlchemyUser(channel=channel, channel_user_id=channel_user_id)

        if not channel_user_id:
            return user

        try:
            stored_user = connection.query(SQLAlchemyUser).filter(SQLAlchemyUser.channel==channel, SQLAlchemyUser.channel_user_id==channel_user_id).first()

            if stored_user is not None:
                user.id = stored_user.id
                user.name = stored_user.name
                user.nickname = stored_user.nickname
                user.profile_image_url = stored_user.profile_image_url
                user.data = loads(stored_user.data) if stored_user.data else {}

            else:
                self.save(user, connection)

        except Exception as ex:
            self.logger.error(
                "Error occured in restoring user from database: "
                + str(ex) + "\n" + traceback.format_exc())

        return user

    def save(self, user, connection):
        """
        Save user

        Parameters
        ----------
        user : User
            User to save
        connection : Connection
            Connection
        """
        # copy and serialize values to store
        user_to_store = deepcopy(user)
        user_to_store.timestamp = datetime.now(self.timezone)
        user_to_store.data = dumps(user_to_store.data)

        # save
        connection.merge(instance=user_to_store)
        connection.commit()


class SQLAlchemyMessageLogStore(MessageLogStore):
    """
    Message log store for Azure SQL Database

    """
    def __init__(self, config=None, timezone=None, logger=None,
                 table_name="messagelog", **kwargs):
        super().__init__(config, timezone, logger, table_name, **kwargs)
        SQLAlchemyMessageLog.__table__.name = self.table_name

    def get_sqls(self):
        """
        Use api instead.

        """
        return {}

    def prepare_table(self, connection, query_params=None):
        """
        Check and create table if not exist

        Parameters
        ----------
        connection : Connection
            Connection for prepare

        query_params : tuple, default None
            Query parameters for checking table
        """
        Base.metadata.create_all(bind=connection.bind, tables=[SQLAlchemyMessageLog.__table__])
        # Always return `False` because the result can't be handled
        return False

    def save(self, request, response, context, connection):
        """
        Write message log

        Parameters
        ----------
        request : Message
            Request message
        response : Response
            Response from chatbot
        context : Context
            Context
        total_ms : int
            Response time (milliseconds)
        connection : Connection
            Connection
        """
        f = self._flatten(request, response, context)
        messagelog = SQLAlchemyMessageLog.from_dict(f)
        messagelog.request_json = request.to_json()
        messagelog.response_json = response.to_json()
        messagelog.context_json = context.to_json()
        connection.add(instance=messagelog)
        connection.commit()


class SQLAlchemyStores(StoreSet):
    connection_provider = SQLAlchemyConnectionProvider
    context_store = SQLAlchemyContextStore
    user_store = SQLAlchemyUserStore
    messagelog_store = SQLAlchemyMessageLogStore
