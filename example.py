""" Console BOT example """
import minette

#Create an instance of Automata
bot = minette.create(
    #tagger=minette.tagger.MeCabTagger, #If MeCab is installed, uncomment this line
    #classifier=MyClassifier            #Your own classifier
)

#Send and receive messages
while True:
    req = input("user> ")
    res = bot.execute(req)
    for message in res:
        print("minette> " + message.text)
