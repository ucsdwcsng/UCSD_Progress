import zmq
import time
import threading
import sys
import io
import csv

import numpy as np

# global UE dictionary (stores all related recieved information from the URs) and ran_index variable
ue_dict = {}
ran_index = None

context = zmq.Context()

# PUB-SUB enables IPC between two sockets
# create a publisher socket
publisher_socket2 = context.socket(zmq.PUB)
publisher_socket2.bind("ipc:///tmp/control_actions")  

# subscriber socket for CQI and SNR
subscriber_cqi_snr_socket = context.socket(zmq.SUB)
# subscribe to all messages
subscriber_cqi_snr_socket.setsockopt_string(zmq.SUBSCRIBE, "")  
# save only last recieved message
subscriber_cqi_snr_socket.setsockopt(zmq.CONFLATE, 1)  
subscriber_cqi_snr_socket.connect("ipc:///tmp/socket_snr_cqi")  

a = 0
b = 0
weights = []
global_sending_flag = False

def send_scheduling_weight(weights, flag): 
    str_to_send = ""
    str_to_send = str_to_send + str(ran_index) + " "
    idx = 0
    global a, b
    while idx < len(weights):
        str_to_send = str_to_send + str(round(weights[idx], 4)) + " "
        idx = idx + 1
    str_to_send = str_to_send + str(a) + " " + str(b) + " "
    publisher_socket2.send_string(str_to_send)
    current_time = round(time.time(), 5)
    print(f"Time: {current_time}s Sent to RAN: {str_to_send} \n")

# get all information from UEs
def get_metrics_multi(): 
    global ue_dict  
    global ran_index  
    global global_sending_flag
    # save all ue's throughput in a dictionary according to the user's rnti
    global cumul_tpt  
    ue_dict.clear()

    ue_no = 0
    tpt = 0

    # from mac.cc - this activates every TTI - rnti, snr, cqi, tx_brate, rx_brate, DL buffer
    message = subscriber_cqi_snr_socket.recv_string() 
    print(f"Received from EdgeRIC: {message}")
    
    try:
        # converts strings to substrings
        data = message.split()
        ran_index = int(data[0])  # First element is ran_index

        while global_sending_flag == False:
            message = subscriber_cqi_snr_socket.recv_string()
            data = message.split()
            ran_index = int(data[0])

            if ran_index < 20000:
                print(f"Discarding message with ran_index: {ran_index}")
                global_sending_flag = False
            else:
                global_sending_flag = True

        for i in range(1, len(data), 7):
            rnti = int(data[i])
            cqi = int(data[i + 1])
            backlog = int(data[i + 2])
            tx_bits = float(data[i + 3])
            rx_bits = float(data[i + 4])
            pd = int(data[i + 5])
            snr = float(data[i + 6].replace('\x00', ''))  # Remove any null characters

            if rnti not in ue_dict:
                ue_dict[rnti] = {
                    'CQI': None,
                    'SNR': None,
                    'Backlog': None,
                    'Pending Data': None,
                    'Tx_brate': None,
                    'Rx_brate': None
                }

            ue_dict[rnti]['CQI'] = cqi
            ue_dict[rnti]['SNR'] = snr
            ue_dict[rnti]['Backlog'] = backlog
            ue_dict[rnti]['Tx_brate'] = tx_bits
            ue_dict[rnti]['Rx_brate'] = rx_bits
            ue_dict[rnti]['Pending Data'] = pd

    except ValueError as e:
        print(f"Error: {e}")

    print(f"RAN Index: {ran_index} \n")
    print(f"UE Dictionary: {ue_dict} \n")
    return ue_dict

def main(): 
    while True:
        ue_data = get_metrics_multi()
        global a, b, weights
        # compute some policy - call the policy with ue_dict
        a = 0
        b = 0
        weights.clear()
        # Initialize weights list with appropriate size (2 * number of UEs)
        weights = [0] * (2 * len(ue_dict))

        # Populate the weights list based on ue_dict
        i = 0
        for rnti in ue_dict.keys():
            if rnti == 73:
                weights[i * 2] = rnti
                weights[i * 2 + 1] = 0.9
            else:
                weights[i * 2] = rnti
                weights[i * 2 + 1] = 0.1
            i += 1

        # send the metrics
        send_scheduling_weight(weights, True)

if __name__ == "__main__":
    main()
