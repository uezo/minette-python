# Minette for Python
Minette is a micro bot framework. Session and user management, Natural language analyzing and architecture for multi-skill/character bot are ready-to-use.

## Caution

Destructive change from version 0.1

If you need version 0.1 install from github.

```
$ pip install git+https://github.com/uezo/minette-python.git@v0.1
```

## Installation

To install minette, simply:

```
$ pip install minette
```

If you want to get the newest version, install from this Github repository.

```
$ pip install git+https://github.com/uezo/minette-python
```

## Running the echo bot

Code like below and run.

```python
from minette import Minette

# Create bot
bot = Minette.create(default_dialog_service=EchoDialogService)

# Start conversation
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

## Architecture of Minette

To create a bot, developers just implement `DialogService(s)` to process the application logic and compose the response message to the user and `DialogRouter` to extract intents and entities from what the user is saying to route the proper DialogService.

[![Architecture](http://uezo.net/img/minette_architecture.png)](http://uezo.net/img/minette_architecture.png)

Any other common operations (e.g. session management) are done by Minette framework.

## Session management (Context management)
Minette provides a data store that enables your bot to continue conversasion accross the requests like HTTP Session. Default SessionStore uses Sqlite but you can make custom SessionStore and change to any database you like.

## User management
Users are identified by internal UserIDs which are given at the first access to the bot. The UserID is determined by the channel (e.g. CONSOLE, LINE, etc) and the user_id of the channel. Minette stores the data of users in Sqlite automatically and you can get (or update) it from User object.

## Task scheduler
Built-in task scheduler is ready-to-use. Your chatbot can do regular jobs without cron and the jobs can use chatbot resources like user repository.

## Natural Language Analyzing
Taggers are the components for analyzing the text of request and the result will be set to request.words property. Minette has two built-in taggers - GoogleTagger and MeCabTagger.

### Google Tagger
GoogleTagger uses Cloud Natural Language API. This separates text into words and provides tags for each of them. (e.g. NOUN, VERB, ADJ ...)

#### Usase
```python
from minette.tagger.google import GoogleTagger
bot = Minette.create(
    tagger=GoogleTagger(api_key="your api key")
)
```

### MeCab Tagger
MeCabTagger uses MeCab which is one of the most popular Japanese morphological analyzer. This provides all information of MeCab nodes. To use this tagger, MeCab and its binding for Python are required.

#### Installing MeCab
- Ubuntu 16.04
```
$ sudo apt-get install mecab libmecab-dev mecab-ipadic
$ sudo apt-get install mecab-ipadic-utf8
```
- Mac OSX
```
$ brew install mecab mecab-ipadic git curl xz
```

#### Installing Binding
```
pip install mecab-python3
```

#### Usase
```python
from minette.tagger.mecab import MeCabTagger
bot = Minette.create(
    tagger=MeCabTagger
)
```

## Adding custom skill
Here is the example of Random Dice Bot.

```python
import random
from minette import Minette
from minette.dialog import DialogService


# Custom dialog service
class DiceDialogService(DialogService):
    # Process logic and build session data
    def process_request(self, request, session, connection):
        session.data = {
            "dice1": random.randint(1, 6),
            "dice2": random.randint(1, 6)
        }

    # Compose response message using session data
    def compose_response(self, request, session, connection):
        return "Dice1:{} / Dice2:{}".format(str(session.data["dice1"]), str(session.data["dice2"]))

if __name__ == "__main__":
    # Create bot
    bot = Minette.create(default_dialog_service=DiceDialogService)
    # Start conversation
    while True:
        req = input("user> ")
        res = bot.chat(req)
        for message in res.messages:
            print("minette> " + message.text)
```

Run and say something to the bot.
```
user> dice
minette> Dice1:2 / Dice2:5
```

## License
This software is licensed under the Apache v2 License.

# Sample Codes

## Echo bot
The first bot that just echoes what you say.
```python
import minette

# create bot
bot = minette.create()

# start conversation
while True:
    req = input("user> ")
    res = bot.chat(req)
    for message in res.messages:
        print("minette> " + message.text)
```
```
user> hello
minette> You said:hello
```

## Greeting Bot
The simplest structure.
```python
from datetime import datetime
from minette import Minette
from minette.dialog import DialogService

# Custom dialog service
class GreetingDialogService(DialogService):
    # Compose response message
    def compose_response(self, request, session, connection):
        now = datetime.now()
        phrase = "It's " + now.strftime("%H:%M") + " now. "
        if now.hour < 12:
            phrase += "Good morning"
        elif now.hour < 18:
            phrase += "Hello"
        else:
            phrase += "Good evening"
        return phrase

if __name__ == "__main__":
    # Create bot
    bot = Minette.create(default_dialog_service=GreetingDialogService)
    # Start conversation
    while True:
        req = input("user> ")
        res = bot.chat(req)
        for message in res.messages:
            print("minette> " + message.text)
