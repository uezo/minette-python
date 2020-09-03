import pytest
from pytz import timezone
from types import GeneratorType

try:
    from minette.tagger.mecabtagger import MeCabTagger, MeCabNode
except Exception:
    # Skip if import dependencies not found
    pytestmark = pytest.mark.skip


def test_init():
    tagger = MeCabTagger(timezone=timezone("Asia/Tokyo"))
    assert tagger.timezone == timezone("Asia/Tokyo")


def test_parse():
    tagger = MeCabTagger()
    # 空文字列
    assert tagger.parse("") == []
    # センテンスあり
    words = tagger.parse("今日は良い天気です")
    assert isinstance(words[0], MeCabNode)
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
    tagger = MeCabTagger()
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


def test_error():
    tagger = MeCabTagger()
    assert tagger.parse(object()) == []
