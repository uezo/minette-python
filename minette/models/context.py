import traceback
from copy import deepcopy

from ..serializer import Serializable
from .priority import Priority
from .topic import Topic


class Context(Serializable):
    """
    Context

    Attributes
    ----------
    channel : str
        Channel
    channel_user_id : str
        Channel user ID
    timestamp : datetime
        Timestamp
    is_new : bool
        True if context is created at this turn
    topic : Topic
        Current topic
    data : dict
        Data slots
    error : dict
        Error info
    """
    def __init__(self, channel=None, channel_user_id=None):
        """
        Parameters
        ----------
        channel : str, default None
            Channel
        channel_user_id : str, default None
            Channel user ID
        """
        self.channel = channel
        self.channel_user_id = \
            channel_user_id if isinstance(channel_user_id, str) else ""
        self.timestamp = None
        self.is_new = True
        self.topic = Topic()
        self.data = {}
        self.error = {}

    def reset(self, keep_data=False):
        """
        Backup to previous topic and remove data

        Parameters
        ----------
        keep_data : bool, default False
            Keep context data to next turn
        """
        # backup previous topic
        self.topic.previous = None
        self.topic.previous = deepcopy(self.topic)
        # remove data if topic not keep_on
        if not self.topic.keep_on:
            self.topic.name = ""
            self.topic.status = ""
            self.topic.priority = Priority.Normal
            self.data = self.data if keep_data else {}
            self.error = {}

    def set_error(self, ex, info=None):
        """
        Set error info

        Parameters
        ----------
        ex : Exception
            Exception
        info : dict, default None
            More information for debugging
        """
        self.error = {
            "exception": str(ex),
            "traceback": traceback.format_exc(),
            "info": info if info else {}}

    @classmethod
    def _types(cls):
        return {
            "topic": Topic
        }
