import traceback
from azure.functions import HttpRequest, HttpResponse
from minette.session import Session
from minette.message import Message, Response
from minette.performance import PerformanceInfo
from minette.dialog.webservice import HttpDialogService


class AzureFunctionsDialogService(HttpDialogService):
    async def run(self, http_request):
        # just return 200 when warmup request
        if await self.is_warmup(http_request):
            return await self.make_response(status_code=200)

        # parse request and session from http request
        try:
            request, session, performance = await self.parse_request(http_request)
        except Exception as ex:
            self.logger.error(f"Invalid request: {str(ex)} \n{traceback.format_exc()}")
            return await self.make_response(error="Invalid request", status_code=400)

        # get connection
        try:
            connection = self.connection_provider.get_connection() if self.connection_provider else None
        except Exception as ex:
            self.logger.error(f"Failed in getting connection: {str(ex)} \n{traceback.format_exc()}")
            return await self.make_response(error="Failed in getting connection", status_code=500)

        # execute dialog_service and return respose
        response = await self.execute(request, session, connection, performance)

        # close connection
        if connection:
            connection.close()

        # make and return response
        try:
            return await self.make_response(
                request=request, session=session, performance=performance, response=response)
        except Exception as ex:
            self.logger.error(f"Failed in making response: {str(ex)} \n{traceback.format_exc()}")
            return await self.make_response(error="Failed in making response", status_code=500)

    async def is_warmup(self, http_request):
        """
        Parameters
        ----------
        http_request : object
            HTTP Request object of Azure Functions

        Returns
        -------
        is_warmup : bool
            Request for warming up or not
        """
        return True if http_request.params.get("warmup", "") else False

    async def parse_request(self, http_request):
        """
        Parameters
        ----------
        http_request : object
            HTTP Request object of Azure Functions

        Returns
        -------
        request : Message
            Request message from user
        session : Session
            Session
        performance : PerformanceInfo
            PerformanceInfo
        """
        req_json = http_request.get_json()
        return Message.from_dict(req_json["request"]), Session.from_dict(req_json["session"]), PerformanceInfo.from_dict(req_json["performance"])

    async def make_response(self, request=None, session=None, performance=None, response=None, error=None, status_code=200, content_type="application/json"):
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
            HTTP Response object of Azure Functions
        """
        data = super().make_response(request, session, performance, response, error, status_code, content_type)
        return HttpResponse(data, status_code=status_code, mimetype=content_type)

    async def execute(self, request, session, connection, performance):
        """
        Main logic of DialogService

        Parameters
        ----------
        request : Message
            Request message
        session : Session
            Session
        exception : Exception
            Exception
        connection : Connection
            Connection
        performance : PerformanceInfo
            Performance information

        Returns
        -------
        response : Response
            Response from chatbot
        """
        try:
            # extract entities
            entities = await self.extract_entities(request, session, connection)
            for k, v in entities.items():
                if not request.entities.get(k, ""):
                    request.entities[k] = v
            performance.append("dialog_service.extract_entities")

            # initialize session data
            if session.topic.is_new:
                session.data = self.get_slots(request, session, connection)
            performance.append("dialog_service.get_slots")

            # process request
            await self.process_request(request, session, connection)
            performance.append("dialog_service.get_slots")

            # compose response
            response_messages = await self.compose_response(request, session, connection)
            if not response_messages:
                self.logger.info("No response")
                response_messages = []
            elif not isinstance(response_messages, list):
                response_messages = [response_messages]
            response = Response()
            for rm in response_messages:
                if isinstance(rm, Message):
                    response.messages.append(rm)
                elif isinstance(rm, str):
                    response.messages.append(request.reply(text=rm))
            performance.append("dialog_service.compose_response")

        except Exception as ex:
            self.logger.error("Error occured in dialog_service: " + str(ex) + "\n" + traceback.format_exc())
            response = Response(messages=[await self.handle_exception(request, session, ex, connection)])

        return response

    async def extract_entities(self, request, session, connection):
        """
        Extract entities from request message

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
        entities : dict
            Entities extracted from request message
        """
        return {}

    async def process_request(self, request, session, connection):
        """
        Process your chatbot's functions/skills and setup session data

        Parameters
        ----------
        request : Message
            Request message
        session : Session
            Session
        connection : Connection
            Connection
        """
        super().process_request(request, session, connection)

    async def compose_response(self, request, session, connection):
        """
        Compose response messages using session data

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
            Response from chatbot
        """
        return super().compose_response(request, session, connection)

    async def handle_exception(self, request, session, exception, connection):
        """
        Handle exception and return error response message

        Parameters
        ----------
        request : Message
            Request message
        session : Session
            Session
        exception : Exception
            Exception
        connection : Connection
            Connection

        Returns
        -------
        response : Response
            Error response from chatbot
        """
        return super().handle_exception(request, session, exception, connection)
