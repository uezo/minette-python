""" Console BOT example """
from datetime import datetime
from minette import automata
from minette.dialog.message import Message

#Create an instance of automata
bot = automata.create(
    #tagger=mecabtagger.MeCabTagger,      #If MeCab is installed, uncomment this line
    #classifier=classifier.MyClassifier   #Your own classifier
)

#Send and receive messages
while True:
    text = input("user> ")
    req = Message(text=text, channel="CONSOLE", channel_user="default_user", timestamp=datetime.now(bot.timezone))
    res = bot.execute(req)
    for message in res:
        print("minette> " + message.text)
