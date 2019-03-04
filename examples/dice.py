import sys
import os
sys.path.append(os.pardir)
import random
from minette import Minette
from minette.dialog import DialogService


# Custom dialog service
class DiceDialogService(DialogService):
    # Process logic and build session data
    def process_request(self, request, session, connection):
        session.data = {
            "dice1": random.randint(1, 6),
            "dice2": random.randint(1, 6)
        }

    # Compose response message using session data
    def compose_response(self, request, session, connection):
        return "Dice1:{} / Dice2:{}".format(str(session.data["dice1"]), str(session.data["dice2"]))


if __name__ == "__main__":
    # Create bot
    bot = Minette.create(default_dialog_service=DiceDialogService)
    # Start conversation
    while True:
        req = input("user> ")
        res = bot.chat(req)
        for message in res.messages:
            print("minette> " + message.text)
