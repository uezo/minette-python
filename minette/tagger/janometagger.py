""" tagger using janome """
import traceback
from janome.tokenizer import Tokenizer

from ..models import WordNode
from .base import Tagger


class JanomeNode(WordNode):
    """
    Parsed word node by Janome

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
        Create instance of JanomeNode

        Parameters
        ----------
        surface : str
            Surface of the word
        features : janome.Token
            Features analyzed by Janome
        """
        ps = features.part_of_speech.split(",")
        return cls(
            surface=surface,
            part=ps[0] if len(ps) > 1 and ps[0] != "*" else "",
            part_detail1=ps[1] if len(ps) > 2 and ps[1] != "*" else "",
            part_detail2=ps[2] if len(ps) > 3 and ps[2] != "*" else "",
            part_detail3=ps[3] if len(ps) > 4 and ps[3] != "*" else "",
            stem_type=features.infl_type if features.infl_type != "*" else "",
            stem_form=features.infl_form if features.infl_form != "*" else "",
            word=features.base_form if features.base_form != "*" else "",
            kana=features.reading if features.reading != "*" else "",
            pronunciation=features.phonetic if features.phonetic != "*" else ""
        )


class JanomeTagger(Tagger):
    """
    Tagger using Janome

    Attributes
    ----------
    config : minette.Config
        Configuration
    timezone : pytz.timezone
        Timezone
    logger : logging.Logger
        Logger
    """

    def __init__(self, config=None, timezone=None, logger=None, *,
                 max_length=Tagger.MAX_LENGTH, user_dic=None, **kwargs):
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
        user_dic : str, default None
             Path to user dictionary (MeCab IPADIC format)
        """
        super().__init__(logger=logger, config=config, timezone=timezone, max_length=max_length)
        self.user_dic = user_dic or config.get("janome_userdic") if config else None
        if self.user_dic:
            self.tokenizer = Tokenizer(self.user_dic, udic_enc="utf8")
        else:
            self.tokenizer = Tokenizer()

    def parse_as_generator(self, text, max_length=None):
        """
        Parse and annotate using Janome, returns Generator

        Parameters
        ----------
        text : str
            Text to analyze
        max_length : int, default 1000
            Max length of the text to parse

        Returns
        -------
        words : Generator of minette.minette.tagger.janometagger.JanomeNode
            Janome nodes
        """
        if self.validate(text, max_length) is False:
            return

        try:
            for token in self.tokenizer.tokenize(text):
                yield JanomeNode.create(token.surface, token)
        except Exception as ex:
            self.logger.error(
                "Janome parsing error: "
                + str(ex) + "\n" + traceback.format_exc())
