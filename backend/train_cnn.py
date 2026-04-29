import os
import cv2
import numpy as np
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Conv2D, MaxPooling2D, Flatten, Dense, Dropout
from tensorflow.keras.utils import to_categorical
from sklearn.model_selection import train_test_split

IMG_SIZE = 100
DATASET_PATH = "known_faces"

X = []
y = []

class_names = sorted(os.listdir(DATASET_PATH))

print("Classes:", class_names)

for label, class_name in enumerate(class_names):
    folder = os.path.join(DATASET_PATH, class_name)

    if not os.path.isdir(folder):
        continue

    for file in os.listdir(folder):
        path = os.path.join(folder, file)

        img = cv2.imread(path)
        if img is None:
            continue

        img = cv2.resize(img, (IMG_SIZE, IMG_SIZE))
        img = img / 255.0

        X.append(img)
        y.append(label)

X = np.array(X)
y = np.array(y)

y = to_categorical(y, num_classes=len(class_names))

X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42
)

model = Sequential([
    Conv2D(32, (3,3), activation="relu", input_shape=(100,100,3)),
    MaxPooling2D(2,2),

    Conv2D(64, (3,3), activation="relu"),
    MaxPooling2D(2,2),

    Flatten(),
    Dense(128, activation="relu"),
    Dropout(0.3),

    Dense(len(class_names), activation="softmax")
])

model.compile(
    optimizer="adam",
    loss="categorical_crossentropy",
    metrics=["accuracy"]
)

model.fit(X_train, y_train, epochs=25, validation_data=(X_test, y_test))

model.save("cnn_face_model.h5")

with open("class_names.txt", "w") as f:
    for name in class_names:
        f.write(name + "\n")

print("Training Done")