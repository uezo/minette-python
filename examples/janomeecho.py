"""
Janome Japanese morphological analysis echo-bot

This example shows the echo-bot that returns the response analyzed by Janome,
pure Python Japanese morphological analysis engine.


Sample conversation
    $ python janomeecho.py

    user> 今日も暑くなりそうですね
    minette> 今日(名詞), も(助詞), 暑く(形容詞), なり(動詞), そう(名詞), です(助動詞), ね(助詞)
    user> もしハワイに行ったらパンケーキをたくさん食べます
    minette> 固有名詞あり: ハワイ

Using user dictionary
    To use user dictionary, pass the path to user dictionary as `user_dic` argument.

    user> 新しい魔法少女リリカルなのはの映画を観ましたか？

    minette without udic> 新しい(形容詞), 魔法(名詞), 少女(名詞), リリカル(名詞), な(助動詞), の(名詞), は(助詞), の(助詞), 映画(名詞), を(助詞), 観(動詞), まし(助動詞), た(助動詞), か(助詞), ？(記号)
    minette with udic> 固有名詞あり: 魔法少女リリカルなのは
"""
import sys
sys.path.append("/Users/uezo/dev/minette-python")

from minette import Minette, DialogService
from minette.tagger.janometagger import JanomeTagger


# Custom dialog service
class DiceDialogService(DialogService):
    def process_request(self, request, context, connection):
        # Text processing using the result of Janome
        context.data["proper_nouns"] = \
            [w.surface for w in request.words if w.part_detail1 == "固有名詞"]

    def compose_response(self, request, context, connection):
        if context.data.get("proper_nouns"):
            # Echo extracted proper nouns when the request contains
            return "固有名詞あり: " + ", ".join(context.data.get("proper_nouns"))
        else:
            # Echo with analysis result
            return ", ".join(["{}({})".format(w.surface, w.part) for w in request.words])


if __name__ == "__main__":
    # Create bot with Janome Tagger
    bot = Minette(
        default_dialog_service=DiceDialogService,
        tagger=JanomeTagger,
        # user_dic="/path/to/userdict"    # <= Uncomment when you use user dict
    )
    # Start conversation
    while True:
        req = input("user> ")
        res = bot.chat(req)
        for message in res.messages:
            print("minette> " + message.text)
