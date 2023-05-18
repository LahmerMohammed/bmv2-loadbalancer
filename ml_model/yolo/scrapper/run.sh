#!/bin/bash
python3.10 -m venv venv
. venv/bin/activate

pip3 install -r requirements.txt

uvicorn main:app --reload --host 0.0.0.0 --port 10001

