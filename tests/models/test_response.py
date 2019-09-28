import pytest

from minette import Response, Message, PerformanceInfo


def test_init():
    msg1 = Message(text="message 1")
    msg2 = Message(text="message 2")
    headers = {"key1": "value1", "key2": 1}
    performance = PerformanceInfo()
    response = Response(messages=[msg1, msg2], headers=headers, performance=performance)
    assert response.messages == [msg1, msg2]
    assert response.headers == headers
    assert isinstance(response.performance, PerformanceInfo)


def test_from_dict():
    # setup response dict
    msg1 = Message(text="message 1")
    msg2 = Message(text="message 2")
    headers = {"key1": "value1", "key2": 1}
    performance = PerformanceInfo()
    response_dict = Response(messages=[msg1, msg2], headers=headers, performance=performance).to_dict()
    # restore
    response = Response.from_dict(response_dict)
    assert response.messages[0].text == msg1.text
    assert response.messages[1].text == msg2.text
    assert response.headers == headers
    assert isinstance(response.performance, PerformanceInfo)
