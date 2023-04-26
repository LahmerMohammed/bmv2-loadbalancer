
from enum import Enum
from typing import Annotated
from PIL import Image
import numpy as np
import io
import cv2
import cvlib as cv

from fastapi import FastAPI, UploadFile, File, HTTPException
from fastapi.responses import JSONResponse


# List available models using Enum for convenience. This is useful when the options are pre-defined.
class Model(str, Enum):
    yolov3tiny = "yolov3-tiny"
    yolov3 = "yolov3"


app = FastAPI(title='Deploying a ML Model with FastAPI')


@app.get("/")
def home():
    return "Congratulations! Your API is working as expected. Now head over to http://localhost:8000/docs."


@app.post('/predict')
async def predict(model: Model, image: UploadFile = File(...)):

    # 1. VALIDATE INPUT FILE
    filename = image.filename
    fileExtension = filename.split(".")[-1] in ("jpg", "jpeg", "png")
    if not fileExtension:
        raise HTTPException(status_code=415, detail="Unsupported file provided.")
    # 2. TRANSFORM RAW IMAGE INTO CV2 image

    # Read image as a stream of bytes
    image_stream = io.BytesIO(image.file.read())

    # Start the stream from the beginning (position zero)
    image_stream.seek(0)

    # Write the stream of bytes into a numpy array
    file_bytes = np.asarray(bytearray(image_stream.read()), dtype=np.uint8)

    # Decode the numpy array as an image
    image = cv2.imdecode(file_bytes, cv2.IMREAD_COLOR)

    # 3. RUN OBJECT DETECTION MODEL

    # Run object detection
    results = cv.detect_common_objects(image, model=model)

    return JSONResponse(content=results)


