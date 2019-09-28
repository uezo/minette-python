"""
Translation Bot

This example shows;
    - how to make the successive conversation using context
    - how to extract intent from what user is saying and route the proper DialogService
    - how to configure API Key using configuration file (minette.ini)

Notes
Signup Microsoft Cognitive Services and get API Key for Translator Text API
https://azure.microsoft.com/ja-jp/services/cognitive-services/


Sample conversation
    $ python translation.py

    user> hello
    minette> You said: hello
    user> ignore
    user> okay
    minette> You said: okay
    user> translate
    minette> Input words to translate into Japanese
    user> I'm feeling happy
    minette> I'm feeling happy in Japanese: 幸せな気分だ
    user> My favorite food is soba
    minette> My favorite food is soba in Japanese: 私の好きな食べ物はそばです。
    user> stop
    minette> Translation finished
    user> thank you
    minette> You said: thank you

"""
from datetime import datetime
import requests
from minette import (
    Minette,
    DialogRouter,
    DialogService,
    EchoDialogService   # built-in EchoDialog
)


class TranslationDialogService(DialogService):
    # Process logic and build context data
    def process_request(self, request, context, connection):
        # Just set the topic.status at the start and the end of translation dialog
        if context.topic.is_new:
            context.topic.status = "start_translation"

        elif request.text == "stop":
            context.topic.status = "end_translation"

        # Translate to Japanese
        else:
            # translate using Azure Cognitive Services
            api_url = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to=ja"
            headers = {
                # set `translation_api_key` at the `minette` section in `minette.ini`
                #
                # [minette]
                # translation_api_key=YOUR_TRANSLATION_API_KEY
                "Ocp-Apim-Subscription-Key": self.config.get("translation_api_key"),
                "Content-type": "application/json"
            }
            data = [{"text": request.text}]
            api_result = requests.post(api_url, headers=headers, json=data).json()
            # set translated text to context
            context.data["translated_text"] = api_result[0]["translations"][0]["text"]
            context.topic.status = "process_translation"

    # Compose response message
    def compose_response(self, request, context, connection):
        if context.topic.status == "start_translation":
            context.topic.keep_on = True
            return "Input words to translate into Japanese"
        elif context.topic.status == "end_translation":
            return "Translation finished"
        elif context.topic.status == "process_translation":
            context.topic.keep_on = True
            return request.text + " in Japanese: " + context.data["translated_text"]


class MyDialogRouter(DialogRouter):
    # Configure intent->dialog routing table
    def register_intents(self):
        self.intent_resolver = {
            # If the intent is "TranslationIntent" then use TranslationDialogService
            "TranslationIntent": TranslationDialogService,
            "EchoIntent": EchoDialogService
        }

    # Implement the intent extraction logic
    def extract_intent(self, request, context, connection):
        # Return TranslationIntent if request contains "translat"
        if "translat" in request.text.lower():
            return "TranslationIntent"

        # Return EchoIntent if request is not "ignore"
        # If "ignore", chatbot doesn't return reply message.
        elif request.text.lower() != "ignore":
            return "EchoIntent"


if __name__ == "__main__":
    # Create bot
    bot = Minette(dialog_router=MyDialogRouter)

    # Start conversation
    while True:
        req = input("user> ")
        res = bot.chat(req)
        for message in res.messages:
            print("minette> " + message.text)
