"""
Prepara los splits train/val/test a partir de ml/datasets/unified/.

Pasos:
  1. Lee cada clase en unified/ y baraja las imagenes (semilla fija).
  2. Divide 70% train, 15% val, 15% test.
  3. Redimensiona a 224x224 (recorte central conservando aspecto).
  4. Solo en TRAIN, genera 2 variantes aumentadas por imagen (rotacion, flip, brillo, zoom).

Val y test NO se aumentan: sirven para medir el modelo con imagenes limpias.
El resultado queda en ml/datasets/splits/{train,val,test}/<clase>/.

Uso:
    python ml/scripts/preparar.py
    python ml/scripts/preparar.py --sin-aumento
"""

import argparse
import random
import sys
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from PIL import Image, ImageEnhance, ImageOps  # noqa: E402

from clases import nombres_clase  # noqa: E402


RAIZ_ML = Path(__file__).resolve().parents[1]
RAIZ_UNIFIED = RAIZ_ML / "datasets" / "unified"
RAIZ_SPLITS = RAIZ_ML / "datasets" / "splits"

TAMANO = 224
PROP_TRAIN, PROP_VAL = 0.70, 0.15
SEMILLA = 42
AUMENTOS_POR_IMAGEN = 2


def redimensionar_cuadrado(img):
    img = ImageOps.exif_transpose(img).convert("RGB")
    ancho, alto = img.size
    lado = min(ancho, alto)
    izq = (ancho - lado) // 2
    arr = (alto - lado) // 2
    img = img.crop((izq, arr, izq + lado, arr + lado))
    return img.resize((TAMANO, TAMANO), Image.LANCZOS)


def variantes_aumentadas(img, rng, n):
    salidas = []
    for _ in range(n):
        v = img
        if rng.random() < 0.5:
            v = ImageOps.mirror(v)
        v = v.rotate(rng.uniform(-20, 20), resample=Image.BILINEAR,
                     fillcolor=(255, 255, 255))
        zoom = rng.uniform(0.8, 1.0)
        lado = int(TAMANO * zoom)
        off = (TAMANO - lado) // 2
        v = v.crop((off, off, off + lado, off + lado)).resize(
            (TAMANO, TAMANO), Image.BILINEAR
        )
        v = ImageEnhance.Brightness(v).enhance(rng.uniform(0.7, 1.3))
        salidas.append(v)
    return salidas


def dividir(imagenes, rng):
    rutas = list(imagenes)
    rng.shuffle(rutas)
    n = len(rutas)
    t = int(n * PROP_TRAIN)
    v = t + int(n * PROP_VAL)
    return rutas[:t], rutas[t:v], rutas[v:]


def procesar_clase(clase, aumentar):
    origen = RAIZ_UNIFIED / clase
    if not origen.exists() or not any(origen.iterdir()):
        print(f"  [{clase}] sin imagenes, se omite")
        return {"train": 0, "val": 0, "test": 0, "train_aumentado": 0}

    imagenes = sorted(origen.glob("*.jpg"))
    rng = random.Random(SEMILLA + hash(clase) % 1000)
    train, val, test = dividir(imagenes, rng)
    conteo = Counter()

    for split, rutas in (("train", train), ("val", val), ("test", test)):
        destino = RAIZ_SPLITS / split / clase
        destino.mkdir(parents=True, exist_ok=True)
        for ruta in rutas:
            try:
                img = redimensionar_cuadrado(Image.open(ruta))
            except Exception as exc:
                print(f"    error {ruta.name}: {exc}", file=sys.stderr)
                continue
            img.save(destino / ruta.name, "JPEG", quality=90)
            conteo[split] += 1
            if split == "train" and aumentar:
                for i, v in enumerate(variantes_aumentadas(img, rng, AUMENTOS_POR_IMAGEN)):
                    v.save(destino / f"{ruta.stem}_aug{i}.jpg", "JPEG", quality=90)
                    conteo["train_aumentado"] += 1

    print(
        f"  [{clase}] train={conteo['train']} (+{conteo['train_aumentado']} aug) "
        f"val={conteo['val']} test={conteo['test']}"
    )
    return conteo


def main():
    parser = argparse.ArgumentParser(description="Genera splits train/val/test.")
    parser.add_argument("--sin-aumento", action="store_true",
                        help="No genera variantes aumentadas en train.")
    args = parser.parse_args()

    if not RAIZ_UNIFIED.exists():
        sys.exit(f"No existe {RAIZ_UNIFIED}. Corre antes: python ml/scripts/unificar.py")

    aumentar = not args.sin_aumento
    print(f"Semilla: {SEMILLA}  |  proporciones: 70/15/15  |  tamano: {TAMANO}x{TAMANO}")
    print(f"Aumento en train: {'si' if aumentar else 'no'}\n")

    total = Counter()
    for clase in nombres_clase():
        c = procesar_clase(clase, aumentar)
        for k, v in c.items():
            total[k] += v

    print(f"\nTOTAL: train={total['train']} (+{total['train_aumentado']} aug) "
          f"val={total['val']} test={total['test']}")


if __name__ == "__main__":
    main()
