# OpenAI Gym Framework and Super Mario Bros
import gym
# Only need to pull this once
# import gym_pull
# gym_pull.pull('github.com/ppaquette/gym-super-mario@gabegrand')
import ppaquette_gym_super_mario
from ppaquette_gym_super_mario import wrappers

# Python modules
import multiprocessing
import numpy as np

# Our code
import hyperparameters as hp
import features as ft
from rewardModel import rewardModel

# Agents
from qAgent import QLearningAgent
from approxQAgent import ApproxQAgent
from approxSarsaAgent import ApproxSarsaAgent

print('-- Creating environment...')
env = gym.make(hp.LEVEL)

print('-- Acquiring multiprocessing lock')
multiprocessing_lock = multiprocessing.Lock()
env.configure(lock=multiprocessing_lock)

# Discretize action space to 14 possible button combinations
wrapper = wrappers.ToDiscrete()
env = wrapper(env)

print('-- Resetting environment')
env.reset()

# Initialize the correct agent
if hp.AGENT_TYPE == 0:
    agent = QLearningAgent()
    print "USING EXACT Q AGENT"
elif hp.AGENT_TYPE == 1:
    agent = ApproxQAgent()
    print "USING APPROX Q AGENT"
elif hp.AGENT_TYPE == 2:
    agent = ApproxSarsaAgent()
    print "USING APPROX SARSA AGENT"
else:
    raise ValueError("Invalid AGENT_TYPE in hyperparameters")

# Load from previous saved Q values
if hp.LOAD_FROM is not None:

    print('Loading Q values from %s' % hp.LOAD_FROM)
    agent.load(hp.LOAD_FROM)

    # Start iterations from where we left off
    j = int(hp.LOAD_FROM[hp.LOAD_FROM.rfind('-')+1:hp.LOAD_FROM.rfind('.pickle')])
    print('Starting at iteration %d' % j)

else:
    j = 0

# Diagnostics
diagnostics = {}

i = 1

while i <= hp.TRAINING_ITERATIONS:

    print('-- Resetting agent')
    agent.reset()

    # Initialize reward function
    rewardFunction = rewardModel()

    print('-- START playing iteration %d / %d' % (i + j, hp.TRAINING_ITERATIONS + j))

    # Sample first action randomly
    action = env.action_space.sample()
    state, reward, _, info = env.step(action)

    # Choose action according to Q
    action = agent.getAction(state)

    while not (info['iteration'] > i):

        # Take action
        nextState, orig_reward, dead, info = env.step(action)

        # Compute custom reward
        reward = rewardFunction.getReward(orig_reward, info)

        # Only factored into update for Sarsa
        nextAction = None
        if hp.AGENT_TYPE == 2:
            nextAction = agent.getAction(nextState)

        # Update Q values; nextAction only used in Sarsa
        agent.update({'state': state,
                      'action': action,
                      'nextState': nextState,
                      'nextAction': nextAction,
                      'reward': reward})

        # Advance the state and action
        state = nextState

        # Choose next action according to Q. If SARSA, nextAction has already been chosen.
        if hp.AGENT_TYPE == 2:
            action = nextAction
        else:
            action = agent.getAction(nextState)

    # Update diagnostics
    diagnostics[i] = {'states_learned': agent.numStatesLearned(),
                      'distance': info['distance'],
                      'score': info['score']}

    print(info)
    print(diagnostics[i])

    # Save Q-values
    if i % hp.SAVE_EVERY == 0:
        print('Saving Q values...')
        agent.save(i, j, diagnostics[i])

    print agent.getWeights()

    # Go to next iteration
    print('Iteration %d / %d complete.' % (i + j, hp.TRAINING_ITERATIONS + j))
    i = info['iteration'];

print('-- Closing environment')
env.close()

print('-- DONE training iterations')
print diagnostics
