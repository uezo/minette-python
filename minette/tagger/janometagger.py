""" tagger using janome """
import traceback
from minette.tagger import WordNode, Tagger
from janome.tokenizer import Tokenizer


class JanomeNode(WordNode):
    """
    Parsed word by Janome

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
    def __init__(self, token):
        """
        Parameters
        ----------
        surface : str
            Surface of the word
        features : list
            Features analyzed by Janome
        """
        self.surface = token.surface
        ps = token.part_of_speech.split(",")
        self.part = ps[0] if len(ps) > 1 and ps[0] != "*" else ""
        self.part_detail1 = ps[1] if len(ps) > 2 and ps[1] != "*" else ""
        self.part_detail2 = ps[2] if len(ps) > 3 and ps[2] != "*" else ""
        self.part_detail3 = ps[3] if len(ps) > 4 and ps[3] != "*" else ""
        self.stem_type = token.infl_type if token.infl_type != "*" else ""
        self.stem_form = token.infl_form if token.infl_form != "*" else ""
        self.word = token.base_form if token.base_form != "*" else ""
        self.kana = token.reading if token.reading != "*" else ""
        self.pronunciation = token.phonetic if token.phonetic != "*" else ""


class JanomeTagger(Tagger):
    """
    Word tagger using Janome

    Attributes
    ----------
    logger : Logger
        Logger
    config : Config
        Configuration of this chatbot
    timezone : timezone
        Timezone of this chatbot
    """

    def __init__(self, user_dic=None, logger=None, config=None, timezone=None):
        """
        Parameters
        ----------
        user_dic : str, default None
             Path for user dictionary (MeCab IPADIC format)
        logger : Logger, default None
            Logger
        config : Config, default None
            Configuration of this chatbot
        timezone : timezone, default None
            Timezone of this chatbot
        """
        super().__init__(logger=logger, config=config, timezone=timezone)
        self.user_dic = user_dic if user_dic else config.get("janome_userdic")
        if self.user_dic:
            self.tokenizer = Tokenizer(self.user_dic, udic_enc="utf8", mmap=True)
        else:
            self.tokenizer = Tokenizer()

    def parse(self, text):
        """
        Analyze and parse text

        Parameters
        ----------
        text : str
            Text to analyze

        Returns
        -------
        words : [JanomeNode]
            Jaonome word nodes
        """
        ret = []
        if not text:
            return ret
        try:
            for token in self.tokenizer.tokenize(text, stream=True):
                ret.append(JanomeNode(token))
        except Exception as ex:
            self.logger.error("Janome parsing error: " + str(ex) + "\n" + traceback.format_exc())
        return ret
