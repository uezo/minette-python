from uuid import uuid4
from ..serializer import Serializable


class User(Serializable):
    """
    User

    Attributes
    ----------
    id : str
        User ID
    name : str
        User name
    nickname : str
        Nickname
    channel : str
        Channel
    channel_user_id : str
        Channel user ID
    data : dict
        User data
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
        self.id = str(uuid4())
        self.name = ""
        self.nickname = ""
        self.channel = channel
        self.channel_user_id = \
            channel_user_id if isinstance(channel_user_id, str) else ""
        self.profile_image_url = ""
        self.data = {}
