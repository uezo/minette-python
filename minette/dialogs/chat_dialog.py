""" Japanese chatting """
import logging
from configparser import ConfigParser
import json
from pytz import timezone
import requests
from minette.session import Session
from minette.dialog import Message, DialogService

class ChatDialogService(DialogService):
    def __init__(self, request:Message, session:Session, logger:logging.Logger=None, config:ConfigParser=None, tzone:timezone=None, api_key="", replace_values:dict=None):
        super().__init__(request=request, session=session, logger=logger, config=config, tzone=tzone)
        self.api_key = api_key
        self.replace_values = replace_values if replace_values else {}

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

    def compose_response(self) -> Message:
        self.session.keep_mode = True if self.session.mode == "srtr" else False
        return self.request.get_reply_message(str(self.session.data))
