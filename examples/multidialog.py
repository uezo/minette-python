import sys, os
sys.path.append(os.pardir)
import random
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

class DiceDialogService(DialogService):
    def process_request(self, request, session, connection):
        session.data = {
            "dice1": random.randint(1, 6),
            "dice2": random.randint(1, 6)
        }

    def compose_response(self, request, session, connection):
        dice1 = str(session.data["dice1"])
        dice2 = str(session.data["dice2"])
        return request.get_reply_message(text="Dice1:" + dice1 + " / Dice2:" + dice2)

class MyClassifier(Classifier):
    def classify(self, request, session, connection):
        if request.text.lower() == "dice":
            return DiceDialogService
        else:
            return GreetingDialogService

if __name__ == "__main__":
    # create bot
    bot = minette.create(classifier=MyClassifier)
    # start conversation
    while True:
        req = input("user> ")
        res = bot.execute(req)
        for message in res:
            print("minette> " + message.text)
