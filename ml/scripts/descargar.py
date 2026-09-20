"""
Descarga el dataset fuente desde Hugging Face a ml/datasets/raw/.

Fuente unica: Densu341/Fresh-rotten-fruit. Es un ZIP con carpetas por
clase (freshapples/, rottenbanana/, ...). Se baja como archivo crudo
porque la libreria datasets tiene un bug al inferir las labels.

unificar.py lee el ZIP directamente con zipfile.

Uso:
    python ml/scripts/descargar.py
"""

import sys
from pathlib import Path

from huggingface_hub import hf_hub_download


RAIZ_RAW = Path(__file__).resolve().parents[1] / "datasets" / "raw"


def main():
    RAIZ_RAW.mkdir(parents=True, exist_ok=True)
    print("[densu341] Densu341/Fresh-rotten-fruit (ZIP, ~3 GB, 22 carpetas)")
    try:
        ruta = hf_hub_download(
            repo_id="Densu341/Fresh-rotten-fruit",
            filename="freshness_fruit.zip",
            repo_type="dataset",
            cache_dir=str(RAIZ_RAW),
        )
        print(f"[densu341] listo en {ruta}")
    except Exception as exc:
        print(f"[densu341] ERROR: {exc}", file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
