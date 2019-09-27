""" Tagger using mecab-service """
import traceback
import requests

from ..models import WordNode
from .base import Tagger


class MeCabServiceNode(WordNode):
    """
    Parsed word node by MeCabServiceTagger

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
        Create instance of MeCabServiceNode

        Parameters
        ----------
        surface : str
            Surface of the word
        features : dict
            Features analyzed by MeCabService
        """
        return cls(
            surface=surface,
            part=features["part"],
            part_detail1=features["part_detail1"],
            part_detail2=features["part_detail2"],
            part_detail3=features["part_detail3"],
            stem_type=features["stem_type"],
            stem_form=features["stem_form"],
            word=features["word"],
            kana=features["kana"],
            pronunciation=features["pronunciation"]
        )


class MeCabServiceTagger(Tagger):
    """
    Tagger using mecab-service

    Attributes
    ----------
    config : minette.Config
        Configuration
    timezone : pytz.timezone
        Timezone
    logger : logging.Logger
        Logger
    api_url : str
        URL for MeCabService API
    """

    def __init__(self, config=None, timezone=None, logger=None, *,
                 api_url=None, **kwargs):
        """
        Parameters
        ----------
        config : Config, default None
            Configuration
        timezone : timezone, default None
            Timezone
        logger : Logger, default None
            Logger
        api_url : str, default None
            URL for MeCabService API.
            If None trial URL is used.
        """
        super().__init__(config=config, timezone=timezone, logger=logger)
        if not api_url:
            self.api_url = "https://api.uezo.net/mecab/parse"
            self.logger.warning(
                "Do not use default API URL for the production environment. "
                "This is for trial use only. "
                "Install MeCab and use MeCabTagger instead.")
        else:
            self.api_url = api_url

    def parse(self, text):
        """
        Parse and annotate using MeCab Service

        Parameters
        ----------
        text : str
            Text to analyze

        Returns
        -------
        words : list of minette.MeCabServiceNode
            MeCabService nodes
        """
        ret = []
        if not text:
            return ret
        try:
            parsed_json = requests.post(
                self.api_url, headers={"content-type": "application/json"},
                json={"text": text}, timeout=10).json()
            ret = [MeCabServiceNode.create(
                n["surface"], n["features"]) for n in parsed_json["nodes"]]
        except Exception as ex:
            self.logger.error(
                "MeCab Service parsing error: "
                + str(ex) + "\n" + traceback.format_exc())
        return ret
