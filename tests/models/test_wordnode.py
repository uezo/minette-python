import pytest

from minette import WordNode


class CustomNode(WordNode):
    @classmethod
    def create(cls, surface, features):
        pass


def test_init():
    node = CustomNode("surface", "part", "part_detail1", "part_detail2", "part_detail3", "stem_type", "stem_form", "word", "kana", "pronunciation")
    assert node.surface == "surface"
    assert node.part == "part"
    assert node.part_detail1 == "part_detail1"
    assert node.part_detail2 == "part_detail2"
    assert node.part_detail3 == "part_detail3"
    assert node.stem_type == "stem_type"
    assert node.stem_form == "stem_form"
    assert node.word == "word"
    assert node.kana == "kana"
    assert node.pronunciation == "pronunciation"
