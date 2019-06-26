""" LINE endpoint example """
import sys
sys.path.append("../../")
from flask import Flask, request, abort, render_template
from minette import Minette
from minette.dialog import EchoDialogService
from minette.channel.line import LineAdapter

bot = Minette.create(default_dialog_service=EchoDialogService)
line_adapter = LineAdapter(bot, channel_secret="<CHANNEL SECRET>", channel_access_token="<CHANNEL ACCESS TOKEN>")
# `threads=0` to use main thread for processing dialog
# line_adapter = LineAdapter(bot, threads=0, channel_secret="<CHANNEL SECRET>", channel_access_token="<CHANNEL ACCESS TOKEN>")
app = Flask(__name__)


@app.route("/callback", methods=["POST"])
def line_endpoint():
    """
    http(s)://your.domain/callback is the endpoint url
    """
    line_adapter.chat(request.get_data(as_text=True), request.headers)
    return "ok"


# message log handler
@app.route("/messagelog", methods=["GET", "POST"])
def messagelog():
    # authorize
    if request.args.get("key", "") != "<PASSWORD YOU LIKE>":
        abort(401)
    # show message log
    ml = bot.get_message_log(count=int(request.args.get("count", 20)))
    return render_template("messagelog.html", ml=ml)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
