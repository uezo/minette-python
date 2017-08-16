""" LINE endpoint example """
import sys
sys.path.append("../../")
from flask import Flask, request, abort
import minette
from minette.channel import LineWorkerThread, LineRequestParser

bot = minette.create(
    #tagger=minette.tagger.MeCabTagger, #If MeCab is installed, uncomment this line
    #classifier=MyClassifier,           #Your own classifier
    config_file="../minette.ini"
)
channel_secret = bot.config.get(section="line_bot_api", key="channel_secret")
channel_access_token = bot.config.get(section="line_bot_api", key="channel_access_token")
worker = LineWorkerThread(bot=bot, channel_secret=channel_secret, channel_access_token=channel_access_token)
worker.start()
parser = LineRequestParser(worker, channel_secret)

app = Flask(__name__)

@app.route("/callback", methods=["POST"])
def callback():
    """
    http(s)://your.domain/callback is the endpoint url
    """
    code = parser.parse_request(request)
    if code != 200:
        abort(code)
    else:
        return "OK"

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001)
