#!/bin/bash

sudo apt update > /dev/null
sudo apt install python3-pip python3-venv 


python3 -m venv venv
. venv/bin/activate

venv/bin/pip3 install -r requirements.txt

if test -e yolov3.weights; then
  echo "Model weights exists."
else
  echo "Model weights not found."
  wget https://pjreddie.com/media/files/yolov3.weights
fi



uvicorn main:app --reload --port 55555

