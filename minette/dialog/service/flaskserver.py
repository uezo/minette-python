from flask import Response as HttpResponse
from minette.session import Session
from minette.message import Message, Response
from minette.performance import PerformanceInfo
from minette.dialog import HttpDialogServer


class FlaskDialogServer(HttpDialogServer):
    def is_warmup(self, http_request):
        return True if http_request.args.get("warmup", "") else False

    def parse_request(self, http_request):
        req_json = http_request.json
        return Message.from_dict(req_json["request"]), Session.from_dict(req_json["session"]), PerformanceInfo.from_dict(req_json["performance"])

    def make_response(self, request=None, session=None, performance=None, response=None, error=None, status_code=200, content_type="application/json"):
        data = super().make_response(request, session, performance, response, error, status_code, content_type)
        return HttpResponse(data, status=status_code, content_type=content_type)
