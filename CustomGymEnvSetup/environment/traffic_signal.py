import os
import sys
from typing import Callable, List, Union, Tuple
import socket
from select import select
import json

import numpy as np
from gymnasium import spaces


        
class TrafficSignal:
    """
    This class represents a Traffic Signal controlling an intersection.

    """

    def __init__(
        self,
        env,
        delta_time: int,
        yellow_time: int,
        min_green: int,
        max_green: int,
        begin_time: int,
    ):
        self.env = env
        self.delta_time = delta_time
        self.yellow_time = yellow_time
        self.min_green = min_green
        self.max_green = max_green
        # self.is_all_red = 0
        self.green_phase = 0
        self.old_phase = None
        self.is_yellow = False
        self.time_since_last_phase_change = 0
        self.next_action_time = begin_time
        
        self.last_density = 0.0
        
        self.density = [0.0] * 4
        self.nb_veh = [0] * 4
        self.phase = [0] * 2


        self.observation_space = spaces.Dict({
            'density': spaces.Box(low=np.array([0.0, 0.0, 0.0, 0.0]), high=np.array([20.0, 20.0, 20.0, 20.0]), shape=(4,), dtype=np.float64),  # Liste des densités dans chaque phase
            'nb_veh': spaces.Box(low=np.array([0, 0, 0, 0]), high=np.array([100, 100, 100, 100]), shape=(4,), dtype=np.int32),  # Liste des nombres de véhicules dans chaque voie
            'phase': spaces.Box(low=np.array([0,0]), high=np.array([1,1]), shape=(2,), dtype=np.int32),  # Liste des 2 phases
        })

        self.action_space = spaces.Discrete(2)

        # Receptions des Donnees (SERVEUR UDP)
        # cree une socket UDP
        
        # socket 2 pour l'envoie
        self.s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        

    
    @property
    def time_to_act(self):
        """Returns True if the traffic signal should act in the current step."""
        return self.next_action_time == self.env.sim_step
    
    def update(self):
        """Updates the traffic signal state.

        If the traffic signal should act, it will set the next green phase and update the next action time.
        """
        self.time_since_last_phase_change += 1 
        if self.is_yellow and self.time_since_last_phase_change == self.yellow_time:
            # On envoi a arduino.py le green phase a considerer
            # socket n'accepte que les donnees de type byte
            green_phase = str(self.green_phase) # on data = "1" ou data = "2"
            green_phase_to_byte = green_phase.encode("utf-8")  # on aura green_phase = b"0"
            # on envoi la donnee au port 8005 a arduino.py
            self.s2.sendto(green_phase_to_byte, ("localhost", 8005))
            print("+++++ time since last phase1 : ", self.time_since_last_phase_change)
            print("+++++ green phase1 : ", green_phase_to_byte)
            self.is_yellow = False

    def set_next_phase(self, new_phase: int):
        """Sets what will be the next green phase and sets yellow phase if the next phase is different than the current.

        Args:
            new_phase (int): Number between [0 ... num_green_phases]
        """

        new_phase = int(new_phase)
        
        if self.green_phase == new_phase or self.time_since_last_phase_change < self.yellow_time + self.min_green:
            # On envoi a arduino.py le green phase a considerer
            # socket n'accepte que les donnees de type byte
            green_phase_str = str(self.green_phase) # on data = "1" ou data = "2"
            green_phase_to_byte = green_phase_str.encode("utf-8")  # on aura green_phase = b"0"
            # on envoi la donnee au port 8005 a arduino.py
            self.s2.sendto(green_phase_to_byte, ("localhost", 8005))
            print("+++++ green phase2 : ", green_phase_to_byte)
            
            self.next_action_time = self.env.sim_step + self.delta_time + self.yellow_time
        else:
            # On passe par un yellow phase
            # On envoi a arduino.py le green phase a considerer
            # socket n'accepte que les donnees de type byte
            data = "Y"+str(self.green_phase)
            data_to_byte = data.encode("utf-8")  # on aura green_phase = b"0"
            # on envoi la donnee au port 8005 a arduino.py
            self.s2.sendto(data_to_byte, ("localhost", 8005))
            print("+++++ yellow phase : ", data_to_byte)
            
            self.green_phase = new_phase
            self.next_action_time = self.env.sim_step + self.delta_time
            print("+++++ SIM_STEP : ", self.env.sim_step)
            print("+++++ NEXT ACTION TIME : ", self.next_action_time)
            self.is_yellow = True
            self.time_since_last_phase_change = 0

    def compute_observation(self):
        """Computes the observation of the traffic signal."""
        # socket pour la reception depuis views.py du projet django
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # lie la socket au port 8015 port d'ecoute
        s.bind(("localhost", 8015))
        s.setblocking(False)

        # socket 1 pour la reception depuis arduino.py
        s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        # lie la socket au port 8016 port d'ecoute
        s1.bind(("localhost", 8016))
        s1.setblocking(False)
        # Reception de l'etat de feu de circulation depuis Arduino
        ready_to_read, _, _ = select([s], [], [], 0.1)  # verifi si un message est dispo dans le socket avant de recevoir le smg

        #the default data if the data wasn't arrived is
        data = {
            "road1": [0,  "Y", 0], # structure = [ road_id , traffic_signal_state, veh_nb ] 
            "road2": [1,  "Y", 0], 
            "road3": [2, "Y", 0],
            "road4": [3, "Y", 0],
        }
        
        stateFeu = ['Y'] * 4
        
        print(" ready  : ", ready_to_read)
        print("+++++++++++++++++++++++++++ (old) : ", data)
        
        if ready_to_read:
            data, address = s.recvfrom(1024)  # format des donnees data = b'{'road1': [0, 'Y', ''], 'road2': [1, 'Y', 0], 'road3': [2, 'Y', ''], 'road4': [3, 'Y', '']}'
            data = data.decode()  # data = '{'road1': [0, 'Y', ''], 'road2': [1, 'Y', 0], 'road3': [2, 'Y', ''], 'road4': [3, 'Y', '']}'
            data = json.loads(data) # to recover the dictionnary data = {'road1': [0, 'Y', ''], 'road2': [1, 'Y', 0], 'road3': [2, 'Y', ''], 'road4': [3, 'Y', '']}
            # Iterate through the dictionary items
            for key, value in data.items():
                # Check if the value is an empty string
                if value[2] == "" or value[2] == '':
                    # Replace the empty string with 0
                    data[key][2] = 0
            print("+++++++++++++++++++++++++++ data from network : ", data)
            
        # Reception de l'etat de feu de circulation depuis Arduino
        ready_to_read_1, _, _ = select([s1], [], [],
                                        0.1)  # verifi si un message est dispo dans le socket avant de recevoir le smg

        print("+++++++++++++++++++++++++++ stateFeu : ", stateFeu)
        if ready_to_read_1:
            stateFeu, address = s1.recvfrom(1024)  # format des donnees data = b'R,R,R,R'
            stateFeu = stateFeu.decode()  # data = 'R,R,R,R'
            stateFeu = stateFeu.split(",")  # data = ['R', 'R', 'R', 'R']
            print("+++++++++++++++++++++++++++ stateFeu from network : ", stateFeu)
            
        road1_density = float(data['road1'][2] / 2)
        road2_density = float(data['road2'][2] / 2)
        road3_density = float(data['road3'][2] / 2)
        road4_density = float(data['road4'][2] / 2)
        
        density = [road1_density, road2_density, road3_density, road4_density]
        
        if (stateFeu[0] == "V" or stateFeu[0] =="Y") and stateFeu[1] == "R":
            phase = [1,0]
        elif (stateFeu[1] == "V" or stateFeu[1] =="Y") and stateFeu[0] == "R":
            phase = [0,1]
        else:
            phase = [0,0]
            
        nb_veh_road1 = data['road1'][2]
        nb_veh_road2 = data['road2'][2]
        nb_veh_road3 = data['road3'][2]
        nb_veh_road4 = data['road4'][2]
        nb_veh = [nb_veh_road1, nb_veh_road2, nb_veh_road3, nb_veh_road4]
        
        observation = {
            'density': np.array(density, dtype=np.float64),
            'nb_veh': np.array(nb_veh, dtype=np.int32),
            'phase': np.array(phase, dtype=np.int32)
        }
        
        self.density = np.array(density, dtype=np.float64)
        self.nb_veh = np.array(nb_veh, dtype=np.int32)
        self.phase = np.array(phase, dtype=np.int32)
        
        print("+++ obs : ", observation)
        return observation

    def compute_reward(self):
        """Computes the reward of the traffic signal."""
        self.last_reward = self.custom_reward()
        return self.last_reward

    def custom_reward(self):
        """
        Calcule la récompense basée sur plusieurs critères.

        Returns:
            float: La somme des trois récompenses.
        """
        
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++
        #
        # REWARD4 DIFF DENSITY : reward4 = self.last_density - density
        #
        #+++++++++++++++++++++++++++++++++++++++++++++++++++++++++++

        phase1_density = (self.density[0] + self.density[2]) /2
        phase2_density = (self.density[1] + self.density[3]) /2
        phases_density = [phase1_density, phase2_density]
        density_sum = sum(phases_density) / 2
        
        reward4 = self.last_density - density_sum
        
        self.last_density = density_sum
        
        return reward4

