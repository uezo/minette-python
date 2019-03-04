""" tagger using mecab """
import traceback
import MeCab
from minette.tagger import WordNode, Tagger


class MeCabNode(WordNode):
    """
    Parsed word by MeCab

    Attributes
    ----------
    surface : str
        Surface of the word
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
    def __init__(self, surface, features):
        """
        Parameters
        ----------
        surface : str
            Surface of the word
        features : list
            Features analyzed by MeCab
        """
        self.surface = surface
        self.part = features[0] if features[0] != "*" else ""
        self.part_detail1 = features[1] if features[1] != "*" else ""
        self.part_detail2 = features[2] if features[2] != "*" else ""
        self.part_detail3 = features[3] if features[3] != "*" else ""
        self.stem_type = features[4] if features[4] != "*" else ""
        self.stem_form = features[5] if features[5] != "*" else ""
        self.word = features[6] if features[6] != "*" else ""
        self.kana = features[7] if len(features) > 7 else ""
        self.pronunciation = features[8] if len(features) > 8 else ""


class MeCabTagger(Tagger):
    """
    Word tagger using MeCab

    Attributes
    ----------
    logger : Logger
        Logger
    config : Config
        Configuration of this chatbot
    timezone : timezone
        Timezone of this chatbot
    """

    def parse(self, text):
        """
        Analyze and parse text

        Parameters
        ----------
        text : str
            Text to analyze

        Returns
        -------
        words : [MeCabNode]
            MeCab word nodes
        """
        ret = []
        if not text:
            return ret
        try:
            m = MeCab.Tagger("-Ochasen")
            # m.parse("") before m.parseToNode(text) against the bug that node.surface is not set
            m.parse("")
            node = m.parseToNode(text)
            while node:
                features = node.feature.split(",")
                if features[0] != "BOS/EOS":
                    ret.append(MeCabNode(node.surface, features))
                node = node.next
        except Exception as ex:
            self.logger.error("MeCab parsing error: " + str(ex) + "\n" + traceback.format_exc())
        return ret
