#!/bin/bash

current_dir=$(pwd)


apt update > /dev/null
apt install python3-pip python3-venv libglvnd-dev mesa-utils ffmpeg libsm6 libxext6 -y 


python3 -m venv venv
. venv/bin/activate

pip3 install -r requirements.txt


# Create directory if it does not exist
if [ ! -d "/root/.cvlib/object_detection/yolo/yolov3" ]; then
  mkdir -p /root/.cvlib/object_detection/yolo/yolov3
fi

# Change to directory
cd /root/.cvlib/object_detection/yolo/yolov3

# Download files
wget https://pjreddie.com/media/files/yolov3.weights &
wget https://github.com/pjreddie/darknet/raw/master/cfg/yolov3.cfg &
wget https://github.com/arunponnusamy/object-detection-opencv/raw/master/yolov3.txt &

# Wait for all downloads to complete
wait

cd /bmv2-loadbalancer/ml_model/yolo/api

uvicorn main:app --reload --host 0.0.0.0 --port 8000

