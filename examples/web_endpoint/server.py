""" Web API endpoint example """
import sys
sys.path.append("../../")
from flask import Flask, request, abort
from minette import Minette
from minette.dialog import EchoDialogService
from minette.serializer import encode_json
from minette.channel.web import WebAdapter

bot = Minette.create(default_dialog_service=EchoDialogService)
web_adapter = WebAdapter(bot)
app = Flask(__name__)


@app.route("/callback", methods=["GET", "POST"])
def callback():
    """
    http(s)://your.domain/callback is the endpoint url
    """
    res = web_adapter.chat(request).json
    print(res)
    return res

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
