#!/usr/bin/env python

import os
import logging
import random
import threading

from flask import Flask
from flask import request

app = Flask(__name__)
in_q = None
out_q = None

log = logging.getLogger('werkzeug')
log.setLevel(logging.ERROR)

@app.get("/")
def handle_info():
    """
    This function is called when the snake is registered.
    See https://docs.battlesnake.com/guides/getting-started#step-4-register-your-battlesnake
    """
    #print("INFO")
    default_info = {
        "apiversion": "1",
        "author": "Anurag Peshne",
        "color": "#fbdd74",
        "head": "beluga",
        "tail": "curled"
    }

    return default_info

@app.post("/start")
def handle_start():
    """
    This function is called everytime the snake is entered into a game.
    request.json contains information about the game that's about to be played.
    """
    global out_q
    
    #print("server start")
    data = request.get_json()
    out_q.put(('start', data))

    #print(f"{data['game']['id']} START")
    return "ok"

@app.post("/move")
def handle_move():
    """
    This function is called on every turn of a game.
    Return a move from ["up", "down", "left" or "right"].
    """
    global in_q
    global out_q

    data = request.get_json()
    res = out_q.put(("move", data))

    #print("MOVE", data)
    move = in_q.get()
    #move = "right"
    return {"move": move}

@app.post("/end")
def handle_end():
    """
    This function is called when a game your snake was in ends.
    It's purely for informational purposes, you don't have to make any decisions here.
    """
    global out_q

    data = request.get_json()
    out_q.put(('end', data))

    #print(f"{data['game']['id']} END")
    return "ok"

def start_server(in_q_param, out_q_param, port_param="8080"):
    global in_q
    global out_q

    in_q = in_q_param
    out_q = out_q_param
    port = int(os.environ.get("PORT", port_param))
    threading.Thread(
        target=lambda: app.run(host="0.0.0.0", port=port, debug=True, use_reloader=False),
        daemon=True).start()

def reset_q():
    global in_q
    global out_q

    # HACK: put many items in the queue so that pending gets are satisfied
    for i in range(10):
        in_q.put("up")
        out_q.put(("dummy", None))

    with in_q.mutex:
        in_q.queue.clear()

    with out_q.mutex:
        out_q.queue.clear()
    print("reset done")
