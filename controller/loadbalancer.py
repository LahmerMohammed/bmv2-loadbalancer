import time
import requests
from abc import ABC, abstractmethod
import threading
import random
# from config import *
from pycaret.regression import load_model, predict_model

model = None

def get_services():
    return {
        8000: {
            "name": "inception_model",
            "servers": [{
                'id': "1",
                'ip': '172.20.0.6',
                'connected_to_sw_port': 1,
                'port': "31111",
                'pod_id': 'e64fe'
            },
                {
                'id': "2",
                'ip': '172.20.0.6',
                'connected_to_sw_port': 1,
                'port': "31112",
                'pod_id': 'e74fe'
            }
            ]
        }
    }


WINDOW = 10

BEST_SERVER = {}


def get_yolo_api_stats(server_ip, port, window=20):
    url = 'http://{}:{}/stats?window={}'.format(server_ip, port, window)
    headers = {'accept': 'application/json'}

    # return requests.get(url, headers=headers).json()
    return 5


def get_pod_stats(server_ip: str, pod_id: str, window: int):
    url = f"http://{server_ip}:10001/stats/{pod_id}?window={window}"
    try:
        # Send a GET request to the server
        # response = requests.get(url)
        # return response.json()
        return 10
    except requests.exceptions.RequestException as e:
        print(e)
        return None





def predict_latency(api_stats, pod_stats, cpu_limit):
    X = [cpu_limit, api_stats["request_rate"], pod_stats["cpu_usage"]] + \
        pod_stats["per_cpu_usage"] + [pod_stats["memory_usage"]]
    
    X = [4.0,10.0,53.1,3.3,3.3,3.2,3.3,3.3,3.3,3.4,3.4,3.4,3.3,3.4,3.4,3.2,3.3,3.3,3.3,560.8]
    
    if model is None:
        model = load_model("./model/DecisionTreeRegressor")

    predicted_latency = predict_model(model, data=X, round=0, verbose=False)
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

        print("Round robin: server_".format(self.next_server[port]))

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

                predicted_latency = predict_latency(yolo_api_stats, pod_stats)
                servers_latency.append((predicted_latency, server))

            # Choose the server with the minimum predicted latency
            best_latency, best_server = min(
                servers_latency, key=lambda x: x[0])
            BEST_SERVER[port] = best_server

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
