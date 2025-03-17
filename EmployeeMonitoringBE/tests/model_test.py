import cv2 as cv
from ultralytics import YOLO

# Parse user inputs
model_path = "../flaskr/ML/PPE_model/my_model.pt"


# Load the model into memory and get labemap
model = YOLO(model_path, task='detect')
labels = model.names
print(labels)
