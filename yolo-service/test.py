import requests
import cv2
import numpy as np
import json

"""
curl -X POST 'http://127.0.0.1:8000/predict?model=yolov3-tiny' --form 'image=@cars.jpg' -H  "accept: application/json"         

"""

url = "http://localhost:55555/predict"

image = '/home/lahmer/Pictures/mohammed.jpg'

files = {'image': (image, open(image, 'rb'), 'image/jpeg')}

headers = {
    'accept': 'application/json'
}


with open(classes, 'r') as f:
    classes = [line.strip() for line in f.readlines()]

def draw_prediction(img, label, confidence, bbox):

    cv2.rectangle(img, (x,y), (x_plus_w,y_plus_h), color, 2)

    cv2.putText(img, label, (x-10,y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 2)


response = requests.post(url, headers=headers, files=files).content.decode('utf-8')
data = json.loads(response)
print(data)
d = data[0]

draw_prediction(image, d["class"], d["confidences"], d["x"], d["y"], d["w"], d["h"])


cv2.imshow("object detection", image)
cv2.waitKey()
    
cv2.imwrite("object-detection.jpg", image)
cv2.destroyAllWindows()


"""
curl -X 'POST' \
  'http://localhost:8000/predict?model=yolov3-tiny' \
  -H 'accept: application/json' \
  -H 'Content-Type: multipart/form-data' \
  -F 'image=@DSC_0820-new-3_104803.jpg;type=image/jpeg'
"""