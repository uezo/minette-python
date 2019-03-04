import sys
import os
sys.path.append(os.pardir)
from datetime import datetime
import requests
from minette import Minette
from minette.dialog import DialogRouter, DialogService, EchoDialogService


class WeatherDialogService(DialogService):
    # Get city name from text (Replace here with some APIs)
    @staticmethod
    def get_city(text):
        t = text.lower()
        if "london" in t:
            return "london"
        elif "paris" in t:
            return "paris"
        elif "tokyo" in t:
            return "tokyo"
        elif "yokohama" in t:
            return "yokohama"
        elif "chiba" in t:
            return "chiba"
        else:
            return ""

    # Extract entities from request message
    def extract_entities(self, request, session, connection):
        return {
            "city": self.get_city(request.text)
        }

    # Get initial session data when the topic starts
    def get_slots(self, request, session, connection):
        return {
            "city": session.previous_data("city", ""),
            "weather": ""
        }

    # Process logic and build session data
    def process_request(self, request, session, connection):
        # Get city from entity or session
        session.data["city"] = request.entities["city"] or session.data["city"]
        # Get weather if the city is determined
        if session.data["city"]:
            try:
                res = requests.get("http://api.openweathermap.org/data/2.5/forecast", params={
                    "APPID": "<YOUR API KEY>",
                    "q": session.data["city"]
                }).json()
                session.data["weather"] = res["list"][0]["weather"][0]["main"]
            except Exception as ex:
                session.set_error(ex)

    # Compose response message
    def compose_response(self, request, session, connection):
        # Return response message
        if session.data["weather"]:
            return session.data["weather"]
        elif session.error:
            return "Error occured. Try again."
        else:
            session.topic.keep_on = True
            return "City name?"


class MyDialogRouter(DialogRouter):
    # Configure intent->dialog routing table
    def configure(self):
        self.intent_resolver = {"WeatherIntent": WeatherDialogService}

    # Set WeatherIntent when user said something starts with "weather"
    def extract_intent(self, request, session, connection):
        if request.text.lower().startswith("weather"):
            return "WeatherIntent"


if __name__ == "__main__":
    # Create bot
    bot = Minette.create(dialog_router=MyDialogRouter, default_dialog_service=EchoDialogService)

    # Start conversation
    while True:
        req = input("user> ")
        res = bot.chat(req)
        for message in res.messages:
            print("minette> " + message.text)
