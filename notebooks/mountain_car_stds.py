import numpy as np
import gym
import pandas as pd
import matplotlib.pyplot as plt
plt.style.use("bmh")


class MountainCarRewardWrapper(gym.RewardWrapper):

    def __init__(self, env):
        super().__init__(env)
        self.state = None
        self.low = self.observation_space.low
        self.high = self.observation_space.high
        self.center = np.array([-.45, .0])
        self.normalize_scaler = np.array([1.05, .07])

    def reset(self, **kwargs):
        self.state = self.env.reset(**kwargs)
        return self.state

    def step(self, action):
        self.state, reward, done, info = self.env.step(action)
        return self.state, self.reward(reward), done, info

    def reward(self, reward):
        won = self.state[1]>.5
        res = np.linalg.norm((self.state-self.center)/self.normalize_scaler)
        res += 100 if won else .0
        return res

def uniform_state_grid(points_per_axis=100):
    s1, s2 = np.linspace(state_low[0], state_high[0], points_per_axis), np.linspace(state_low[1],
                                                                                          state_high[1],
                                                                                          points_per_axis)
    return np.array([np.array([x, y]) for x in s1 for y in s2])


def plot(xys, v):
    plt.scatter(xys[:, 0], xys[:, 1], c=v, s=10)
    plt.grid(True)
    plt.colorbar()


def plot_Q(qlearning_agent, a=None):
    xys = uniform_state_grid()
    actions = range(actions_num) if a is None else a
    plt.figure(figsize=(15, 5))
    for action in actions:
        plt.subplot(1, len(actions), action + 1)
        plt.title("Q(s in S, action = {})".format(action))
        Qs = np.array([qlearning_agent.Q(xy, action) for xy in xys])
        plot(xys, Qs)

    plt.show()

def run(agent, episodes=1000, verbose=True):
    df = pd.DataFrame()
    states, actions, rewards, states_, dones = [], [], [], [], []

    for episode in range(episodes):

        state = env.reset()
        episode_reward = 0
        step_count = 0
        done = False
        while not done:

            action = agent.act(state)
            state_, reward, done, _ = env.step(action)

            agent.observe(state, action, reward, state_, episode=episode, step=step_count)

            episode_reward += reward

            states.append(state)
            actions.append(action)
            rewards.append(reward)
            states_.append(state_)
            dones.append(done)

            state = state_

            step_count+= 1

        if verbose:
            print('Episode {} finished after {} steps with total reward {}'.format(episode,
                                                                                   step_count,
                                                                                   episode_reward))

    df = pd.concat([df, pd.DataFrame(np.array(states), columns=['state1', 'state2'])], axis=1)
    df = pd.concat([df, pd.DataFrame(np.array(actions), columns=['action'])], axis=1)
    df = pd.concat([df, pd.DataFrame(np.array(rewards), columns=['reward'])], axis=1)
    df = pd.concat([df, pd.DataFrame(np.array(states_), columns=['state1_', 'state2_'])], axis=1)
    df = pd.concat([df, pd.DataFrame(np.array(dones), columns=['dones'])], axis=1)
    df['episode'] = df['dones'].cumsum()-df['dones'] # number of episode

    return df

def plot_state_path(df_ep, episode=0):
    plt.plot(df_ep['state1'], df_ep['state2'], linewidth=.5, label='episode {}'.format(episode))
    plt.scatter([df_ep['state1'][0]], [df_ep['state2'][0]], c='g', marker='^')
    plt.scatter([df_ep['state1_'][len(df_ep['state1_'])-1]], [df_ep['state2_'][len(df_ep['state2_'])-1]], c='r',
                marker='v')
    plt.xlabel('pos')
    plt.ylabel('vel')

def plot_reward(df_ep, episode=0):
    plt.plot(df_ep['reward'], label='total(ep={})={},'.format(episode, df_ep['reward'].sum()))

def show_episode(df, episode=-1):
    if episode<0:
        episode = df['episode'][len(df['episode'])-1]

    df_ep = df[df['episode']==episode].reset_index()
    plt.subplot(1, 2, 1)
    plot_state_path(df_ep, episode)
    plt.subplot(1, 2, 2)
    plot_reward(df_ep, episode)
    plt.legend()
    plt.show()

################### VARIABLES ###################
unwrapped_env = gym.make("MountainCar-v0")
env = MountainCarRewardWrapper(unwrapped_env)

state_low, state_high = env.observation_space.low, env.observation_space.high
actions_num = env.action_space.n