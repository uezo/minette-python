from abc import ABC, abstractmethod
from ..serializer import Serializable


class WordNode(ABC, Serializable):
    """
    Base class of parsed word

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
    def __init__(self, surface, part, part_detail1, part_detail2, part_detail3,
                 stem_type, stem_form, word, kana, pronunciation):
        self.surface = surface
        self.part = part
        self.part_detail1 = part_detail1
        self.part_detail2 = part_detail2
        self.part_detail3 = part_detail3
        self.stem_type = stem_type
        self.stem_form = stem_form
        self.word = word
        self.kana = kana
        self.pronunciation = pronunciation

    @classmethod
    @abstractmethod
    def create(cls, surface, features):
        pass
