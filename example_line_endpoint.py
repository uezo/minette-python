""" LINE endpoint example """
from flask import Flask, request, abort
from minette import automata
from minette.channel.line_adapter import WorkerThread, RequestParser

bot = automata.create(
    #tagger=mecabtagger.MeCabTagger(),
    #classifier=classifier.MyClassifier()
)
channel_secret = bot.config.get("line_bot_api", "channel_secret")
channel_access_token = bot.config.get("line_bot_api", "channel_access_token")
worker = WorkerThread(bot=bot, channel_secret=channel_secret, channel_access_token=channel_access_token)
worker.start()
parser = RequestParser(worker, channel_secret)

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
