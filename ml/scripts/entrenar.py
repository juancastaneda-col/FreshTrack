"""
Entrena el modelo de reconocimiento con transfer learning sobre MobileNetV2.

Estrategia:
  Fase 1 - feature extraction:
    - MobileNetV2 preentrenado en ImageNet, capas base CONGELADAS.
    - Solo se entrena el head (GAP + Dropout + Dense).
    - 5 epochs, Adam(1e-3).
  Fase 2 - fine-tuning:
    - Se descongelan las ultimas 30 capas del MobileNetV2.
    - Learning rate muy bajo (Adam 1e-5) para no romper los pesos.
    - 3 epochs adicionales.

Ademas:
  - class_weight balanceado para compensar el desbalance 10:1 del dataset.
  - EarlyStopping para cortar si no mejora.
  - Guarda el modelo en ml/modelos/modelo.keras y las clases en clases.json.

Uso:
    py -3.11 ml/scripts/entrenar.py
"""

import json
import os
import sys
from pathlib import Path

# Forzar UTF-8 en Windows para que Keras pueda imprimir su progress bar.
sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
os.environ["PYTHONIOENCODING"] = "utf-8"

import numpy as np
import tensorflow as tf
from tensorflow.keras import layers, models
from tensorflow.keras.applications import MobileNetV2
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
from tensorflow.keras.callbacks import EarlyStopping, ReduceLROnPlateau, ModelCheckpoint


RAIZ_ML = Path(__file__).resolve().parents[1]
RAIZ_SPLITS = RAIZ_ML / "datasets" / "splits"
RAIZ_MODELOS = RAIZ_ML / "modelos"

TAMANO = 224
BATCH = 32
EPOCHS_HEAD = 5
EPOCHS_FINE = 3
CAPAS_A_DESCONGELAR = 30
SEMILLA = 42


def cargar_dataset(split):
    """Carga un split (train/val/test) como tf.data.Dataset. Preserva class_names."""
    ds = tf.keras.utils.image_dataset_from_directory(
        RAIZ_SPLITS / split,
        image_size=(TAMANO, TAMANO),
        batch_size=BATCH,
        shuffle=(split == "train"),
        seed=SEMILLA,
    )
    class_names = ds.class_names
    ds = ds.map(lambda x, y: (preprocess_input(x), y),
                num_parallel_calls=tf.data.AUTOTUNE)
    return ds.prefetch(tf.data.AUTOTUNE), class_names


def calcular_class_weight(class_names):
    """Peso por clase = total / (n_clases * conteo_clase). Compensa desbalance."""
    conteos = {}
    for c in class_names:
        conteos[c] = sum(1 for _ in (RAIZ_SPLITS / "train" / c).glob("*.jpg"))
    total = sum(conteos.values())
    pesos = {}
    for i, c in enumerate(class_names):
        pesos[i] = total / (len(class_names) * conteos[c])
    return pesos, conteos


def construir_modelo(num_clases):
    """MobileNetV2 congelado + head propio."""
    base = MobileNetV2(
        input_shape=(TAMANO, TAMANO, 3),
        include_top=False,
        weights="imagenet",
    )
    base.trainable = False

    entrada = tf.keras.Input(shape=(TAMANO, TAMANO, 3))
    x = base(entrada, training=False)
    x = layers.GlobalAveragePooling2D()(x)
    x = layers.Dropout(0.3)(x)
    x = layers.Dense(128, activation="relu")(x)
    x = layers.Dropout(0.3)(x)
    salida = layers.Dense(num_clases, activation="softmax")(x)

    return models.Model(entrada, salida), base


def main():
    RAIZ_MODELOS.mkdir(parents=True, exist_ok=True)

    print("Cargando datasets...")
    train_ds, class_names = cargar_dataset("train")
    val_ds, _ = cargar_dataset("val")
    print(f"Clases ({len(class_names)}): {class_names}")

    pesos, conteos = calcular_class_weight(class_names)
    print("\nConteo por clase (train, sin aumento):")
    for c, n in sorted(conteos.items(), key=lambda x: x[1]):
        print(f"  {c}: {n}  (peso {pesos[class_names.index(c)]:.2f})")

    modelo, base = construir_modelo(len(class_names))
    print(f"\nModelo: {modelo.count_params():,} parametros totales")

    callbacks = [
        EarlyStopping(monitor="val_accuracy", patience=3, restore_best_weights=True),
        ReduceLROnPlateau(monitor="val_loss", factor=0.5, patience=2, min_lr=1e-7),
        ModelCheckpoint(str(RAIZ_MODELOS / "modelo.keras"),
                        monitor="val_accuracy", save_best_only=True),
    ]

    print("\n== Fase 1: feature extraction (base congelado) ==")
    modelo.compile(
        optimizer=tf.keras.optimizers.Adam(1e-3),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    modelo.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS_HEAD,
        class_weight=pesos,
        callbacks=callbacks,
    )

    print(f"\n== Fase 2: fine-tuning (ultimas {CAPAS_A_DESCONGELAR} capas del base) ==")
    base.trainable = True
    for capa in base.layers[:-CAPAS_A_DESCONGELAR]:
        capa.trainable = False

    modelo.compile(
        optimizer=tf.keras.optimizers.Adam(1e-5),
        loss="sparse_categorical_crossentropy",
        metrics=["accuracy"],
    )
    modelo.fit(
        train_ds,
        validation_data=val_ds,
        epochs=EPOCHS_HEAD + EPOCHS_FINE,
        initial_epoch=EPOCHS_HEAD,
        class_weight=pesos,
        callbacks=callbacks,
    )

    # Guarda las clases en el orden exacto que las conoce el modelo.
    with open(RAIZ_MODELOS / "clases.json", "w", encoding="utf-8") as f:
        json.dump(class_names, f, ensure_ascii=False, indent=2)

    print(f"\nListo. Modelo guardado en {RAIZ_MODELOS / 'modelo.keras'}")
    print(f"      Clases guardadas en {RAIZ_MODELOS / 'clases.json'}")


if __name__ == "__main__":
    main()
