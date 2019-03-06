""" Clova endpoint example """
import sys
import os
sys.path.append(os.pardir)
from flask import Flask, request
from minette import Minette
from minette.dialog import DialogService, DialogRouter
from minette.channel.clova import ClovaAdapter
from weather import WeatherDialogService


class IntentEchoDialogService(DialogService):
    def compose_response(self, request, session, connection):
        if request.type == "IntentRequest":
            return "Intent is {}".format(request.intent)
        else:
            return "Request type is {}".format(request.type)


class ClovaDialogRouter(DialogRouter):
    def configure(self):
        self.intent_resolver = {
            # To use weather skill, set intent WeatherIntent and slot city:"tokyo"
            "WeatherIntent": WeatherDialogService
        }

bot = Minette.create(default_dialog_service=IntentEchoDialogService, dialog_router=ClovaDialogRouter)
clova_adapter = ClovaAdapter(bot, application_id="<YOUR APPLICATION ID>", debug=True)
app = Flask(__name__)


@app.route("/clova", methods=["POST"])
def clova_endpoint():
    res = clova_adapter.chat(request.data, request.headers)
    return res.json

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5678)
