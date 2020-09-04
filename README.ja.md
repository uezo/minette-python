# Minette for Python
[![Downloads](https://pepy.tech/badge/minette)](https://pepy.tech/project/minette)

Minette はチャットボットを開発するための軽量で拡張可能なフレームワークです。とても簡単に開発できる上に、スパゲッティコードになることなく複雑なBOTにまで拡張していくことができます。

[🇬🇧README in English](https://github.com/uezo/minette-python/blob/master/README.md)

# 🎉 version 0.4.2 is available

- 0.4.2 Aug 26, 2020
    - [Janome 0.4](https://mocobeta.github.io/janome/)に対応しました
- 0.4.1 Aug 7, 2020
    - SQLAlchemyをサポートしました（試験的）。利用方法は [examples/todo.py](https://github.com/uezo/minette-python/blob/master/examples/todo.py) を参照ください。


# 🚀 クイックスタート

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
from minette.adapter.lineadapter import LineAdapter

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

その他の例については[examples.ja.md](https://github.com/uezo/minette-python/blob/master/examples.ja.md)を参照してください。


# 📦 インストール

```
$ pip install minette
```


# ✅ 対応プラットフォーム

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

# 📚 依存ライブラリ

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

# ✨ 特長

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

## 対話のテスト
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

# 💝 コントリビューション

[コントリビューションガイド](https://github.com/uezo/minette-python/blob/master/CONTRIBUTING.md)を参照してください🙏

# ⚖️ ライセンス
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
$ pip install mecab-python3==1.0.1
```
~~0.996.1時点では`surface`が想定通りにならないバグ？があるため、0.7のインストールをお勧めします。~~ 解決済み


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
