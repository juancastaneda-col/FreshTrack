"""
Evalua el modelo entrenado sobre el conjunto de prueba.

Genera:
  - ml/modelos/reporte.txt         precision global + precision por clase
  - ml/modelos/matriz_confusion.png matriz de confusion normalizada

Uso:
    py -3.11 ml/scripts/evaluar.py
"""

import json
import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
os.environ["PYTHONIOENCODING"] = "utf-8"

import matplotlib
matplotlib.use("Agg")  # sin display, para correr en background
import matplotlib.pyplot as plt
import numpy as np
import tensorflow as tf
from sklearn.metrics import (classification_report, confusion_matrix,
                             accuracy_score)
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input


RAIZ_ML = Path(__file__).resolve().parents[1]
RAIZ_SPLITS = RAIZ_ML / "datasets" / "splits"
RAIZ_MODELOS = RAIZ_ML / "modelos"

TAMANO = 224
BATCH = 32


def cargar_test():
    ds = tf.keras.utils.image_dataset_from_directory(
        RAIZ_SPLITS / "test",
        image_size=(TAMANO, TAMANO),
        batch_size=BATCH,
        shuffle=False,
    )
    class_names = ds.class_names
    ds = ds.map(lambda x, y: (preprocess_input(x), y),
                num_parallel_calls=tf.data.AUTOTUNE)
    return ds.prefetch(tf.data.AUTOTUNE), class_names


def main():
    modelo_path = RAIZ_MODELOS / "modelo.keras"
    if not modelo_path.exists():
        sys.exit(f"No existe {modelo_path}. Corre entrenar.py primero.")

    print(f"Cargando modelo {modelo_path}...")
    modelo = tf.keras.models.load_model(modelo_path)

    print("Cargando test set...")
    test_ds, class_names = cargar_test()

    print("Prediciendo...")
    y_true = np.concatenate([y.numpy() for _, y in test_ds])
    y_pred_probs = modelo.predict(test_ds, verbose=1)
    y_pred = y_pred_probs.argmax(axis=1)

    precision_global = accuracy_score(y_true, y_pred)
    reporte_dict = classification_report(y_true, y_pred, target_names=class_names,
                                         output_dict=True, zero_division=0)
    reporte_txt = classification_report(y_true, y_pred, target_names=class_names,
                                        zero_division=0)

    # --- Reporte de texto ---
    salida = []
    salida.append("== Evaluacion del modelo ==\n")
    salida.append(f"Precision global (accuracy): {precision_global:.4f}\n")
    salida.append(f"Total imagenes de test: {len(y_true)}\n")
    salida.append(f"Clases: {len(class_names)}\n\n")
    salida.append("Precision, recall y F1 por clase:\n")
    salida.append(reporte_txt)
    salida.append("\n\n")

    # Precision >= 85%?
    meta = 0.85
    if precision_global >= meta:
        salida.append(f"OK: cumple la meta de >= {meta*100:.0f}% en test.\n")
    else:
        salida.append(f"ADVERTENCIA: precision {precision_global:.2%} < meta {meta:.0%}.\n")
        salida.append("Sugerencias: mas epochs, mas datos por clase minoritaria, "
                      "class_weight mas agresivo, o revisar imagenes mal etiquetadas.\n")

    reporte_path = RAIZ_MODELOS / "reporte.txt"
    reporte_path.write_text("".join(salida), encoding="utf-8")
    print(f"\nReporte guardado en {reporte_path}")
    print("\n" + "".join(salida))

    # --- Matriz de confusion ---
    cm = confusion_matrix(y_true, y_pred, normalize="true")
    fig, ax = plt.subplots(figsize=(12, 10))
    im = ax.imshow(cm, interpolation="nearest", cmap="Blues", vmin=0, vmax=1)
    ax.set_title(f"Matriz de confusion (normalizada)\nprecision global: {precision_global:.2%}")
    ax.set_xlabel("Prediccion")
    ax.set_ylabel("Real")
    ax.set_xticks(range(len(class_names)))
    ax.set_yticks(range(len(class_names)))
    ax.set_xticklabels(class_names, rotation=45, ha="right", fontsize=8)
    ax.set_yticklabels(class_names, fontsize=8)
    for i in range(len(class_names)):
        for j in range(len(class_names)):
            valor = cm[i, j]
            if valor > 0.01:
                color = "white" if valor > 0.5 else "black"
                ax.text(j, i, f"{valor:.2f}", ha="center", va="center",
                        color=color, fontsize=6)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    fig.tight_layout()

    cm_path = RAIZ_MODELOS / "matriz_confusion.png"
    fig.savefig(cm_path, dpi=150, bbox_inches="tight")
    print(f"Matriz de confusion guardada en {cm_path}")

    # Tambien guardo el reporte_dict como JSON, util para reportes automaticos
    with open(RAIZ_MODELOS / "reporte.json", "w", encoding="utf-8") as f:
        json.dump({
            "precision_global": precision_global,
            "por_clase": reporte_dict,
            "clases": class_names,
        }, f, ensure_ascii=False, indent=2)


if __name__ == "__main__":
    main()
