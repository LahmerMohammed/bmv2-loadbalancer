#!/bin/bash

#apt update > /dev/null
#apt install python3-pip python3-venv libglvnd-dev mesa-utils ffmpeg libsm6 libxext6 -y 


#python3 -m venv venv
#. venv/bin/activate

#pip3 install -r requirements.txt

#mkdir -p /root/.cvlib/object_detection/yolo/yolov3

#yolo_path=/root/.cvlib/object_detection/yolo/yolov3

# Download files
#wget https://pjreddie.com/media/files/yolov3.weights -O ${yolo_path}/yolov3.weights
#wget https://github.com/pjreddie/darknet/raw/master/cfg/yolov3.cfg -O ${yolo_path}/yolov3.cfg
#wget https://github.com/arunponnusamy/object-detection-opencv/raw/master/yolov3.txt -O ${yolo_path}/yolov3.txt

uvicorn main:app --reload --host 0.0.0.0 --port 8000

