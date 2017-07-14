# Minette for Python
Minette is a micro Bot framework. Session and user management, Natural language analyzing and architecture for multi-skill/character bot are ready-to-use.

## Installation
`git clone` or download this project and set path. We are preparing for `pip`.
```
$ git clone https://github.com/uezo/minette-python.git
```

## Running the echo bot
Make example.py and run.
```python
from minette import automata
from minette.dialog.message import Message

# create bot
bot = automata.create()

# start conversation
while True:
    text = input("user> ")
    req = Message(text=text)
    res = bot.execute(req)
    for message in res:
        print("minette> " + message.text)
```

```
$ python example.py
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
from minette.taggers.googletagger import GoogleTagger
bot = automata.create(
    tagger=GoogleTagger(api_key="your api key")
)
```

### MeCab Tagger
MeCabTagger uses MeCab which is one of the most popular Japanese morphological analyzer. This provides all information of MeCab nodes. To use this tagger, MeCab and its binding for Python are required.

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
from minette.taggers.mecabtagger import MeCabTagger
bot = automata.create(
    tagger=MeCabTagger
)
```

## Adding custom conversation
Minette detect the intention of the user in the `Classifier` and delegate to proper `DialogService` to process the application logic and compose response messages.

Here is the example. RateDialogService calculate ＄->¥ exchange rate and MyClassifier has a rule to delegate when the input is numeric.

```python
from minette import automata
from minette.dialog.message import Message
from minette.dialog.dialog_service import DialogService
from minette.dialog.classifier import Classifier

class RateDialogService(DialogService):
    def compose_response(self):
        yen = int(self.request.text) * 100
        return self.request.get_reply_message("$" + self.request.text + " = ¥" + str(yen))

class MyClassifier(Classifier):
    def classify(self, request, session):
        if request.text.isdecimal():
            return RateDialogService
        else:
            return DialogService

if __name__ == "__main__":
    # create bot
    bot = automata.create(classifier=MyClassifier)

    # start conversation
    while True:
        text = input("user> ")
        req = Message(text=text)
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
Minette has a DialogService for Japanese chatting using docomo API. All you have to do is adding a rule to the classifier!
```python
from minette.dialog.dialog_service import ChatDialogService
return ChatDialogService(request=request, session=session, logger=self.logger, api_key="your api key")
```

## License
This software is licensed under the Apache v2 License.

# Sample Codes

## Echo bot
The first bot that just echoes what you say.
```python
from minette import automata
from minette.dialog.message import Message

# create bot
bot = automata.create()

# start conversation
while True:
    text = input("user> ")
    req = Message(text=text)
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
from minette import automata
from minette.dialog.message import Message
from minette.dialog.dialog_service import DialogService
from minette.dialog.classifier import Classifier

class GreetingDialogService(DialogService):
    def compose_response(self):
        now = datetime.now()
        if now.hour < 12:
            phrase = "Good morning"
        elif now.hour < 18:
            phrase = "Hello"
        else:
            phrase = "Good evening"
        return self.request.get_reply_message(text=phrase)

class MyClassifier(Classifier):
    def classify(self, request, session):
        return GreetingDialogService

if __name__ == "__main__":
    # create bot
    bot = automata.create(classifier=MyClassifier)

    # start conversation
    while True:
        text = input("user> ")
        req = Message(text=text)
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
from minette import automata
from minette.dialog.message import Message
from minette.dialog.dialog_service import DialogService
from minette.dialog.classifier import Classifier

class DiceDialogService(DialogService):
    def process_request(self):
        self.session.data = {
            "dice1": random.randint(1, 6),
            "dice2": random.randint(1, 6)
        }

    def compose_response(self):
        dice1 = str(self.session.data["dice1"])
        dice2 = str(self.session.data["dice2"])
        return self.request.get_reply_message(text="Dice1:" + dice1 + " / Dice2:" + dice2)

class MyClassifier(Classifier):
    def classify(self, request, session):
        return DiceDialogService

if __name__ == "__main__":
    # create bot
    bot = automata.create(classifier=MyClassifier)
    # start conversation
    while True:
        text = input("user> ")
        req = Message(text=text)
        res = bot.execute(req)
        for message in res:
            print("minette> " + message.text)
```

## Dice and Greeting Bot
Switching DialogService by request.text.

```python
import random
from datetime import datetime
from minette import automata
from minette.dialog.message import Message
from minette.dialog.dialog_service import DialogService
from minette.dialog.classifier import Classifier

class GreetingDialogService(DialogService):
    def compose_response(self):
        now = datetime.now()
        if now.hour < 12:
            phrase = "Good morning"
        elif now.hour < 18:
            phrase = "Hello"
        else:
            phrase = "Good evening"
        return self.request.get_reply_message(text=phrase)

class DiceDialogService(DialogService):
    def process_request(self):
        self.session.data = {
            "dice1": random.randint(1, 6),
            "dice2": random.randint(1, 6)
        }

    def compose_response(self):
        dice1 = str(self.session.data["dice1"])
        dice2 = str(self.session.data["dice2"])
        return self.request.get_reply_message(text="Dice1:" + dice1 + " / Dice2:" + dice2)

class MyClassifier(Classifier):
    def classify(self, request, session):
        if request.text.lower() == "dice":
            return DiceDialogService
        else:
            return GreetingDialogService

if __name__ == "__main__":
    # create bot
    bot = automata.create(classifier=MyClassifier)
    # start conversation
    while True:
        text = input("user> ")
        req = Message(text=text)
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
