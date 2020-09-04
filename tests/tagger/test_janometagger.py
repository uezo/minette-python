import sys
import os
sys.path.append(os.pardir)
import pytest
from pytz import timezone
from types import GeneratorType

try:
    from minette.tagger.janometagger import JanomeTagger, JanomeNode
except Exception:
    # Skip if import dependencies not found
    pytestmark = pytest.mark.skip


def test_init():
    tagger = JanomeTagger(timezone=timezone("Asia/Tokyo"))
    assert tagger.timezone == timezone("Asia/Tokyo")


def test_parse():
    tagger = JanomeTagger()
    # 空文字列
    assert tagger.parse("") == []
    # センテンスあり
    words = tagger.parse("今日は良い天気です")
    assert isinstance(words[0], JanomeNode)
    # 今日
    assert words[0].surface == "今日"
    assert words[0].part == "名詞"
    assert words[0].part_detail1 == "副詞可能"
    assert words[0].word == "今日"
    assert words[0].kana == "キョウ"
    assert words[0].pronunciation == "キョー"
    # 良い
    assert words[2].surface == "良い"
    assert words[2].part == "形容詞"
    assert words[2].part_detail1 == "自立"
    assert words[2].stem_type == "形容詞・アウオ段"
    assert words[2].stem_form == "基本形"
    assert words[2].word == "良い"
    assert words[2].kana == "ヨイ"
    assert words[2].pronunciation == "ヨイ"


def test_parse_as_generator():
    tagger = JanomeTagger()
    # 空文字列
    empty_words_gen = tagger.parse_as_generator("")
    assert isinstance(empty_words_gen, GeneratorType)
    empty_words = [ew for ew in empty_words_gen]
    assert empty_words == []
    # センテンスあり
    words = tagger.parse_as_generator("今日は良い天気です")
    assert isinstance(words, GeneratorType)
    i = 0
    for w in words:
        if i == 0:
            assert w.surface == "今日"
            assert w.part == "名詞"
            assert w.part_detail1 == "副詞可能"
            assert w.word == "今日"
            assert w.kana == "キョウ"
            assert w.pronunciation == "キョー"
        elif i == 2:
            assert w.surface == "良い"
            assert w.part == "形容詞"
            assert w.part_detail1 == "自立"
            assert w.stem_type == "形容詞・アウオ段"
            assert w.stem_form == "基本形"
            assert w.word == "良い"
            assert w.kana == "ヨイ"
            assert w.pronunciation == "ヨイ"
        i += 1


def test_parse_with_max():
    tagger = JanomeTagger(max_length=8)
    # over instance max_length
    words_9 = tagger.parse("今日は良い天気です")
    assert words_9 == []
    # over instance max_length but under inline
    words_9_max10 = tagger.parse("今日は良い天気です", max_length=10)
    assert words_9_max10[0].surface == "今日"
    # under instance max_length but over inline
    words_9_max7 = tagger.parse("今日は良い天気", max_length=6)
    assert words_9_max7 == []


def test_parse_gen_with_max():
    tagger = JanomeTagger(max_length=8)
    # over instance max_length
    words_9 = [w for w in tagger.parse_as_generator("今日は良い天気です")]
    assert words_9 == []
    # over instance max_length but under inline
    words_9_max10 = [w for w in tagger.parse_as_generator("今日は良い天気です", max_length=10)]
    assert words_9_max10[0].surface == "今日"
    # under instance max_length but over inline
    words_9_max7 = [w for w in tagger.parse_as_generator("今日は良い天気", max_length=6)]
    assert words_9_max7 == []


def test_error():
    tagger = JanomeTagger()
    with pytest.raises(TypeError):
        tagger.parse(object())
