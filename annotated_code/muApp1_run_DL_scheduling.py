###### This file reads from param_edgeric.txt to decide the scheduling algorithm
## update PF and RL models
import argparse
import os
import pickle
import sys
from collections import defaultdict
from datetime import datetime
from threading import Thread
import numpy as np

#import gym
import pandas as pd

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
import math
import time

import torch
import redis
from edgeric_messenger import *

# dictionary stores throughput for each UE for each TTI
cumul_tpt = np.array([]) 

def eval_loop_weight(eval_episodes, idx_algo):
    global total_tpt
    key_index = 0

    with open('tpt_max_cqi.csv', 'a') as f:
        writer = csv.writer(f)
    
        for i_episode in range(eval_episodes):
            cnt = 0
            flag = True
            cnt_demo = 0
            key_algo = "algo"
            # default
            value_algo = "Half resource for each UE" 
            # save cumulative throughput for each episode (TTI)
   
            if(idx_algo == 0):
                flag = False # to be deleted
                weights = fixed_weights(flag)
                # transmit weights to RAN
                send_scheduling_weight(weights, True)
                value_algo = "Fixed Weights"

            # algo1 Max CQI       
            if(idx_algo == 1):
                weights = algo1_maxCQI_multi()
                send_scheduling_weight(weights, True)
                value_algo = "MaxCQI"
    
            # algo2 Max Weight
            if(idx_algo == 2):
                weights = algo2_maxWeight_multi()
                send_scheduling_weight(weights, True)
                value_algo = "MaxWeight"
        
            # ignoring for now
            # algo3 PropFair
            if(idx_algo == 3):
                weights = algo3_propFair_multi(prev_weight_x, prev_weight_y, flag, f_stalls_timeseries) 
                rnti_weights, prev_weights, avg_CQIs = algo2_propFair_multi(prev_weights, avg_CQIs, flag)
                send_scheduling_weight(weights, True)
                value_algo = "Proportional Fairness"
            
            if(flag == True):
                cnt = 0
                flag = False   

            writer.writerow([total_tpt])

def fixed_weights():
    # get data from RAN stack
    ue_data = get_metrics_multi() 
    numues = len(ue_data)
    # for each UE, the Radio Network Temporary Identifier and the corresponding weight will be stored
    weights = np.zeros(numues * 2)
    RNTIs = list(ue_data.keys())

    for i in range(numues):
        # single array, values are stored in pairs
        weights[i*2+0] = RNTIs[i]
        # equally allocate
        weights[i*2+1] = 1/numues
    
    return weights
              
def algo1_maxCQI_multi():
    global total_tpt

    ue_data = get_metrics_multi() 
    numues = len(ue_data)
    weights = np.zeros(numues * 2)

    # extract CQIs and RNTIs, ignore the unncessary data
    tpt = [data['Tx_brate'] for data in ue_data.values()]
    total_tpt = sum(tpt)
    #cumul_tpt = np.append(cumul_tpt, total_tpt)

    CQIs = [data['CQI'] for data in ue_data.values()]
    RNTIs = list(ue_data.keys())

    # all CQIs must be positive
    if min(CQIs) > 0: 
        # helps select the UE with the highest CQI
        maxIndex = np.argmax(CQIs)
        new_weights = np.zeros(numues)
        
        # if all UEs except one are given a low weight, the remaining UE will be given a high weight and ensure it all adds upto 1
        high = 1 - ((numues - 1) * 0.1)
        low = 0.1

        for i in range(numues):
            if i == maxIndex:
                new_weights[i] = high
            else:
                new_weights[i] = low
            
            weights[i*2+0] = RNTIs[i]
            weights[i*2+1] = new_weights[i]
        
        return weights
        
    else:  
        for i in range(numues):
            weights[i*2+0] = RNTIs[i]
            weights[i*2+1] = 1/numues
        return weights

def algo2_maxWeight_multi():
    global total_tpt

    # ue_data is a dictionary with RNTI as the key and the corresponding data for the current TTI as the value
    ue_data = get_metrics_multi() 
    numues = len(ue_data)
    weights = np.zeros(numues * 2)

    # extract CQIs and RNTIs, ignore the unncessary data
    tpt = [data['Tx_brate'] for data in ue_data.values()]
    total_tpt = sum(tpt)
    #cumul_tpt = np.append(cumul_tpt, total_tpt)

    # extract CQIs and BLs along with RNTIs
    CQIs = [data['CQI'] for data in ue_data.values()]
    RNTIs = list(ue_data.keys())
    BLs = [data['Backlog'] for data in ue_data.values()]
    if (min(CQIs) > 0): 
        sum_CQI = np.sum(CQIs)
        sum_BL = np.sum(BLs) 
        if (sum_BL != 0):
            # weights = cqi * bl
            new_weights = CQIs/sum_CQI * BLs/sum_BL
            
        else:
            new_weights = CQIs/sum_CQI
   
        for i in range(numues):
            weights[i*2+0] = RNTIs[i]
            weights[i*2+1] = new_weights[i]
    
    else:  
         for i in range(numues):
            weights[i*2+0] = RNTIs[i]
            weights[i*2+1] = 1/numues
    
    return weights 

