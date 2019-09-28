import pytest

from copy import deepcopy

from minette import Topic, Priority


def test_init():
    topic = Topic()
    assert topic.name == ""
    assert topic.status == ""
    assert topic.is_new is False
    assert topic.keep_on is False
    assert topic.previous is None
    assert topic.priority == Priority.Normal


def test_is_changed():
    # create topic
    topic = Topic()
    topic.name = "favorite_fruit"
    topic.previous = deepcopy(topic)
    # keep topic
    topic.name = "favorite_fruit"
    assert topic.is_changed is False
    # change topic
    topic.name = "favorite_sushi"
    assert topic.is_changed is True
