""" Base class for UserStore """
from abc import ABC, abstractmethod
import traceback
from logging import getLogger
from datetime import datetime
from pytz import timezone as tz

from ..serializer import dumps, loads
from ..models import User


class UserStore(ABC):
    """
    Base class for UserStore to read/write user information

    Attributes
    ----------
    config : minette.Config
        Configuration
    timezone : pytz.timezone
        Timezone
    logger : logging.Logger
        Logger
    table_name : str
        Database table name for read/write user data
    sqls : dict
        SQLs used in ContextStore
    """

    def __init__(self, config=None, timezone=None, logger=None,
                 table_name="user", **kwargs):
        """
        Parameters
        ----------
        config : minette.Config, default None
            Configuration
        timezone : pytz.timezone, default None
            Timezone
        logger : logging.Logger, default None
            Logger
        table_name : str, default "user"
            Database table name for read/write user data
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

    def get(self, channel, channel_user_id, connection):
        """
        Get user by channel and channel_user_id

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
        user : minette.User
            User
        """
        user = User(channel=channel, channel_user_id=channel_user_id)
        if not channel_user_id:
            return user
        try:
            cursor = connection.cursor()
            cursor.execute(self.sqls["get_user"], (channel, channel_user_id))
            row = cursor.fetchone()
            if row is not None:
                # convert to dict
                if isinstance(row, dict):
                    record = row
                else:
                    record = dict(
                        zip([column[0] for column in cursor.description], row))
                # convert type
                record["data"] = loads(record["data"])
                # restore user
                user.id = record["user_id"]
                user.name = record["name"]
                user.nickname = record["nickname"]
                user.profile_image_url = record["profile_image_url"]
                user.data = record["data"] if record["data"] else {}
            else:
                cursor.execute(self.sqls["add_user"], (
                    channel, channel_user_id, user.id,
                    datetime.now(self.timezone), user.name, user.nickname,
                    user.profile_image_url, None)
                )
                connection.commit()
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
        user : minette.User
            User to save
        connection : Connection
            Connection
        """
        user_dict = user.to_dict()
        serialized_data = dumps(user_dict["data"])
        cursor = connection.cursor()
        cursor.execute(self.sqls["save_user"], (
            datetime.now(self.timezone), user.name, user.nickname,
            user.profile_image_url, serialized_data, user.channel,
            user.channel_user_id)
        )
        connection.commit()
