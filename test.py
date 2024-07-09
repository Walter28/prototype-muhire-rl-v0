import gymnasium as gym
from CustomGymEnvSetup import *
import os
from stable_baselines3 import PPO
from stable_baselines3.dqn.dqn import DQN

env = gym.make('maquette-muhire-rl-v0')

from stable_baselines3 import PPO
PPO_path = os.path.join('Training', 'PPO_model_NEW3')
model = PPO.load(PPO_path, env=env)

obs, info = env.reset()

for i in range(100000):
    action = env.action_space.sample()  # agent policy that uses the observation and info
    # action, _state = model.predict(obs, deterministic=True)
    #obs, rewards, terminated, truncated, info = vec_env.step(action)
    obs, reward, terminated, truncated, info = env.step(action)
    
    print(f" Action : ", action)
    #print(f" Obs : ", obs)
    print(f" Reward : ", reward)
    print(f" Obs : ", obs['nb_veh'])
    print(f" ")
    # # print(f" Observation : ", obs)
    print(f" Info : ", info)