import sys
import os
sys.path.append(os.pardir)
import pytest

from minette.config import Config


def test_init_without_file():
    config = Config(None)
    assert config.get("timezone", section="minette") == "UTC"


def test_init_file_not_exist():
    config = Config(None)
    assert config.get("timezone", section="minette") == "UTC"


def test_get():
    config = Config("config/test_config.ini")
    assert config.get("key1") == "value1"
    assert config.get("key2") is None
    assert config.get("key3", section="invalid_section", default="default_value") == "default_value"


def test_get_without_section():
    config = Config("config/test_config_empty.ini")
    assert config.get("timezone") == "UTC"
