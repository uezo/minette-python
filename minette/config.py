""" Configuration management """
import os
from configparser import ConfigParser


class Config:
    """
    Configuration management

    Attributes
    ----------
    confg_parser : ConfigParser
        ConfigParser used internally
    """

    def __init__(self, config_file):
        """
        Parameters
        ----------
        config_file : str
            Path to configuration file
        """
        self.confg_parser = ConfigParser()
        if config_file and len(self.confg_parser.read(config_file)) == 0:
            print("Can't read/find configuration file: {}".format(config_file))
            print("Initialize with default configuration instead")

        if not self.confg_parser.has_section("minette"):
            self.confg_parser.add_section("minette")
            self.confg_parser.set("minette", "timezone", "UTC")
            self.confg_parser.set(
                "minette", "log_file", "ENV::MINETTE_LOGFILE")
            self.confg_parser.set(
                "minette", "connection_str", "ENV::MINETTE_CONNECTION_STR")

    def get(self, key, default=None, section="minette"):
        if section in self.confg_parser.sections():
            ret = self.confg_parser[section].get(key, default)
        else:
            ret = default
        if str(ret).startswith("ENV::"):
            ret = os.environ.get(ret[5:], default)
        return ret
