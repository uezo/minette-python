import pytest
from pytz import timezone
from types import GeneratorType

from minette import Tagger


def test_init():
    tagger = Tagger(timezone=timezone("Asia/Tokyo"))
    assert tagger.timezone == timezone("Asia/Tokyo")


def test_parse():
    tagger = Tagger()
    assert tagger.parse("今日は良い天気です") == []


def test_parse_as_generator():
    tagger = Tagger()
    assert isinstance(tagger.parse_as_generator("今日は良い天気です"), GeneratorType)
