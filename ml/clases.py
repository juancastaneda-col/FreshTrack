"""
Catálogo de clases del modelo de visión de FreshTrack.

Un solo modelo que identifica alimento + estado en una sola prediccion.
De los 30 items del catalogo general (backend/app/catalogo.py), solo
7 tienen dataset publico con pares fresco/danado utilizables. Los otros
23 se manejan por registro manual (HU-05).

Clases: 7 alimentos x 2 estados + 'no_reconocido' = 15 clases.

Los id_alimento coinciden con los del catalogo del backend para poder
mapear la prediccion del modelo a un item de la base de datos.
"""


# (id_alimento, nombre_visible, slug_para_carpetas)
_RECONOCIDOS = [
    (1,  "Banano",   "banano"),
    (2,  "Manzana",  "manzana"),
    (3,  "Naranja",  "naranja"),
    (14, "Tomate",   "tomate"),
    (15, "Pepino",   "pepino"),
    (16, "Pimentón", "pimenton"),
    (26, "Papa",     "papa"),
]

ESTADOS = ("fresco", "danado")

CLASE_NO_RECONOCIDO = "no_reconocido"


def nombres_clase():
    """Lista ordenada de las 15 clases: 7 alimentos x 2 estados + no_reconocido."""
    clases = []
    for _, _, slug in _RECONOCIDOS:
        for estado in ESTADOS:
            clases.append(f"{slug}_{estado}")
    clases.append(CLASE_NO_RECONOCIDO)
    return clases


def alimentos_reconocidos():
    """Devuelve la lista de (id_alimento, nombre, slug). Usable desde el backend."""
    return list(_RECONOCIDOS)


def parsear_clase(nombre_clase):
    """Descompone 'banano_fresco' en (id_alimento=1, nombre='Banano', estado='fresco').

    Devuelve None si la clase es 'no_reconocido' o no esta en el catalogo.
    """
    if nombre_clase == CLASE_NO_RECONOCIDO:
        return None
    for estado in ESTADOS:
        sufijo = f"_{estado}"
        if nombre_clase.endswith(sufijo):
            slug = nombre_clase[: -len(sufijo)]
            for id_alimento, nombre, s in _RECONOCIDOS:
                if s == slug:
                    return {"id_alimento": id_alimento, "nombre": nombre, "estado": estado}
    return None


if __name__ == "__main__":
    clases = nombres_clase()
    print(f"Total: {len(clases)} clases")
    for c in clases:
        print(f"  - {c}")
