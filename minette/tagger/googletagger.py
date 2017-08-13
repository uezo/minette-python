""" tagger using Google Cloud Natural Languege API """
import traceback
import requests
from minette.tagger import WordNode, Tagger

class GoogleNode(WordNode):
    def __init__(self, token):
        super().__init__()
        self.word = token["text"]["content"]
        self.part = token["partOfSpeech"]["tag"]

class GoogleTagger(Tagger):
    def __init__(self, api_key="", logger=None, config=None, tzone=None):
        """
        :param api_key: API Key for Google Cloud Natural Language API
        :type api_key: str
        :param logger: Logger
        :type logger: logging.Logger
        :param config: Config
        :type config: Config
        :param tzone: Timezone
        :type tzone: timezone
        """
        super().__init__(logger=logger, config=config, tzone=tzone)
        self.api_key = api_key
        if not api_key and config:
            self.api_key = config.get("googletagger_api_key")

    def parse(self, text, lang="en"):
        """
        :param text: Text to analyze
        :type text: str
        :param lang: Language
        :type lang: str
        :return: GoogleNode
        :rtype: [GoogleNode]
        """
        ret = []
        if text == "":
            return ret
        try:
            parsed_json = self.__get_entities_json(text, lang)
            for node in parsed_json["tokens"]:
                ret.append(GoogleNode(node))
        except Exception as ex:
            self.logger.error("Google parsing error: " + str(ex) + "\n" + traceback.format_exc())
        return ret

    def __get_entities_json(self, text, lang):
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
