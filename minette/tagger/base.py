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

    def __init__(self, config=None, timezone=None, logger=None, **kwargs):
        """
        Parameters
        ----------
        config : Config, default None
            Configuration
        timezone : timezone, default None
            Timezone
        logger : Logger, default None
            Logger
        """
        self.config = config
        self.timezone = timezone
        self.logger = logger or getLogger(__name__)

    def parse(self, text):
        """
        Analyze and parse text

        Parameters
        ----------
        text : str
            Text to analyze

        Returns
        -------
        words : list of minette.WordNode
            Word nodes
        """
        return []
