""" Console BOT example """
from minette import automata

#Create an instance of automata
bot = automata.create(
    #tagger=mecabtagger.MeCabTagger,      #If MeCab is installed, uncomment this line
    #classifier=classifier.MyClassifier   #Your own classifier
)

#Send and receive messages
while True:
    req = input("user> ")
    res = bot.execute(req)
    for message in res:
        print("minette> " + message.text)
