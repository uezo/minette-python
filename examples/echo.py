""" Console BOT example """
import sys
import os
sys.path.append(os.pardir)
from minette import Minette
from minette.dialog import EchoDialogService


# Create an instance of Minette with EchoDialogService
bot = Minette.create(default_dialog_service=EchoDialogService)

# Send and receive messages
while True:
    req = input("user> ")
    res = bot.chat(req)
    for message in res.messages:
        print("minette> " + message.text)
