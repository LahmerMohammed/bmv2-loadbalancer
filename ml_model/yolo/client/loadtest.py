from locust import HttpUser, between, task
from locust.runners import MasterRunner


server_ip = "34.154.94.220"
endpoint = "http://{}:32474/predict".format(server_ip)


class LoadTest(HttpUser):
    wait_time = between(1, 5)

    @task
    def predict(self):
        image_name = 'images/cars.jpg'
        files = {'image': (image_name, open(image_name, 'rb'), 'image/jpeg')}
        headers = {'accept': 'application/json'}
        self.client.post("/predict?model=yolov3-tiny",
                         files=files, headers=headers)


options = {
    "user_classes": [LoadTest],
    "host": "http://34.154.94.220:32474",
    "num_clients": 1,
    "spawn_rate": 2,
    "stop_timeout": 10,
}


