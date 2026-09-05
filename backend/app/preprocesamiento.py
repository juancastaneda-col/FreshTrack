"""
Preprocesamiento de la imagen de la factura antes de pasarla al OCR.se mejora la foto
por si esta torcidam, con sombras o desenfocada, para que el ocr funcione bien debemos entregar
una foto limpia. entonces con esto se enderaza la imagen y despues se pone blanco y negro para que se aprecie
mejor
"""

import cv2
import numpy as np


ANCHO_OBJETIVO = 1600  


def redimensionar(imagen):
    """Lleva la imagen a un ancho fijo conservando la proporción.
    """
    alto, ancho = imagen.shape[:2]
    if ancho == ANCHO_OBJETIVO:
        return imagen
    escala = ANCHO_OBJETIVO / ancho
    nuevo_alto = int(alto * escala)
    #
    interpolacion = cv2.INTER_CUBIC if escala > 1 else cv2.INTER_AREA
    return cv2.resize(imagen, (ANCHO_OBJETIVO, nuevo_alto), interpolation=interpolacion)


def a_grises(imagen):
    """Convierte a escala de grises. El color no aporta nada para leer texto."""
    if len(imagen.shape) == 2:
        return imagen
    return cv2.cvtColor(imagen, cv2.COLOR_BGR2GRAY)


def calcular_inclinacion(gris):
    """Calcula cuántos grados está torcida la imagen.
    Se binariza, se toman los píxeles oscuros (el texto) y se busca el
    rectángulo mínimo que los contiene. El ángulo de ese rectángulo es
    la inclinación de la factura.
    """
    invertida = cv2.bitwise_not(gris)
    _, umbral = cv2.threshold(invertida, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)

    coords = np.column_stack(np.where(umbral > 0))
    if len(coords) < 100: 
        return 0.0

    angulo = cv2.minAreaRect(coords)[-1]
    if angulo < -45:
        angulo = 90 + angulo

    if abs(angulo) > 15:
        return 0.0
    return -angulo


def enderezar(gris):
    """Rota la imagen para dejar el texto horizontal."""
    angulo = calcular_inclinacion(gris)
    if abs(angulo) < 0.5:  # ya está prácticamente derecha
        return gris

    alto, ancho = gris.shape[:2]
    centro = (ancho // 2, alto // 2)
    matriz = cv2.getRotationMatrix2D(centro, angulo, 1.0)
    return cv2.warpAffine(
        gris, matriz, (ancho, alto),
        flags=cv2.INTER_CUBIC,
        borderMode=cv2.BORDER_REPLICATE,
    )


def mejorar_contraste(gris):
    """Aplica CLAHE para emparejar la iluminación.

    Una foto de factura suele tener una parte más iluminada que otra
    (la sombra de la mano, el reflejo de la luz). CLAHE mejora el
    contraste por zonas en vez de aplicar el mismo ajuste a toda la
    imagen, que es justo lo que necesitamos.
    """
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    return clahe.apply(gris)


def quitar_ruido(gris):
    """Suaviza el ruido de la cámara sin desdibujar los bordes del texto."""
    return cv2.bilateralFilter(gris, d=5, sigmaColor=50, sigmaSpace=50)


def binarizar(gris):
    """Deja la imagen en blanco y negro puro.
    Se usa umbral adaptativo (no un valor fijo) porque el papel de la
    factura no está iluminado de forma uniforme.
    """
    return cv2.adaptiveThreshold(
        gris, 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY,
        blockSize=31,   # impar; tamaño de la ventana de análisis
        C=15,           # constante que se resta a la media
    )


def preparar(imagen_bgr, binarizada=True):
    """Ejecuta el pipeline completo de preprocesamiento.
    Recibe la imagen como la lee OpenCV (BGR) y devuelve la imagen
    lista para el OCR.
    """
    img = redimensionar(imagen_bgr)
    img = a_grises(img)
    img = enderezar(img)
    img = quitar_ruido(img)
    img = mejorar_contraste(img)
    if binarizada:
        img = binarizar(img)
    return img


def preparar_variantes(imagen_bgr):
    """Devuelve varias versiones de la imagen para probar cuál lee mejor.

    En la práctica ninguna configuración funciona para todas las
    facturas: la binarización ayuda con papel térmico gastado pero a
    veces borra texto claro. Generamos las dos y dejamos que el OCR
    decida cuál dio mejor resultado.
    """
    return {
        "binarizada": preparar(imagen_bgr, binarizada=True),
        "escala_grises": preparar(imagen_bgr, binarizada=False),
    }
