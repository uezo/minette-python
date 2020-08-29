import traceback
from datetime import datetime, timezone, MAXYEAR
from time import time

from azure.cosmosdb.table.tableservice import TableService
from azure.common import AzureMissingResourceHttpError

from .connectionprovider import ConnectionProvider
from .contextstore import ContextStore
from .userstore import UserStore
from .messagelogstore import MessageLogStore
from .storeset import StoreSet

from ..models import (
    Context,
    Topic,
    User
)

from ..serializer import dumps, loads


class AzureTableConnection(TableService):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, traceback):
        pass


class AzureTableConnectionProvider(ConnectionProvider):
    """
    Connection provider for Azure Table Storage

    Attributes
    ----------
    connection_str : str
        Connection string
    """
    def get_connection(self):
        """
        Get connection

        Returns
        -------
        connection : Connection
            Database connection
        """
        return AzureTableConnection(connection_string=self.connection_str)


class AzureTableContextStore(ContextStore):
    """
    Context store for Azure SQL Database to enable successive conversation

    """
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
        if not connection.exists(self.table_name):
            connection.create_table(self.table_name)
            return True
        else:
            return False

    def get(self, channel, channel_user_id, connection):
        """
        Get context for channel and channel_user_id

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
        context : Context
            Context for channel and channel_user_id
        """
        context = Context(channel, channel_user_id)
        context.timestamp = datetime.now(self.timezone)
        if not channel_user_id:
            return context
        try:
            row = connection.get_entity(self.table_name, channel, channel_user_id)
            if row is not None:
                # convert type
                row["topic_previous"] = loads(row["topic_previous"])
                row["data"] = loads(row["data"])
                # check context timeout. AzureTableStorage always returns timestamp with UTC timezone
                last_access = row["local_timestamp"].astimezone(self.timezone)
                if (datetime.now(self.timezone) - last_access).total_seconds() <= self.timeout:
                    # restore context if not timeout
                    context.topic.name = row["topic_name"]
                    context.topic.status = row["topic_status"]
                    context.topic.priority = row["topic_priority"]
                    context.topic.previous = Topic.from_dict(row["topic_previous"]) if row["topic_previous"] else None
                    context.data = row["data"] if row["data"] else {}
                    context.is_new = False
        except Exception as ex:
            self.logger.error("Error occured in restoring context from database: " + str(ex) + "\n" + traceback.format_exc())
        return context

    def save(self, context, connection):
        """
        Save context

        Parameters
        ----------
        context : Context
            Context to save
        connection : Connection
            Connection
        """
        if not context.channel_user_id:
            return
        # serialize some elements
        context_dict = context.to_dict()
        serialized_previous_topic = dumps(context_dict["topic"]["previous"])
        serialized_data = dumps(context_dict["data"])
        # save
        entity = {
            "PartitionKey": context.channel,
            "RowKey": context.channel_user_id,
            "local_timestamp": context.timestamp,
            "topic_name": context.topic.name,
            "topic_status": context.topic.status,
            "topic_previous": serialized_previous_topic,
            "topic_priority": context.topic.priority,
            "data": serialized_data
        }
        connection.insert_or_replace_entity(self.table_name, entity)


class AzureTableUserStore(UserStore):
    """
    User store for Azure SQL Database

    """
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
        if not connection.exists(self.table_name):
            connection.create_table(self.table_name)
            return True
        else:
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
        user = User(channel=channel, channel_user_id=channel_user_id)
        if not channel_user_id:
            return user
        try:
            row = connection.get_entity(self.table_name, channel, channel_user_id)
            # convert type
            row["data"] = loads(row["data"])
            # restore user
            user.id = row["user_id"]
            user.name = row["name"]
            user.nickname = row["nickname"]
            user.profile_image_url = row["profile_image_url"]
            user.data = row["data"] if row["data"] else {}

        except AzureMissingResourceHttpError as amrherr:
            # add new user if user is not found
            if "ResourceNotFound" in amrherr.args[0]:
                entity = {
                    "PartitionKey": channel,
                    "RowKey": channel_user_id,
                    "local_timestamp": datetime.now(self.timezone),
                    "user_id": user.id,
                    "name": user.name,
                    "nickname": user.nickname,
                    "profile_image_url": user.profile_image_url,
                    "data": dumps({})
                }
                connection.insert_entity(self.table_name, entity)
            else:
                self.logger.error("Resouce is missing on Azure Table: " + str(amrherr) + "\n" + traceback.format_exc())

        except Exception as ex:
            print(ex)
            self.logger.error("Error occured in restoring user from Azure Table: " + str(ex) + "\n" + traceback.format_exc())
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
        user_dict = user.to_dict()
        serialized_data = dumps(user_dict["data"])
        entity = {
            "PartitionKey": user.channel,
            "RowKey": user.channel_user_id,
            "local_timestamp": datetime.now(self.timezone),
            "user_id": user.id,
            "name": user.name,
            "nickname": user.nickname,
            "profile_image_url": user.profile_image_url,
            "data": serialized_data
        }
        connection.insert_or_replace_entity(self.table_name, entity)


class AzureTableMessageLogStore(MessageLogStore):
    """
    Message log store for Azure SQL Database

    """
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
        if not connection.exists(self.table_name):
            connection.create_table(self.table_name)
            return True
        else:
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
        epoch_max = datetime(MAXYEAR, 12, 31, 23, 59, 59, 999999, timezone.utc).timestamp()
        entity = self._flatten(request, response, context)
        entity["PartitionKey"] = request.channel_user_id
        entity["RowKey"] = str(epoch_max - time())
        entity["request_json"] = request.to_json()
        entity["response_json"] = response.to_json()
        entity["context_json"] = context.to_json()
        connection.insert_entity(self.table_name, entity)
        return entity["RowKey"]


class AzureTableStores(StoreSet):
    connection_provider = AzureTableConnectionProvider
    context_store = AzureTableContextStore
    user_store = AzureTableUserStore
    messagelog_store = AzureTableMessageLogStore
