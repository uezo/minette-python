from flask import Flask, request, abort
from minette.serializer import encode_json
from minette.channel import WebAdapter

class WebEndpoint:
    def __init__(self, bot, port):
        self.bot = bot
        self.port = port
        self.adapter = WebAdapter()
        self.app = Flask(__name__)

        @self.app.route("/callback", methods=["GET", "POST"])
        def callback():
            req = self.adapter.parse_request(request)
            res = self.bot.execute(req)
            return self.adapter.serialize_response(res)

    def start(self):
        self.app.run(host="0.0.0.0", port=self.port)
