""" Core module of Minette """
from time import time
import logging
import traceback
from copy import deepcopy
from pytz import timezone as tz
import asyncio
from minette import Minette
from minette.database import ConnectionProvider
from minette.session import SessionStore, Topic
from minette.user import UserRepository
from minette.dialog import DialogRouter, DialogService
from minette.tagger import Tagger
from minette.message import Message, MessageLogger, Response
from minette.task import Scheduler
from minette.util import get_class
from minette.config import Config
from minette.performance import PerformanceInfo


class AsyncMinette(Minette):
    """
    Asynchronous Chatbot (Just DialogService.execute at this moment)

    Attributes
    ----------
    connection_provider : ConnectionProvider
        Connection provider
    session_store: SessionStore
        Session store
    user_repository: UserRepository
        User repository
    dialog_router: DialogRouter
        Dialog router
    default_dialog_service : DialogService, default None
        Default dialog service for unhandled request
    task_scheduler : Scheduler
        Task scheduler
    message_logger: MessageLogger
        Message logger
    tagger: Tagger
        Tagger
    logger : logging.Logger
        Logger
    config : Config
        Configuration
    timezone : timezone
        Timezone
    prepare_table : bool
        Create tables if not existing
    """

    async def chat(self, request):
        """
        Interface to chat with your bot

        Parameters
        ----------
        request : Message
            Message to chatbot

        Returns
        -------
        response : Response
            Response from chatbot
        """
        try:
            performance = PerformanceInfo()
            request = Message(text=request) if isinstance(request, str) else request
            # connection
            connection = self.connection_provider.get_connection()
            performance.append("connection_provider.get_connection")
            # tagger
            request.words = self.tagger.parse(request.text)
            performance.append("tagger.parse")
            # user
            request.user = self.get_user(request, connection)
            performance.append("get_user")
            # session
            session = self.get_session(request, connection)
            performance.append("get_session")
            # route dialog
            dialog_service = self.dialog_router.execute(request, session, connection, performance)
            performance.append("dialog_router.execute")
            # process dialog
            if asyncio.iscoroutinefunction(dialog_service.execute):
                response = await dialog_service.execute(request, session, connection, performance)
            else:
                response = dialog_service.execute(request, session, connection, performance)
            performance.append("dialog_service.execute")
            # save session
            session = self.save_session(session, connection)
            performance.append("save_session")
            # save user
            self.save_user(request.user, connection)
            performance.append("save_user")
        except Exception as ex:
            self.logger.error("Error occured in chat: " + str(ex) + "\n" + traceback.format_exc())
            response = Response()
        finally:
            # set performance info to response
            response.performance = performance
            if connection:
                # message log
                try:
                    self.message_logger.write(request, response, session, connection)
                except Exception as ex:
                    self.logger.error("Error occured in logging message: " + str(ex) + "\n" + traceback.format_exc())
                # close connection
                connection.close()
        return response
