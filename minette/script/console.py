""" Default console script """
import sys, os
from argparse import ArgumentParser
import importlib
import minette

class ConsoleApp:
    def __init__(self, bot, _):
        self.bot = bot
    
    def start(self):
        while True:
            req = input("user> ")
            res = self.bot.execute(req)
            for message in res:
                print("minette> " + message.text)

def main(args=sys.argv):
    #default
    config_file = os.path.join(os.path.dirname(__file__), "default_ini.py")
    port = 5050
    #get arguments
    usage = "Usage: python {} [--config <config_file>] [--web|--line <port_number>] [--help]".format(__file__)
    argparser = ArgumentParser(usage=usage)
    argparser.add_argument('-c', '--config', dest='config_file', help="Path to configuration file. (path/to/minette.ini)")
    argparser.add_argument('-w', '--web', nargs="?", type=int, const=5050, help="Start as Web endpoint. Port number is 5050 as default")
    argparser.add_argument('-l', '--line', nargs="?", type=int, const=5050, help="Start as LINE endpoint. Port number is 5050 as default")
    args = argparser.parse_args()
    #setup app
    if args.config_file:
        config_file = args.config_file
        abs_path = os.path.abspath(config_file)
        home_dir = os.path.dirname(abs_path)
        sys.path.append(home_dir)
    if args.web:
        m = importlib.import_module("minette.script.web")
        app_class = m.WebEndpoint
        port = args.web
    elif args.line:
        m = importlib.import_module("minette.script.line")
        app_class = m.LineEndpoint
        port = args.line
    else:
        app_class = ConsoleApp
    #start bot
    bot = minette.create(config_file=config_file)
    app = app_class(bot, port)
    app.start()

if __name__ == "__main__":
    main()
