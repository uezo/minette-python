import os
from configparser import ConfigParser


class Config:
    """
    Configuration management

    Attributes
    ----------
    confg_parser : ConfigParser
        ConfigParser using internally
    """

    def __init__(self, config_file):
        """
        Parameters
        ----------
        config_file : str
            Path to configuration file
        """
        self.confg_parser = ConfigParser()
        self.confg_parser.read(config_file)
        if not self.confg_parser.has_section("minette"):
            self.confg_parser.add_section("minette")
            self.confg_parser.set("minette", "timezone", "ENV::MINETTE_TIMEZONE")
            self.confg_parser.set("minette", "logfile", "ENV::MINETTE_LOGFILE")
            self.confg_parser.set("minette", "connection_str", "ENV::MINETTE_CONNECTION_STR")
            self.confg_parser.set("minette", "database_presets", "ENV::DB_PRESETS")
            self.confg_parser.set("minette", "default_dialog_router", "ENV::DEFAULT_DIALOG_ROUTER")
            self.confg_parser.set("minette", "default_dialog_service", "ENV::DEFAULT_DIALOG_SERVICE")
            self.confg_parser.set("minette", "chatting_api_key", "ENV::CHAT_API_KEY")
            self.confg_parser.set("minette", "google_api_key", "ENV::GOOGLE_API_KEY")
        if not self.confg_parser.has_section("line_bot_api"):
            self.confg_parser.add_section("line_bot_api")
            self.confg_parser.set("line_bot_api", "channel_secret", "ENV::LINE_CHANNEL_SECRET")
            self.confg_parser.set("line_bot_api", "channel_access_token", "ENV::LINE_ACCESS_TOKEN")

    def get(self, key, section=None, default=None):
        ret = self.confg_parser[section if section else "minette"].get(key, default)
        if str(ret).startswith("ENV::"):
            env_key = ret[5:]
            if env_key in os.environ:
                ret = os.environ[env_key]
            else:
                ret = default
        return ret
