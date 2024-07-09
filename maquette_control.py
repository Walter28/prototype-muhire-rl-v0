import os
import time
from stable_baselines3 import PPO
import socket
from select import select
import json
import numpy as np
import random

# Constants
MIN_GREEN = 5
YELLOW = 2
MAX_GREEN = 30

# stateFeu = ['R'] * 4
# data = {
#             "road1": [0,  "R", 0], # structure = [ road_id , traffic_signal_state, veh_nb ] 
#             "road2": [1,  "R", 0], 
#             "road3": [2, "R", 0],
#             "road4": [3, "R", 0],
#         }

# Initialize environment and model
# PPO_path = os.path.join('Training', 'PPO_model_NEW3') #uncomment this if u use this terminal
PPO_path = "E:/prototype-muhire-rl-v0/Training/PPO_model_NEW3" # uncomment this if u run this file from arduino.py with  Subprocess.Popen
model = PPO.load(PPO_path)

s2 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

# Initialize phase variables
cpt = 0
current_phase = 0
time_in_phase = 0
time_to_decide = 0
decision_time = 5  # Time in seconds to take a decision

initial_time = time.time()

observation = {}
stateFeu = None
data = None # RoadInfos

def compute_datas(s, s1):
        """Computes the observation, roadsInfo and stateFeu of the traffic signal."""
        global observation
        global stateFeu
        global data

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
        
        # print(" ready  : ", ready_to_read)
        # print("+++++++++++++++++++++++++++ (old) : ", data)
        
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

        # print("+++++++++++++++++++++++++++ stateFeu : ", stateFeu)
        if ready_to_read_1:
            stateFeu, address = s1.recvfrom(1024)  # format des donnees data = b'R,R,R,R'
            stateFeu = stateFeu.decode()  # data = 'R,R,R,R'
            stateFeu = stateFeu.split(",")  # data = ['R', 'R', 'R', 'R']
            # print("+++++++++++++++++++++++++++ stateFeu from network : ", stateFeu)
            
        nb_veh_road1 = int(data['road1'][2]) + random.randrange(0, 4)
        nb_veh_road2 = int(data['road2'][2]) + 1
        nb_veh_road3 = int(data['road3'][2]) + 1
        nb_veh_road4 = int(data['road4'][2]) + random.randrange(0, 4)
        nb_veh = [nb_veh_road1, nb_veh_road2, nb_veh_road3, nb_veh_road4]
            
        road1_density = float(nb_veh_road1 / 40)
        road2_density = float(nb_veh_road2 / 40)
        road3_density = float(nb_veh_road3 / 40)
        road4_density = float(nb_veh_road4 / 40)
        
        density = [road1_density, road2_density, road3_density, road4_density]
        
        # if (stateFeu[0] == "V" or stateFeu[0] =="Y") and stateFeu[1] == "R":
        #     phase = [1,0]
        # elif (stateFeu[1] == "V" or stateFeu[1] =="Y") and stateFeu[0] == "R":
        #     phase = [0,1]
        # else:
        #     phase = [0,0]
        if current_phase == 0:
            phase = [1,0]
        if current_phase == 1:
            phase = [0,1]
            
        
        observation = {
            'density': np.array(density, dtype=np.float64),
            'nb_veh': np.array(nb_veh, dtype=np.int32),
            'phase': np.array(phase, dtype=np.int32)
        }
        
        density = np.array(density, dtype=np.float64)
        nb_veh = np.array(nb_veh, dtype=np.int32)
        phase = np.array(phase, dtype=np.int32)
        
        # print("+++ obs : ", observation)
        return observation, data, stateFeu


# socket pour la reception depuis views.py du projet django
s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# lie la socket au port 8020 port d'ecoute
s.bind(("localhost", 8020))
s.setblocking(False)

# socket 1 pour la reception depuis arduino.py
s1 = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
# lie la socket au port 8016 port d'ecoute
s1.bind(("localhost", 8016))
s1.setblocking(False)

while True:
    # global stateFeu
    # global data
    # global s2
        
    obs, roadsInfo, stateFeu = compute_datas(s, s1)  # Replace with actual method to retrieve current state
    
    print("++++ obs : ", obs)
    print("++++ StateFeu : ", stateFeu)
    print(f"")
    if time_to_decide == decision_time:
        # Get current state from the environment (you need to define how to get state from the real environment)
        
        # Predict action using the trained model
        action, _states = model.predict(obs, deterministic=True)
        print("++++ Action : ", action)
        print("++++ Cureent Phase : ", current_phase)
        
        if action != current_phase:
            # Send yellow phase command to Arduino
            # On passe par un yellow phase
            # socket n'accepte que les donnees de type byte
            yellow = "Y"+str(current_phase)
            yellow_to_byte = yellow.encode("utf-8")  # on aura green_phase = b"0"
            # on envoi la donnee au port 8005 a arduino.py
            s2.sendto(yellow_to_byte, ("localhost", 8005))
            time.sleep(YELLOW)
            
            # Change the phase
            current_phase = action
            time_in_phase = 0
            time_to_decide = 0
        else:
            time_to_decide = 0
        
    # Send the current phase command to Arduino
    # socket n'accepte que les donnees de type byte
    green_phase_str = str(current_phase) # on data = "1" ou data = "2"
    green_phase_to_byte = green_phase_str.encode("utf-8")  # on aura green_phase = b"0"
    # on envoi la donnee au port 8005 a arduino.py
    s2.sendto(green_phase_to_byte, ("localhost", 8005))
    
    # Wait for one second
    time.sleep(1)
    
    # Increment time in phase
    time_in_phase += 1
    time_to_decide += 1
    print("---> time iin phase : ", time_in_phase)
    print("---> time to decide : ", time_to_decide)
    
    # If we exceed MAX_GREEN, we need to change the phase
    if time_in_phase >= MAX_GREEN:
        # Send yellow phase command to Arduino
        # On passe par un yellow phase
        # socket n'accepte que les donnees de type byte
        yellow = "Y"+str(current_phase)
        yellow_to_byte = yellow.encode("utf-8")  # on aura green_phase = b"0"
        # on envoi la donnee au port 8005 a arduino.py
        s2.sendto(yellow_to_byte, ("localhost", 8005))
        time.sleep(YELLOW)
        
        # Change the phase
        current_phase = 1 - current_phase  # Toggle between 0 and 1
        time_in_phase = 0
        time_to_decide = 0
        
        
time.sleep(10)
