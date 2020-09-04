""" tagger using mecab """
import traceback
import MeCab

from ..models import WordNode
from .base import Tagger


class MeCabNode(WordNode):
    """
    Parsed word node by MeCab

    Attributes
    ----------
    surface : str
        Surface of word
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

    @classmethod
    def create(cls, surface, features):
        """
        Create instance of MeCabNode

        Parameters
        ----------
        surface : str
            Surface of the word
        features : list
            Features analyzed by MeCab
        """
        return cls(
            surface=surface,
            part=features[0] if features[0] != "*" else "",
            part_detail1=features[1] if features[1] != "*" else "",
            part_detail2=features[2] if features[2] != "*" else "",
            part_detail3=features[3] if features[3] != "*" else "",
            stem_type=features[4] if features[4] != "*" else "",
            stem_form=features[5] if features[5] != "*" else "",
            word=features[6] if features[6] != "*" else "",
            kana=features[7] if len(features) > 7 else "",
            pronunciation=features[8] if len(features) > 8 else ""
        )


class MeCabTagger(Tagger):
    """
    Tagger using MeCab

    Attributes
    ----------
    config : minette.Config
        Configuration
    timezone : pytz.timezone
        Timezone
    logger : logging.Logger
        Logger
    """

    def parse_as_generator(self, text, max_length=None):
        """
        Analyze and parse text using MeCab, returns Generator

        Parameters
        ----------
        text : str
            Text to analyze
        max_length : int, default 1000
            Max length of the text to parse

        Returns
        -------
        words : list of minette.tagger.mecabtagger.MeCabNode
            MeCab word nodes
        """
        if self.validate(text, max_length) is False:
            return

        try:
            m = MeCab.Tagger("-Ochasen")
            # m.parse("") before m.parseToNode(text) against the bug that node.surface is not set
            m.parse("")
            node = m.parseToNode(text)
            while node:
                features = node.feature.split(",")
                if features[0] != "BOS/EOS":
                    yield MeCabNode.create(node.surface, features)
                node = node.next
        except Exception as ex:
            self.logger.error(
                "MeCab parsing error: "
                + str(ex) + "\n" + traceback.format_exc())
