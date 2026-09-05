"""
Sirve para probar el pipeline sin tener que levantar la base de datos.
Cuando el backend esté conectado, esta lista se reemplaza por la
consulta SQL_BUSCAR_ALIAS del módulo matching.
"""


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
