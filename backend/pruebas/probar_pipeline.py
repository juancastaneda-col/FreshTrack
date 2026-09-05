"""
Prueba el pipeline completo (preprocesamiento -> OCR -> parser -> matching)
sobre las facturas de prueba y mide qué tan bien funciona.

Para cada factura se sabe de antemano qué alimentos del catálogo
deberían detectarse, así que se puede calcular cuántos encontró bien,
cuántos se le escaparon y cuántos inventó.
"""

import os
import sys
import time

import cv2

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.catalogo import CATALOGO_ALIAS
from app.matching import asociar_catalogo
from app.ocr import extraer_texto
from app.parser_factura import parsear_factura

CARPETA = os.path.join(os.path.dirname(__file__), "facturas")

# Alimentos del catálogo que SÍ deberían salir en cada factura.
# Los productos que no son fruta ni verdura (leche, arroz) no cuentan:
# el catálogo no los tiene y está bien que no se identifiquen.
ESPERADOS = {
    "01_exito_limpia.png": {
        "Tomate", "Banano", "Aguacate", "Lechuga",
        "Zanahoria", "Cebolla larga", "Papa",
    },
    "02_exito_torcida.png": {
        "Tomate", "Banano", "Aguacate", "Lechuga",
        "Zanahoria", "Cebolla larga", "Papa",
    },
    "03_d1_gastada.png": {
        "Manzana", "Naranja", "Pimentón", "Cilantro", "Pepino",
    },
    "04_carulla_sombra.png": {
        "Fresa", "Brócoli", "Espinaca", "Limón",
        "Papaya", "Habichuela", "Mango",
    },
    "05_carulla_peor_caso.png": {
        "Fresa", "Brócoli", "Espinaca", "Limón",
        "Papaya", "Habichuela", "Mango",
    },
}


def procesar(ruta):
    imagen = cv2.imread(ruta)
    inicio = time.time()
    ocr = extraer_texto(imagen)
    candidatos = parsear_factura(ocr["texto"])
    productos = asociar_catalogo(candidatos, CATALOGO_ALIAS)
    return ocr, productos, round(time.time() - inicio, 2)


def main():
    print("=" * 72)
    print("PRUEBA DEL PIPELINE DE OCR — HU-03")
    print("=" * 72)

    total_esperados = 0
    total_encontrados = 0
    total_falsos = 0

    for archivo in sorted(os.listdir(CARPETA)):
        if not archivo.endswith(".png"):
            continue

        ruta = os.path.join(CARPETA, archivo)
        ocr, productos, segundos = procesar(ruta)

        esperados = ESPERADOS.get(archivo, set())
        detectados = {p["nombre_sugerido"] for p in productos if p["nombre_sugerido"]}

        encontrados = esperados & detectados
        faltantes = esperados - detectados
        falsos = detectados - esperados

        total_esperados += len(esperados)
        total_encontrados += len(encontrados)
        total_falsos += len(falsos)

        print(f"\n{archivo}")
        print(f"  confianza OCR : {ocr['confianza']:.0%}  ({ocr['variante']})")
        print(f"  tiempo        : {segundos}s")
        print(f"  líneas candidatas: {len(productos)}")
        print(f"  identificados : {len(encontrados)}/{len(esperados)}  "
              f"-> {', '.join(sorted(encontrados)) or 'ninguno'}")
        if faltantes:
            print(f"  NO detectados : {', '.join(sorted(faltantes))}")
        if falsos:
            print(f"  falsos positivos: {', '.join(sorted(falsos))}")

        sin_identificar = [p for p in productos if not p["nombre_sugerido"]]
        if sin_identificar:
            muestras = [p["descripcion"][:28] for p in sin_identificar[:4]]
            print(f"  sin identificar ({len(sin_identificar)}): {' | '.join(muestras)}")

    print("\n" + "=" * 72)
    print("RESUMEN")
    print("=" * 72)
    cobertura = total_encontrados / total_esperados if total_esperados else 0
    print(f"  Productos esperados en total : {total_esperados}")
    print(f"  Identificados correctamente  : {total_encontrados}  ({cobertura:.0%})")
    print(f"  Falsos positivos             : {total_falsos}")


if __name__ == "__main__":
    main()
