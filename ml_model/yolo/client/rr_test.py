from threading import Thread
import requests
from enum import Enum
import yaml
from time import sleep
import subprocess
from k8s import KubernetesCLI
import json
import threading
import time


server_ip = ""

def get_yolo_api_stats(port: int, window=20):
    url = f'http://{server_ip}:{port}/stats?window={window}'
    headers = {'accept': 'application/json'}

    return requests.get(url, headers=headers).json()

def get_pod_stats(pod_id: str, window: int):
    url = f"http://{server_ip}:10001/stats/{pod_id}?window={window}"

    try:
        # Send a GET request to the server
        response = requests.get(url)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(e)
        return None
    

rps_values = list(range(5, 71, 5)).insert(0, 1)

pod_ids = ["6fa4837d-8cbe-4142-aef6-ebb148e83c44", "d40f3288-f2b3-4d5b-9953-ddb53f3eb0ea"]

if __name__ == '__main__':
    try:
        
        subprocess.run(['node', 'req_gen.js', '1', '1', '10'],
                            check=True, capture_output=True, text=True)
    except subprocess.CalledProcessError as e:
        print(e.stderr)



    for rps in rps_values:
        
        
        print("Starting test load ....")
        start_time = time.perf_counter()
        try:

            subprocess.run(['node', 'req_gen.js', str(rps), '1', '60'],
                                   check=True, capture_output=True, text=True)

        except subprocess.CalledProcessError as e:
            print(e.stderr)

        duration = int(time.perf_counter() - start_time)
        print("Load test finished in {} s.".format(duration))
        stats_file = open('stats.txt', 'a')

        yolo_api_stats_1 = get_yolo_api_stats(window=duration, port=31111)
        pod_stats_1 = get_pod_stats(pod_id=pod_ids[0], window=duration)

        yolo_api_stats_2 = get_yolo_api_stats(window=duration, port=31112)
        pod_stats_2 = get_pod_stats(pod_id=pod_ids[1], window=duration)
        
        stats_file.write("{} {} {} {} {}\n".format(
            rps,
            pod_stats_1["cpu_usage"],
            pod_stats_2["cpu_usage"],
            yolo_api_stats_1["request_latency"],
            yolo_api_stats_2["request_latency"],
        ))

        stats_file.close()