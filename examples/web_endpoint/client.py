""" Web API client example """
import sys
import os
sys.path.append("../../")
import requests
from minette.message import Message

while True:
    req_text = input("user> ")
    # Query with params
    res = requests.get("http://localhost:5002/callback", params={"text": req_text}).json()
    # # Query with JSON
    # msg = Message(text=req_text + " (json)")
    # res = requests.post("http://localhost:5002/callback", data=msg.to_json(), headers={"content-type": "application/json"}).json()
    for message in res:
        print("minette> " + message["text"])
