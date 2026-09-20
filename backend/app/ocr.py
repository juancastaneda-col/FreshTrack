"""
Ejecución del OCR con Tesseract.

Se prueban las variantes de la imagen generadas en el preprocesamiento
y se escoge la que dio mayor confianza promedio. Es una estrategia
sencilla que mejora bastante el resultado frente a usar una sola
configuración fija.
"""

import os
import shutil

import pytesseract
from pytesseract import Output

from .preprocesamiento import preparar_variantes

import pytesseract
pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR"
# --psm 6 = "asumir un bloque uniforme de texto".
# Es el modo que mejor funciona con facturas, porque son una columna
# de líneas. El modo automático tiende a confundirse con los logos.
CONFIG_TESSERACT = "--oem 3 --psm 6"
IDIOMA = "spa"


def _configurar_tesseract():
    """Encuentra Tesseract aunque su carpeta no este en el PATH de Windows."""
    configurado = os.getenv("TESSERACT_CMD")
    candidatos = [
        configurado,
        shutil.which("tesseract"),
        r"C:\Program Files\Tesseract-OCR\tesseract.exe",
        r"C:\Program Files (x86)\Tesseract-OCR\tesseract.exe",
    ]
    for candidato in candidatos:
        if candidato and os.path.isfile(candidato):
            pytesseract.pytesseract.tesseract_cmd = candidato
            return candidato
    return None


_configurar_tesseract()


def _confianza_promedio(datos):
    """Promedia la confianza que Tesseract asigna a cada palabra."""
    valores = [
        int(c) for c in datos["conf"]
        if str(c).lstrip("-").isdigit() and int(c) >= 0
    ]
    if not valores:
        return 0.0
    return sum(valores) / len(valores) / 100.0


def _texto_de_datos(datos):
    """Reconstruye el texto agrupando las palabras por línea.

    Tesseract devuelve palabra por palabra con sus coordenadas. Las
    agrupamos por (bloque, párrafo, línea) para recuperar la estructura
    de renglones de la factura, que es lo que necesita el parser.
    """
    lineas = {}
    for i, palabra in enumerate(datos["text"]):
        if not palabra.strip():
            continue
        clave = (datos["block_num"][i], datos["par_num"][i], datos["line_num"][i])
        lineas.setdefault(clave, []).append(palabra)

    return "\n".join(" ".join(palabras) for _, palabras in sorted(lineas.items()))


def extraer_texto(imagen_bgr):
    """Corre el OCR sobre la imagen y devuelve el mejor resultado.

    Retorna un diccionario con el texto extraído, la confianza global
    y cuál variante de preprocesamiento resultó ganadora.
    """
    variantes = preparar_variantes(imagen_bgr)

    mejor = {"texto": "", "confianza": 0.0, "variante": None}

    for nombre, imagen in variantes.items():
        datos = pytesseract.image_to_data(
            imagen,
            lang=IDIOMA,
            config=CONFIG_TESSERACT,
            output_type=Output.DICT,
        )
        confianza = _confianza_promedio(datos)
        if confianza > mejor["confianza"]:
            mejor = {
                "texto": _texto_de_datos(datos),
                "confianza": round(confianza, 3),
                "variante": nombre,
            }

    return mejor
