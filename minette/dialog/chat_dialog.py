""" Japanese chatting """
import logging
import traceback
from time import time
import json
from pytz import timezone
from datetime import datetime
import requests
import base64
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

    @classmethod
    def extract_mode(cls, b64string):
        decoded_string = base64.b64decode(b64string).decode("utf-8")
        command = json.loads(decoded_string)
        return command["mode"]

    def get_app_id(self):
        reg_req = {
            "botId": "Chatting",
            "appKind": "minette_chat_dialog",
            }
        reg_res = requests.post("https://api.apigw.smt.docomo.ne.jp/naturalChatting/v1/registration?APIKEY=" + self.api_key, json.dumps(reg_req)).json()
        return reg_res["appId"]

    def process_request(self, request, session, connection):
        session.chat_context = session.chat_context if session.chat_context else self.get_app_id()
        chat_req = {
            "language": "ja-JP",
            "botId": "Chatting",
            "appId": session.chat_context,
            "voiceText": request.text,
            "clientData":{
                "option":{
                    "mode": "srtr" if session.mode == "srtr" else "",
                }
            }
        }
        if request.user.nickname != "":
            chat_req["clientData"]["option"]["nickname"] = request.user.nickname
        chat_res = requests.post("https://api.apigw.smt.docomo.ne.jp/naturalChatting/v1/dialogue?APIKEY=" + self.api_key, json.dumps(chat_req)).json()
        chat_mode = self.extract_mode(chat_res["command"])
        session.mode = chat_mode if chat_mode == "srtr" else ""
        chat_str = chat_res["systemText"]["utterance"]
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
