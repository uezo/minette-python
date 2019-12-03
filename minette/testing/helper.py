from time import time

from ..core import Minette
from ..models import Message


class MinetteForTest(Minette):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.default_channel = kwargs.get("default_channel", "")
        self.case_id = str(int(time() * 10000000))

    def chat(self, request, **kwargs):
        self.logger.info("start testcase: " + self.case_id)
        # convert to Message
        if isinstance(request, str):
            request = Message(text=request, **kwargs)
        # set channel and channel_user_id for this test case
        if request.channel == "console":
            request.channel = self.default_channel or request.channel
        if request.channel_user_id == "anonymous":
            request.channel_user_id = "user" + self.case_id
        # chat and return response
        response = super().chat(request)
        if response.messages:
            response.text = response.messages[0].text
        else:
            response.text = ""
        self.logger.info("end testcase: " + self.case_id)
        return response
