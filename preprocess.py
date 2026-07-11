import numpy as np
import cv2

def preprocess_canvas(img_array):
    gray = cv2.cvtColor(img_array, cv2.COLOR_BGR2GRAY)
    _, binary = cv2.threshold(gray, 127, 255, cv2.THRESH_BINARY)
    
    coords = cv2.findNonZero(binary)
    if coords is None:
        return None
    
    x, y, w, h = cv2.boundingRect(coords)
    margin = 4
    x = max(0, x - margin)
    y = max(0, y - margin)
    w = min(binary.shape[1] - x, w + 2*margin)
    h = min(binary.shape[0] - y, h + 2*margin)
    digit = binary[y:y+h, x:x+w]
    
    result = np.zeros((28, 28), dtype=np.uint8)
    
    if w > h:
        new_w = 20
        new_h = max(1, int(h * (20 / w)))
    else:
        new_h = 20
        new_w = max(1, int(w * (20 / h)))
    
    resized = cv2.resize(digit, (new_w, new_h), interpolation=cv2.INTER_AREA)
    start_x = (28 - new_w) // 2
    start_y = (28 - new_h) // 2
    result[start_y:start_y+new_h, start_x:start_x+new_w] = resized
    
    result = result.astype('float32') / 255.0
    result = np.expand_dims(result, axis=(0, 3))
    return result
