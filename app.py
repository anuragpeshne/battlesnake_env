#!/usr/bin/env python

import env

import random

def agent_get_action(state):
    possible_moves = ["up", "down", "right", "left"]
    return random.choice(possible_moves)

for i_episode in range(10):
    print("Episode:", i_episode)
    done = False
    initial_state = env.reset(train_mode=True)
    score = 0
    t = 0

    state = initial_state
    while not done:
        t += 1
        print("step:", i_episode, t)
        action = agent_get_action(state)
        next_state, reward, done = env.step(action)
        state = next_state
        # agent.step(state, action, reward, next_state, done)
        score += reward
        #print("app:", next_state, action, reward, done)
        print("app:", action, reward, done)

print("app: done")
env.close()
