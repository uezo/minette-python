# Minette for Python
[![Downloads](https://pepy.tech/badge/minette)](https://pepy.tech/project/minette)

Minette はチャットボットを開発するための軽量で拡張可能なフレームワークです。とても簡単に開発できる上に、スパゲッティコードになることなく複雑なBOTにまで拡張していくことができます。

[🇬🇧README in English](./README.md)

# 🎉 version 0.4.1

- SQLAlchemyをサポートしました（試験的）。利用方法は [examples/todo.py](https://github.com/uezo/minette-python/blob/master/examples/todo.py) を参照ください。

# 📦 インストール

```
$ pip install minette
```

# 🤖 おうむ返しBOTのサンプル

テスト用のおうむ返しであれば一瞬で試すことができます。

```python
from minette import Minette, EchoDialogService

# ビルトインされたおうむ返し部品を使ってBOTを起動
bot = Minette(default_dialog_service=EchoDialogService)

# コンソール入出力でやりとり
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

LINEBOTを作るのも同じくらい簡単です。

```python
from flask import Flask, request
from minette import Minette, EchoDialogService
from minette.adaper.lineadapter import LineAdapter

# LINE接続部品を使ってBOTを起動
bot = LineAdapter(default_dialog_service=EchoDialogService)

# WebサーバとAPIエンドポイントの設定
app = Flask(__name__)

@app.route("/", methods=["POST"])
def handle_webhook():
    bot.handle_http_request(request.data, request.headers)
    return "ok"

# Webサーバの起動
app.run(port=12345)
```

# 実行環境

Python 3.5以上。開発は主に3.7.7（on Mac OSX）で行なっています。

## メッセージングサービス

- LINE
- Clova
- Symphony

`minette.Adapter`を拡張した独自クラスを作成することで、FacebookやSlackなど他のサービスに接続することもできます。

## データベース

- SQLite
- Azure SQL Database
- Azure Table Storage
- MySQL (Tested on 8.0.13)

`minette.datastore` パッケージ内の Context / User / MessageLog の各クラスを拡張することで、上記以外のお好みのデータベースを利用することもできます。また、SQLAlchemyがサポートしているデータベースであれば、Engineの接続文字列を指定するだけで利用できる可能性があります。

## 形態素解析エンジン

- MeCab
- Janome

クラウドサービスとして提供されているものや他の言語の形態素解析エンジンも `minette.Tagger` を拡張したクラスを実装することで利用できるようになります。
MeCabやJanomeのインストール方法についてはページ下部にAppendixとしてまとめましたので必要に応じて参照してください。

# 依存ライブラリ

(必須)
- requests >= 2.21.0
- pytz >= 2018.9
- schedule >= 0.6.0

(オプション)
- line-bot-sdk >= 1.12.1 (for LINE)
- clova-cek-sdk >= 1.1.1
- sym-api-client-python >= 0.1.16 (for Symphony)
- pyodbc >= 4.0.26 (for Azure SQL Databsae)
- azure-cosmosdb-table >= 1.0.5 (for Azure Table Storage)
- MySQLdb (for MySQL)
- SQLAlchemy (for SQLAlchemyStores)
- mecab-python3 >= 1.0.1 (for MeCabTagger)
- Janome >= 0.3.8 (for Janome Tagger)

# 特長

`DialogService(s)` と `DialogRouter` という2つの部品を実装するだけでチャットボットを開発することができます。

- DialogService: 対話シナリオに剃ってビジネスロジックを処理し、その結果に応じた応答メッセージを組み立てる
- DialogRouter: 発話からインテント（BOTへの指示内容）とエンティティ（指示の関連情報）を抽出し、それに応じて適切な`DialogService`を呼び出す

[![Architecture](http://uezo.net/img/minette_architecture.png)](http://uezo.net/img/minette_architecture.png)

上記以外の共通機能（コンテキスト管理など）はフレームワークによって行われるため、開発者はアプリケーションに集中することができます。

## コンテキスト管理

文脈を意識した会話を行えるようにするため、Minetteはコンテキスト管理の機能を提供しています。WebシステムでいうところのHTTPセッションに相当する機能です。これを利用することで、以前の発話における処理結果を利用することができます。

データの格納
```python
# `context.topic.keep_on`に`True`を設定することで、次回のリクエストで格納したデータを利用することができます
context.data["pizza_name"] = "Seafood Pizza"
context.topic.keep_on = True
```

データの取得
```python
pizza_name = context.data["pizza_name"]
```

## ユーザー管理
ユーザーはチャネルとチャネル(e.g LINE, FB Messanger etc)におけるユーザーIDの2つをキーに一意に管理されます。初回アクセス時に自動的にユーザーが登録され、また、アプリケーションロジック内で修正したユーザー情報は自動的に保存されます。

```python
# 変更したユーザー情報は自動的に保存されます。コンテキストとは異なり、明示的に削除するまで情報は維持されます
request.user.nickname = "uezo"
request.user.data["horoscope"] = "cancer"
```

## 形態素解析
`Tagger`は形態素解析のための部品で、解析結果はリクエスト情報に自動的に格納され各`DialogService`（アプリケーション）で利用することができます。
Minetteには`MeCabTagger`、`MeCabServiceTagger`、`JanomeTagger`の3つのTaggerが最初から組み込まれています。

```python
>>> from minette import *
>>> tagger = MeCabServiceTagger()
Do not use default API URL for the production environment. This is for trial use only. Install MeCab and use MeCabTagger instead.
>>> words = tagger.parse("今日は良い天気です")
>>> words[0].to_dict()
{'surface': '今日', 'part': '名詞', 'part_detail1': '副詞可能', 'part_detail2': '', 'part_detail3': '', 'stem_type': '', 'stem_form': '', 'word': '今日', 'kana': 'キョウ', 'pronunciation': 'キョー'}
```

`DialogService`での利用例は以下の通り。
```python
def process_request(self, request, context, connection):
    # request.text == "今日は良い天気です" から名詞を抽出。
    nouns = [w.surface for w in request.words if w.part == "名詞"]
    # ["今日", "天気"]をコンテキストデータに格納
    context.data["nouns"] = nouns
```


## タスクスケジューラー
定期実行のためのタスクのスケジューラーが利用可能です。

```python
class MyTask(Task):
    # `do`メソッドに定期実行したい処理内容を実装します
    def do(self, arg1, arg2):
        # スケジューラーのロガーが各タスクの中でも利用することができます
        self.logger.info("Task started!: {} / {}".format(arg1, arg2))

# スケジューラーオブジェクトの生成
sc = Scheduler()
# 3秒ごとに`MyTask`の処理内容を実行するように登録
sc.every_seconds(MyTask, seconds=3, arg1="val1", arg2="val2")
# 定期実行の開始
sc.start()
```

## メッセージログ
リクエスト、応答、コンテキストの対話ログが保存されます。デバッグやリリース後の改善活動にお役立てください。

# サンプルコード

同じものが`examples`にも格納されていますので、すぐに動かしたい方はそちらを利用してください。

## さいころBOT

このサンプルコードは、チャットボットの処理ロジックの実装と、処理結果を利用した応答メッセージの組み立ての方法の例です。

```python
import random
from minette import Minette, DialogService


# カスタムの対話部品
class DiceDialogService(DialogService):
    # ロジックを処理して結果をコンテキストに格納
    def process_request(self, request, context, connection):
        context.data = {
            "dice1": random.randint(1, 6),
            "dice2": random.randint(1, 6)
        }

    # コンテキスト情報を使って応答データを組み立て
    def compose_response(self, request, context, connection):
        return "Dice1:{} / Dice2:{}".format(
            str(context.data["dice1"]), str(context.data["dice2"]))


if __name__ == "__main__":
    # BOTの起動
    bot = Minette(default_dialog_service=DiceDialogService)
    # 対話の開始
    while True:
        req = input("user> ")
        res = bot.chat(req)
        for message in res.messages:
            print("minette> " + message.text)
```

実行結果は以下の通り。

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

SQLAlchemy（0.4.1で実験的サポート）を使ってTodoリスト管理BOTを作るサンプルです。`Session`のインスタンスがリクエスト毎に生成され、DialogServiceの中で利用することができます。

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


## 翻訳BOT

このサンプルコードは以下の方法について解説するものです。

- コンテキスト情報を利用した継続的な対話（文脈のある対話）
- インテントの識別とそれに応じた適切な対話部品へのルーティング
- 設定ファイル（minette.ini）へのAPIキーの設定

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
    EchoDialogService   # 組み込みのおうむ返し部品
)

class TranslationDialogService(DialogService):
    # ロジックを処理して結果をコンテキストに格納
    def process_request(self, request, context, connection):
        # 翻訳処理の開始・終了時には`topic.status`を更新のみ行う
        if context.topic.is_new:
            context.topic.status = "start_translation"

        elif request.text == "stop":
            context.topic.status = "end_translation"

        # 日本語への翻訳処理
        else:
            #  Azure Cognitive Servicesを用いて翻訳
            api_url = "https://api.cognitive.microsofttranslator.com/translate?api-version=3.0&to=ja"
            headers = {
                # 事前に `translation_api_key` を `minette.ini` の `minette` セクションに追加しておきます
                #
                # [minette]
                # translation_api_key=YOUR_TRANSLATION_API_KEY
                "Ocp-Apim-Subscription-Key": self.config.get("translation_api_key"),
                "Content-type": "application/json"
            }
            data = [{"text": request.text}]
            api_result = requests.post(api_url, headers=headers, json=data).json()
            # 翻訳語の文章をコンテキストデータに保存
            context.data["translated_text"] = api_result[0]["translations"][0]["text"]
            context.topic.status = "process_translation"

    # コンテキスト情報を使って応答データを組み立て
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
    # intent->dialog のルーティングテーブルを定義
    def register_intents(self):
        self.intent_resolver = {
            # インテントが"TranslationIntent"のとき、`TranslationDialogService`を利用する
            "TranslationIntent": TranslationDialogService,
            "EchoIntent": EchoDialogService
        }

    # インテントの抽出ロジックを定義
    def extract_intent(self, request, context, connection):
        # リクエスト本文に「translat」が含まれる時 `TranslationIntent` と解釈する
        if "translat" in request.text.lower():
            return "TranslationIntent"

        # リクエスト本文が「ignore」でないとき `EchoIntent` と解釈する
        # この場合「ignore」のときはインテントが抽出されないため、BOTは何も応答メッセージを返さない
        elif request.text.lower() != "ignore":
            return "EchoIntent"


if __name__ == "__main__":
    # BOTの起動
    bot = Minette(dialog_router=MyDialogRouter)

    # 対話の開始
    while True:
        req = input("user> ")
        res = bot.chat(req)
        for message in res.messages:
            print("minette> " + message.text)
```

チャットボットとお話してみましょう。

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

# 対話のテスト
Minetteは対話クラスのテストを支援するための機能を提供しています。

- テストケース毎（テスト関数毎）に異なる `channel_user_id` を自動でセットします。
- `chat` メソッドに `Message` オブジェクトの生成に必要な引数を渡すことができます。`bot.chat(Message(text="hello", intent="HelloIntent"))` のかわりに `bot.chat("hello", intent="HelloIntent")` と呼び出すことができるため、テストコードをよりスッキリさせることができます。
- `chat` からも戻り値の `Response` オブジェクトに `response.messages[0].text` の値をセットした `text` アトリビュートを追加します。

pytestでの利用例は以下の通り。

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


# ライセンス
Apache v2 License

# Appendix

## Janome Taggerのセットアップ

### 依存ライブラリのインストール
```
$ pip install janome
```

### 使い方

```python
from minette.tagger.janometagger import JanomeTagger
bot = Minette.create(
    tagger=JanomeTagger
)
```

MeCab IPADICフォーマットのユーザー辞書がある場合、設定ファイル（minette.ini）に以下の通り定義することで利用することができます。

```ini
janome_userdic = /path/to/userdic.csv
```

## MeCab Taggerのセットアップ

### MeCabのインストール
- Ubuntu 16.04
```
$ sudo apt-get install mecab libmecab-dev mecab-ipadic
$ sudo apt-get install mecab-ipadic-utf8
```
- Mac OSX
```
$ brew install mecab mecab-ipadic git curl xz
```

### Pythonバインディングのインストール
```
$ pip install mecab-python3==0.7
```
0.996.1時点では`surface`が想定通りにならないバグ？があるため、0.7のインストールをお勧めします。


### 使い方
```python
from minette.tagger.mecab import MeCabTagger
bot = Minette.create(
    tagger=MeCabTagger
)
```

# Appendix2 version 0.3からの移行について

- いくつかのパッケージが変更になっており、特定ベンダーに依存しない全てのクラスは `minette` からインポートするようになりました。
- `Minette` インスタンスの生成方法。コンストラクターで直接生成するようになりました。
- `Session` から `Context` に名称を変更しています。また、`session` という引数をとるものもすべて `context` に変更しました。
- `minette.user.User#save()` を廃止しました。アプリロジックでユーザー情報を保存するには、 `UserStore` インスタンスを生成してください。
- `SessionStore` -> `ContextStore`, `UserRepository` -> `UserStore`, `MessageLogger` -> `MessageLogStore`
- `LineAdapter` のHTTPリクエストを受け取るメソッドは、`chat` から `handle_http_request` に変更しました。

もし version 0.3 をインストールしたい場合、Githubのリリースパッケージから入手してください。

```
$ pip install git+https://github.com/uezo/minette-python.git@v0.3
```
