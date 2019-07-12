import traceback
from linebot.exceptions import InvalidSignatureError
from linebot.models import Profile
from aiolinebot import AioLineBotApi
from minette.message import Message, Response
from minette.channel.line import LineAdapter


class AsyncLineAdapter(LineAdapter):
    """
    Asynchronous adapter for LINE Messaging API

    Attributes
    ----------
    minette : Minette
        Instance of Minette
    channel_secret : str
        Channel Secret for your LINE Bot
    channel_access_token : str
        Channel Access Token for your LINE Bot
    api : AioLineBotApi
        LINE Messaging API using aiohttp
    threads : int
        Number of worker thread
    thread_pool : [WorkerThread]
        Pool of worker threads for processing queued requests
    logger : Logger
        Logger
    debug : bool
        Debug mode
    """

    def __init__(
        self, minette, channel_secret, channel_access_token, *,
        api=None, threads=0, logger=None, debug=False
    ):
        """
        Parameters
        ----------
        minette : Minette
            Instance of Minette
        channel_secret : str or None, default None
            Channel Secret for your LINE Bot
        channel_access_token : str or None, default None
            Channel Access Token for your LINE Bot
        api : AioLineBotApi, default None
            Asynchronous Messaging API interface
        threads : int, default 16
            Number of worker thread
        logger : Logger, default None
            Logger
        debug : bool, default False
            Debug mode
        """
        api = api or AioLineBotApi(channel_access_token)
        super().__init__(
            minette, channel_secret, channel_access_token,
            api=api, threads=threads, logger=logger, debug=debug
        )

    async def chat(self, request_data_as_text, request_headers):
        """
        Interface to chat with LINE Bot

        Parameters
        ----------
        request_data_as_text : str
            Request data from LINE Messaging API as string
        request_headers : dict
            Request headers from LINE Messaging API as dict

        Returns
        -------
        response : Response
            Response that shows queued status
        """
        try:
            events = self.parser.parse(request_data_as_text, request_headers.get("X-Line-Signature", ""))
            for ev in events:
                message = self.to_minette_message(ev)
                reply_token = ev.reply_token if hasattr(ev, "reply_token") else ""
                response = await self.minette.chat(message)
                line_messages = [self.to_line_message(m) for m in response.messages]
                if line_messages:
                    await self.reply(line_messages, reply_token)
            return Response(messages=[Message(text="done", type="system")])
        except InvalidSignatureError as ise:
            self.logger.error("Request signiture is invalid: " + str(ise) + "\n" + traceback.format_exc())
            return Response(messages=[Message(text="invalid signiture", type="system")])
        except Exception as ex:
            self.logger.error("Request parsing error: " + str(ex) + "\n" + traceback.format_exc())
            return Response(messages=[Message(text="failure in parsing request", type="system")])

    async def reply(self, line_messages, reply_token, timeout=5):
        """
        Send reply messages to LINE Messaging API

        Parameters
        ----------
        line_messages : list
            List of SendMessage objects
        reply_token : str
            ReplyToken for LINE Messaging API
        timeout : int
            Timeout (seconds)
        """
        await self.api.reply_message(reply_token, line_messages, timeout=timeout)

    async def push(self, channel_user_id, line_messages, timeout=5):
        """
        Interface to push messages to user

        Parameters
        ----------
        channel_user_id : str
            Destination user
        line_messages : list
            List of SendMessage objects
        timeout : int
            Timeout (seconds)

        Returns
        -------
        success : bool
            Message pushed successfully or not
        """
        await self.api.push_message(channel_user_id, line_messages, timeout)

    async def update_profile(self, user, timeout=5):
        """
        Update user profile by LINE Messaging API

        Parameters
        ----------
        user : User
            User to update
        """
        if not user.channel_user_id:
            return None
        try:
            profile = await self.api.get_profile(user.channel_user_id, timeout)
            user.name = profile.display_name
            user.profile_image_url = profile.picture_url
            return profile
        except Exception as ex:
            self.logger.error("Error occured in updating profile: " + str(ex) + "\n" + traceback.format_exc())
            return None
