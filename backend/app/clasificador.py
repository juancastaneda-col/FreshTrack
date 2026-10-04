"""
Clasificación de alimentos frescos/dañados usando el modelo TFLite de FreshTrack.

Carga el modelo una sola vez al primer uso (lazy) para no ralentizar el arranque
del servidor. Las llamadas posteriores reutilizan el intérprete ya inicializado.
"""

import json
import sys
from pathlib import Path

import cv2
import numpy as np

RUTA_ML      = Path(__file__).resolve().parents[2] / "ml"
RUTA_MODELO  = RUTA_ML / "modelos" / "modelo.tflite"
RUTA_CLASES  = RUTA_ML / "modelos" / "clases.json"

TAMANO = 224
CONFIANZA_MINIMA = 0.60  # Por debajo de esto, devolvemos "no_reconocido"

_interpreter = None
_clases      = None


def _cargar():
    global _interpreter, _clases
    if _interpreter is not None:
        return

    try:
        import ai_edge_litert.interpreter as litert
        _interpreter = litert.Interpreter(model_path=str(RUTA_MODELO))
    except ImportError:
        try:
            import tensorflow as tf
            _interpreter = tf.lite.Interpreter(model_path=str(RUTA_MODELO))
        except ImportError:
            try:
                import tflite_runtime.interpreter as tflite
                _interpreter = tflite.Interpreter(model_path=str(RUTA_MODELO))
            except ImportError:
                raise RuntimeError(
                    "Se necesita ai-edge-litert, tensorflow o tflite-runtime. "
                    "Ejecuta: pip install ai-edge-litert"
                )

    _interpreter.allocate_tensors()

    with open(RUTA_CLASES, encoding="utf-8") as f:
        _clases = json.load(f)


def _preprocesar(imagen_bgr):
    """Resize a 224×224 y normaliza a [-1, 1] (MobileNetV2 preprocess_input)."""
    rgb  = cv2.cvtColor(imagen_bgr, cv2.COLOR_BGR2RGB)
    redim = cv2.resize(rgb, (TAMANO, TAMANO), interpolation=cv2.INTER_AREA)
    arr  = redim.astype(np.float32)
    arr  = (arr / 127.5) - 1.0
    return arr[np.newaxis, ...]


def _parsear_clase(nombre_clase, clases_ml):
    """Convierte 'tomate_fresco' en su id_alimento y estado."""
    # Mapa slug → (id_alimento, nombre_visible) — debe coincidir con ml/clases.py
    RECONOCIDOS = {
        "banano":   (1,  "Banano"),
        "manzana":  (2,  "Manzana"),
        "naranja":  (3,  "Naranja"),
        "tomate":   (14, "Tomate"),
        "pepino":   (15, "Pepino"),
        "pimenton": (16, "Pimentón"),
        "papa":     (26, "Papa"),
    }
    if nombre_clase == "no_reconocido":
        return None
    for estado in ("fresco", "danado"):
        if nombre_clase.endswith(f"_{estado}"):
            slug = nombre_clase[: -(len(estado) + 1)]
            if slug in RECONOCIDOS:
                id_alim, nombre = RECONOCIDOS[slug]
                return {"id_alimento": id_alim, "nombre": nombre, "estado": estado}
    return None


def clasificar(imagen_bgr):
    """Clasifica una imagen BGR de OpenCV y devuelve el resultado.

    Retorna un dict con:
        clase          — nombre de la clase predicha
        id_alimento    — id en el catálogo del backend (None si no reconocido)
        nombre         — nombre legible del alimento (None si no reconocido)
        estado         — "fresco" | "danado" (None si no reconocido)
        confianza      — probabilidad 0-1
        no_reconocido  — True si el modelo no identificó el alimento
    """
    _cargar()

    entrada = _interpreter.get_input_details()
    salida  = _interpreter.get_output_details()

    _interpreter.set_tensor(entrada[0]["index"], _preprocesar(imagen_bgr))
    _interpreter.invoke()

    probs     = _interpreter.get_tensor(salida[0]["index"])[0]
    idx       = int(np.argmax(probs))
    confianza = float(probs[idx])
    clase     = _clases[idx]

    if clase == "no_reconocido" or confianza < CONFIANZA_MINIMA:
        return {
            "clase": clase,
            "id_alimento": None,
            "nombre": None,
            "estado": None,
            "confianza": round(confianza, 4),
            "no_reconocido": True,
        }

    info = _parsear_clase(clase, _clases)
    if info is None:
        return {
            "clase": clase,
            "id_alimento": None,
            "nombre": None,
            "estado": None,
            "confianza": round(confianza, 4),
            "no_reconocido": True,
        }

    return {
        "clase": clase,
        "id_alimento": info["id_alimento"],
        "nombre": info["nombre"],
        "estado": info["estado"],
        "confianza": round(confianza, 4),
        "no_reconocido": False,
    }
