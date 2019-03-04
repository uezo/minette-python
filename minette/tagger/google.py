""" tagger using Google Cloud Natural Languege API """
import traceback
import requests
from minette.tagger import WordNode, Tagger


class GoogleNode(WordNode):
    """
    Parsed word by Google

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
    def __init__(self, token):
        """
        Parameters
        ----------
        token : dict
            Result of each words by Google Cloud Natural Language API
        """
        super().__init__()
        self.word = token["text"]["content"]
        self.part = token["partOfSpeech"]["tag"]


class GoogleTagger(Tagger):
    """
    Word tagger using Google Cloud Natural Language API

    Attributes
    ----------
    api_key : str
            API Key for Google Cloud Natural Language API
    logger : Logger
        Logger
    config : Config
        Configuration of this chatbot
    timezone : timezone
        Timezone of this chatbot
    """

    def __init__(self, api_key=None, logger=None, config=None, timezone=None):
        """
        Parameters
        ----------
        api_key : str, default None
             API Key for Google Cloud Natural Language API
        logger : Logger, default None
            Logger
        config : Config, default None
            Configuration of this chatbot
        timezone : timezone, default None
            Timezone of this chatbot
        """
        super().__init__(logger=logger, config=config, timezone=timezone)
        self.api_key = api_key
        if not api_key and config:
            self.api_key = config.get("googletagger_api_key")

    def parse(self, text, lang="en"):
        """
        Analyze and parse text

        Parameters
        ----------
        text : str
            Text to analyze
        lang : str
            Language of text to analyze

        Returns
        -------
        words : [GoogleNode]
            Google word nodes
        """
        ret = []
        if not text:
            return ret
        try:
            parsed_json = self._get_entities_json(text, lang)
            for node in parsed_json["tokens"]:
                ret.append(GoogleNode(node))
        except Exception as ex:
            self.logger.error("Google parsing error: " + str(ex) + "\n" + traceback.format_exc())
        return ret

    def _get_entities_json(self, text, lang):
        """
        Call Google API

        Parameters
        ----------
        text : str
            Text to analyze
        lang : str
            Language of text to analyze

        Returns
        -------
        parsed_json : dict
            Response from Google as JSON
        """
        url = "https://language.googleapis.com/v1/documents:analyzeSyntax?key={}".format(self.api_key)
        header = {"Content-Type": "application/json"}
        body = {
            "document": {
                "type": "PLAIN_TEXT",
                "language": lang,
                "content": text
            },
            "encodingType": "UTF8"
        }
        return requests.post(url, headers=header, json=body).json()
