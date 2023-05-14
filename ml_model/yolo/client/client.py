from threading import Thread
import requests
from enum import Enum
import yaml
from time import sleep
import subprocess
from k8s import KubernetesCLI
import json

server_ip = "10.198.0.11"

images = ['images/cars.jpg']

yolo_service_endpoint = "http://{}:31977".format(server_ip)

POD_NAME = "yolo-v3"
class Model(str, Enum):
    yolov3tiny = "yolov3-tiny"
    yolov3 = "yolov3"


def get_stats(window=20):
    url = '{}/stats?window={}'.format(yolo_service_endpoint, window)
    headers = {'accept': 'application/json'}

    return requests.get(url, headers=headers)


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

def get_pod_status(pod_name: str):
    url = "http://{}:14000/pods/{}/status".format(server_ip, pod_name)

    # Send a GET request to the server
    response = requests.get(url)

    # Check the status code of the response
    if response.status_code == 200:
        # If the response is successful, print the status of the pod
        print(f"Pod status: {response.json()['status']}")
    else:
        # If the response is not successful, print the error message
        return None


kubernetes = KubernetesCLI()


cpu_values = ["1500m", "2000m", "2500m", "3000m", "3500m", "4000m", "4500m", "5000m"]
cpu_usage = []
STOP_THREAD = False

def save_pod_stats():
    print("thread has started ...")
    global cpu_usage
    global STOP_THREAD
    pod_metrics = kubernetes.get_pod_stat(POD_NAME)
    while not STOP_THREAD:
        if pod_metrics != None:
            cpu_usage.append(pod_metrics["containers"][0]["usage"]["cpu"])
        sleep(5)
        pod_metrics = kubernetes.get_pod_stat(POD_NAME)

def analyze_cpu_usage(cpu_usage_list):
    # Convert each usage value to an integer in nanocores
    cpu_usage_ints = [int(value.strip('n')) for value in cpu_usage_list]

    # Convert to millicores and calculate average, max, and min
    cpu_usage_millicores = [usage_int // 1000000 for usage_int in cpu_usage_ints]
    avg_cpu_usage = sum(cpu_usage_millicores) / len(cpu_usage_millicores)
    max_cpu_usage = max(cpu_usage_millicores)
    min_cpu_usage = min(cpu_usage_millicores)

    # Return the results as a tuple
    return (avg_cpu_usage, max_cpu_usage, min_cpu_usage)

def main():
    global cpu_usage
    global STOP_THREAD
    stats_file = open('stats.txt', 'a')

    for cpu in cpu_values:
        
        thread = Thread(target=save_pod_stats)
        # Delete pod if exist
        kubernetes.delete_pod(POD_NAME)
        print("Deleting pod {} ....".format(POD_NAME))
        while kubernetes.pod_exists(name=POD_NAME):
            sleep(2)
        
        print("Pod {} was deleted successfully.".format(POD_NAME))

        print('Running scenario: cpu = {}'.format(cpu))

        print('Adding pod with new cpu limits ...')
        kubernetes.create_pod('../templates/pod.yaml', cpu=cpu)
        yolo_api_status = get_yolo_api_status()
        print('The pod isn\'t ready yet!')
        while yolo_api_status == None:
            sleep(2)
            yolo_api_status = get_yolo_api_status()
        print('The new pod was added successfully')

        print("Starting test load ....")
        thread.start()
        try:
            subprocess.run(['locust', '-f', 'loadtest.py', '--headless',
                                     '--users', '10', '--spawn-rate', '10', '--run-time','50s',
                                     '--host', yolo_service_endpoint, '--skip-log-setup', '--csv', 'locust.csv'], 
                                     check=True, capture_output=True, text=True)
            
            STOP_THREAD = True
            print("Thread has stopped")
        except subprocess.CalledProcessError as e:
            print(e.stderr)

        print("Load test finished .")
        
        stats = get_stats(window=40).content

        stats_file.write("cpu: " + cpu + " : " + str(stats) + str(analyze_cpu_usage(cpu_usage)) + "\n")
        print(cpu_usage[:3])
        cpu_usage = []

    stats_file.close()


if __name__ == '__main__':
    main()

"""
import cv2
from cvlib.object_detection import draw_bbox


def draw_box_arond_predicted_objects(image_name, bbox, label, conf):
    image = cv2.imread(image_name)

    output_image = draw_bbox(image, bbox, label, conf)

    cv2.imshow('Object detection', output_image)
    cv2.waitKey()
    cv2.destroyAllWindows()

usage': {'cpu': '2227090n', 'memory': '827592Ki'}
usage': {'cpu': '2652553529n', 'memory': '828380Ki'}


"""
