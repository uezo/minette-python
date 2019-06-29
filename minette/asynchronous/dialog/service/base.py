import traceback
from minette.session import Session
from minette.message import Message, Response
from minette.performance import PerformanceInfo
from minette.dialog import DialogService


class AsyncDialogService(DialogService):
    async def execute(self, request, session, connection, performance):
        """
        Main logic of AsyncDialogService

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
