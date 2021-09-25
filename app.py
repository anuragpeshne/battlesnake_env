#!/usr/bin/env python

import wrapper

import random

def agent_get_action():
    possible_moves = ["up", "down", "right", "left"]
    return random.choice(possible_moves)

for i_episode in range(10):
    print(i_episode)
    done = False
    initial_state = wrapper.reset(train_mode=False)
    score = 0
    t = 0
    while not done:
        t += 1
        print("step:", i_episode, t)
        action = agent_get_action()
        next_state, reward, done = wrapper.step(action)
        # agent.step(state, action, reward, next_state, done)
        score += reward
        #print("app:", next_state, action, reward, done)
        print("app:", action, reward, done)

print("app: done")
wrapper.close()
