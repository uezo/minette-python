import os
from configparser import ConfigParser

class Config:
    def __init__(self, config_file=""):
        self.confg_parser = ConfigParser()
        self.confg_parser.read(config_file if config_file else "./minette.ini")
    
    def get(self, key, section="", default=""):
        ret = self.confg_parser[section if section else "minette"].get(key, default)
        if str(ret).startswith("ENV::"):
            env_key = ret[5:]
            if env_key in os.environ:
                ret = os.environ[env_key]
            else:
                ret = default
        return ret

    def getint(self, key, section="", default=0):
        return int(self.get(key, section, default))
