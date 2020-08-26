""" Base class for channel adapters """
from abc import ABC, abstractmethod
import traceback
from logging import Logger
from concurrent.futures import ThreadPoolExecutor

from ..core import Minette


class Adapter(ABC):
    """
    Base class for channel adapters

    Attributes
    ----------
    bot : minette.Minette
        Instance of Minette
    config : minette.Config
        Configuration
    timezone : pytz.timezone
        Timezone
    logger : logging.Logger
        Logger
    threads : int
        Number of worker threads to process requests
    executor : ThreadPoolExecutor
        Thread pool of workers
    debug : bool
        Debug mode
    """

    def __init__(self, bot=None, *, threads=None, debug=False, **kwargs):
        """
        Parameters
        ----------
        bot : minette.Minette, default None
            Instance of Minette.
            If None, create new instance of Minette by using `**kwargs`
        threads : int, default None
            Number of worker threads to process requests
        debug : bool, default None
            Debug mode
        """
        self.bot = bot or Minette(**kwargs)
        self.config = self.bot.config
        self.timezone = self.bot.timezone
        self.logger = self.bot.logger
        self.threads = threads
        if self.threads != 0:
            self.logger.info("Use worker threads to handle events")
            self.executor = ThreadPoolExecutor(
                max_workers=self.threads, thread_name_prefix="AdapterThread")
        else:
            self.logger.info("Use main thread to handle events")
            self.executor = None
        self.debug = debug

    def handle_event(self, event):
        """
        Handle event from channel

        Parameters
        ----------
        event : object
            Event data from channel

        Returns
        -------
        channel_messages : list
            List of messages in channel specific format
        """
        if self.debug:
            self.logger.info(event)
        token = self._extract_token(event)
        message = self._to_minette_message(event)
        response = self.bot.chat(message)
        channel_messages = [
            self._to_channel_message(m) for m in response.messages]
        return channel_messages, token

    def _extract_token(self, event):
        """
        Extract token from event

        Parameters
        ----------
        event : object
            Event data from channel

        Returns
        -------
        token : str or object
            Token data for channel
        """
        return ""

    @staticmethod
    @abstractmethod
    def _to_minette_message(event):
        """
        Convert channel event into internal Message object

        Parameters
        ----------
        event : object
            Event data from channel

        Returns
        -------
        message : minette.Message
            Request message
        """
        pass

    @staticmethod
    @abstractmethod
    def _to_channel_message(message):
        """
        Convert internal Message object into channel formatted message

        Parameters
        ----------
        message : minette.Message
            Response message

        Returns
        -------
        channel_message : object
            Channel formatted message
        """
        pass
