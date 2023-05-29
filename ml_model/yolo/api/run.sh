#!/bin/bash

redis-server &
#uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
gunicorn main:app -b 0.0.0.0:8000 --workers $1 --threads $2 --worker-class uvicorn.workers.UvicornWorker