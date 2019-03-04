import sys
import os
sys.path.append(os.pardir)
from datetime import datetime
from minette import Minette
from minette.dialog import DialogService


# Custom dialog service
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


if __name__ == "__main__":
    # Create bot
    bot = Minette.create(default_dialog_service=GreetingDialogService)
    # Start conversation
    while True:
        req = input("user> ")
        res = bot.chat(req)
        for message in res.messages:
            print("minette> " + message.text)
