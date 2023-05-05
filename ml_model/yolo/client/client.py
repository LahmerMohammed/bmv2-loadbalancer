import requests
from enum import Enum

NUMBER_OF_REQUESTS = 100
endpoint = "http://localhost:8000/predict"
images = ['cars.jpg', 'bus.jpg']


# List available models using Enum for convenience. This is useful when the options are pre-defined.
class Model(str, Enum):
    yolov3tiny = "yolov3-tiny"
    yolov3 = "yolov3"   

"""
import cv2
from cvlib.object_detection import draw_bbox


def draw_box_arond_predicted_objects(image_name, bbox, label, conf):
    image = cv2.imread(image_name)

    output_image = draw_bbox(image, bbox, label, conf)

    cv2.imshow('Object detection', output_image)
    cv2.waitKey()
    cv2.destroyAllWindows()
"""
def get_stats():
    url = 'http://localhost:8000/stats?window=10'
    headers = {'accept': 'application/json'}

    return requests.get(url, headers=headers)

def predict(image_name: str, model: Model = 'yolov3'):
    params = {'model': model}
    headers = {'accept': 'application/json'}
    files = {'image': (image_name, open(image_name, 'rb'), 'image/jpeg')}

    return requests.post(
        endpoint, params=params, headers=headers, files=files).json()




if __name__ == '__main__':
    number_of_images = len(images)
    for i in range(NUMBER_OF_REQUESTS):
        predict(image_name=images[i % number_of_images])
    
    print(get_stats().content)
