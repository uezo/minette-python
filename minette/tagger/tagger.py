""" WordNode datamodel and base class of Tagger(do nothing) """
import logging
from minette.serializer import JsonSerializable

class WordNode(JsonSerializable):
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
    def __init__(self, logger=None, config=None, tzone=None):
        """
        :param logger: Logger
        :type logger: logging.Logger
        :param config: Config
        :type config: Config
        :param tzone: Timezone
        :type tzone: timezone
        """
        self.logger = logger if logger else logging.getLogger(__name__)
        self.config = config
        self.timezone = tzone

    def parse(self, text):
        """
        :param text: Text to analyze
        :type text: str
        :return: Word nodes
        :rtype: [WordNode]
        """
        return []
