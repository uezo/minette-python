import sys, os
sys.path.append(os.pardir)
import requests
import minette
from minette.dialog import Message, DialogService, Classifier
from minette.dialog.chat_dialog import ChatDialogService
from minette.session import ModeStatus

class TranslationDialogService(DialogService):
    def process_request(self, request, session, connection):
        if session.mode_status == ModeStatus.Start:
            session.mode = "translation"
        else:
            if request.text == "翻訳終わり":
                session.mode_status = ModeStatus.End
            else:
                res = requests.post("https://translation.googleapis.com/language/translate/v2", data={
                    "key": self.config.get("google_api_key"),
                    "q": request.text,
                    "target": "en"
                }).json()
                session.data = res["data"]["translations"][0]["translatedText"].replace("&#39;", "'")

    def compose_response(self, request, session, connection):
        if session.mode_status == ModeStatus.Start:
            text = "翻訳したい文章を入力してください。「翻訳終わり」で翻訳モードを終了します"
            session.keep_mode = True
        elif session.mode_status == ModeStatus.Continue:
            text = "English: " + session.data
            session.keep_mode = True
        else:
            text = "はい、翻訳は終わりにします"
        return request.get_reply_message(text)

class MyClassifier(Classifier):
    def classify(self, request, session, connection):
        if "翻訳して" in request.text or session.mode == "translation":
            return TranslationDialogService
        else:
            return ChatDialogService

if __name__ == "__main__":
    # create bot
    bot = minette.create(classifier=MyClassifier)
    # start conversation
    while True:
        req = input("user> ")
        res = bot.execute(req)
        for message in res:
            print("minette> " + message.text)
