""" Japanese chatting """
import logging
import traceback
from time import time
import json
from pytz import timezone
from datetime import datetime
import requests
from minette.session import Session
from minette.dialog import Message, DialogService

class ChatDialogService(DialogService, object):
    def __init__(self, logger=None, config=None, tzone=None, api_key="", replace_values=None, chat_logfile=""):
        super().__init__(logger=logger, config=config, tzone=tzone)
        self.api_key = api_key
        if not api_key and config:
            self.api_key = config.get("chatting_api_key")
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

    def process_request(self, request, session, connection):
        chat_req = {
            "utt": request.text,
            "context": session.chat_context,
            "mode": "srtr" if session.mode == "srtr" else "",
            }
        if request.user.nickname != "":
            chat_req["nickname"] = request.user.nickname
        chat_res = requests.post("https://api.apigw.smt.docomo.ne.jp/dialogue/v1/dialogue?APIKEY=" + self.api_key, json.dumps(chat_req)).json()
        session.chat_context = chat_res["context"]
        session.mode = chat_res["mode"] if chat_res["mode"] == "srtr" else ""
        chat_str = chat_res["utt"]
        for k, v in self.replace_values.items():
            chat_str = chat_str.replace(k, v)
        session.data = chat_str
        if self.chat_logger:
            try:
                self.chat_logger.debug(json.dumps(chat_res))
            except Exception as ex:
                self.logger.error("Error occured in logging chat message for debug: " + str(ex) + "\n" + traceback.format_exc())

    def compose_response(self, request, session, connection):
        session.keep_mode = True if session.mode == "srtr" else False
        return request.get_reply_message(session.data)
