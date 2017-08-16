import sys, os
sys.path.append(os.pardir)
import random
import minette
from minette.dialog import Message, DialogService, Classifier

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

if __name__ == "__main__":
    # create bot
    bot = minette.create(default_dialog_service=DiceDialogService)
    # start conversation
    while True:
        req = input("user> ")
        res = bot.execute(req)
        for message in res:
            print("minette> " + message.text)
