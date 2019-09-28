# Minette for Python
Minette is a minimal and extensible chatbot framework. It is extremely easy to develop and the architecture preventing to be spaghetti code enables you to scale up to complex chatbot.


## Caution

__Destructive change from version 0.3__

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

# Installation

To install minette, simply:

```
$ pip install minette
```

If you want to get the newest version, install from this Github repository.

```
$ pip install git+https://github.com/uezo/minette-python
```

# Running the echo bot

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
from minette.adaper.lineadapter import LineAdapter

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

Python 3.5 or higher is supported. Mainly developed using Python 3.6.6 on Mac OSX.

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
- mecab-python3 == 0.7 (for MeCabTagger. Latest version has a critical bug)
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
$ pip install mecab-python3
```

### Usase
```python
from minette.tagger.mecab import MeCabTagger
bot = Minette.create(
    tagger=MeCabTagger
)
```
