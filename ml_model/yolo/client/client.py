import requests
from enum import Enum
import yaml
from time import sleep
import subprocess


server_ip = "34.154.94.220"

endpoint = "http://{}:32474".format(server_ip)
images = ['images/cars.jpg']


class Model(str, Enum):
    yolov3tiny = "yolov3-tiny"
    yolov3 = "yolov3"


def get_stats():
    url = 'http://{}:32474/stats?window=20'.format(server_ip)
    headers = {'accept': 'application/json'}

    return requests.get(url, headers=headers)


def predict(image_name: str, model: Model = 'yolov3-tiny'):
    params = {'model': model}
    headers = {'accept': 'application/json'}
    files = {'image': (image_name, open(image_name, 'rb'), 'image/jpeg')}

    return requests.post(
        endpoint, params=params, headers=headers, files=files)

def get_yolo_api_status():
    headers = {'accept': 'application/json'}
    url = "http://{}:32474/health".format(server_ip)

    try:
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Check for HTTP errors
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
        print(f"Error: {response.json()['message']}")

def add_pod(pod: dict): 
    url = "http://{}:14000/pods".format(server_ip)
    print(pod)
    response = requests.post(url, json=pod)

    if response.status_code == 200:
        print("Pod created successfully.")
    else:
        print(f"Error: {response}")




NUMBER_OF_REQUESTS = 50


cpu_values = ["2652m"]

if __name__ == '__main__':
    for cpu in cpu_values:
    
        # Check if pod don't exist

        f = open('../templates/pod.yaml')
        pod = yaml.safe_load(f)
        pod["spec"]["containers"][0]["resources"]["limits"]["cpu"] = cpu
        add_pod(pod=pod)
        yolo_api_status = get_yolo_api_status()
        while yolo_api_status == None:
            sleep(10)
            print('The pod isn\'t ready yet!')
            yolo_api_status = get_yolo_api_status()
        
        print('The pod is ready !')

        response = predict("images/cars.jpg")

        sleep(30)

        result = subprocess.run(['locust', '-f', 'loadtest.py', '--headless',
                                 '--users', '5', '--spawn-rate', '5', '--run-time','25s',
                                 '--host', 'http://34.154.94.220:32474', '--skip-log-setup'], 
                                 check=True, capture_output=True, text=True)
        
        print(get_stats().content)




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