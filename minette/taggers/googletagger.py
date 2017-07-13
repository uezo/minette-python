""" tagger using Google Cloud Natural Languege API """
from typing import List
import logging
import traceback
from configparser import ConfigParser
from pytz import timezone
import requests
from minette.taggers.tagger import WordNode, Tagger

class GoogleNode(WordNode):
    def __init__(self, token):
        super().__init__()
        self.word = token["text"]["content"]
        self.part = token["partOfSpeech"]["tag"]

class GoogleTagger(Tagger):
    def __init__(self, api_key, logger:logging.Logger=None, config:ConfigParser=None, tzone:timezone=None):
        super().__init__(logger=logger, config=config, tzone=tzone)
        self.api_key = api_key

    def parse(self, text, lang="en") -> List[GoogleNode]:
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
