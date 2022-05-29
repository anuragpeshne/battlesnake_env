#!/usr/bin/env python

import queue
import time

from os.path import expanduser
from subprocess import Popen, DEVNULL

import piped_server

BATTLESNAKE_EXE = expanduser("~") + "/go/bin/battlesnake"
WORLD_W = 11
WORLD_H = 11
SNAKE_NAME = "Test"
SNAKE_URL = "http://localhost:8080"
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

    delay = 0
    if train_mode:
        delay = 1000

    if not piped_server_started:
        piped_server.start_server(server_pipe_in, server_pipe_out)
        piped_server_started = True
        
        # TODO poll /
        time.sleep(0.01)
    
    cmdline = [
        BATTLESNAKE_EXE,
        "play",
        "--sequential",
        "--delay", str(delay),
        "--gametype", "solo", # "standard",
        "--height", str(WORLD_H),
        "--width", str(WORLD_W),
        "--timeout", str(MOVE_TIMEOUT),
        "--name", SNAKE_NAME,
        "--url", SNAKE_URL,
    ]
    battlesnake_process = Popen(
        cmdline,
        stderr=DEVNULL)

    _ = server_pipe_out.get(True, 500 / 1000)
    endpoint, start_state_out = server_pipe_out.get(True, 500 / 1000)
    next_state, reward, done = parse_server_out(endpoint, start_state_out)
    return (next_state, reward, done)

def step(action):
    server_pipe_in.put(action)
    try:
        endpoint, output_data = server_pipe_out.get(True, 500 / 1000)
    except queue.Empty:
        endpoint, output_data = ("dead", None)
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
    elif endpoint == "dead":
        done = True
        reward = -1
        next_state = out_data
    else:
        done = True
        reward = 1
        next_state = out_data
    return (next_state, reward, done)