```
```
user> hello
minette> Good morning
```

## Dice Bot
Override process_request method to execute application logic and compose_response method to compose the response message.
```python
import random
from minette import Minette
from minette.dialog import DialogService

# Custom dialog service
class DiceDialogService(DialogService):
    # Process logic and build session data
    def process_request(self, request, session, connection):
        session.data = {
            "dice1": random.randint(1, 6),
            "dice2": random.randint(1, 6)
        }

    # Compose response message using session data
    def compose_response(self, request, session, connection):
        return "Dice1:{} / Dice2:{}".format(str(session.data["dice1"]), str(session.data["dice2"]))

if __name__ == "__main__":
    # Create bot
    bot = Minette.create(default_dialog_service=DiceDialogService)
    # Start conversation
    while True:
        req = input("user> ")
        res = bot.chat(req)
        for message in res.messages:
            print("minette> " + message.text)
```

## Multi-skill Bot
Switching GreetingDialogService and DiceDialogService using `DialogRouter`.

```python
import random
from datetime import datetime
from minette import Minette
from minette.dialog import DialogRouter, DialogService, EchoDialogService

class GreetingDialogService(DialogService):
    def compose_response(self, request, session, connection):
        now = datetime.now()
        phrase = "It's " + now.strftime("%H:%M") + " now. "
        if now.hour < 12:
            phrase += "Good morning"
        elif now.hour < 18:
            phrase += "Hello"
        else:
            phrase += "Good evening"
        return phrase

class DiceDialogService(DialogService):
    # Process logic and build session data
    def process_request(self, request, session, connection):
        session.data = {
            "dice1": random.randint(1, 6),
            "dice2": random.randint(1, 6)
        }
    # Compose response message using session data
    def compose_response(self, request, session, connection):
        return "Dice1:{} / Dice2:{}".format(str(session.data["dice1"]), str(session.data["dice2"]))

class MyDialogRouter(DialogRouter):
    # Configure intent->dialog routing table
    def configure(self):
        self.intent_resolver = {
            "DiceIntent": DiceDialogService, 
            "GreetingIntent": GreetingDialogService
        }

    # Set DiceIntent when user says "dice" or GreetingIntent when user says "hello"
    def extract_intent(self, request, session, connection):
        if request.text.lower() == "dice":
            return "DiceIntent"
        elif request.text.lower() == "hello":
            return "GreetingIntent"

if __name__ == "__main__":
    # Create bot
    bot = Minette.create(dialog_router=MyDialogRouter, default_dialog_service=EchoDialogService)
    # Start conversation
    while True:
        req = input("user> ")
        res = bot.execute(req)
        for message in res:
            print("minette> " + message.text)
```

```
user> hello
minette> Good morning
user> はろー
minette> You said: はろー
user> dice
minette> Dice1:2 / Dice2:4
```

## Continue topic
Switching translation and echo using session.
You can switch to the `translation` mode by saying "翻訳して" and switch back to echo by saying "翻訳終わり".

```python
from datetime import datetime
import requests
from minette import Minette
from minette.dialog import DialogRouter, DialogService, EchoDialogService


class TranslationDialogService(DialogService):
    # Process logic and build session data
    def process_request(self, request, session, connection):
        if session.topic.is_new:
            session.topic.status = "start_translation"
        elif request.text == "翻訳終わり":
            session.topic.status = "end_translation"
        else:
            res = requests.post("https://translation.googleapis.com/language/translate/v2", data={
                "key": self.config.get("google_api_key"),
                "q": request.text,
                "target": "ja"
            }).json()
            session.data["translated_text"] = res["data"]["translations"][0]["translatedText"].replace("&#39;", "'")
            session.topic.status = "process_translation"

    # Compose response message
    def compose_response(self, request, session, connection):
        if session.topic.status == "start_translation":
            session.topic.keep_on = True
            return "日本語に翻訳します。英語を入力してください"
        elif session.topic.status == "end_translation":
            return "翻訳を終了しました"
        elif session.topic.status == "process_translation":
            session.topic.keep_on = True
            return request.text + " in Japanese: " + session.data["translated_text"]


class MyDialogRouter(DialogRouter):
    # Configure intent->dialog routing table
    def configure(self):
        self.intent_resolver = {"TranslationIntent": TranslationDialogService}

    # Set TranslationIntent when user said something contains "翻訳"
    def extract_intent(self, request, session, connection):
        if request.text == "翻訳":
            return "TranslationIntent"


if __name__ == "__main__":
    # Create bot
    bot = Minette.create(dialog_router=MyDialogRouter, default_dialog_service=EchoDialogService)

    # Start conversation
    while True:
        req = input("user> ")
        res = bot.chat(req)
        for message in res.messages:
            print("minette> " + message.text)
```

```
user> hello
minette> You said: hello
user> 翻訳
minette> 日本語に翻訳します。英語を入力してください
user> hello
minette> hello in Japanese: こんにちは
user> Good
minette> Good in Japanese: 良い
user> 翻訳終わり
minette> 翻訳を終了しました
user> テスト
minette> You said: テスト
```
