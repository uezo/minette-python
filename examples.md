
# Sample codes

These codes are included in `examples` if you want to try mmediately.

# 🎲 Dice bot

This example shows you how to implement your logic and build the reply message using the result of logic.

```python
import random
from minette import Minette, DialogService


# Custom dialog service
class DiceDialogService(DialogService):
    # Process logic and build context data
    def process_request(self, request, context, connection):
        context.data = {
            "dice1": random.randint(1, 6),
            "dice2": random.randint(1, 6)
        }

    # Compose response message using context data
    def compose_response(self, request, context, connection):
        return "Dice1:{} / Dice2:{}".format(
            str(context.data["dice1"]), str(context.data["dice2"]))


if __name__ == "__main__":
    # Create bot
    bot = Minette(default_dialog_service=DiceDialogService)
    # Start conversation
    while True:
        req = input("user> ")
        res = bot.chat(req)
        for message in res.messages:
            print("minette> " + message.text)
```

Run it.

```
$ python dice.py

user> dice
minette> Dice1:1 / Dice2:2
user> more
minette> Dice1:4 / Dice2:5
user> 
minette> Dice1:6 / Dice2:6
```


# ✅ Todo bot

This example shows the simplest usage of SQLAlchemy experimentally supported at 0.4.1. You can use `Session` created for each request.

```python
from minette import Minette, DialogService
from minette.datastore.sqlalchemystores import SQLAlchemyStores, Base
from datetime import datetime
from sqlalchemy import Column, Integer, String, DateTime, Boolean

# Define datamodel
class TodoModel(Base):
    __tablename__ = "todolist"
    id = Column("id", Integer, primary_key=True, autoincrement=True)
    created_at = Column("created_at", DateTime, default=datetime.utcnow())
    text = Column("title", String(255))
    is_closed = Column("is_closed", Boolean, default=False)

# TodoDialog
class TodoDialogService(DialogService):
    def process_request(self, request, context, connection):

        # Note: Session of SQLAlchemy is provided as argument `connection`

        # Register new item
        if request.text.lower().startswith("todo:"):
            item = TodoModel()
            item.text = request.text[5:].strip()
            connection.add(item)
            connection.commit()
            context.data["item"] = item
            context.topic.status = "item_added"

        # Close item
        elif request.text.lower().startswith("close:"):
            item_id = int(request.text[6:])
            item = connection.query(TodoModel).filter(TodoModel.id==item_id).first()
            if item:
                item.is_closed = True
                connection.commit()
                context.data["item"] = item
                context.topic.status = "item_closed"
            else:
                context.data["item_id"] = item_id
                context.topic.status = "item_not_found"

        # Get item list
        elif request.text.lower().startswith("list") or request.text.lower().startswith("show"):
            if "all" in request.text.lower():
                items = connection.query(TodoModel).all()
            else:
                items = connection.query(TodoModel).filter(TodoModel.is_closed==0).all()
            if items:
                context.data["items"] = items
                context.topic.status = "item_listed"
            else:
                context.topic.status = "no_items"

    # Return reply message to user
    def compose_response(self, request, context, connection):
        if context.topic.status == "item_added":
            return "New item created: □ #{} {}".format(context.data["item"].id, context.data["item"].text)
        elif context.topic.status == "item_closed":
            return "Item closed: ✅#{} {}".format(context.data["item"].id, context.data["item"].text)
        elif context.topic.status == "item_not_found":
            return "Item not found: #{}".format(context.data["item_id"])
        elif context.topic.status == "item_listed":
            text = "Todo:"
            for item in context.data["items"]:
                text += "\n{}#{} {}".format("□ " if item.is_closed == 0 else "✅", item.id, item.text)
            return text
        elif context.topic.status == "no_items":
            return "No todo item registered"
        else:
            return "Something wrong :("

# Create an instance of Minette with TodoDialogService and SQLAlchemyStores
bot = Minette(
    default_dialog_service=TodoDialogService,
    data_stores=SQLAlchemyStores,
    connection_str="sqlite:///todo.db",
    db_echo=False)

# Create table(s) using engine
Base.metadata.create_all(bind=bot.connection_provider.engine)

# Send and receive messages
while True:
    req = input("user> ")
    res = bot.chat(req)
    for message in res.messages:
        print("minette> " + message.text)
```

Run it.

```bash
$ python todo.py

user> todo: Buy beer
minette> New item created: □ #1 Buy beer
user> todo: Take a bath
minette> New item created: □ #2 Take a bath
user> todo: Watch anime
minette> New item created: □ #3 Watch anime
user> close: 2
minette> Item closed: ✅#2 Take a bath
user> list
minette> Todo:
□ #1 Buy beer
□ #3 Watch anime
user> list all
minette> Todo:
□ #1 Buy beer
✅#2 Take a bath
□ #3 Watch anime
```


# 🇯🇵 Translation bot

This example shows;
- how to make the successive conversation using context
- how to extract intent from what user is saying and route the proper DialogService
- how to configure API Key using configuration file (minette.ini)

```python
"""
Translation Bot

Notes
Signup Microsoft Cognitive Services and get API Key for Translator Text API
https://azure.microsoft.com/ja-jp/services/cognitive-services/

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
```

Let's talk to your chatbot!

```
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
```
