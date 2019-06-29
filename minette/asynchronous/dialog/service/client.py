import traceback
import aiohttp
from minette.message import Response
from minette.dialog import HttpDialogClient
from minette.serializer import encode_json


class AsyncHttpDialogClient(HttpDialogClient):
    async def execute(self, request, session, connection, performance):
        try:
            service_response = await self.fetch(request, session, performance)
            response = await self.handle_service_response(service_response, request, session, connection, performance)
        except Exception as ex:
            self.logger.error(f"Error occured in dialog_service(client): {str(ex)} \n{traceback.format_exc()}")
            response = Response(messages=[self.handle_exception(request, session, ex, connection)])
        performance.append("dialog_service.execute")
        return response

    async def fetch(self, request, session, performance):
        data = encode_json({"request": request.to_dict(), "session": session.to_dict(), "performance": performance.to_dict()})
        async with aiohttp.ClientSession() as client_session:
            async with client_session.post(self.endpoint_uri, data=data, headers={"Content-Type": "application/json"}, timeout=60) as resp:
                return await resp.json()

    async def handle_service_response(self, service_response, request, session, connection, performance):
        return super().handle_service_response(service_response, request, session, connection, performance)
