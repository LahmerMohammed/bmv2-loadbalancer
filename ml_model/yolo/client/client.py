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


server_ip = "10.198.0.11"

images = ['images/cars.jpg']

yolo_service_endpoint = "http://{}:30946".format(server_ip)

POD_NAME = "yolo-v3"


class Model(str, Enum):
    yolov3tiny = "yolov3-tiny"
    yolov3 = "yolov3"


def get_yolo_api_stats(window=20):
    url = '{}/stats?window={}'.format(yolo_service_endpoint, window)
    headers = {'accept': 'application/json'}

    return requests.get(url, headers=headers).json()


def predict(image_name: str, model: Model = 'yolov3-tiny'):
    params = {'model': model}
    headers = {'accept': 'application/json'}
    files = {'image': (image_name, open(image_name, 'rb'), 'image/jpeg')}

    return requests.post(
        yolo_service_endpoint, params=params, headers=headers, files=files)


def get_yolo_api_status():
    headers = {'accept': 'application/json'}
    url = "{}/health".format(yolo_service_endpoint)

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check for HTTP errors
        print(response.json())
        return response.json()
    except requests.exceptions.RequestException as e:
        return None
    

def get_pod_stats(pod_id: str, window: int):
    url = f"http://10.198.0.11:9000/stats/{pod_id}?window={window}"

    try:
        # Send a GET request to the server
        response = requests.get(url)
        return response.json()
    except requests.exceptions.RequestException as e:
        print(e)
        return None


kubernetes = KubernetesCLI()


cpu_values = ["1000m", "2000m", "3000m", "4000m"]
rps_values = [1, 8, 16, 32, 64, 128]


def main():
    global cpu_values
    global rps_values

    for rps in rps_values:
        for cpu in cpu_values:
            stats_file = open('stats.txt', 'a')
            # Delete pod if exist
            kubernetes.delete_pod(POD_NAME)
            print("Deleting pod {} ....".format(POD_NAME))
            while kubernetes.pod_exists(name=POD_NAME):
                sleep(2)

            print("Pod {} was deleted successfully.".format(POD_NAME))

            print('Running scenario: cpu = {}'.format(cpu))

            print('Adding pod with new cpu limits ...')
            response = kubernetes.create_pod('../templates/pod.yaml', cpu=cpu)

            pod_id = response.metadata.uid

            yolo_api_status = get_yolo_api_status()
            print(f"The pod --{pod_id}-- isn\'t ready yet!")
            while yolo_api_status == None:
                sleep(2)
                yolo_api_status = get_yolo_api_status()

            print("Starting test load ....")
            try:

                subprocess.run(['node', 'req_gen.js', str(rps)],
                               check=True, capture_output=True, text=True)

            except subprocess.CalledProcessError as e:
                print(e.stderr)

            print("Load test finished .")

            yolo_api_stats = get_yolo_api_stats(window=25)
            pod_stats = get_pod_stats(pod_id=pod_id, window=25)

            stats_file.write("{} {} {} {} {} {} {} {} {}".format(
                rps, cpu, 
                yolo_api_stats["request_rate"], 
                yolo_api_stats["request_latency"], 
                pod_stats["cpu_usage"],
                " ".join(map(str, pod_stats["per_cpu_usage"]))
                ),
                pod_stats["memory_usage"]
            )

            stats_file.close()


if __name__ == '__main__':
    main()
