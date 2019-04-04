""" tagger using mecab-service """
import requests
import traceback
from minette.tagger import WordNode, Tagger


class MeCabServiceNode(WordNode):
    """
    Parsed word by MeCabServiceNode

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
    def __init__(self, node):
        """
        Parameters
        ----------
        node : dict
            Nodes analyzed by MeCabService
        """
        self.surface = node["surface"]
        self.part = node["part"]
        self.part_detail1 = node["part_detail1"]
        self.part_detail2 = node["part_detail2"]
        self.part_detail3 = node["part_detail3"]
        self.stem_type = node["stem_type"]
        self.stem_form = node["stem_form"]
        self.word = node["word"]
        self.kana = node["kana"]
        self.pronunciation = node["pronunciation"]


class MeCabServiceTagger(Tagger):
    def __init__(self, logger=None, config=None, timezone=None):
        super().__init__(logger=logger, config=config, timezone=timezone)
        self.api_url = "https://api.uezo.net/mecab/parse"
        self.logger.warn("Do not use MeCabService tagger for the production environment. This is for trial use only. Install MeCab and use MeCabTagger instead.")

    def parse(self, text):
        """
        Parse and annotate using MeCab Service

        Parameters
        ----------
        text : str
            Text to analyze

        Returns
        -------
        words : [MeCabServiceNode]
            MeCabService nodes
        """
        ret = []
        if not text:
            return ret
        try:
            parsed_json = requests.post(self.api_url, headers={"content-type": "application/json"}, json={"text": text}).json()
            ret = [MeCabServiceNode(w) for w in parsed_json["words"]]
        except Exception as ex:
            self.logger.error("MeCab Service parsing error: " + str(ex) + "\n" + traceback.format_exc())
        return ret
