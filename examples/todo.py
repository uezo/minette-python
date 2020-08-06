"""
TodoBot

This example for using SQLAlchemy


Sample conversation
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
"""

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

        # Note: connection is an instance of Session of SQLAlchemy

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
