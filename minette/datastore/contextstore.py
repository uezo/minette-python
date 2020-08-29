""" Base class for ContextStore """
from abc import ABC, abstractmethod
import traceback
from logging import getLogger
from datetime import datetime
from pytz import timezone as tz

from ..serializer import dumps, loads
from ..models import Context, Topic


class ContextStore(ABC):
    """
    Base class for ContextStore to enable successive conversation

    Attributes
    ----------
    config : minette.Config
        Configuration
    timezone : pytz.timezone
        Timezone
    logger : logging.Logger
        Logger
    table_name : str
        Database table name for read/write context data
    sqls : dict
        SQLs used in ContextStore
    timeout : int
        Context timeout (Seconds)
    """

    def __init__(self, config=None, timezone=None, logger=None,
                 table_name="context", *, timeout=300, **kwargs):
        """
        Parameters
        ----------
        config : minette.Config, default None
            Configuration
        timezone : pytz.timezone, default None
            Timezone
        logger : logging.Logger, default None
            Logger
        table_name : str, default "context"
            Database table name for read/write context data
        timeout : int, default 300
            Context timeout (Seconds)
        """
        self.config = config
        self.timezone = timezone or (
            tz(config.get("timezone", default="UTC")) if config else tz("UTC"))
        self.logger = logger if logger else getLogger(__name__)
        self.table_name = table_name
        self.timeout = timeout
        self.sqls = self.get_sqls()

    @abstractmethod
    def get_sqls(self):
        pass

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
        cursor = connection.cursor()
        cursor.execute(self.sqls["prepare_check"], prepare_params or tuple())
        if not cursor.fetchone():
            cursor.execute(self.sqls["prepare_create"])
            connection.commit()
            return True
        else:
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
        context = Context(channel, channel_user_id)
        context.timestamp = datetime.now(self.timezone)
        if not channel_user_id:
            return context
        try:
            cursor = connection.cursor()
            cursor.execute(
                self.sqls["get_context"], (channel, channel_user_id))
            row = cursor.fetchone()
            if row is not None:
                # convert to dict
                if isinstance(row, dict):
                    record = row
                else:
                    record = dict(
                        zip([column[0] for column in cursor.description], row))
                # convert type
                record["topic_previous"] = \
                    loads(record["topic_previous"])
                record["data"] = loads(record["data"])
                # check context timeout
                if record["timestamp"].tzinfo:
                    last_access = record["timestamp"].astimezone(self.timezone)
                else:
                    last_access = self.timezone.localize(record["timestamp"])
                gap = datetime.now(self.timezone) - last_access
                if gap.total_seconds() <= self.timeout:
                    # restore context if not timeout
                    context.topic.name = record["topic_name"]
                    context.topic.status = record["topic_status"]
                    context.topic.priority = record["topic_priority"]
                    context.topic.previous = Topic.from_dict(
                        record["topic_previous"]) \
                        if record["topic_previous"] else None
                    context.data = record["data"] if record["data"] else {}
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
        context : minette.Context
            Context to save
        connection : Connection
            Connection
        """
        if not context.channel_user_id:
            return
        # serialize some elements
        context_dict = context.to_dict()
        serialized_previous_topic = \
            dumps(context_dict["topic"]["previous"])
        serialized_data = dumps(context_dict["data"])
        # save
        cursor = connection.cursor()
        cursor.execute(self.sqls["save_context"], (
            context.channel, context.channel_user_id, context.timestamp,
            context.topic.name, context.topic.status,
            serialized_previous_topic, context.topic.priority,
            serialized_data))
        connection.commit()
