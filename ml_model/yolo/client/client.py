import requests
import cv2
from cvlib.object_detection import draw_bbox
import argparse
from ml_model.yolo import Model


def predict_and_draw_bbox(image_name: str, model: Model = 'yolov3-tiny'):
    url = 'http://localhost:8000/predict'
    params = {'model': model}
    headers = {'accept': 'application/json'}
    files = {'image': (image_name, open(image_name, 'rb'), 'image/jpeg')}

    bbox, label, conf = requests.post(
        url, params=params, headers=headers, files=files).json()

    image = cv2.imread(image_name)

    output_image = draw_bbox(image, bbox, label, conf)

    cv2.imshow('Object detection', output_image)
    cv2.waitKey()
    cv2.destroyAllWindows()


if __name__ == '__main__':

    parser = argparse.ArgumentParser(
        description='Object detection using YOLOv3')

    # Add the arguments
    parser.add_argument('--image', type=str, help='path to the image file')
    parser.add_argument('--model', type=Model,  choices=[model.value for model in list(
        Model)], help='name of the YOLOv3-tiny model', default='yolov3-tiny')

    # Parse the arguments
    args = parser.parse_args()
    predict_and_draw_bbox(image_name=args.image, model=args.model.value)
