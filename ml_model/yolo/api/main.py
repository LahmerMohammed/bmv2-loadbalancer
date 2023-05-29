from PIL import Image
import numpy as np
import io
import cv2
import cvlib as cv
from fastapi import FastAPI, UploadFile, HTTPException
from enum import Enum
import time
import asyncio
from typing import List
import datetime

from redis import Redis
redis = Redis(host='localhost')





# List available models using Enum for convenience. This is useful when the options are pre-defined.
class Model(str, Enum):
    yolov3tiny = "yolov3-tiny"
    yolov3 = "yolov3"


app = FastAPI(title='Deploying a ML Model with FastAPI')

data = {
    'REQUEST_COUNTER': [],
    'REQUEST_LATENCY': []
}

lock = asyncio.Lock()

WINDOW = 10



@app.on_event("startup")
async def clear_redis():
    redis.flushdb()


@app.get("/")
def home():
    return "Congratulations! Your API is working as expected. Now head over to http://localhost:8000/docs."


@app.middleware("http")
async def update_metrics(request, call_next):
    global data
    if str(request.url.path) != '/predict':
        response = await call_next(request)
        return response

    start_time = time.time()
    response = await call_next(request)
    total_time = time.time() - start_time
    timestamp = time.time()

    redis.zadd('request', {str(timestamp): total_time})

    return response

@app.get('/stats')
async def get_stats(window: int = WINDOW):
    global data

    if window is not None and window <= 0:
        return {"window": "Window must be a positive integer greather than zero !"}


    starting_from = time.perf_counter() - window


    requests = redis.zrangebyscore('request', '-inf', '+inf', withscores=True)


    if len(requests) == 0:
        raise HTTPException(
            status_code=404, detail="No stats")

    included_requests = []
    for r in requests:
        timestamp = float(r[0].decode())
        if timestamp >= starting_from:
            included_requests.append((r[0].decode(), r[1]))

    included_requests = sorted(included_requests, key=lambda x: x[0])


    request_latency = [score for _, score in included_requests]
    interval = float(included_requests[-1][0]) - float(included_requests[0][0])

    print(interval)
    print(request_latency)
    request_rate = -1 if interval == 0 else len(included_requests) / interval


    return {
        "request_rate": round(request_rate, 2),
        "request_latency": -1 if len(request_latency) == 0 else  round(sum(request_latency) / len(request_latency), 2),
        "total_requests": len(included_requests)
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post('/predict')
async def predict(model: Model, images: List[UploadFile]):
    global data
    
    # 1. VALIDATE INPUT FILE
    responses = []
    for image in images:
        filename = image.filename
        fileExtension = filename.split(".")[-1] in ("jpg", "jpeg", "png")
        if not fileExtension:
            raise HTTPException(
                status_code=415, detail="Unsupported file provided.")

# 2.     TRANSFORM RAW IMAGE INTO CV2 image

        # Read image as a stream of bytes
        image_stream = io.BytesIO(await image.read())
        pil_image = Image.open(image_stream)

        # Write the stream of bytes into a numpy array
        numpy_image = np.array(pil_image)

        # Decode the numpy array as an image
        opencv_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)


# 3.     RUN OBJECT DETECTION MODEL

        # Run object detection
        response = cv.detect_common_objects(opencv_image, model=model)

        responses.append(response)

        # Return objects detected in the image
    return responses
