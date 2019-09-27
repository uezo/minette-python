"""
Dicebot

This example shows how to implement your logic
and build the reply message using the result of logic


Sample conversation
    $ python dice.py

    user> dice
    minette> Dice1:1 / Dice2:2
    user> more
    minette> Dice1:4 / Dice2:5
    user> 
    minette> Dice1:6 / Dice2:6

"""
import random
from minette import Minette, DialogService


# Custom dialog service
class DiceDialogService(DialogService):
    # Process logic and build context data
    def process_request(self, request, context, connection):
        context.data = {
            "dice1": random.randint(1, 6),
            "dice2": random.randint(1, 6)
        }

    # Compose response message using context data
    def compose_response(self, request, context, connection):
        return "Dice1:{} / Dice2:{}".format(
            str(context.data["dice1"]), str(context.data["dice2"]))


if __name__ == "__main__":
    # Create bot
    bot = Minette(default_dialog_service=DiceDialogService)
    # Start conversation
    while True:
        req = input("user> ")
        res = bot.chat(req)
        for message in res.messages:
            print("minette> " + message.text)
