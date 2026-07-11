import numpy as np
from keras.models import load_model
from config import MODEL_PATH

_model = None

def get_model():
    global _model
    if _model is None:
        _model = load_model(MODEL_PATH)
    return _model

def predict_digit(processed_img):
    model = get_model()
    pred = model.predict(processed_img, verbose=0)
    digit = np.argmax(pred)
    confidence = np.max(pred) * 100
    return digit, confidence
