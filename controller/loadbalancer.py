import time
import requests
from abc import ABC, abstractmethod
import threading
import random
from config import *
from pycaret.regression import load_model, predict_model
import pandas as pd
import json


WINDOW = 10
model = load_model("./controller/model/DecisionTreeRegressor")
BEST_SERVER = {}
COLUMNS = ['cpu_limit', 'req_rate', 'cpu', 'cpu0', 'cpu1', 'cpu2', 'cpu3', 'cpu4', 'cpu5', 'cpu6',
           'cpu7', 'cpu8', 'cpu9', 'cpu10', 'cpu11', 'cpu12', 'cpu13', 'cpu14', 'cpu15', 'memory_usage']




def get_yolo_api_stats(server_ip, port, window=5):
    try:
        url = 'http://{}:{}/stats?window=30'.format(server_ip, port, window)
        print(url)
        headers = {'accept': 'application/json'}
        return requests.get(url, headers=headers).json()
    except requests.exceptions.RequestException:
        return {}


def get_pod_stats(server_ip: str, pod_id: str, window: int):
    url = f"http://10.10.1.1:10001/stats/{pod_id}?window=30"
    try:
        # Send a GET request to the server
        response = requests.get(url)
        return response.json()
        
    except requests.exceptions.RequestException as e:
        print(e)
        return {}

counter = 0
def predict_latency(api_stats, pod_stats, cpu_limit) -> float:
    global model
    request_rate = 0.0 
    if "request_rate" in api_stats:
        request_rate = api_stats["request_rate"]
    
    cpu_usage = 0.0
    per_cpu_usage = [0.0]*16
    memory_usage = 0.0
    if "cpu_usage" in pod_stats:
        cpu_usage = pod_stats["cpu_usage"]
        per_cpu_usage = pod_stats["per_cpu_usage"]
        memory_usage = pod_stats["memory_usage"]


    X =[[cpu_limit, request_rate, cpu_usage] + per_cpu_usage + [memory_usage] ]
    df = pd.DataFrame(X)     
    df.columns = COLUMNS 
    
    predicted_latency = predict_model(model, data=df)["prediction_label"].values[0]


    return predicted_latency


class LoadBalancer(ABC):

    @abstractmethod
    def get_next_server(self, port: int):
        pass


class RoundRobin(LoadBalancer):
    def __init__(self):
        self.next_server = {}

    def get_next_server(self, port: int):
        services = get_services()

        if port not in self.next_server:
            self.next_server[port] = 0
            return services[port]["servers"][0]

        self.next_server[port] = (
            self.next_server[port] + 1) % len(services[port]["servers"])

        return services[port]["servers"][self.next_server[port]]


class MachineLearningLoadBalancer(LoadBalancer):
    def __init__(self, update_interval=1):
        self.update_interval = update_interval
        self.update_thread = threading.Thread(target=self.run_update)

    def get_next_server(self, port: int):

        if port not in BEST_SERVER:
            BEST_SERVER[port] = {}
        return BEST_SERVER[port]

    def updated_ranking(self):

        services = get_services()

        for port, service in services.items():
            if port not in BEST_SERVER:
                BEST_SERVER[port] = {}

            servers_latency = []

            for server in service["servers"]:
                yolo_api_stats = get_yolo_api_stats(
                    server_ip=server["ip"], window=WINDOW,
                    port=server["port"]
                )

                pod_stats = get_pod_stats(
                    server_ip=server["port"],
                    pod_id=server["pod_id"], window=WINDOW)

                predicted_latency = predict_latency(
                    yolo_api_stats, pod_stats, cpu_limit=server["cpu_limit"])
                servers_latency.append((predicted_latency, server)) 

            with open('filename.txt', 'a') as file:
            # Write a float to the file
                file.write(str(servers_latency) + ' ')
                best_latency, best_server = min(
                    servers_latency, key=lambda x: x[0])

                BEST_SERVER[port] = best_server
                file.write(" " + str(best_latency) + '\n')
                file.write("************************\n")

    def run_update(self):
        while True:
            self.updated_ranking()
            time.sleep(self.update_interval)

    def start_update_thread(self):
        self.update_thread.start()

    def stop_update_thread(self):
        self.update_thread.join()



"""
load_balancer = MachineLearningLoadBalancer()

load_balancer.start_update_thread()

for i in range(100):
    time.sleep(1)
    print(load_balancer.get_next_server(8000))

load_balancer.stop_update_thread()
"""
