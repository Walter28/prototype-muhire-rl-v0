import os
import sys
from pathlib import Path
from typing import Callable, Optional, Tuple, Union
import time
   
import gymnasium as gym
import numpy as np
import pandas as pd

from .traffic_signal import TrafficSignal

class RealEnvironment(gym.Env):

    metadata = {
        "render_modes": ["human", "rgb_array"],
    }

    def __init__(
        self,
        begin_time: int = 0,
        delta_time: int = 5,
        yellow_time: int = 2,
        min_green: int = 5,
        max_green: int = 60,
        add_agent_info: bool = True,
        render_mode: Optional[str] = None,
    ) -> None:
        """Initialize the environment."""

        self.begin_time = begin_time
        self.delta_time = delta_time  # seconds on sumo at each step
        self.min_green = min_green
        self.max_green = max_green
        self.yellow_time = yellow_time
        self.initial_time = time.time()

        self.traffic_signal = TrafficSignal(
                self,
                self.delta_time,
                self.yellow_time,
                self.min_green,
                self.max_green,
                self.begin_time,
            )
        

        self.reward_range = (-float("inf"), float("inf"))
        self.episode = 0
        self.observation = None
        self.reward = 0.0
        
        self.fixed_ts_phase_id = 0
        

    def reset(self):
        """Reset the environment."""

        self.episode += 1
        self.metrics = []


        self.traffic_signal = TrafficSignal(
                self,
                self.delta_time,
                self.yellow_time,
                self.min_green,
                self.max_green,
                self.begin_time,
            )

        return self._compute_observation(), self._compute_info()
    
    @property
    def sim_step(self) -> float:
        """Return current simulation second on SUMO."""
        actual_time = int(time.time() -  self.initial_time)
        return actual_time

    def step(self, action: int):
        """Apply the action(s) and then step the simulation for delta_time seconds.
        """

        self._apply_action(action)
        self._run_steps()

        observation = self._compute_observation()
        reward = self._compute_reward()
        dones = self._compute_done()
        terminated = False  # there are no 'terminal' states in this environment
        truncated = dones  # episode ends when sim_step >= max_steps
        info = self._compute_info()

        return observation, reward, terminated, truncated, info
        # return np.array([45.0], dtype=np.float32), reward, done, info

    def _run_steps(self):
        time_to_act = False
        while not time_to_act:
            # time.sleep(1)
            # print("+++++ time since last phase env : ", self.traffic_signal.time_since_last_phase_change)
            self.traffic_signal.update()
            if self.traffic_signal.time_to_act:
                time_to_act = True

    def _apply_action(self, action):
        """Set the next green phase for the traffic signals.

        Args:
            action: If single-agent, actions is an int between 0 and self.num_green_phases (next green phase)
        """
        
        # print("can act ? ",self.traffic_signal.time_to_act)
        if self.traffic_signal.time_to_act:
            self.traffic_signal.old_phase = self.traffic_signal.green_phase
            # print("can act ? ",self.traffic_signal.time_to_act)
            self.traffic_signal.set_next_phase(action)
            
                    
    def _compute_done(self):
        return None

    def _compute_info(self):
        return {}

    def _compute_observation(self):
        
        #if self.traffic_signal.time_to_act:
        self.observation = self.traffic_signal.compute_observation()
        return self.observation

    def _compute_reward(self):
        if self.traffic_signal.time_to_act:
            # print(f" next time to act {self.traffic_signal.next_action_time}")
            # print("")
            self.reward = self.traffic_signal.compute_reward() 
            return self.reward

    @property
    def observation_space(self):
        """Return the observation space of a traffic signal.

        Only used in case of single-agent environment.
        """
        return self.traffic_signal.observation_space

    @property
    def action_space(self):
        """Return the action space of a traffic signal.

        Only used in case of single-agent environment.
        """
        return self.traffic_signal.action_space

    def _get_agent_info(self):
        return {}

    def close(self):
        """Stop the video streaming in django"""

    def __del__(self):
        """Close the environment and stop the SUMO simulation."""
        self.close()