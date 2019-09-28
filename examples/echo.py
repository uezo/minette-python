"""
Echobot

This example shows the simple echo-bot


Sample conversation
    $ python echo.py

    user> hello
    minette> You said: hello
    user> I love soba
    minette> You said: I love soba

"""
from minette import Minette, DialogService


# EchoDialog
class EchoDialogService(DialogService):
    # Return reply message to user
    def compose_response(self, request, context, connection):
        return "You said: {}".format(request.text)


# Create an instance of Minette with EchoDialogService
bot = Minette(default_dialog_service=EchoDialogService)

# Send and receive messages
while True:
    req = input("user> ")
    res = bot.chat(req)
    for message in res.messages:
        print("minette> " + message.text)
