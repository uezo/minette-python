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
from minette.util import date_to_str

class ChatDialogService(DialogService):
    def __init__(self, request, session, logger=None, config=None, tzone=None, connection=None, api_key="", replace_values=None, debug=False):
        super().__init__(request=request, session=session, logger=logger, config=config, tzone=tzone, connection=connection)
        self.api_key = api_key
        self.replace_values = replace_values if replace_values else {}
        self.debug = debug

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
        self.debug_chat_message(chat_res)

    def compose_response(self):
        self.session.keep_mode = True if self.session.mode == "srtr" else False
        return self.request.get_reply_message(str(self.session.data))

    def debug_chat_message(self, chat_json):
        """
        :param chat_json: JSON to log
        """
        if self.debug is False:
            return
        try:
            start_time = time()
            chat_json_str = json.dumps(chat_json)
            now = datetime.now(self.timezone)
            cursor = self.connection.cursor()
            sql = "insert into chatlog(timestamp, overhead, text) values (%s,%s,%s)"
            overhead = int((time() - start_time) * 1000)
            cursor.execute(sql, (date_to_str(now, True), overhead, chat_json_str))
            self.connection.commit()
        except Exception as ex:
            self.logger.error("Error occured in logging chat message for debug: " + str(ex) + "\n" + traceback.format_exc())

    @classmethod
    def prepare_table(cls, connection_provider):
        """
        :param connection_provider: MySQLConnectionProvider to create table if not existing
        :type connection_provider: MySQLConnectionProvider
        """
        connection = connection_provider.get_connection()
        cursor = connection.cursor()
        cursor.execute("create table chatlog(timestamp DATETIME, overhead INT, text VARCHAR(4000))")
        connection.commit()
