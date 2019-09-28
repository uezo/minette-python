import pytest

from minette import User


def test_user():
    user = User(channel="TEST", channel_user_id="user_id")
    assert len(user.id) > 10
    assert user.name == ""
    assert user.nickname == ""
    assert user.channel == "TEST"
    assert user.channel_user_id == "user_id"
    assert user.profile_image_url == ""
    assert user.data == {}
