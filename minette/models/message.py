from datetime import datetime
from pytz import timezone as tz
from copy import copy

from ..serializer import Serializable
from .payload import Payload
from .priority import Priority
from .user import User


class Message(Serializable):
    """
    Message

    Attributes
    ----------
    id : str
        Message ID
    type : str
        Message type
    timestamp : datetime
        Timestamp
    channel : str
        Channel
    channel_detail : str
        Detail information of channel
    channel_user_id : str
        User ID for channel
    channel_message : Any
        Original message from channel
    token : Any
        Token to do actions to the channel
    user : User
        User
    group : Group
        Group
    text : str
        Body of message
    words : list of minette.WordNode
        Word nodes parsed by tagger
    payloads : list of minette.Payload
        Payloads
    intent : str
        Intent extracted from message
    intent_priority : int
        Priority for processing intent
    entities : dict
        Entities extracted from message
    is_adhoc : bool
        Process adhoc or not
    """
    def __init__(self, id=None, type="text", channel="console",
                 channel_detail=None, channel_user_id="anonymous",
                 timestamp=None, channel_message=None, token=None,
                 user=None, group=None, text=None, payloads=None, intent=None,
                 intent_priority=None, entities=None, is_adhoc=False):
        """
        Parameters
        ----------
        id : str, default None
            Message ID
        type : str default "text"
            Message type
        channel : str, default "console"
            Channel
        channel_detail : str, default None
            Detail information of channel
        channel_user_id : str, default "anonymous"
            User ID for channel
        channel_message : Any, default None
            Original message from channel
        token : Any, default None
            Token to do actions to the channel
        text : str, default None
            Body of message
        payloads : list of minette.Payload, default None
            Payloads
        """
        self.id = id or ""
        self.type = type
        self.timestamp = timestamp or datetime.now(tz("UTC"))
        self.channel = channel
        self.channel_detail = channel_detail or ""
        self.channel_user_id = channel_user_id
        self.channel_message = channel_message
        self.token = token or ""
        self.user = user
        self.group = group
        self.text = text or ""
        self.words = []
        self.payloads = payloads or []
        self.intent = intent or ""
        self.intent_priority = intent_priority or Priority.Normal
        self.entities = entities or {}
        self.is_adhoc = is_adhoc

    def to_reply(self, text=None, payloads=None, type="text"):
        """
        Get reply message for this message

        Parameters
        ----------
        text : str, default None
            Body of reply message
        payloads : list of minette.Payload, default None
            Payloads
        type : str default "text"
            Message type

        Returns
        -------
        reply_message : minette.Message
            Reply message for this message
        """
        message = copy(self)
        message.timestamp = datetime.now(message.timestamp.tzinfo)
        message.channel_message = None
        message.type = type
        message.text = text
        message.words = []
        message.payloads = payloads if payloads else []
        message.intent = ""
        message.entities = {}
        message.is_adhoc = False
        return message

    def reply(self, text=None, payloads=None, type="text"):
        print("WARNING: `reply` is deprecated and will be deleted at version 0.5. Use `to_reply` instead.")
        return self.to_reply(text=text, payloads=payloads, type=type)

    def to_dict(self):
        """
        Convert Message object to dict

        Returns
        -------
        message_dict : dict
            Message dictionary
        """
        message_dict = super().to_dict()
        # channel_message is not JSON serializable
        message_dict["channel_message"] = str(message_dict["channel_message"])
        return message_dict

    @classmethod
    def _types(cls):
        return {
            "user": User,
            "payloads": Payload
        }
