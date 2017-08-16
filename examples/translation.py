import sys, os
sys.path.append(os.pardir)
import requests
import minette
from minette.dialog import Message, DialogService, Classifier

class TranslationDialogService(DialogService):
    def process_request(self, request, session, connection):
        res = requests.post("https://translation.googleapis.com/language/translate/v2", data={
            "key": self.config.get("google_api_key"),
            "q": request.text,
            "target": "ja"
        }).json()
        session.data = res["data"]["translations"][0]["translatedText"].replace("&#39;", "'")

    def compose_response(self, request, session, connection):
        return request.get_reply_message(request.text + " in Japanese: " + session.data)

if __name__ == "__main__":
    # create bot
    bot = minette.create(default_dialog_service=TranslationDialogService)

    # start conversation
    while True:
        req = input("user> ")
        res = bot.execute(req)
        for message in res:
            print("minette> " + message.text)
