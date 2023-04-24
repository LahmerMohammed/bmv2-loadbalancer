
from typing import Annotated
from PIL import Image
import numpy as np
import io
import cv2

from model import predict


from fastapi import FastAPI, UploadFile
from fastapi.responses import JSONResponse

app = FastAPI()


@app.post('/predict')
async def root(image: UploadFile):

    file_content = await image.read()
    pil_image = Image.open(io.BytesIO(file_content))
    numpy_image = np.array(pil_image)
    opencv_image = cv2.cvtColor(numpy_image, cv2.COLOR_RGB2BGR)
    results = predict(opencv_image)
    
    results = [{k: int(v) if isinstance(v, np.int64) else v for k, v in d.items()} for d in results] 
    print(results)

    return JSONResponse(content=results)