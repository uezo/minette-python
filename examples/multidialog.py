import sys
import os
sys.path.append(os.pardir)
import random
from datetime import datetime
from minette import Minette
from minette.dialog import DialogRouter, DialogService, EchoDialogService


class GreetingDialogService(DialogService):
    # Compose response message
    def compose_response(self, request, session, connection):
        now = datetime.now()
        phrase = "It's " + now.strftime("%H:%M") + " now. "
        if now.hour < 12:
            phrase += "Good morning"
        elif now.hour < 18:
            phrase += "Hello"
        else:
            phrase += "Good evening"
        return phrase


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


class MyDialogRouter(DialogRouter):
    # Configure intent->dialog routing table
    def configure(self):
        self.intent_resolver = {
            "DiceIntent": DiceDialogService, 
            "GreetingIntent": GreetingDialogService
        }

    # Set DiceIntent when user says "dice" or GreetingIntent when user says "hello"
    def extract_intent(self, request, session, connection):
        if request.text.lower() == "dice":
            return "DiceIntent"
        elif request.text.lower() == "hello":
            return "GreetingIntent"


if __name__ == "__main__":
    # Create bot
    bot = Minette.create(dialog_router=MyDialogRouter, default_dialog_service=EchoDialogService)
    # Start conversation
    while True:
        req = input("user> ")
        res = bot.chat(req)
        for message in res.messages:
            print("minette> " + message.text)
