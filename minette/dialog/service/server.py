import logging
import traceback
from time import time
from pytz import timezone as tz
from minette.config import Config
from minette.session import Session
from minette.message import Message, Response
from minette.dialog.service import DialogService
from minette.serializer import encode_json


class HttpDialogServer:
    """
    Base class of HTTP-Based DialogService Server

    Attributes
    ----------
    logger : Logger
        Logger
    config : Config
        Configuration
    timezone : timezone
        Timezone
    connection_str : str
        Connection string for database
    connection_provider : ConnectionProvider
        ConnectionProvider
    """

    def __init__(self, dialog_service, config_file="./minette.ini", connection_provider=None):
        """
        Parameters
        ----------
        dialog_service : DialogService
            DialogService to publish as web service
        config_file : str, default "./minette.ini"
            Path for configuration file
        connection_provider : ConnectionProvider, default None
            Database connection provider
        """
        if isinstance(dialog_service, type):
            dialog_service = dialog_service()

        # setup config, logger, timezone and connection
        dialog_service.config = dialog_service.config or Config(config_file)
        self.config = dialog_service.config
        dialog_service.logger = dialog_service.logger or Minette.get_logger(logfile=self.config.get("logfile")) if self.config.get("logfile") else logging
        self.logger = dialog_service.logger
        dialog_service.timezone = dialog_service.timezone or tz(self.config.get("timezone", default="UTC"))
        self.timezone = dialog_service.timezone
        self.connection_provider = connection_provider
        if not self.connection_provider:
            connection_provider_classname = self.config.get("connection_provider")
            connection_str = self.config.get("connection_str")
            if connection_provider_classname and connection_str:
                self.connection_provider = get_class(connection_provider_classname)(connection_str)

        # set instance of dialog_service
        self.dialog_service = dialog_service

    def run(self, http_request):
        # just return 200 when warmup request
        if self.is_warmup(http_request):
            return self.make_response(status_code=200)

        # parse request and session from http request
        try:
            request, session, performance = self.parse_request(http_request)
        except Exception as ex:
            self.logger.error(f"Invalid request: {str(ex)} \n{traceback.format_exc()}")
            return self.make_response(error="Invalid request", status_code=400)

        # get connection
        try:
            connection = self.connection_provider.get_connection() if self.connection_provider else None
        except Exception as ex:
            self.logger.error(f"Failed in getting connection: {str(ex)} \n{traceback.format_exc()}")
            return self.make_response(error="Failed in getting connection", status_code=500)

        # execute dialog_service and return respose
        response = self.dialog_service.execute(request, session, connection, performance)

        # close connection
        if connection:
            connection.close()

        # make and return response
        try:
            return self.make_response(
                request=request, session=session, performance=performance, response=response)
        except Exception as ex:
            self.logger.error(f"Failed in making response: {str(ex)} \n{traceback.format_exc()}")
            return self.make_response(error="Failed in making response", status_code=500)

    def is_warmup(self, http_request):
        """
        Parameters
        ----------
        http_request : object
            HTTP Request object that depends on Web application frameworks

        Returns
        -------
        is_warmup : bool
            Request for warming up or not
        """
        return False

    def parse_request(self, http_request):
        """
        Parameters
        ----------
        http_request : object
            HTTP Request object that depends on Web application frameworks

        Returns
        -------
        request : Message
            Request message from user
        session : Session
            Session
        performance : PerformanceInfo
            PerformanceInfo
        """
        return None, None, None

    def make_response(self, request=None, session=None, performance=None, response=None, error=None, status_code=200, content_type="application/json"):
        """
        Parameters
        ----------
        request : Message, default None
            Request message
        session : Session
            Session, default None
        performance : PerformanceInfo
            Performance information
        response : Response, default None
            Response from chatbot
        error : str, default None
            Error message
        status_code : int, default 200
            Status code
        content_type : str, default "application/json"
            Content type set in response header

        Returns
        -------
        response : object
            HTTP Response object that depends on Web application frameworks
        """
        request_dict = request.to_dict() if request else None
        session_dict = session.to_dict() if session else None
        performance_dict = performance.to_dict() if performance else None
        response_dict = response.to_dict() if response else []
        data = encode_json(
            {
                "request": request_dict,
                "session": session_dict,
                "performance": performance_dict,
                "response": response_dict,
                "error": error
            }
        )
        return data
