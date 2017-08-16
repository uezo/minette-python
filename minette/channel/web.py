""" Adapter for WebAPI """
from minette.dialog import Message, Payload
from minette.serializer import encode_json

class WebAdapter:
    def parse_request(self, request):
        json = request.json
        if json:
            msg = Message.from_dict(json)
        else:
            msg = Message(channel="web")
            msg.text = request.args.get("text")
            if request.args.get("media"):
                p = Payload()
                p.url = request.args.get("media")
                p.content_type = request.args.get("media_type") if request.args.get("media_type") else p.content_type
                msg.payloads.append(p)
        return msg

    def serialize_response(self, messages):
        return encode_json([m.to_dict() for m in messages])
