#!/usr/bin/env python

import time
import requests

from os.path import expanduser
from multiprocessing import Queue
from queue import Empty
from subprocess import Popen, DEVNULL

from . import piped_server
#import piped_server

PIPED_SERVER_PORT = "7891"

BATTLESNAKE_EXE = expanduser("~") + "/go/bin/battlesnake"
WORLD_W = 11
WORLD_H = 11
SNAKE_NAME = "Test-RL"
SNAKE_URL = "http://localhost:" + PIPED_SERVER_PORT
MOVE_TIMEOUT = int(10e5)  # to enable explorative development using notebooks

class Env:
    def __init__(self):
        self.server_pipe_in = None
        self.server_pipe_out = None
        self.battlesnake_process = None
        self.piped_server_proc = None

    def reset(self, train_mode=False):
        # clean old stuff
        if self.battlesnake_process is not None:
            if self.battlesnake_process.poll() is None:
                self.battlesnake_process.kill()
                self.battlesnake_process.wait()
            assert self.battlesnake_process.poll() is not None
            self.battlesnake_process = None

        if self.piped_server_proc is not None:
            self.piped_server_proc.terminate()
            self.piped_server_proc.join()
            self.piped_server_proc = None

        self.server_pipe_in = Queue()
        self.server_pipe_out = Queue()
        self.piped_server_proc = piped_server.start_server(
                self.server_pipe_in,
                self.server_pipe_out,
                PIPED_SERVER_PORT)
        self.piped_server_proc.start()
        self.poll_server()

        delay = 0
        if not train_mode:
            delay = 100

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
            "--url", SNAKE_URL,]
        self.battlesnake_process = Popen(
            cmdline,
            stderr=DEVNULL)

        endpoint, start_state_out = self.server_pipe_out.get(True, timeout=500 / 1000)
        # initial state (/start req) and the first step (first /move) have the same
        # input, so discard the first piped input
        endpoint, start_state_out = self.server_pipe_out.get(True, timeout=500 / 1000)
        next_state, reward, done = self.parse_server_out(endpoint, start_state_out)
        return (next_state, reward, done)

    def step(self, action):
        self.server_pipe_in.put(action)
        try:
            endpoint, output_data = self.server_pipe_out.get(True, timeout=500 / 1000)
        except Empty:
            endpoint, output_data = ("dead", None)
        next_state, reward, done = self.parse_server_out(endpoint, output_data)
        return (next_state, reward, done)

    def close(self):
        self.piped_server_proc.terminate()
        self.piped_server_proc.join()
        exit(0)

    def parse_server_out(self, endpoint, out_data):
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

    def poll_server(self):
        success = False
        for timeperiod in [0.001, 0.01, 0.05, 0.1, 0.5, 1, 5]:
            try:
                res = requests.get("http://localhost:" + PIPED_SERVER_PORT)
                success = True
                break
            except requests.exceptions.ConnectionError:
                time.sleep(timeperiod)

        if not success:
            raise "Polling failed"
