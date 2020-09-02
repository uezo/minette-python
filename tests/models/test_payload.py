import pytest

from minette import Payload


def test_init():
    payload = Payload(content_type="image/jpeg", url="http://uezo.net/img/minette_architecture.png", thumb="https://thumb")
    assert payload.content_type == "image/jpeg"
    assert payload.url == "http://uezo.net/img/minette_architecture.png"
    assert payload.thumb == "https://thumb"
    assert payload.headers == {}
    assert payload.content is None
