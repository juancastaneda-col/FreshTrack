"""
Llena ml/datasets/unified/no_reconocido/ con imagenes que NO son frutas
ni verduras, bajadas de Tiny ImageNet.

Tiny ImageNet tiene 200 clases (perros, camiones, iglesias, guitarras,
etc.). Filtramos las pocas clases que son comida/frutas/verduras para
que el modelo no se confunda.

Uso:
    python ml/scripts/no_reconocido.py
    python ml/scripts/no_reconocido.py --n 300
"""

import argparse
import hashlib
import io
import sys
from pathlib import Path

from datasets import load_dataset


RAIZ_ML = Path(__file__).resolve().parents[1]
DESTINO = RAIZ_ML / "datasets" / "unified" / "no_reconocido"


# Synsets de Tiny ImageNet que son comida o frutas/verduras.
# Se saltan para no ensenarle al modelo que un banano es 'no_reconocido'.
SYNSETS_COMIDA = {
    "n07579787",  # plate
    "n07583066",  # guacamole
    "n07614500",  # ice cream
    "n07615774",  # ice lolly
    "n07684084",  # loaf of bread
    "n07695742",  # pretzel
    "n07711569",  # mashed potato
    "n07715103",  # cauliflower
    "n07720875",  # bell pepper
    "n07734744",  # mushroom
    "n07742313",  # Granny Smith apple
    "n07747607",  # orange
    "n07749582",  # lemon
    "n07753592",  # banana
    "n07768694",  # pomegranate
    "n07871810",  # meatloaf
    "n07873807",  # pizza
    "n07875152",  # potpie
    "n07920052",  # espresso
}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--n", type=int, default=500,
                        help="Numero de imagenes a copiar (default 500).")
    parser.add_argument("--semilla", type=int, default=42,
                        help="Semilla para el shuffle streaming (default 42).")
    args = parser.parse_args()

    DESTINO.mkdir(parents=True, exist_ok=True)

    print(f"Descargando/streaming Tiny ImageNet (200 clases)...")
    ds = load_dataset("zh-plus/tiny-imagenet", streaming=True)
    conjunto = ds["train"].shuffle(seed=args.semilla, buffer_size=10_000)
    labels = ds["train"].features["label"].names

    copiadas = 0
    saltadas_comida = 0
    duplicadas = 0

    for fila in conjunto:
        if copiadas >= args.n:
            break
        etiqueta = labels[fila["label"]]
        if etiqueta in SYNSETS_COMIDA:
            saltadas_comida += 1
            continue
        try:
            img = fila["image"].convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=90)
            datos = buf.getvalue()
            nombre = hashlib.md5(datos).hexdigest() + ".jpg"
            destino = DESTINO / nombre
            if destino.exists():
                duplicadas += 1
                continue
            destino.write_bytes(datos)
            copiadas += 1
        except Exception as exc:
            print(f"  error: {exc}", file=sys.stderr)

    print(f"\nlisto: {copiadas} imagenes en {DESTINO}")
    print(f"  saltadas por ser comida: {saltadas_comida}")
    print(f"  duplicadas: {duplicadas}")
    print("\nsiguiente paso: python ml/scripts/preparar.py")


if __name__ == "__main__":
    main()
