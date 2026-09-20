"""
Unifica el dataset descargado en carpetas por clase canonica de FreshTrack.

Lee el ZIP de Densu341 desde el cache y copia cada imagen a
ml/datasets/unified/<clase>/<hash>.jpg, donde la clase es una de las
14 combinaciones alimento_estado (banano_fresco, banano_danado, ...).

La clase 'no_reconocido' se llena a mano despues, con fotos que no
son ninguna fruta ni verdura.

Uso:
    python ml/scripts/unificar.py
    python ml/scripts/unificar.py --limite 50   # smoke test
"""

import argparse
import hashlib
import io
import sys
import zipfile
from collections import Counter
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from huggingface_hub import hf_hub_download  # noqa: E402
from PIL import Image  # noqa: E402

from clases import nombres_clase  # noqa: E402


RAIZ_ML = Path(__file__).resolve().parents[1]
RAIZ_RAW = RAIZ_ML / "datasets" / "raw"
RAIZ_UNIFIED = RAIZ_ML / "datasets" / "unified"


# Cuerpo del label del dataset (sin 'fresh'/'rotten') -> slug de FreshTrack.
# Los typos del dataset original (patato, tamto) se mapean tambien.
DENSU341_A_SLUG = {
    "apples":   "manzana",
    "banana":   "banano",
    "capsicum": "pimenton",
    "cucumber": "pepino",
    "oranges":  "naranja",
    "potato":   "papa",
    "patato":   "papa",   # typo en el dataset
    "tomato":   "tomate",
    "tamto":    "tomate", # typo en el dataset
}


def parsear_etiqueta(etiqueta):
    """'freshbanana' -> ('banano_fresco'). None si no aplica."""
    e = etiqueta.lower()
    if e.startswith("fresh"):
        estado, cuerpo = "fresco", e[5:]
    elif e.startswith("rotten"):
        estado, cuerpo = "danado", e[6:]
    else:
        return None
    slug = DENSU341_A_SLUG.get(cuerpo)
    if slug is None:
        return None
    return f"{slug}_{estado}"


def guardar(imagen_pil, carpeta):
    """Guarda como JPEG en carpeta, con nombre = MD5 (dedup natural)."""
    carpeta.mkdir(parents=True, exist_ok=True)
    buf = io.BytesIO()
    imagen_pil.convert("RGB").save(buf, format="JPEG", quality=90)
    datos = buf.getvalue()
    destino = carpeta / (hashlib.md5(datos).hexdigest() + ".jpg")
    if destino.exists():
        return False
    destino.write_bytes(datos)
    return True


def main():
    parser = argparse.ArgumentParser(description="Unifica el dataset en ml/datasets/unified/")
    parser.add_argument("--limite", type=int, default=None,
                        help="Procesa como maximo N imagenes (util para pruebas).")
    args = parser.parse_args()

    RAIZ_UNIFIED.mkdir(parents=True, exist_ok=True)

    zip_path = hf_hub_download(
        repo_id="Densu341/Fresh-rotten-fruit",
        filename="freshness_fruit.zip",
        repo_type="dataset",
        cache_dir=str(RAIZ_RAW),
    )
    print(f"zip: {zip_path}\n")

    stats = Counter()
    ignoradas = Counter()

    with zipfile.ZipFile(zip_path) as zf:
        for entry in zf.namelist():
            if args.limite is not None and stats["procesadas"] >= args.limite:
                break
            if entry.endswith("/"):
                continue

            partes = entry.split("/")
            if len(partes) < 2:
                continue
            etiqueta = partes[-2]

            clase = parsear_etiqueta(etiqueta)
            if clase is None:
                ignoradas[etiqueta] += 1
                stats["ignoradas"] += 1
                continue

            try:
                with zf.open(entry) as f:
                    img = Image.open(io.BytesIO(f.read()))
                if guardar(img, RAIZ_UNIFIED / clase):
                    stats["copiadas"] += 1
                else:
                    stats["duplicadas"] += 1
            except Exception as exc:
                stats["errores"] += 1
                print(f"  error en {entry}: {exc}", file=sys.stderr)
            stats["procesadas"] += 1

    print(f"procesadas: {stats['procesadas']}")
    for k in ("copiadas", "duplicadas", "ignoradas", "errores"):
        if stats[k]:
            print(f"  {k}: {stats[k]}")
    if ignoradas:
        print("\netiquetas fuera del catalogo (ignoradas):")
        for etiq, n in ignoradas.most_common():
            print(f"  - {etiq}: {n}")

    print("\n== resumen por clase ==")
    esperadas = set(nombres_clase())
    esperadas.discard("no_reconocido")  # se llena a mano
    encontradas = set()
    for carpeta in sorted(RAIZ_UNIFIED.iterdir()):
        if not carpeta.is_dir():
            continue
        n = sum(1 for _ in carpeta.glob("*.jpg"))
        marca = "" if carpeta.name in esperadas else "  (?)"
        print(f"  {carpeta.name}: {n}{marca}")
        encontradas.add(carpeta.name)
    faltantes = esperadas - encontradas
    if faltantes:
        print(f"\nclases SIN imagenes: {sorted(faltantes)}")

    print("\n(recordatorio: llenar unified/no_reconocido/ a mano)")


if __name__ == "__main__":
    main()
