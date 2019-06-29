import traceback
import requests
from minette.message import Message, Response
from minette.session import Session
from minette.performance import PerformanceInfo
from minette.dialog.service import DialogService
from minette.serializer import encode_json


class HttpDialogClient(DialogService):
    """
    Base class of client for DialogService provided as WebService

    Attributes
    ----------
    logger : Logger
        Logger
    config : Config
        Configuration
    timezone : timezone
        Timezone
    endpoint_uri : str
        Endpoint URI of WebService
    """

    def __init__(self, logger=None, config=None, timezone=None):
        """
        Parameters
        ----------
        logger : Logger, default None
            Logger
        config : Config, default None
            Configuration
        timezone : timezone, default None
            Timezone
        """
        super().__init__(logger, config, timezone)
        self.endpoint_uri = ""

    def execute(self, request, session, connection, performance):
        try:
            service_response = self.fetch(request, session, performance)
            response = self.handle_service_response(service_response, request, session, connection, performance)
        except Exception as ex:
            self.logger.error(f"Error occured in dialog_service(client): {str(ex)} \n{traceback.format_exc()}")
            response = Response(messages=[self.handle_exception(request, session, ex, connection)])
        return response

    def fetch(self, request, session, performance):
        """
        Call and fetch data from WebService

        Parameters
        ----------
        request : Message
            Request message
        session : Session
            Session
        performance : PerformanceInfo
            Performance information

        Returns
        -------
        http_response_json : dict
            HTTP Response parsed into dict
        """
        data = encode_json({"request": request.to_dict(), "session": session.to_dict(), "performance": performance.to_dict()})
        return requests.post(self.endpoint_uri, data=data, headers={"Content-Type": "application/json"}, timeout=60).json()

    def handle_service_response(self, service_response, request, session, connection, performance):
        """
        Update session and request and make response

        Parameters
        ----------
        request : Message
            Request message
        session : Session
            Session
        connection : Connection
            Connection

        Returns
        -------
        response : Response
            Response from remote DialogService
        """
        if service_response.get("error", ""):
            error = service_response["error"]
            self.logger.error(f"Error occured in dialog_service(remote): {error}")
            return Response(messages=[self.handle_exception(request, session, None, connection)])
        else:
            # update request, session and performance
            res_request = Message.from_dict(service_response["request"])
            request.entities = res_request.entities
            res_session = Session.from_dict(service_response["session"])
            session.topic = res_session.topic
            session.data = res_session.data
            session.error = res_session.error
            performance.ticks.extend(service_response["performance"]["ticks"])
            # make response data
            return Response.from_dict(service_response["response"])
