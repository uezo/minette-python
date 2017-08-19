from flask import Flask, request, abort
from minette.serializer import encode_json
from minette.channel.line import LineAdapter, LineWorkerThread

class LineEndpoint:
    def __init__(self, bot, port):
        self.bot = bot
        self.port = port
        channel_secret = self.bot.config.get(section="line_bot_api", key="channel_secret")
        channel_access_token = self.bot.config.get(section="line_bot_api", key="channel_access_token")
        worker = LineWorkerThread(bot=bot, channel_secret=channel_secret, channel_access_token=channel_access_token)
        worker.start()
        self.adapter = LineAdapter(worker, channel_secret)
        self.app = Flask(__name__)

        @self.app.route("/callback", methods=["GET", "POST"])
        def callback():
            code = self.adapter.parse_request(request)
            if code != 200:
                abort(code)
            else:
                return "OK"

    def start(self):
        self.app.run(host="0.0.0.0", port=self.port)
