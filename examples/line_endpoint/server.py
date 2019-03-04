""" LINE endpoint example """
import sys
sys.path.append("../../")
from flask import Flask, request
from minette import Minette
from minette.dialog import EchoDialogService
from minette.channel.line import LineAdapter

bot = Minette.create(default_dialog_service=EchoDialogService)
line_adapter = LineAdapter(bot, channel_secret="<CHANNEL SECRET>", channel_access_token="<CHANNEL ACCESS TOKEN>")
app = Flask(__name__)


@app.route("/callback", methods=["POST"])
def line_endpoint():
    """
    http(s)://your.domain/callback is the endpoint url
    """
    line_adapter.chat(request.get_data(as_text=True), request.headers)
    return "ok"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
