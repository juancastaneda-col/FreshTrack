"""
Genera facturas sintéticas que imitan formatos reales colombianos.

Sirven para probar el pipeline sin depender de tener facturas físicas
a la mano. Cada una simula una condición distinta: papel limpio, foto
torcida, papel térmico gastado, poca luz.
"""

import os
import random

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont

CARPETA = os.path.join(os.path.dirname(__file__), "facturas")

FUENTE_MONO = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf"
FUENTE_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSansMono-Bold.ttf"


FACTURAS = {
    "exito": {
        "encabezado": [
            "ALMACENES EXITO S.A.",
            "NIT 890.900.608-9",
            "CC ROBLEDO - MEDELLIN",
            "TEL 604 3399999",
            "FACTURA POS No. 4471-882301",
            "FECHA 28/08/2026  HORA 18:42",
            "CAJA 07   CAJERO MARTINEZ L.",
            "--------------------------------",
            "DESCRIPCION        CANT    VALOR",
            "--------------------------------",
        ],
        "productos": [
            "TOMATE CHONTO KG    1,250    4.375",
            "BANANO URABA        6 UND    3.600",
            "AGUACATE HASS       2 UND    7.980",
            "LECHUGA BATAVIA     1 UND    2.900",
            "ZANAHORIA KG        0,800    2.240",
            "CEBOLLA JUNCA       1 MANOJO 1.800",
            "PAPA PASTUSA KG     2,000    5.800",
            "LECHE ENTERA 1L     2 UND    8.400",
        ],
        "pie": [
            "--------------------------------",
            "SUBTOTAL                  37.095",
            "IVA 19%                    1.596",
            "TOTAL                     38.691",
            "EFECTIVO                  40.000",
            "CAMBIO                     1.309",
            "--------------------------------",
            "GRACIAS POR SU COMPRA",
            "www.exito.com",
        ],
    },
    "d1": {
        "encabezado": [
            "TIENDAS D1 S.A.S",
            "NIT 900.512.936-1",
            "LAURELES MEDELLIN",
            "RESOLUCION DIAN 18764003219",
            "FACTURA 00219-45512",
            "FECHA 29/08/2026",
            "================================",
        ],
        "productos": [
            "MANZANA ROJA UND       3   4.500",
            "NARANJA VALENCIA KG  1,5   3.750",
            "PIMENTON ROJO UND      2   2.400",
            "CILANTRO MANOJO        1     900",
            "PEPINO COHOMBRO UND    2   1.800",
            "ARROZ DIANA 500G       1   2.650",
        ],
        "pie": [
            "================================",
            "TOTAL A PAGAR         16.000",
            "TARJETA DEBITO        16.000",
            "APROBACION 445120",
            "GRACIAS POR PREFERIRNOS",
        ],
    },
    "carulla": {
        "encabezado": [
            "CARULLA VIVERO S.A.",
            "NIT 890.900.608-9",
            "SUCURSAL POBLADO",
            "FACTURA ELECTRONICA POS",
            "PREFIJO CAR CONSECUTIVO 88213",
            "FECHA 30/08/2026 HORA 09:15",
            "CAJERO: RAMIREZ J.",
            "--------------------------------",
        ],
        "productos": [
            "FRESA X 500G           1   6.900",
            "BROCOLI UND            1   3.400",
            "ESPINACA MANOJO        2   3.800",
            "LIMON TAHITI KG      0,5   1.950",
            "PAPAYA MARADOL KG    1,8   5.400",
            "HABICHUELA KG        0,4   2.200",
            "MANGO TOMMY KG       1,2   4.800",
        ],
        "pie": [
            "--------------------------------",
            "SUBTOTAL              28.450",
            "DESCUENTO PUNTOS       1.000",
            "TOTAL                 27.450",
            "TARJETA CREDITO       27.450",
            "PQRS: 018000 510000",
        ],
    },
}


def dibujar(nombre, datos, ancho=520):
    """Dibuja la factura como imagen de texto sobre fondo claro."""
    lineas = datos["encabezado"] + datos["productos"] + datos["pie"]
    alto = 60 + len(lineas) * 26 + 40

    img = Image.new("RGB", (ancho, alto), (252, 251, 248))
    dibujo = ImageDraw.Draw(img)

    fuente = ImageFont.truetype(FUENTE_MONO, 15)
    fuente_titulo = ImageFont.truetype(FUENTE_BOLD, 17)

    y = 30
    for i, linea in enumerate(lineas):
        f = fuente_titulo if i == 0 else fuente
        dibujo.text((24, y), linea, fill=(25, 25, 25), font=f)
        y += 26

    return np.array(img)[:, :, ::-1]  # PIL RGB -> OpenCV BGR


def rotar(imagen, grados):
    alto, ancho = imagen.shape[:2]
    matriz = cv2.getRotationMatrix2D((ancho // 2, alto // 2), grados, 1.0)
    return cv2.warpAffine(imagen, matriz, (ancho, alto),
                          borderValue=(240, 238, 235))


def degradar(imagen, nivel=0.5):
    """Simula papel térmico gastado y foto con ruido."""
    img = imagen.astype(np.float32)
    # Baja el contraste acercando todo al gris
    img = 128 + (img - 128) * (1 - 0.45 * nivel)
    # Ruido de sensor
    img += np.random.normal(0, 9 * nivel, img.shape)
    return np.clip(img, 0, 255).astype(np.uint8)


def sombra(imagen):
    """Simula la sombra de la mano al tomar la foto."""
    alto, ancho = imagen.shape[:2]
    gradiente = np.linspace(1.0, 0.62, ancho).reshape(1, ancho, 1)
    return np.clip(imagen.astype(np.float32) * gradiente, 0, 255).astype(np.uint8)


def main():
    os.makedirs(CARPETA, exist_ok=True)
    random.seed(7)
    np.random.seed(7)

    generadas = []

    # 1. Éxito, condiciones ideales
    img = dibujar("exito", FACTURAS["exito"])
    cv2.imwrite(f"{CARPETA}/01_exito_limpia.png", img)
    generadas.append("01_exito_limpia.png")

    # 2. Éxito, foto torcida
    cv2.imwrite(f"{CARPETA}/02_exito_torcida.png", rotar(img, -6))
    generadas.append("02_exito_torcida.png")

    # 3. D1, papel gastado
    img2 = dibujar("d1", FACTURAS["d1"])
    cv2.imwrite(f"{CARPETA}/03_d1_gastada.png", degradar(img2, 0.7))
    generadas.append("03_d1_gastada.png")

    # 4. Carulla, con sombra
    img3 = dibujar("carulla", FACTURAS["carulla"])
    cv2.imwrite(f"{CARPETA}/04_carulla_sombra.png", sombra(img3))
    generadas.append("04_carulla_sombra.png")

    # 5. Carulla, torcida y degradada (el peor caso)
    peor = degradar(rotar(img3, 4), 0.6)
    cv2.imwrite(f"{CARPETA}/05_carulla_peor_caso.png", peor)
    generadas.append("05_carulla_peor_caso.png")

    print(f"Generadas {len(generadas)} facturas en {CARPETA}")
    for g in generadas:
        print("  -", g)


if __name__ == "__main__":
    main()
