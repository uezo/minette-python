# Minette for Python
Minette is a micro Bot framework. Session and user management, Natural language analyzing and architecture for multi-skill/character bot are ready-to-use.

## Installation
`git clone` or download this project and set path. We are preparing for `pip`.
```
$ git clone https://github.com/uezo/minette-python.git
```

## Running the echo bot
Code like below and run.

```python
import minette

# create bot
bot = minette.create()

# start conversation
while True:
    req = input("user> ")
    res = bot.execute(req)
    for message in res:
        print("minette> " + message.text)
```

```
$ python echo.py
user> hello
minette> You said: hello
```

## Session management
Minette provides a data store that enables your bot to continue conversasion accross the requests like HTTP Session. Default SessionStore uses Sqlite but you can make custom SessionStore and change to any database you like.

## User management
Users are identified by internal UserIDs which are given at the first access to the bot. The UserID is determined by the channel (e.g. CONSOLE, LINE, etc) and the user_id of the channel. Minette stores the data of users in Sqlite automatically and you can get (or update) it from User object.

## Natural Language Analyzing
Taggers are the components for analyzing the text of request and the result will be set to request.words property. Minette has two built-in taggers - GoogleTagger and MeCabTagger.

### Google Tagger
GoogleTagger uses Cloud Natural Language API. This separates text into words and provides tags for each of them. (e.g. NOUN, VERB, ADJ ...)

#### Usase
```python
from minette.tagger.google import GoogleTagger
bot = minette.create(
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
bot = minette.create(
    tagger=MeCabTagger
)
```

## Adding custom conversation
Minette detect the intention of the user in the `Classifier` and delegate to proper `DialogService` to process the application logic and compose response messages.

Here is the example. RateDialogService calculate ＄->¥ exchange rate and MyClassifier has a rule to delegate when the input is numeric.

```python
import minette
from minette.dialog import Message, DialogService, Classifier

class RateDialogService(DialogService):
    def compose_response(self, request, session, connection):
        yen = int(request.text) * 100
        return request.get_reply_message("$" + request.text + " = ¥" + str(yen))

class MyClassifier(Classifier):
    def classify(self, request, session, connection):
        if request.text.isdecimal():
            return RateDialogService
        else:
            return DialogService

if __name__ == "__main__":
    # create bot
    bot = automata.create(classifier=MyClassifier)

    # start conversation
    while True:
        req = input("user> ")
        res = bot.execute(req)
        for message in res:
            print("minette> " + message.text)
```

Run and say "3" to the bot.
```
user> 3
minette> $3 = ¥300
```
If you say non-numeric words, bot echoes what you say.
```
user> hello
minette> You said: hello
```

## Built-in Chatting (Japanese Only)
Minette has a DialogService for Japanese chatting using docomo API. All you have to do is just adding 2 lines in config file! (minette.ini)
```python
[minette]
default_dialog_service = minette.dialog.chat_dialog.ChatDialogService
chatting_api_key = YOUR_API_KEY
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
    res = bot.execute(req)
    for message in res:
        print("minette> " + message.text)
```
```
user> hello
minette> You said:hello
```

## Greeting Bot
The simplest structure. All logic is implemented in a custom DialogService.
```python
from datetime import datetime
import minette
from minette.dialog import Message, DialogService, Classifier

class GreetingDialogService(DialogService):
    def compose_response(self, request, session, connection):
        now = datetime.now()
        if now.hour < 12:
            phrase = "Good morning"
        elif now.hour < 18:
            phrase = "Hello"
        else:
            phrase = "Good evening"
        return request.get_reply_message(text=phrase)

if __name__ == "__main__":
    # create bot
    bot = minette.create(default_dialog_service=GreetingDialogService)
    # start conversation
    while True:
        req = input("user> ")
        res = bot.execute(req)
        for message in res:
            print("minette> " + message.text)
```
```
user> hello
minette> Good morning
```

## Dice Bot
Override process_request method to execute application logic.
```python
import random
import minette
from minette.dialog import Message, DialogService, Classifier

class DiceDialogService(DialogService):
    def process_request(self, request, session, connection):
        session.data = {
            "dice1": random.randint(1, 6),
            "dice2": random.randint(1, 6)
        }

    def compose_response(self, request, session, connection):
        dice1 = str(session.data["dice1"])
        dice2 = str(session.data["dice2"])
        return request.get_reply_message(text="Dice1:" + dice1 + " / Dice2:" + dice2)

if __name__ == "__main__":
    # create bot
    bot = minette.create(default_dialog_service=DiceDialogService)
    # start conversation
    while True:
        req = input("user> ")
        res = bot.execute(req)
        for message in res:
            print("minette> " + message.text)
```