def algo3_propFair_multi(prev_weights, avg_CQIs, flag):
    ue_data = get_metrics_multi()
    numues = len(ue_data)
    weights = np.zeros(numues * 2)

    # extract CQIs and BLs along with RNTIs
    CQIs = [data['CQI'] for data in ue_data.values()]
    RNTIs = list(ue_data.keys())
    BLs = [data['Backlog'] for data in ue_data.values()]

    if (min(CQIs)>0): 
        gamma = 0.1 
        if(avg_CQIs[0] == 0): avg_CQIs[0]=CQIs[0]
        if(avg_CQIs[1] == 0): avg_CQIs[1]=CQIs[1]
        
        avg_CQIs = avg_CQIs*(1-gamma) + CQIs*(gamma)
        
        #normalize the weights
        temp_weights = CQIs/avg_CQIs 
        new_weights = np.round(temp_weights/(np.sum(temp_weights)), 2)       
        
        prev_weights = new_weights

        for i in range(env.numArms):
            weights[i*2+0] = RNTIs[i]
            weights[i*2+1] = prev_weights[i]
        
    else:
        for i in range(env.numArms):
            weights[i*2+0] = RNTIs[i]
            weights[i*2+1] = prev_weights[i]

    return weights, prev_weights, avg_CQIs

# an episode here represents how many times the model performs an action (i.e., schedules weights)
def eval_loop_model(num_episodes, out_dir):
    global total_tpt

    output_dir = out_dir 
    # loaded to CPU
    model = torch.load(os.path.join(output_dir, "model_demo.pt"), map_location=torch.device('cpu'))
    model.eval()

    with open('tpt_rl.csv', 'a') as f:
        writer = csv.writer(f)

        for episode in range(num_episodes):
            ue_data = get_metrics_multi() 
            numues = len(ue_data)
            weights = np.zeros(numues * 2)

            # extract CQIs and RNTIs, ignore the unncessary data
            tpt = [data['Tx_brate'] for data in ue_data.values()]
            total_tpt = sum(tpt)
            #cumul_tpt = np.append(cumul_tpt, total_tpt)
            writer.writerow([total_tpt])

            # extract CQIs and BLs along with RNTIs
            CQIs = [data['CQI'] for data in ue_data.values()]
            RNTIs = list(ue_data.keys())
            BLs = [data['Backlog'] for data in ue_data.values()]
            mbs = np.ones(numues)*300000

            # 1s seperate the data for each UE
            # [BL1, CQI1, 1, BL2, CQI2, 1, ...]
            obs = np.array(
                [
                    param[ue]
                    for ue in range(numues)
                    for param in (BLs, CQIs, mbs)
                ],
                dtype=np.float32,
            )  

            obs = torch.from_numpy(obs)
            # converts the tensor to a 2D tensor (what the model expects)
            obs = torch.unsqueeze(obs, dim=0)

            with torch.no_grad():       
                action = model.select_action(obs)
                action = torch.squeeze(action)

                for ue in range(numues):
                    # calculates percentage of the resources allocated to each UE 
                    percentage_RBG = action[ue] / sum(action)       
                    weights[ue*2+1] = percentage_RBG
                    weights[ue*2] = RNTIs[ue]

                send_scheduling_weight(weights, True) 
    
algorithm_mapping = {
    "Max CQI": 1,
    "Max Weight": 2,
    "Proportional Fair (PF)": 3,
    "Round Robin": 4,
    "RL": 20  
}

# RL model is 2 UEs, 5Mbps, 21Mbps, random walk
rl_model_mapping = {
    "Initial Model": "./rl_model/initial_model",
    "Half Trained Model": "./rl_model/half_trained_model",
    "Fully Trained Model": "./rl_model/fully_trained_model"
} 

# establish a Redis connection (assuming Redis server is running locally)
redis_db = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)

if __name__ == "__main__":
    while True:
        try:
            selected_algorithm = "RL"
            if selected_algorithm:
                idx_algo = algorithm_mapping.get(selected_algorithm, None)

                if idx_algo is not None:
                    print("Algorithm index: ", idx_algo)
                    # for traditional scheduling algorithms
                    if idx_algo < 20:
                        eval_loop_weight(2000, idx_algo)  
                    # for RL model execution
                    elif idx_algo == 20:  
                        rl_model_name = "Fully Trained Model"
                        if rl_model_name:
                            rl_model_path = rl_model_mapping.get(rl_model_name)
                            if rl_model_path:
                                print(f"Executing RL model at: {rl_model_path}")
                                eval_loop_model(2000, rl_model_path)
                            else:
                                print(f"Unknown RL model selected: {rl_model_name}")
                        else:
                            print("No RL model selected or RL model key does not exist in Redis.")
                else:
                    print("Unknown algorithm selected:", selected_algorithm)
            else:
                print("No algorithm selected or algorithm key does not exist in Redis.")
                
        except redis.exceptions.RedisError as e:
            print("Redis error:", e)
        except Exception as e:
            print(f"An unexpected error occurred: {e}")        
