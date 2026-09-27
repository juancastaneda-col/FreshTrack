"""Prepara todos los artefactos necesarios para identificar alimentos.

Uso desde la raiz del proyecto:
    python ml/scripts/preparar_modelo.py

La ejecucion puede tardar porque descarga varios GB y entrena MobileNetV2.
Si el modelo ya existe, no vuelve a entrenar salvo que se use --forzar.
"""

import argparse
import subprocess
import sys
from pathlib import Path


RAIZ_PROYECTO = Path(__file__).resolve().parents[2]
RAIZ_MODELOS = RAIZ_PROYECTO / "ml" / "modelos"


def ejecutar(nombre, *argumentos):
    script = RAIZ_PROYECTO / "ml" / "scripts" / f"{nombre}.py"
    print(f"\n== {nombre} ==", flush=True)
    subprocess.run(
        [sys.executable, str(script), *argumentos],
        cwd=RAIZ_PROYECTO,
        check=True,
    )


def main():
    parser = argparse.ArgumentParser(description="Genera el modelo TFLite de FreshTrack.")
    parser.add_argument(
        "--forzar",
        action="store_true",
        help="Vuelve a ejecutar todo el pipeline aunque ya exista modelo.tflite.",
    )
    args = parser.parse_args()

    if (RAIZ_MODELOS / "modelo.tflite").exists() and not args.forzar:
        print("El modelo ya existe. Usa --forzar para regenerarlo.")
        return

    ejecutar("descargar")
    ejecutar("unificar")
    ejecutar("no_reconocido")
    ejecutar("preparar")
    ejecutar("entrenar")
    ejecutar("evaluar")
    ejecutar("exportar")
    print("\nModelo listo. Ya puedes iniciar backend y frontend.")


if __name__ == "__main__":
    main()