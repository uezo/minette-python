# Minette for Python
[![Downloads](https://pepy.tech/badge/minette)](https://pepy.tech/project/minette)

Minette is a minimal and extensible chatbot framework. It is extremely easy to develop and the architecture preventing to be spaghetti code enables you to scale up to complex chatbot.

[🇯🇵日本語のREADMEはこちら](https://github.com/uezo/minette-python/blob/master/README.ja.md)

# 🎉 version 0.4.2 is available

- 0.4.2 Aug 26, 2020
    - Support [Janome 0.4](https://mocobeta.github.io/janome/en/)
- 0.4.1 Aug 7, 2020
    - SQLAlchemy is supported (experimental). See also [examples/todo.py](https://github.com/uezo/minette-python/blob/master/examples/todo.py)


# 🚀 Quick start

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

See also [examples.md](https://github.com/uezo/minette-python/blob/master/examples.ja.md) to get more examples.


# 📦 Installation

```
$ pip install minette
```


# ✅ Supported Platforms

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

# 📚 Dependencies

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

# ✨ Features

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

## Testing Dialogs
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

# 💝 Contribution

See the [Contribution Guideline](https://github.com/uezo/minette-python/blob/master/CONTRIBUTING.md)


# ⚖️ License
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
$ pip install mecab-python3==1.0.1
```
~~Version 0.996.1 has a bug(?) so we strongly recommend to use version 0.7.~~ Fixed at current version


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
