""" Base class for MessageLogStore """
from abc import ABC, abstractmethod
from logging import getLogger
from pytz import timezone as tz

from ..serializer import dumps


class MessageLogStore(ABC):
    """
    Base class for MessageLogStore to analyze the communication

    Attributes
    ----------
    config : minette.Config
        Configuration
    timezone : pytz.timezone
        Timezone
    logger : logging.Logger
        Logger
    table_name : str
        Database table name for read/write message log data
    sqls : dict
        SQLs used in ContextStore
    """
    def __init__(self, config=None, timezone=None, logger=None,
                 table_name="messagelog", **kwargs):
        """
        Parameters
        ----------
        config : minette.Config, default None
            Configuration
        timezone : pytz.timezone, default None
            Timezone
        logger : logging.Logger, default None
            Logger
        table_name : str, default "messagelog"
            Database table name for read/write message log data
        """
        self.config = config
        self.timezone = timezone or (
            tz(config.get("timezone", default="UTC")) if config else tz("UTC"))
        self.logger = logger if logger else getLogger(__name__)
        self.table_name = table_name
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
        """
        cursor = connection.cursor()
        cursor.execute(self.sqls["prepare_check"], prepare_params or tuple())
        if not cursor.fetchone():
            cursor.execute(self.sqls["prepare_create"])
            connection.commit()
            return True
        else:
            return False

    def _flatten(self, request, response, context):
        return {
            # request
            "channel": request.channel,
            "channel_detail": request.channel_detail,
            "channel_user_id": request.channel_user_id,
            "request_timestamp": request.timestamp,
            "request_id": request.id,
            "request_type": request.type,
            "request_text": request.text,
            "request_payloads": dumps(
                [p.to_dict() for p in request.payloads]),
            "request_intent": request.intent,
            "request_is_adhoc": request.is_adhoc,
            # response
            "response_type": response.messages[0].type if response.messages else "",
            "response_text": response.messages[0].text if response.messages else "",
            "response_payloads": dumps([p.to_dict() for p in response.messages[0].payloads]) if response.messages else "",
            "response_milliseconds": response.performance.milliseconds,
            # context
            "context_is_new": context.is_new,
            "context_topic_name": context.topic.name,
            "context_topic_status": context.topic.status,
            "context_topic_is_new": context.topic.is_new,
            "context_topic_keep_on": context.topic.keep_on,
            "context_topic_priority": context.topic.priority,
            "context_error": dumps(context.error),
        }

    def save(self, request, response, context, connection):
        """
        Write message log

        Parameters
        ----------
        request : minette.Message
            Request to chatbot
        response : minette.Response
            Response from chatbot
        context : minette.Context
            Context
        connection : Connection
            Connection
        """
        f = self._flatten(request, response, context)
        cursor = connection.cursor()
        cursor.execute(self.sqls["write"], (
            f["channel"],
            f["channel_detail"],
            f["channel_user_id"],
            f["request_timestamp"],
            f["request_id"],
            f["request_type"],
            f["request_text"],
            f["request_payloads"],
            f["request_intent"],
            f["request_is_adhoc"],
            f["response_type"],
            f["response_text"],
            f["response_payloads"],
            f["response_milliseconds"],
            f["context_is_new"],
            f["context_topic_name"],
            f["context_topic_status"],
            f["context_topic_is_new"],
            f["context_topic_keep_on"],
            f["context_topic_priority"],
            f["context_error"],
            request.to_json(),
            response.to_json(),
            context.to_json())
        )
        connection.commit()
