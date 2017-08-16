""" Web API endpoint example """
import sys
sys.path.append("../../")
from flask import Flask, request, abort
import minette
from minette.serializer import encode_json
from minette.channel import WebAdapter

bot = minette.create(
    #tagger=minette.tagger.MeCabTagger, #If MeCab is installed, uncomment this line
    #classifier=MyClassifier,           #Your own classifier
    config_file="../minette.ini"
)
adapter = WebAdapter()

app = Flask(__name__)

@app.route("/callback", methods=["GET", "POST"])
def callback():
    """
    http(s)://your.domain/callback is the endpoint url
    """
    req = adapter.parse_request(request)
    res = bot.execute(req)
    return adapter.serialize_response(res)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5002)
