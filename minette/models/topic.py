from ..serializer import Serializable
from .priority import Priority


class Topic(Serializable):
    """
    Topic

    Attributes
    ----------
    name : str
        Name of topic
    status : str
        Status of topic
    is_new : bool
        True if topic starts at this turn
    keep_on : bool
        True to keep this topic at next turn
    previous : minette.Topic
        Previous topic object
    priority : int
        Priority of topic
    is_changed : bool
        True if topic is changed at this turn
    """
    def __init__(self):
        self.name = ""
        self.status = ""
        self.is_new = False
        self.keep_on = False
        self.previous = None
        self.priority = Priority.Normal

    @property
    def is_changed(self):
        if self.previous and self.previous.name == self.name:
            return False
        else:
            return True
