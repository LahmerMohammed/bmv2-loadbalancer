
import os, sys
sys.path.append('../../yolo')


from PIL import Image
import numpy as np
import io
import cv2
import cvlib as cv
from fastapi import FastAPI, UploadFile, HTTPException
from enum import Enum


# List available models using Enum for convenience. This is useful when the options are pre-defined.
class Model(str, Enum):
    yolov3tiny = "yolov3-tiny"
    yolov3 = "yolov3"   

app = FastAPI(title='Deploying a ML Model with FastAPI')

@app.get("/")
def home():
    return "Congratulations! Your API is working as expected. Now head over to http://localhost:8000/docs."


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.post('/predict')
async def predict(model: Model, image: UploadFile):

# 1. VALIDATE INPUT FILE
    filename = image.filename
    fileExtension = filename.split(".")[-1] in ("jpg", "jpeg", "png")
    if not fileExtension:
        raise HTTPException(status_code=415, detail="Unsupported file provided.")
    
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