## Dice and Greeting Bot
Switching DialogService by request.text.

```python
import random
from datetime import datetime
import minette
from minette.dialog import Message, DialogService, Classifier

class GreetingDialogService(DialogService):
    def compose_response(self, request, session, connection):
        now = datetime.now()
        if now.hour < 12:
            phrase = "Good morning"
        elif now.hour < 18:
            phrase = "Hello"
        else:
            phrase = "Good evening"
        return request.get_reply_message(text=phrase)

class DiceDialogService(DialogService):
    def process_request(self, request, session, connection):
        session.data = {
            "dice1": random.randint(1, 6),
            "dice2": random.randint(1, 6)
        }

    def compose_response(self, request, session, connection):
        dice1 = str(session.data["dice1"])
        dice2 = str(session.data["dice2"])
        return request.get_reply_message(text="Dice1:" + dice1 + " / Dice2:" + dice2)

class MyClassifier(Classifier):
    def classify(self, request, session, connection):
        if request.text.lower() == "dice":
            return DiceDialogService
        else:
            return GreetingDialogService

if __name__ == "__main__":
    # create bot
    bot = minette.create(classifier=MyClassifier)
    # start conversation
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
minette> Good morning
user> dice
minette> Dice1:2 / Dice2:4
```

## Translation Bot
Translation bot using Google translation API.

```python
import requests
import minette
from minette.dialog import Message, DialogService, Classifier

class TranslationDialogService(DialogService):
    def process_request(self, request, session, connection):
        res = requests.post("https://translation.googleapis.com/language/translate/v2", data={
            "key": "YOUR_API_KEY",
            "q": request.text,
            "target": "en"
        }).json()
        session.data = res["data"]["translations"][0]["translatedText"].replace("&#39;", "'")

    def compose_response(self, request, session, connection):
        return request.get_reply_message("英語に翻訳：" + session.data)

if __name__ == "__main__":
    # create bot
    bot = minette.create(default_dialog_service=TranslationDialogService)

    # start conversation
    while True:
        req = input("user> ")
        res = bot.execute(req)
        for message in res:
            print("minette> " + message.text)
```
```
user> こんにちは
minette> 英語に翻訳：Hello
user> おなかがすきました
minette> 英語に翻訳：I'm hungry
```

## Translation and chatting bot
Switching translation and chatting using `session.mode`.
You can switch to the `translation` mode by saying "翻訳して" and switch back to chatting by saying "翻訳終わり".

```python
import requests
import minette
from minette.dialog import Message, DialogService, Classifier
from minette.dialog.chat_dialog import ChatDialogService
from minette.session import ModeStatus

class TranslationDialogService(DialogService):
    def process_request(self, request, session, connection):
        if session.mode_status == ModeStatus.Start:
            session.mode = "translation"
        else:
            if request.text == "翻訳終わり":
                session.mode_status = ModeStatus.End
            else:
                res = requests.post("https://translation.googleapis.com/language/translate/v2", data={
                    "key": "YOUR_API_KEY",
                    "q": request.text,
                    "target": "en"
                }).json()
                session.data = res["data"]["translations"][0]["translatedText"].replace("&#39;", "'")

    def compose_response(self, request, session, connection):
        if session.mode_status == ModeStatus.Start:
            text = "翻訳したい文章を入力してください。「翻訳終わり」で翻訳モードを終了します"
            session.keep_mode = True
        elif session.mode_status == ModeStatus.Continue:
            text = "English: " + session.data
            session.keep_mode = True
        else:
            text = "はい、翻訳は終わりにします"
        return request.get_reply_message(text)

class MyClassifier(Classifier):
    def classify(self, request, session, connection):
        if "翻訳して" in request.text or session.mode == "translation":
            return TranslationDialogService
        else:
            return ChatDialogService(request, session, self.logger, self.config, self.timezone, connection)

if __name__ == "__main__":
    # create bot
    bot = minette.create(classifier=MyClassifier)
    # start conversation
    while True:
        req = input("user> ")
        res = bot.execute(req)
        for message in res:
            print("minette> " + message.text)
```



