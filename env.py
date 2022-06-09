#!/usr/bin/env python

import time
import requests

from os.path import expanduser
from multiprocessing import Queue
from queue import Empty
from subprocess import Popen, DEVNULL, PIPE

from . import piped_server
#import piped_server

BATTLESNAKE_EXE = expanduser("~") + "/go/bin/battlesnake"
SNAKE_NAME = "Test"
SNAKE_URL = "http://localhost:8080"
MOVE_TIMEOUT = int(10e5)  # to enable explorative development using notebooks

server_pipe_in = Queue()
server_pipe_out = Queue()
battlesnake_process = None
server_started = False

def reset(world_w=11, world_h=11, train_mode=False):
    global battlesnake_process
    global server_started
    global server_pipe_in
    global server_pipe_out

    # clean old stuff
    if battlesnake_process is not None:
        if battlesnake_process.poll() is None:
            battlesnake_process.kill()
            battlesnake_process.wait()
        assert battlesnake_process.poll() is not None
        battlesnake_process = None

    if not server_started:
        piped_server.start_server(server_pipe_in, server_pipe_out)
        server_started = True
        poll_server()
    else:
        #print("reset")
        piped_server.reset_q()
        time.sleep(0.1)
        #print("q clear")

    delay = 0
    if not train_mode:
        delay = 100

    cmdline = [
        BATTLESNAKE_EXE,
        "play",
        "--sequential",
        "--delay", str(delay),
        "--gametype", "solo", # "standard",
        "--height", str(world_h),
        "--width", str(world_w),
        "--timeout", str(MOVE_TIMEOUT),
        "--name", SNAKE_NAME,
        "--url", SNAKE_URL,]
    battlesnake_process = Popen(
        cmdline,
        stderr=DEVNULL)

    endpoint, start_state_out = server_pipe_out.get(True, 500 / 1000)
    next_state, reward, done = parse_server_out(endpoint, start_state_out)
    return (next_state, reward, done)

def step(action):
    global server_pipe_in
    global server_pipe_out

    server_pipe_in.put(action)
    try:
        endpoint, output_data = server_pipe_out.get(True, 200 / 1000)
    except Empty:
        endpoint, output_data = ("dead", None)
    next_state, reward, done = parse_server_out(endpoint, output_data)
    return (next_state, reward, done)

def close():
    # TODO: close pipe server

    exit(0)
    
if __name__ == "__main__":
    pass

def parse_server_out(endpoint, out_data):
    if (endpoint == "start" or
        endpoint == "move"):
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

def poll_server():
    for timeperiod in [0.001, 0.01, 0.05, 0.1]:
        try:
            res = requests.get("http://localhost:8080")
            break
        except requests.exceptions.ConnectionError:
            time.sleep(timeperiod)
