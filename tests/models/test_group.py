import pytest

from minette import Group


def test_init():
    group = Group(id="group_id", type="room")
    assert group.id == "group_id"
    assert group.type == "room"
