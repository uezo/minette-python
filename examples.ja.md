
# サンプルコード

同じものが`examples`にも格納されていますので、すぐに動かしたい方はそちらを利用してください。

# 🎲 さいころBOT

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


# ✅ Todo bot

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


# 🇬🇧 翻訳BOT

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
