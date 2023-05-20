from PIL import Image
import numpy as np
import io
import cv2
import cvlib as cv
from fastapi import FastAPI, UploadFile, HTTPException
from enum import Enum
import datetime
from multiprocessing import Manager
manager = Manager()

# List available models using Enum for convenience. This is useful when the options are pre-defined.
class Model(str, Enum):
    yolov3tiny = "yolov3-tiny"
    yolov3 = "yolov3"

from multiprocessing import Manager


app = FastAPI(title='Deploying a ML Model with FastAPI')
manager = Manager()

REQUEST_COUNTER = manager.list([])
REQUEST_LATENCY = manager.list([])
WINDOW = 10


@app.get("/")
def home():
    return "Congratulations! Your API is working as expected. Now head over to http://localhost:8000/docs."


@app.middleware("http")
async def update_metrics(request, call_next):
    global app
    if str(request.url.path) != '/predict':
        response = await call_next(request)
        return response
    

    timestamp = datetime.datetime.now()
    REQUEST_COUNTER.append(timestamp)

    
    start_time = datetime.datetime.now()
    response = await call_next(request)
    end_time = datetime.datetime.now()
    total_time = (end_time - start_time).total_seconds()

    timestamp = datetime.datetime.now()
    REQUEST_LATENCY.append({
        'timestamp': datetime.datetime.now(),
        'value': total_time
    })
    return response

@app.get('/stats')
async def get_stats(window: int = WINDOW):
    global app

    if window is not None and window <= 0:
        return {"window": "Window must be a positive integer greather than zero !"}
    
    starting_from = datetime.datetime.now() - datetime.timedelta(seconds=window) 
    
    
    request_rate = 0
    for req_c in reversed(app.REQUEST_COUNTER): 
        if req_c < starting_from:
            break
        request_rate = request_rate + 1
    

    request_latency = []
    for req_l in reversed(REQUEST_LATENCY): 
        if req_l['timestamp'] < starting_from:
            break
        request_latency.append(req_l['value'])
    
    
    return {
        "request_rate": round(request_rate / window, 2),
        "request_latency": -1 if len(request_latency) == 0 else  round(sum(request_latency) / len(request_latency), 2)
    }

@app.get("/health")
def health():
    return {"status": "ok"}

@app.post('/predict')
async def predict(model: Model, image: UploadFile):

    # 1. VALIDATE INPUT FILE
    filename = image.filename
    fileExtension = filename.split(".")[-1] in ("jpg", "jpeg", "png")
    if not fileExtension:
        raise HTTPException(
            status_code=415, detail="Unsupported file provided.")

# 2. TRANSFORM RAW IMAGE INTO CV2 image

    # Read image as a stream of bytes
    image_stream = io.BytesIO(await image.read())
    pil_image = Image.open(image_stream)

    # Write the stream of bytes into a numpy array
    numpy_image = np.array(pil_image)

    # Decode the numpy array as an image
    opencv_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)


# 3. RUN OBJECT DETECTION MODEL

    # Run object detection
    response = cv.detect_common_objects(opencv_image, model=model)

    # Return objects detected in the image
    return response
