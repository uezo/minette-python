""" WordNode datamodel and base class of Tagger(do nothing) """
from logging import getLogger
from minette.serializer import JsonSerializable


class WordNode(JsonSerializable):
    """
    Base class of parsed word

    Attributes
    ----------
    part : str
        Part of the word
    part_detail1 : str
        Detail1 of part
    part_detail2 : str
        Detail2 of part
    part_detail3 : str
        Detail3 of part
    stem_type : str
        Stem type
    stem_form : str
        Stem form
    word : str
        Word itself
    kana : str
        Japanese kana of the word
    pronunciation : str
        Pronunciation of the word
    """
    def __init__(self):
        self.part = ""
        self.part_detail1 = ""
        self.part_detail2 = ""
        self.part_detail3 = ""
        self.stem_type = ""
        self.stem_form = ""
        self.word = ""
        self.kana = ""
        self.pronunciation = ""


class Tagger:
    """
    Base class of word tagger

    Attributes
    ----------
    logger : Logger
        Logger
    config : Config
        Configuration of this chatbot
    timezone : timezone
        Timezone of this chatbot
    """

    def __init__(self, logger=None, config=None, timezone=None):
        """
        Parameters
        ----------
        logger : Logger, default None
            Logger
        config : Config, default None
            Configuration of this chatbot
        timezone : timezone, default None
            Timezone of this chatbot
        """
        self.logger = logger if logger else getLogger(__name__)
        self.config = config
        self.timezone = timezone

    def parse(self, text):
        """
        Analyze and parse text

        Parameters
        ----------
        text : str
            Text to analyze

        Returns
        -------
        words : [WordNode]
            Word nodes
        """
        return []
