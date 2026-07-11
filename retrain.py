import numpy as np
import cv2
import glob
import os
import keras

def load_corrections():
    images, labels = [], []
    for label in range(10):
        folder = f"corrections/{label}"
        if not os.path.exists(folder):
            continue
        for file in glob.glob(f"{folder}/*.png"):
            img = cv2.imread(file, cv2.IMREAD_GRAYSCALE)
            img = cv2.resize(img, (28, 28))
            img = img / 255.0
            images.append(img)
            labels.append(label)
    return np.array(images), np.array(labels)

# Загружаем модель
model = keras.models.load_model('mnist_cnn.keras')

# Загружаем исправления
corr_x, corr_y = load_corrections()
print(f"Загружено {len(corr_x)} исправлений")

if len(corr_x) > 0:
    corr_x = np.expand_dims(corr_x, axis=3)
    corr_y_cat = keras.utils.to_categorical(corr_y, 10)
    
    model.compile(
        optimizer=keras.optimizers.Adam(0.0001),
        loss='categorical_crossentropy',
        metrics=['accuracy']
    )
    
    model.fit(corr_x, corr_y_cat, epochs=20, batch_size=8)
    model.save('mnist_final.keras')
    print("Модель обновлена!")
