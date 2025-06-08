import os
import sys
import cv2
import numpy as np
import tensorflow as tf
from tensorflow import keras
import tensorflow_datasets as tfds
from datasets import load_dataset
from tensorflow.keras import layers, models
from pathlib import Path

# === Konfiguration ===
MODEL_PATH = "model/image_classifier.h5"
IMAGE_SIZE = (128, 128)
BATCH_SIZE = 32
EPOCHS = 5
DATASET_NAME = "XAI/OpenImages-Inpainted"  # <- Du kannst das hier ändern in jedes ImageDataset bei HF

def preprocess(example):
    image = tf.image.resize(example['image'], IMAGE_SIZE)
    image = tf.cast(image, tf.float32) / 255.0
    label = example['labels']
    return {'image': image, 'label': label}

def convert_to_tf_dataset(hf_dataset, batch_size):
    return hf_dataset.to_tf_dataset(
        columns=['image'],
        label_cols='label',
        shuffle=True,
        batch_size=batch_size
    )


def load_data():
    # Lade Training und Validation Split
    train_ds = load_dataset("XAI/OpenImages-Inpainted", split="train")
    val_ds = load_dataset("XAI/OpenImages-Inpainted", split="validation")

    # Anzahl der Klassen
    label_info = train_ds.features["label"]
    num_classes = label_info.num_classes

    # Preprocessing
    def preprocess(example):
        image = tf.image.resize(example['image'], IMAGE_SIZE)
        image = tf.cast(image, tf.float32) / 255.0
        label = example['label']  # 👈 FIXED HERE
        return {'image': image, 'label': label}

    train_ds = train_ds.map(preprocess)
    val_ds = val_ds.map(preprocess)

    def to_tf(ds):
        return ds.to_tf_dataset(
            columns="image",
            label_cols="label",
            shuffle=True,
            batch_size=BATCH_SIZE
        ).prefetch(tf.data.AUTOTUNE)

    return to_tf(train_ds), to_tf(val_ds), num_classes
    
def build_model(num_classes):
    model = models.Sequential([
        layers.InputLayer(input_shape=(*IMAGE_SIZE, 3)),
        layers.Conv2D(32, (3,3), activation='relu'),
        layers.MaxPooling2D(),
        layers.Conv2D(64, (3,3), activation='relu'),
        layers.MaxPooling2D(),
        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.Dense(num_classes, activation='softmax')
    ])
    model.compile(optimizer='adam',
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])
    return model

def train_model():
    train, val, num_classes = load_data()

    model = create_model(num_classes)
    model.compile(
        optimizer='adam',
        loss='sparse_categorical_crossentropy',
        metrics=['accuracy']
    )

    print("🚀 Starte Training...")
    model.fit(train, validation_data=val, epochs=EPOCHS)

    # Modell speichern
    os.makedirs("model", exist_ok=True)
    model.save("model/image_classifier.h5")  # Optional (älteres HDF5-Format)
    print("✅ Modell gespeichert unter model/image_classifier")

def create_model(num_classes):
    model = keras.Sequential([
        layers.Input(shape=(*IMAGE_SIZE, 3)),
        layers.Conv2D(32, 3, activation='relu'),
        layers.MaxPooling2D(),
        layers.Conv2D(64, 3, activation='relu'),
        layers.MaxPooling2D(),
        layers.Conv2D(128, 3, activation='relu'),
        layers.MaxPooling2D(),
        layers.Flatten(),
        layers.Dense(128, activation='relu'),
        layers.Dropout(0.3),
        layers.Dense(num_classes, activation='softmax')
    ])
    return model

def infer_webcam():
    print("📷 Starte Webcam und lade Modell...")
    if not os.path.exists(MODEL_PATH):
        print("❌ Modell nicht gefunden. Bitte zuerst mit `python -t iclass.py` trainieren.")
        return

    model = tf.keras.models.load_model(MODEL_PATH)

    # Hole Labels aus Huggingface
    dataset_info = load_dataset("XAI/OpenImages-Inpainted", split="test")
    labels = dataset_info.features['label'].names  # <- Singular 'label'

    cap = cv2.VideoCapture(0)

    while True:
        ret, frame = cap.read()
        if not ret:
            continue

        img = cv2.resize(frame, IMAGE_SIZE)
        img = np.expand_dims(img / 255.0, axis=0)
        preds = model.predict(img)
        label_idx = np.argmax(preds)
        label = labels[label_idx]
        confidence = np.max(preds)

        text = f"{label} ({confidence*100:.1f}%)"
        cv2.putText(frame, text, (10,30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,255,0), 2)
        cv2.imshow("Live Prediction", frame)

        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    cv2.destroyAllWindows()

if __name__ == "__main__":
    if "-t" in sys.argv:
        train_model()
    else:
        infer_webcam()
