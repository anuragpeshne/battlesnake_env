#!/usr/bin/env python

import queue
import time

from os.path import expanduser
from subprocess import Popen

import piped_server

BATTLESNAKE_EXE = expanduser("~") + "/go/bin/battlesnake"
WORLD_W = 11
WORLD_H = 11
SNAKE_NAME = "Test"
SNAKE_URL = "http://127.0.0.1:8080"
MOVE_TIMEOUT = 1000

server_pipe_in = queue.Queue()
server_pipe_out = queue.Queue()
battlesnake_process = None
piped_server_started = False

def reset(train_mode=False):
    global server_pipe_in
    global server_pipe_out
    global battlesnake_process
    
    server_pipe_in = queue.Queue()
    server_pipe_out = queue.Queue()
    piped_server.reset_q(server_pipe_in, server_pipe_out)

    return start(train_mode)

def start(train_mode):
    global battlesnake_process
    global piped_server_started

    delay = 100
    if train_mode:
        delay = 1000

    if not piped_server_started:
        piped_server.start_server(server_pipe_in, server_pipe_out)
        piped_server_started = True
        
        # TODO poll /
        time.sleep(2)
    
    battlesnake_process = Popen([
        BATTLESNAKE_EXE,
        "play",
        "--delay", str(delay),
        "--gametype", "solo", # "standard",
        "--height", str(WORLD_H),
        "--width", str(WORLD_W),
        "--timeout", str(MOVE_TIMEOUT),
        "--name", SNAKE_NAME,
        "--url", SNAKE_URL,
    ])

    _ = server_pipe_out.get(True, 500 / 1000)
    endpoint, start_state_out = server_pipe_out.get(True, 500 / 1000)
    next_state, reward, done = parse_server_out(endpoint, start_state_out)
    return (next_state, reward, done)

def step(action):
    server_pipe_in.put(action)
    endpoint, output_data = server_pipe_out.get(True, 500 / 1000)
    next_state, reward, done = parse_server_out(endpoint, output_data)
    return (next_state, reward, done)

def close():
    # TODO: close pipe server

    exit(0)
    
if __name__ == "__main__":
    pass

def parse_server_out(endpoint, out_data):
    if endpoint == "start":
        done = False
        reward = 0
        next_state = None
    elif endpoint == "move":
        done = False
        reward = 0
        next_state = out_data
    else:
        done = True
        reward = 0
        next_state = out_data
    return (next_state, reward, done)
