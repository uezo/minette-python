""" Japanese chatting """
import logging
import traceback
from time import time
from configparser import ConfigParser
import json
from pytz import timezone
from datetime import datetime
import requests
from minette.session import Session
from minette.dialog import Message, DialogService

class ChatDialogService(DialogService):
    def __init__(self, request, session, logger=None, config=None, tzone=None, connection=None, api_key="", replace_values=None, chat_logfile=""):
        super().__init__(request=request, session=session, logger=logger, config=config, tzone=tzone, connection=connection)
        self.api_key = api_key
        if not api_key and config:
            self.api_key = config["minette"].get("chatting_api_key", "")
        self.replace_values = replace_values if replace_values else {}
        self.chat_logger = None
        if chat_logfile:
            logger = logging.getLogger(__name__)
            logger.setLevel(logging.DEBUG)
            formatter = logging.Formatter('%(asctime)s - %(message)s')
            stream_handler = logging.StreamHandler()
            stream_handler.setLevel(logging.DEBUG)
            stream_handler.setFormatter(formatter)
            logger.addHandler(stream_handler)
            file_handler = logging.FileHandler(filename=chat_logfile)
            file_handler.setLevel(logging.DEBUG)
            file_handler.setFormatter(formatter)
            logger.addHandler(file_handler)
            self.chat_logger = logger

    def process_request(self):
        chat_req = {
            "utt": self.request.text,
            "context": self.session.chat_context,
            "mode": "srtr" if self.session.mode == "srtr" else "",
            }
        if self.request.user.nickname != "":
            chat_req["nickname"] = self.request.user.nickname
        chat_res = requests.post("https://api.apigw.smt.docomo.ne.jp/dialogue/v1/dialogue?APIKEY=" + self.api_key, json.dumps(chat_req)).json()
        self.session.chat_context = chat_res["context"]
        self.session.mode = chat_res["mode"] if chat_res["mode"] == "srtr" else ""
        chat_str = str(chat_res["utt"])
        for k, v in self.replace_values.items():
            chat_str = chat_str.replace(k, v)
        self.session.data = chat_str
        if self.chat_logger:
            try:
                self.chat_logger.debug(json.dumps(chat_res))
            except Exception as ex:
                self.logger.error("Error occured in logging chat message for debug: " + str(ex) + "\n" + traceback.format_exc())

    def compose_response(self):
        self.session.keep_mode = True if self.session.mode == "srtr" else False
        return self.request.get_reply_message(str(self.session.data))
