import pytest
from pytz import timezone

try:
    from minette.tagger.mecabservice import (
        MeCabServiceTagger,
        MeCabServiceNode
    )
except Exception:
    # Skip if import dependencies not found
    pytestmark = pytest.mark.skip


def test_init():
    tagger = MeCabServiceTagger(timezone=timezone("Asia/Tokyo"))
    assert tagger.timezone == timezone("Asia/Tokyo")


def test_parse():
    tagger = MeCabServiceTagger()
    # 空文字列
    assert tagger.parse("") == []
    # センテンスあり
    words = tagger.parse("今日は良い天気です")
    assert isinstance(words[0], MeCabServiceNode)
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


def test_error():
    tagger = MeCabServiceTagger(api_url="https://")
    assert tagger.api_url == "https://"
    assert tagger.parse("今日は良い天気です") == []
