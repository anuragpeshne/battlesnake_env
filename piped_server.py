#!/usr/bin/env python

import os
import queue

from flask import Flask
from flask import request

app = Flask(__name__)
in_q = None
out_q = None

@app.get("/")
def handle_info():
    """
    This function is called when the snake is registered.
    See https://docs.battlesnake.com/guides/getting-started#step-4-register-your-battlesnake
    """
    print("INFO")
    default_info = {
        "apiversion": "1",
        "author": "Anurag Peshne",
        "color": "#fbdd74",
        "head": "beluga",
        "tail": "curled"
    }

    return __get_from_q(default_info)

@app.post("/start")
def handle_start():
    """
    This function is called everytime the snake is entered into a game.
    request.json contains information about the game that's about to be played.
    """
    data = request.get_json()
    out_q.put(data)

    print(data)
    print(f"{data['game']['id']} START")
    return "ok"

@app.post("/move")
def handle_move():
    """
    This function is called on every turn of a game.
    Return a move from ["up", "down", "left" or "right"].
    """
    data = request.get_json()
    out_q.put(data)

    print(data)
    possible_moves = ["up", "down", "left" or "right"]
    random_move = random.choice(possible_moves)

    move = __get_from_q(in_q, random_move)

    return {"move": move}


@app.post("/end")
def end():
    """
    This function is called when a game your snake was in ends.
    It's purely for informational purposes, you don't have to make any decisions here.
    """
    data = request.get_json()
    out_q.put(data)

    print(f"{data['game']['id']} END")
    return "ok"

def __get_from_q(q, default_value):
    try:
        return q.get(True, 500 / 1000)
    except queue.Empty:
        return default_value

if __name__ == "__main__":
    print("Starting Battlesnake Server...")
    in_q = queue.Queue()
    out_q = queue.Queue()
    port = int(os.environ.get("PORT", "8080"))
    app.run(host="0.0.0.0", port=port, debug=True)
