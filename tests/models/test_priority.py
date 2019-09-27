import pytest

from minette import Priority


def test_class():
    assert Priority.Highest == 100
    assert Priority.High == 75
    assert Priority.Normal == 50
    assert Priority.Low == 25
    assert Priority.Ignore == 0
