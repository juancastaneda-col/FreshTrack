"""
Sirve para probar el pipeline sin tener que levantar la base de datos.
Cuando el backend esté conectado, esta lista se reemplaza por la
consulta SQL_BUSCAR_ALIAS del módulo matching.
"""

from datetime import timedelta


_DATOS = [
    (1,  "Banano",           ["banano criollo", "banano uraba", "banano"]),
    (2,  "Manzana",          ["manzana roja", "manzana verde", "manzana"]),
    (3,  "Naranja",          ["naranja valencia", "naranja"]),
    (4,  "Mandarina",        ["mandarina"]),
    (5,  "Papaya",           ["papaya maradol", "papaya"]),
    (6,  "Piña",             ["pina gold", "pina", "piña"]),
    (7,  "Mango",            ["mango tommy", "mango"]),
    (8,  "Fresa",            ["fresa"]),
    (9,  "Uva",              ["uva isabella", "uva"]),
    (10, "Pera",             ["pera"]),
    (11, "Aguacate",         ["aguacate hass", "aguacate"]),
    (12, "Maracuyá",         ["maracuya"]),
    (13, "Limón",            ["limon tahiti", "limon mandarino", "limon"]),
    (14, "Tomate",           ["tomate chonto", "tomate larga vida", "tomate"]),
    (15, "Pepino",           ["pepino cohombro", "pepino"]),
    (16, "Pimentón",         ["pimenton rojo", "pimenton"]),
    (17, "Zanahoria",        ["zanahoria"]),
    (18, "Cebolla cabezona", ["cebolla cabezona", "cebolla blanca"]),
    (19, "Cebolla larga",    ["cebolla larga", "cebolla junca"]),
    (20, "Lechuga",          ["lechuga batavia", "lechuga crespa", "lechuga"]),
    (21, "Espinaca",         ["espinaca"]),
    (22, "Brócoli",          ["brocoli"]),
    (23, "Habichuela",       ["habichuela"]),
    (24, "Repollo",          ["repollo"]),
    (25, "Plátano",          ["platano verde", "platano maduro", "platano"]),
    (26, "Papa",             ["papa pastusa", "papa criolla", "papa"]),
    (27, "Yuca",             ["yuca"]),
    (28, "Arracacha",        ["arracacha"]),
    (29, "Remolacha",        ["remolacha"]),
    (30, "Cilantro",         ["cilantro"]),
]


def cargar_alias():
    """Aplana el catálogo a la estructura que espera el módulo matching."""
    alias = []
    for id_alimento, nombre, textos in _DATOS:
        for texto in textos:
            alias.append({
                "id_alimento": id_alimento,
                "nombre": nombre,
                "texto_normalizado": texto,
            })
    return alias


CATALOGO_ALIAS = cargar_alias()


# Días de vida útil por par (alimento, condición). Fuente: db/01_esquema_y_catalogo.sql
# (referencia USDA FoodKeeper). "fuera" = ambiente, "nevera" = refrigerado.
_VIDA_UTIL = {
    "Banano":           {"fuera":  5, "nevera":  9},
    "Manzana":          {"fuera":  7, "nevera": 30},
    "Naranja":          {"fuera":  7, "nevera": 21},
    "Mandarina":        {"fuera":  7, "nevera": 14},
    "Papaya":           {"fuera":  4, "nevera":  7},
    "Piña":             {"fuera":  3, "nevera":  5},
    "Mango":            {"fuera":  5, "nevera":  7},
    "Fresa":            {"fuera":  2, "nevera":  5},
    "Uva":              {"fuera":  3, "nevera":  7},
    "Pera":             {"fuera":  5, "nevera": 14},
    "Aguacate":         {"fuera":  4, "nevera":  7},
    "Maracuyá":         {"fuera":  7, "nevera": 21},
    "Limón":            {"fuera": 10, "nevera": 30},
    "Tomate":           {"fuera":  5, "nevera": 10},
    "Pepino":           {"fuera":  4, "nevera":  7},
    "Pimentón":         {"fuera":  5, "nevera": 14},
    "Zanahoria":        {"fuera": 14, "nevera": 30},
    "Cebolla cabezona": {"fuera": 30, "nevera": 60},
    "Cebolla larga":    {"fuera":  7, "nevera": 14},
    "Lechuga":          {"fuera":  2, "nevera":  7},
    "Espinaca":         {"fuera":  2, "nevera":  5},
    "Brócoli":          {"fuera":  3, "nevera":  7},
    "Habichuela":       {"fuera":  3, "nevera":  7},
    "Repollo":          {"fuera":  7, "nevera": 30},
    "Plátano":          {"fuera":  7, "nevera": 10},
    "Papa":             {"fuera": 21, "nevera": 60},
    "Yuca":             {"fuera":  4, "nevera": 10},
    "Arracacha":        {"fuera":  7, "nevera": 14},
    "Remolacha":        {"fuera":  7, "nevera": 21},
    "Cilantro":         {"fuera":  2, "nevera":  7},
}


def _resumen(id_alimento, nombre):
    vida = _VIDA_UTIL.get(nombre, {})
    return {
        "id_alimento": id_alimento,
        "nombre": nombre,
        "dias_fuera": vida.get("fuera"),
        "dias_nevera": vida.get("nevera"),
    }


def buscar(consulta):
    """Devuelve alimentos que coinciden por nombre o alias con la consulta."""
    q = (consulta or "").strip().lower()
    if len(q) < 2:
        return []
    resultados = []
    vistos = set()
    for id_alimento, nombre, textos in _DATOS:
        if id_alimento in vistos:
            continue
        if q in nombre.lower() or any(q in t for t in textos):
            resultados.append(_resumen(id_alimento, nombre))
            vistos.add(id_alimento)
    return resultados


def obtener(id_alimento):
    """Devuelve el alimento por su id, o None si no está en el catálogo."""
    for aid, nombre, _ in _DATOS:
        if aid == id_alimento:
            return _resumen(aid, nombre)
    return None


def calcular_vencimiento(id_alimento, condicion, fecha_registro):
    """Suma los días de vida útil a la fecha de registro. None si no hay datos."""
    info = obtener(id_alimento)
    if info is None:
        return None
    dias = info["dias_nevera"] if condicion == "nevera" else info["dias_fuera"]
    if dias is None:
        return None
    return fecha_registro + timedelta(days=dias)
