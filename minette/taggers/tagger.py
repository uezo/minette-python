""" WordNode datamodel and base class of Tagger(do nothing) """
from typing import List
import logging

class WordNode:
    def __init__(self):
        self.part = ""
        self.part_detail1 = ""
        self.part_detail2 = ""
        self.part_detail3 = ""
        self.stem_type = ""
        self.stem_form = ""
        self.word = ""
        self.kana = ""
        self.pronunciation = ""

class Tagger:
    def __init__(self, logger:logging.Logger=None):
        self.logger = logger

    def parse(self, text) -> List[WordNode]:
        return []
