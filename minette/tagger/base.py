""" Base for Taggers """
from logging import getLogger


class Tagger:
    """
    Base class for word taggers

    Attributes
    ----------
    config : minette.Config
        Configuration
    timezone : pytz.timezone
        Timezone
    logger : logging.Logger
        Logger
    """
    MAX_LENGTH = 1000

    def __init__(self, config=None, timezone=None, logger=None, *,
                 max_length=MAX_LENGTH, **kwargs):
        """
        Parameters
        ----------
        config : Config, default None
            Configuration
        timezone : timezone, default None
            Timezone
        logger : Logger, default None
            Logger
        max_length : int, default 1000
            Max length of the text to parse
        """
        self.config = config
        self.timezone = timezone
        self.logger = logger or getLogger(__name__)
        self.max_length = max_length

    def validate(self, text, max_length=None):
        if not text:
            return False
        elif max_length is not None:
            if len(text) > max_length:
                return False
        elif len(text) > self.max_length:
            return False

        return True

    def parse_as_generator(self, text, max_length=None):
        """
        Analyze and parse text, returns Generator

        Parameters
        ----------
        text : str
            Text to analyze
        max_length : int, default None
            Max length of the text to parse

        Returns
        -------
        words : Generator of minette.WordNode (empty)
            Word nodes
        """
        yield from ()

    def parse(self, text, max_length=None):
        """
        Analyze and parse text

        Parameters
        ----------
        text : str
            Text to analyze
        max_length : int, default None
            Max length of the text to parse

        Returns
        -------
        words : list of minette.WordNode (empty)
            Word nodes
        """
        return [wn for wn in self.parse_as_generator(text, max_length)]
