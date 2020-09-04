import sys
import os
sys.path.append(os.pardir)
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


def test_validate():
    tagger = Tagger(max_length=5)
    assert tagger.validate("こんにちは") is True
    assert tagger.validate("ごきげんよう") is False
    assert tagger.validate("こんにちは", max_length=4) is False
    assert tagger.validate("ごきげんよう", max_length=6) is True
    with pytest.raises(TypeError):
        tagger.validate(object())
    with pytest.raises(TypeError):
        tagger.validate(1)

    tagger_nomax = Tagger()
    assert tagger_nomax.max_length == 1000
