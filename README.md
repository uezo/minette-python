# Minette for Python
[![Downloads](https://pepy.tech/badge/minette)](https://pepy.tech/project/minette)

Minette is a minimal and extensible chatbot framework. It is extremely easy to develop and the architecture preventing to be spaghetti code enables you to scale up to complex chatbot.

[🇯🇵日本語のREADMEはこちら](./README.ja.md)

# 🎉 version 0.4.2 is available

- 0.4.2 Aug 26, 2020
    - Support [Janome 0.4](https://mocobeta.github.io/janome/en/)
- 0.4.1 Aug 7, 2020
    - SQLAlchemy is supported (experimental). See also [examples/todo.py](https://github.com/uezo/minette-python/blob/master/examples/todo.py)

# 📦 Installation

To install minette, simply:

```
$ pip install minette
```

# 🤖 Running the echo bot

Running echo bot is extremely easy.

```python
from minette import Minette, EchoDialogService

# Create chatbot instance using EchoDialogService
bot = Minette(default_dialog_service=EchoDialogService)

# Send and receive messages
while True:
    req = input("user> ")
    res = bot.chat(req)
    for message in res.messages:
        print("minette> " + message.text)
```

```
$ python echo.py
user> hello
minette> You said: hello
```

Creating LINE bot is also super easy.

```python
from flask import Flask, request
from minette import Minette, EchoDialogService
from minette.adapter.lineadapter import LineAdapter

# Create chatbot wrapped by LINE adapter
bot = LineAdapter(default_dialog_service=EchoDialogService)

# Create web server and its request handler
app = Flask(__name__)

@app.route("/", methods=["POST"])
def handle_webhook():
    bot.handle_http_request(request.data, request.headers)
    return "ok"

# Start web server
app.run(port=12345)
```

# Supported Platforms

Python 3.5 or higher is supported. Mainly developed using Python 3.7.7 on Mac OSX.

## Messaging Service

- LINE
- Clova
- Symphony

You can connect to other messaging services by extending `minette.Adapter`.

## Database

- SQLite
- Azure SQL Database
- Azure Table Storage
- MySQL (Tested on 8.0.13)

You can use other databases you like by extending the classes in `minette.datastore` package. (Context / User / MessageLog)
Or, maybe you can use supported databases by SQLAlchemy by just setting connection string for it.

## Tagger

- MeCab
- Janome

You can use other morphological engines including cloud services and for other languages by extending `minette.Tagger`.
To setup and use MeCab and Janome Tagger, see the Appendix at the bottom of this page.

# Dependencies

(Required)
- requests >= 2.21.0
- pytz >= 2018.9
- schedule >= 0.6.0

(Optional)
- line-bot-sdk >= 1.12.1 (for LINE)
- clova-cek-sdk >= 1.1.1
- sym-api-client-python >= 0.1.16 (for Symphony)
- pyodbc >= 4.0.26 (for Azure SQL Databsae)
- azure-cosmosdb-table >= 1.0.5 (for Azure Table Storage)
- MySQLdb (for MySQL)
- SQLAlchemy (for SQLAlchemyStores)
- mecab-python3 >= 1.0.1 (for MeCabTagger)
- Janome >= 0.3.8 (for Janome Tagger)

# Features

To create a bot, developers just implement `DialogService(s)` and `DialogRouter`.

- DialogService: process the application logic and compose the response message to the user
- DialogRouter: extract intents and entities from request message to route the proper DialogService

[![Architecture](http://uezo.net/img/minette_architecture.png)](http://uezo.net/img/minette_architecture.png)

Any other common operations (e.g. context management) are done by framework.

## Context management
Minette provides a data store that enables your bot to continue conversasion accross the requests like HTTP Session.

Set data
```python
# to use context data at the next request, set `True` to `context.topic.keep_on` in DialogService
context.data["pizza_name"] = "Seafood Pizza"
context.topic.keep_on = True
```

Get data
```python
pizza_name = context.data["pizza_name"]
```

## User management
Users are identified by the Channel (e.g LINE, FB Messanger etc) and the UserID for the Channel. Each users are automatically registered at the first access and each changes for user is saved automatically.

```python
# framework saves the updated user info automatically and keep them until the app delete them
request.user.nickname = "uezo"
request.user.data["horoscope"] = "cancer"
```

## Natural language analyzing
Taggers are the components for analyzing the text of request and the result will be automatically set to request object. Minette has 3 built-in taggers for Japanese - MeCabTagger, MeCabServiceTagger and JanomeTagger.

```python
>>> from minette import *
>>> tagger = MeCabServiceTagger()
Do not use default API URL for the production environment. This is for trial use only. Install MeCab and use MeCabTagger instead.
>>> words = tagger.parse("今日は良い天気です")
>>> words[0].to_dict()
{'surface': '今日', 'part': '名詞', 'part_detail1': '副詞可能', 'part_detail2': '', 'part_detail3': '', 'stem_type': '', 'stem_form': '', 'word': '今日', 'kana': 'キョウ', 'pronunciation': 'キョー'}
```

Sample use case in `DialogService` is here.
```python
def process_request(self, request, context, connection):
    # extract nouns from request.text == "今日は良い天気です"
    nouns = [w.surface for w in request.words if w.part == "名詞"]
    # set ["今日", "天気"] to context data
    context.data["nouns"] = nouns
```

## Task scheduler
Built-in task scheduler is ready-to-use. Your chatbot can run periodic jobs without cron.

```python
class MyTask(Task):
    # implement periodic task in `do` method
    def do(self, arg1, arg2):
        # The Logger of scheduler is available in each tasks
        self.logger.info("Task started!: {} / {}".format(arg1, arg2))

# Create Scheculer
sc = Scheduler()
# Register the task. This task runs every 3 seconds
sc.every_seconds(MyTask, seconds=3, arg1="val1", arg2="val2")
# Start the scheduler
sc.start()
```

## Message Log
Request, response and context at each turns are stored as Message Log. It provides you the very useful information to debug and improve your chatbot.

# Sample codes

These codes are included in `examples` if you want to try mmediately.

## Dice bot

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


## Todo bot

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


## Translation bot

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

# Testing Dialogs
Minette provides a helper to test dialogs. This is an example using `pytest`.

- `channel_user_id` for each test cases(functions) is set to request automatically.
- `chat` method takes arguments for `Message`. This enables you `bot.chat("hello", intent="HelloIntent")` instead of `bot.chat(Message(text="hello", intent="HelloIntent"))` to make your test code simple.
- Response from `chat` has `text` attribute that equals to `response.messages[0].text`.

```python
import pytest
from minette import Message, DialogService, Priority, Payload
from minette.test.helper import MinetteForTest

# dialogs to test
class FooDialog(DialogService):
    def compose_response(self, request, context, connetion):
        return "foo:" + request.text

class BarDialog(DialogService):
    def compose_response(self, request, context, connetion):
        context.topic.keep_on = True
        return "bar:" + request.text

class PayloadDialog(DialogService):
    def compose_response(self, request, context, connetion):
        return "payload:" + str(request.payloads[0].content)

# bot created for each test functions
@pytest.fixture(scope="function")
def bot():
    # use MinetteForTest instead of Minette
    return MinetteForTest(
        intent_resolver={
            "FooIntent": FooDialog,
            "BarIntent": BarDialog,
            "PayloadIntent": PayloadDialog
        },
    )

# test cases function using bot
def test_example(bot):
    # trigger intent
    assert bot.chat("hello", intent="FooIntent").text == "foo:hello"
    # empty response without intent
    assert bot.chat("hello").text == ""
    # trigger other intent
    assert bot.chat("hello", intent="BarIntent").text == "bar:hello"
    # context and topic is kept by dialog service
    assert bot.chat("hi", intent="FooIntent").text == "bar:hi"
    assert bot.chat("yo").text == "bar:yo"
    # update topic by higher priority request
    assert bot.chat("hello", intent="FooIntent", intent_priority=Priority.High).text == "foo:hello"

def test_payload(bot):
    # use Message to test your dialog with payloads, channel_message and so on
    assert bot.chat(Message(
        intent="PayloadIntent",
        type="data",
        text="hello",
        payloads=[Payload(content={"key1": "value1"})]
    )).text == "payload:" + str({"key1": "value1"})
```


# License
This software is licensed under the Apache v2 License.

# Appendix

## Setup Janome Tagger

### Install dependency
```
$ pip install janome
```

### Usage

```python
from minette.tagger.janometagger import JanomeTagger
bot = Minette.create(
    tagger=JanomeTagger
)
```

If you have a user dictionary in MeCab IPADIC format, configure like below in minette.ini.

```ini
janome_userdic = /path/to/userdic.csv
```

## Setup MeCab Tagger

### Installing MeCab
- Ubuntu 16.04
```
$ sudo apt-get install mecab libmecab-dev mecab-ipadic
$ sudo apt-get install mecab-ipadic-utf8
```
- Mac OSX
```
$ brew install mecab mecab-ipadic git curl xz
```

### Installing python binding
```
$ pip install mecab-python3==0.7
```
Version 0.996.1 has a bug(?) so we strongly recommend to use version 0.7.


### Usase
```python
from minette.tagger.mecab import MeCabTagger
bot = Minette.create(
    tagger=MeCabTagger
)
```

# Appendix2. Migration from version 0.3

- Some packages are deprecated. All standard classes can be imported from `minette`.
- The way to create instance of `Minette` is changed. (just call constructor)
- `Session` is renamed to `Context`. The arguments named `session` is also changed.
- `minette.user.User#save()` is deleted. Create `UserStore` and call `save(user)` instead.
- `SessionStore` -> `ContextStore`, `UserRepository` -> `UserStore`, `MessageLogger` -> `MessageLogStore`
- HTTP request handler method of `LineAdapter` is changed to `handle_http_request`.

If you need version 0.3 install from github.

```
$ pip install git+https://github.com/uezo/minette-python.git@v0.3
```
