from ..serializer import Serializable
from .performance import PerformanceInfo
from .message import Message


class Response(Serializable):
    """
    Response from chatbot

    Attributes
    ----------
    messages : list of minette.Message
        Response messages
    headers : dict
        Response header
    performance : minette.PerformanceInfo
        Performance information of each steps in chat()
    """
    def __init__(self, messages=None, headers=None, performance=None):
        """
        Parameters
        ----------
        messages : list of minette.Message, default None
            Response messages. If None, `[]` is set to `messages`.
        headers : dict, default None
            Response headers. If None, `{}` is set to `headers`
        performance : minette.PerformanceInfo, default None
            Performance information of each steps in chat().
            If None, create new PerformanceInfo object.
        """
        self.messages = messages or []
        self.headers = headers or {}
        self.performance = performance or PerformanceInfo()

    @classmethod
    def _types(cls):
        return {
            "messages": Message,
            "performance": PerformanceInfo
        }
