import time
import requests
from abc import ABC, abstractmethod
import threading
import random
from config import *


WINDOW = 10


def get_yolo_api_stats(server_ip, port, window=20):
    url = 'http://{}:{}/stats?window={}'.format(server_ip, port, window)
    headers = {'accept': 'application/json'}

    #return requests.get(url, headers=headers).json()
    return 5


def get_pod_stats(server_ip: str, pod_id: str, window: int):
    url = f"http://{server_ip}:10001/stats/{pod_id}?window={window}"
    try:
        # Send a GET request to the server
        #response = requests.get(url)
        #return response.json()
        return 10
    except requests.exceptions.RequestException as e:
        print(e)
        return None


def predict_latency(api_stats, pod_stats):
    return random.randint(1, 5)



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
        return self.next_server[port]


class MachineLearningLoadBalancer(LoadBalancer):
    def __init__(self, update_interval=1):
        self.best_server = {}
        self.update_interval = update_interval
        self.update_thread = threading.Thread(target=self.run_update)


    def get_next_server(self, port: int):
        return self.best_server[port]

    def updated_ranking(self):

        services = get_services()
        
        for port, service in services.items():
            if port not in self.best_server:
                self.best_server[port] = {}

            servers_latency = []

            for server in service["servers"]:
                yolo_api_stats = get_yolo_api_stats(
                    server_ip=server["ip"], window=WINDOW,
                    port=server["port"]
                    )

                pod_stats = get_pod_stats(
                    server_ip=server["port"], 
                    pod_id=server["pod_id"], window=WINDOW)
                

                predicted_latency = predict_latency(yolo_api_stats, pod_stats)
                servers_latency.append((predicted_latency, server))

            # Choose the server with the minimum predicted latency
            best_latency, best_server = min(servers_latency, key=lambda x: x[0])

            self.best_server[port] = best_server

    def run_update(self):
        while True:
            self.updated_ranking()
            time.sleep(self.update_interval)

    def start_update_thread(self):
        self.update_thread.start()

    def stop_update_thread(self):
        self.update_thread.join()
        


load_balancer = MachineLearningLoadBalancer()

load_balancer.start_update_thread()

for i in range(100):
    time.sleep(1)
    print(load_balancer.get_next_server(8000))


load_balancer.stop_update_thread()