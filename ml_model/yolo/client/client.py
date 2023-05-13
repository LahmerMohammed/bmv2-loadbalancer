from threading import Thread
import requests
from enum import Enum
import yaml
from time import sleep
import subprocess
from k8s import KubernetesCLI


server_ip = "34.154.187.246"

endpoint = "http://{}:32474".format(server_ip)
images = ['images/cars.jpg']


POD_NAME = "yolo-v3"
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
        return None


kubernetes = KubernetesCLI()



cpu_values = ["3052m", "4052m"]
cpu_usage = []

STOP_THREAD = False

def save_pod_stats():
    global cpu_usage
    global STOP_THREAD
    sleep(10)
    pod_metrics = kubernetes.get_pod_stat(POD_NAME)
    while not STOP_THREAD:
        if pod_metrics != None:
            cpu_usage.append(pod_metrics[0]["containers"][0]["usage"]["cpu"])
        sleep(1)
        pod_metrics = kubernetes.get_pod_stat(POD_NAME)


def main():
    global cpu_usage
    global STOP_THREAD
    stats_file = open('stats.txt', 'a')

    for cpu in cpu_values:
        
        thread = Thread(target=save_pod_stats)
        # Delete pod if exist
        kubernetes.delete_pod(POD_NAME)
        yolo_api_status = get_yolo_api_status()
        print("Deleting pod {} ....".format(POD_NAME))
        while yolo_api_status != None:
            yolo_api_status = get_yolo_api_status()
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
                                     '--users', '5', '--spawn-rate', '1', '--run-time','30s',
                                     '--host', 'http://{}:32474'.format(server_ip), '--skip-log-setup'], 
                                     check=True, capture_output=True, text=True)
            
            STOP_THREAD = True
        except subprocess.CalledProcessError as e:
            print(e.stderr)

        print("Load test finished .")
        
        stats = get_stats().content

        stats_file.write("cpu: " + cpu + " : " + str(stats) + str(cpu_usage) + "\n")
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
