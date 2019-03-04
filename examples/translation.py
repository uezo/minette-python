import sys
import os
sys.path.append(os.pardir)
from datetime import datetime
import requests
from minette import Minette
from minette.dialog import DialogRouter, DialogService, EchoDialogService


class TranslationDialogService(DialogService):
    # Process logic and build session data
    def process_request(self, request, session, connection):
        if session.topic.is_new:
            session.topic.status = "start_translation"
        elif request.text == "翻訳終わり":
            session.topic.status = "end_translation"
        else:
            res = requests.post("https://translation.googleapis.com/language/translate/v2", data={
                "key": self.config.get("google_api_key"),
                "q": request.text,
                "target": "ja"
            }).json()
            session.data["translated_text"] = res["data"]["translations"][0]["translatedText"].replace("&#39;", "'")
            session.topic.status = "process_translation"

    # Compose response message
    def compose_response(self, request, session, connection):
        if session.topic.status == "start_translation":
            session.topic.keep_on = True
            return "日本語に翻訳します。英語を入力してください"
        elif session.topic.status == "end_translation":
            return "翻訳を終了しました"
        elif session.topic.status == "process_translation":
            session.topic.keep_on = True
            return request.text + " in Japanese: " + session.data["translated_text"]


class MyDialogRouter(DialogRouter):
    # Configure intent->dialog routing table
    def configure(self):
        self.intent_resolver = {"TranslationIntent": TranslationDialogService}

    # Set TranslationIntent when user said something contains "翻訳"
    def extract_intent(self, request, session, connection):
        if request.text == "翻訳":
            return "TranslationIntent"


if __name__ == "__main__":
    # Create bot
    bot = Minette.create(dialog_router=MyDialogRouter, default_dialog_service=EchoDialogService)

    # Start conversation
    while True:
        req = input("user> ")
        res = bot.chat(req)
        for message in res.messages:
            print("minette> " + message.text)
