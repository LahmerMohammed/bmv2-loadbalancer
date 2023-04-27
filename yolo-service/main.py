
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
async def predict(model: Model, image: UploadFile):

    file_content = await image.read()
    pil_image = Image.open(io.BytesIO(file_content))
    numpy_image = np.array(pil_image)
    opencv_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
    

    response = cv.detect_common_objects(opencv_image, model=model)

    return response


