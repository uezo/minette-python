""" tagger using mecab """
import traceback
import MeCab
from minette.tagger import WordNode, Tagger

class MeCabNode(WordNode):
    def __init__(self, features):
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
    def parse(self, text):
        """
        :param text: Text to analyze
        :type text: str
        :return: MeCabNodes
        :rtype: [MeCabNode]
        """
        ret = []
        if text == "":
            return ret
        try:
            m = MeCab.Tagger("-Ochasen")
            m.parse("") #m.parse("") before m.parseToNode(text) against the bug that node.surface is not set
            node = m.parseToNode(text)
            while node:
                features = node.feature.split(",")
                if features[0] != "BOS/EOS":
                    ret.append(MeCabNode(features))
                node = node.next
        except Exception as ex:
            self.logger.error("MeCab parsing error: " + str(ex) + "\n" + traceback.format_exc())
        return ret
