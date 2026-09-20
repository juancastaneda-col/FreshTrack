"""
Exporta el modelo .keras a TensorFlow Lite (.tflite) para uso en el celular.

Genera dos versiones:
  - modelo.tflite       sin cuantizar (float32)   ~8-12 MB
  - modelo_int8.tflite  cuantizado a int8         ~2-3 MB, mas rapido en movil

Uso:
    py -3.11 ml/scripts/exportar.py
"""

import os
import sys
from pathlib import Path

sys.stdout.reconfigure(encoding="utf-8", errors="replace")
sys.stderr.reconfigure(encoding="utf-8", errors="replace")
os.environ["PYTHONIOENCODING"] = "utf-8"

import numpy as np
import tensorflow as tf
from tensorflow.keras.applications.mobilenet_v2 import preprocess_input


RAIZ_ML = Path(__file__).resolve().parents[1]
RAIZ_MODELOS = RAIZ_ML / "modelos"
RAIZ_SPLITS = RAIZ_ML / "datasets" / "splits"

TAMANO = 224


def generador_representativo(n=100):
    """Muestras del train para calibrar la cuantizacion int8."""
    ds = tf.keras.utils.image_dataset_from_directory(
        RAIZ_SPLITS / "train",
        image_size=(TAMANO, TAMANO),
        batch_size=1,
        shuffle=True,
        seed=42,
    )
    ds = ds.map(lambda x, y: preprocess_input(x))
    for i, x in enumerate(ds):
        if i >= n:
            break
        yield [x]


def main():
    modelo_path = RAIZ_MODELOS / "modelo.keras"
    if not modelo_path.exists():
        sys.exit(f"No existe {modelo_path}. Corre entrenar.py primero.")

    print(f"Cargando modelo {modelo_path}...")
    modelo = tf.keras.models.load_model(modelo_path)

    # --- Version float32 ---
    print("\nConvirtiendo a TFLite float32...")
    conv = tf.lite.TFLiteConverter.from_keras_model(modelo)
    tflite_f32 = conv.convert()
    salida_f32 = RAIZ_MODELOS / "modelo.tflite"
    salida_f32.write_bytes(tflite_f32)
    print(f"  {salida_f32}  ({len(tflite_f32) / 1024:.0f} KB)")

    # --- Version int8 (cuantizada) ---
    print("\nConvirtiendo a TFLite int8 (usando 100 muestras del train)...")
    conv = tf.lite.TFLiteConverter.from_keras_model(modelo)
    conv.optimizations = [tf.lite.Optimize.DEFAULT]
    conv.representative_dataset = generador_representativo
    conv.target_spec.supported_ops = [tf.lite.OpsSet.TFLITE_BUILTINS_INT8]
    conv.inference_input_type = tf.int8
    conv.inference_output_type = tf.int8
    try:
        tflite_int8 = conv.convert()
        salida_int8 = RAIZ_MODELOS / "modelo_int8.tflite"
        salida_int8.write_bytes(tflite_int8)
        print(f"  {salida_int8}  ({len(tflite_int8) / 1024:.0f} KB)")
    except Exception as exc:
        print(f"  ADVERTENCIA: no se pudo cuantizar a int8: {exc}", file=sys.stderr)
        print("  El .tflite float32 sigue siendo utilizable.", file=sys.stderr)

    print("\nListo. Estos .tflite se copian al bundle de la app movil.")
    print("Se necesita tambien ml/modelos/clases.json para mapear los indices "
          "que predice el modelo a nombres.")


if __name__ == "__main__":
    main()
