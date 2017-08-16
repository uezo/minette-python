import sys, os
sys.path.append(os.pardir)
from datetime import datetime
import minette
from minette.dialog import Message, DialogService, Classifier

class GreetingDialogService(DialogService):
    def compose_response(self, request, session, connection):
        now = datetime.now()
        phrase = "It's " + now.strftime("%H:%M") + " now. "
        if now.hour < 12:
            phrase += "Good morning"
        elif now.hour < 18:
            phrase += "Hello"
        else:
            phrase += "Good evening"
        return request.get_reply_message(text=phrase)

if __name__ == "__main__":
    # create bot
    bot = minette.create(default_dialog_service=GreetingDialogService)
    # start conversation
    while True:
        req = input("user> ")
        res = bot.execute(req)
        for message in res:
            print("minette> " + message.text)
