# Datasets — visión artificial (HU-07)

Pipeline para preparar el conjunto de imágenes que entrena el modelo de HU-08.

## Alimentos que el modelo reconoce (7)

Solo se entrenan las frutas y verduras que tienen dataset público con pares fresco/dañado utilizables. El resto de los 30 items del catálogo de FreshTrack quedan **únicamente por registro manual (HU-05)**.

| # | Alimento  | id_alimento | Slug       |
|---|-----------|-------------|------------|
| 1 | Banano    | 1           | banano     |
| 2 | Manzana   | 2           | manzana    |
| 3 | Naranja   | 3           | naranja    |
| 4 | Tomate    | 14          | tomate     |
| 5 | Pepino    | 15          | pepino     |
| 6 | Pimentón  | 16          | pimenton   |
| 7 | Papa      | 26          | papa       |

**Total: 7 alimentos × 2 estados (fresco/danado) + `no_reconocido` = 15 clases.**

Fuente de verdad: `ml/clases.py`.

Los otros 23 alimentos del catálogo (aguacate, mango, fresa, uva, limón, mandarina, pera, papaya, piña, maracuyá, zanahoria, cebolla cabezona, cebolla larga, lechuga, espinaca, brócoli, habichuela, repollo, plátano, yuca, arracacha, remolacha, cilantro) siguen disponibles por HU-05 (registro manual). El vencimiento se calcula con `_VIDA_UTIL` del catálogo (`backend/app/catalogo.py`).

## Dataset fuente

**[Densu341/Fresh-rotten-fruit](https://huggingface.co/datasets/Densu341/Fresh-rotten-fruit)** — ZIP de ~3 GB con 22 carpetas por clase (freshapples, rottenbanana, ...). Licencia openrail.

Se bajan como archivo crudo con `hf_hub_download` porque la librería `datasets` tiene un bug al inferir las labels de este dataset. `unificar.py` lee el ZIP directo con `zipfile`.

**Clase `no_reconocido`:** se llena automáticamente con 500 imágenes de Tiny ImageNet (200 clases: perros, camiones, iglesias, guitarras, etc.) filtrando cualquier cosa que sea comida. Corre `python ml/scripts/no_reconocido.py` antes de `preparar.py`.

## Estructura de carpetas

```
ml/datasets/
├── raw/                       <- descarga del ZIP (gitignored, se regenera)
├── unified/<clase>/*.jpg      <- imagenes mapeadas a nuestras 15 clases (gitignored)
└── splits/
    ├── train/  <- 70% + aumento de datos
    ├── val/    <- 15% sin aumento
    └── test/   <- 15% sin aumento
```

## Cómo regenerar todo

```bash
# 1. Instalar dependencias
pip install -r ml/requirements.txt

# 2. Descargar el ZIP a raw/
python ml/scripts/descargar.py

# 3. Unificar en nuestras 15 clases (revisar log si hay etiquetas sin mapear)
python ml/scripts/unificar.py

# 4. Llenar la clase no_reconocido con imagenes de Tiny ImageNet (auto)
python ml/scripts/no_reconocido.py

# 5. Generar splits train/val/test con aumento en train
python ml/scripts/preparar.py
```

Cada script imprime al final un conteo por clase.

## Conteos actuales (última corrida)

| Clase | Total unificado | Train | Train + aug | Val | Test |
|---|---:|---:|---:|---:|---:|
| manzana_danado | 2,943 | 2,060 | 6,180 | 441 | 442 |
| banano_danado | 2,754 | 1,927 | 5,781 | 413 | 414 |
| manzana_fresco | 2,088 | 1,461 | 4,383 | 313 | 314 |
| naranja_danado | 1,998 | 1,398 | 4,194 | 299 | 301 |
| banano_fresco | 1,962 | 1,373 | 4,119 | 294 | 295 |
| naranja_fresco | 1,854 | 1,297 | 3,891 | 278 | 279 |
| tomate_fresco | 1,803 | 1,262 | 3,786 | 270 | 271 |
| tomate_danado | 1,793 | 1,255 | 3,765 | 268 | 270 |
| pimenton_fresco | 990 | 693 | 2,079 | 148 | 149 |
| pimenton_danado | 901 | 630 | 1,890 | 135 | 136 |
| papa_danado | 802 | 561 | 1,683 | 120 | 121 |
| papa_fresco | 536 | 375 | 1,125 | 80 | 81 |
| pepino_danado | 421 | 294 | 882 | 63 | 64 |
| pepino_fresco | 283 | 198 | 594 | 42 | 43 |
| no_reconocido | 500 | 350 | 1,050 | 75 | 75 |
| **TOTAL** | **21,628** | **15,134** | **45,402** | **3,239** | **3,255** |

Desbalance: manzana_danado (2,943) vs pepino_fresco (283) → **10:1**. En HU-08, usar `class_weight` o oversampling.

## Notas técnicas

- **Tamaño:** todas las imágenes salen a **224×224** (estándar para MobileNetV2).
- **Semilla:** 42 (reproducible).
- **Aumento en train:** cada imagen genera 2 variantes con rotación aleatoria (±20°), flip horizontal 50%, zoom hasta 80%, brillo entre 70% y 130%.
- **Dedup:** los nombres de archivo en `unified/` son el MD5 del contenido → si la misma imagen viene por dos rutas queda una sola vez.
- **Etiquetas ignoradas del dataset fuente:** `okra` y `bittergourd` (quimbombó y melón amargo, fuera del catálogo).
