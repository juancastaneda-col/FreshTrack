"""Inferencia del modelo TFLite de alimentos y estado."""

import json
import os
from pathlib import Path

import cv2
import numpy as np


TAMANO_MODELO = 224
CONFIANZA_MINIMA = 0.65
VERSION_MODELO = "hu09-v1"
ESTADOS_VISIBLES = {
    "fresco": "fresco",
    "danado": "dañado",
    "verde": "verde",
    "maduro": "maduro",
    "damaged": "dañado",
    "fresh": "fresco",
}

_INTERPRETER = None
_CLASES = None


def _cargar_interprete():
    global _INTERPRETER, _CLASES
    if _INTERPRETER is not None:
        return _INTERPRETER, _CLASES

    raiz_proyecto = Path(__file__).resolve().parents[2]
    ruta_modelo = Path(os.getenv("FRESHTRACK_MODELO", str(raiz_proyecto / "ml/modelos/modelo.tflite")))
    ruta_clases = Path(os.getenv("FRESHTRACK_CLASES", str(raiz_proyecto / "ml/modelos/clases.json")))
    if not ruta_modelo.exists():
        raise FileNotFoundError(
            f"No existe el modelo de cámara en {ruta_modelo}. "
            "Prepara el entorno con: python ml/scripts/preparar_modelo.py"
        )
    try:
        from tflite_runtime.interpreter import Interpreter
    except ImportError:
        try:
            from tensorflow.lite.python.interpreter import Interpreter
        except ImportError as error:
            raise RuntimeError("Instala tflite-runtime o tensorflow para usar la cámara") from error

    _INTERPRETER = Interpreter(model_path=str(ruta_modelo))
    _INTERPRETER.allocate_tensors()
    if not ruta_clases.exists():
        raise FileNotFoundError(f"No existe el mapa de clases en {ruta_clases}")
    _CLASES = json.loads(ruta_clases.read_text(encoding="utf-8"))
    return _INTERPRETER, _CLASES


def _preparar_imagen(contenido):
    imagen = cv2.imdecode(np.frombuffer(contenido, np.uint8), cv2.IMREAD_COLOR)
    if imagen is None:
        raise ValueError("La imagen no se pudo leer o está dañada")
    imagen = cv2.cvtColor(imagen, cv2.COLOR_BGR2RGB)
    imagen = cv2.resize(imagen, (TAMANO_MODELO, TAMANO_MODELO)).astype(np.float32)
    return (imagen / 127.5) - 1.0


def identificar(contenido):
    """Devuelve la mejor predicción y si supera el umbral de aceptación."""
    interprete, clases = _cargar_interprete()
    entrada = interprete.get_input_details()[0]
    salida = interprete.get_output_details()[0]
    datos = _preparar_imagen(contenido)[None, ...]
    if entrada["dtype"] == np.uint8:
        escala, cero = entrada["quantization"]
        datos = np.clip(datos / escala + cero, 0, 255).astype(np.uint8)
    elif entrada["dtype"] != np.float32:
        datos = datos.astype(entrada["dtype"])
    interprete.set_tensor(entrada["index"], datos)
    interprete.invoke()
    probabilidades = interprete.get_tensor(salida["index"])[0].astype(np.float32)
    if salida["dtype"] in (np.int8, np.uint8):
        escala, cero = salida["quantization"]
        probabilidades = (probabilidades - cero) * escala
    # El modelo entrenado termina en softmax y TFLite ya devuelve
    # probabilidades. Solo aplica softmax si otro modelo entrega logits.
    suma = float(np.sum(probabilidades))
    es_probabilidad = (
        np.all(probabilidades >= 0)
        and np.all(probabilidades <= 1)
        and np.isclose(suma, 1.0, atol=1e-3)
    )
    if not es_probabilidad:
        probabilidades = np.exp(probabilidades - np.max(probabilidades))
        probabilidades /= np.sum(probabilidades)
    indice = int(np.argmax(probabilidades))
    clase = clases[indice]
    confianza = round(float(probabilidades[indice]), 3)
    partes = clase.rsplit("_", 1)
    alimento = partes[0].replace("_", " ").title() if len(partes) == 2 else None
    estado = ESTADOS_VISIBLES.get(partes[-1]) if len(partes) == 2 else None
    reconocido = clase != "no_reconocido" and alimento is not None and estado is not None
    aceptado = reconocido and confianza >= CONFIANZA_MINIMA
    return {
        "clase": clase,
        "nombre": alimento if reconocido else None,
        "estado": estado if reconocido else None,
        "confianza": confianza,
        "reconocido": reconocido,
        "aceptado": aceptado,
        "repetir": reconocido and confianza < CONFIANZA_MINIMA,
    }