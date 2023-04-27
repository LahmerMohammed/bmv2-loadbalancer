#!/bin/bash

apt update > /dev/null
apt install python3-pip python3-venv libglvnd-dev mesa-utils -y


python3 -m venv venv
. venv/bin/activate

venv/bin/pip3 install -r requirements.txt

uvicorn main:app --reload --host 0.0.0.0 --port 8000 &

