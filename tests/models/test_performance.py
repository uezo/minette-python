import pytest
from time import sleep

from minette import PerformanceInfo


def test_init():
    performance = PerformanceInfo()
    assert isinstance(performance.start_time, float)
    assert performance.ticks == []
    assert performance.milliseconds == 0


def test_append():
    performance = PerformanceInfo()
    sleep(2)
    performance.append("operation")
    assert performance.ticks[0][1] > 1
    assert performance.milliseconds > 0
