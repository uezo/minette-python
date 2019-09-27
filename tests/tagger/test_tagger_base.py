import pytest
from pytz import timezone

from minette import Tagger


def test_init():
    tagger = Tagger(timezone=timezone("Asia/Tokyo"))
    assert tagger.timezone == timezone("Asia/Tokyo")


def test_parse():
    tagger = Tagger()
    assert tagger.parse("今日は良い天気です") == []
