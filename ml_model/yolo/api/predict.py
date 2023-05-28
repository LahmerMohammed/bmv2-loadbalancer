from PIL import Image
import numpy as np
import cv2
import cvlib as cv
from enum import Enum
import sys



# List available models using Enum for convenience. This is useful when the options are pre-defined.
class Model(str, Enum):
    yolov3tiny = "yolov3-tiny"
    yolov3 = "yolov3"

def predict(model: Model, image_path: str):
    # 1. Load the image from file path
    pil_image = Image.open(image_path)
    
    # 2. Transform PIL image into CV2 image
    cv_image = cv2.cvtColor(np.array(pil_image), cv2.COLOR_RGB2BGR)

    # 3. Run object detection model
    response = cv.detect_common_objects(cv_image, model=model)

    return response


if __name__ == "__main__":
    # Check if the image path is provided as a command-line argument
    if len(sys.argv) < 3:
        print("Image path or Model is missing.")
        print("Usage: python script.py <image_path>")
        sys.exit(1)

    # Get the image path from command-line arguments
    image_path = sys.argv[1]

    # Specify the model
    model = sys.argv[2]

    # Perform object detection
    result = predict(model, image_path)

    # Print the detected objects
    print(result)