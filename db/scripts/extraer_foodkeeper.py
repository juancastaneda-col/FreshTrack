"""
Extrae de la base de datos oficial de USDA FoodKeeper los días de vida útil
de los 30 alimentos del catálogo de FreshTrack y genera el SQL para
actualizar la tabla vida_util.

Fuente: FSIS - FoodKeeper Data (data.gov, licencia CC0 dominio público)

Criterio: se toma el valor MÍNIMO del rango que da FoodKeeper. Si dicen
que la manzana dura de 4 a 6 semanas en nevera, usamos 4. Es coherente
con la regla conservadora que ya definimos para el proyecto: es mejor
avisarle al usuario un poco antes que un poco después.
"""

import csv

ARCHIVO = "/tmp/ing.csv"


MAPEO = {
    "Banano":           ("Bananas", ""),
    "Manzana":          ("Apples", ""),
    "Naranja":          ("Citrus fruit", "lemon, lime, orange"),
    "Mandarina":        ("Citrus fruit", "lemon, lime, orange"),
    "Papaya":           ("Papaya, mango, feijoa, passionfruit, casaha melon", ""),
    "Piña":             ("Pineapple", ""),
    "Mango":            ("Papaya, mango, feijoa, passionfruit, casaha melon", ""),
    "Fresa":            ("Strawberries", ""),
    "Uva":              ("Grapes", ""),
    "Pera":             ("Peaches, nectarines, plums, pears, sapote", ""),
    "Aguacate":         ("Avocados", ""),
    "Maracuyá":         ("Papaya, mango, feijoa, passionfruit, casaha melon", ""),
    "Limón":            ("Citrus fruit", "lemon, lime, orange"),
    "Tomate":           ("Tomatoes", ""),
    "Pepino":           ("Cucumbers", ""),
    "Pimentón":         ("Peppers", ""),
    "Zanahoria":        ("Carrots, parsnips", ""),
    "Cebolla cabezona": ("Onions", "yellow, white, red, etc."),
    "Cebolla larga":    ("Onions", "spring or green"),
    "Lechuga":          ("Lettuce", "iceberg, romaine"),
    "Espinaca":         ("Lettuce", "leaf, spinach"),
    "Brócoli":          ("Broccoli and broccoli raab (rapini)", ""),
    "Habichuela":       ("Beans and peas", "green, fava, lima"),
    "Repollo":          ("Cabbage", ""),
    "Plátano":          ("Plantains", ""),
    "Papa":             ("Potatoes", ""),
    "Yuca":             ("Yuca/cassava", ""),
    "Remolacha":        ("Beets", ""),
    "Cilantro":         ("Cilantro", ""),
   
}

FACTOR_DIAS = {"days": 1, "weeks": 7, "months": 30, "years": 365}


def a_dias(valor, metrica):
    """Convierte '4' + 'Weeks' a 28 días."""
    if not valor or not metrica:
        return None
    factor = FACTOR_DIAS.get(metrica.strip().lower())
    if not factor:
        return None
    try:
        return int(round(float(valor) * factor))
    except ValueError:
        return None


def dias_de(fila, prefijo):
    """Lee los días de una condición, probando primero DOP y luego la normal.

    FoodKeeper usa dos juegos de columnas: las 'DOP' son desde la fecha de
    compra, que es justo nuestro caso. Las otras aplican desde que el
    producto madura o se abre.
    """
    for col_min, col_metric in [
        (f"DOP_{prefijo}_Min", f"DOP_{prefijo}_Metric"),
        (f"{prefijo}_Min", f"{prefijo}_Metric"),
    ]:
        dias = a_dias(fila.get(col_min), fila.get(col_metric))
        if dias:
            return dias
    return None


def main():
    filas = list(csv.DictReader(open(ARCHIVO, encoding="utf-8-sig")))

    def buscar(nombre, subtitulo):
        for f in filas:
            if f["Name"].strip() != nombre:
                continue
            sub = (f["Name_subtitle"] or "").strip()
            if subtitulo == "" or sub.startswith(subtitulo):
                return f
        return None

    print("=" * 78)
    print(f"{'ALIMENTO':20}{'AMBIENTE':>10}{'NEVERA':>10}   ORIGEN")
    print("=" * 78)

    actualizaciones = []
    sin_datos = []

    for alimento, clave in MAPEO.items():
        fila = buscar(*clave)
        if not fila:
            sin_datos.append((alimento, f"no se encontró '{clave[0]}'"))
            continue

        ambiente = dias_de(fila, "Pantry")
        nevera = dias_de(fila, "Refrigerate")

        # El tomate no trae columnas numericas: FoodKeeper lo indica en la
        # nota de texto ("Until Ripe, then 7 days").
        if alimento == "Tomate":
            ambiente = ambiente or 7

        origen = fila["Name"][:34]
        print(f"{alimento:20}{str(ambiente or '-'):>10}{str(nevera or '-'):>10}   {origen}")

        if ambiente:
            actualizaciones.append((alimento, 1, ambiente, fila["Name"]))
        if nevera:
            actualizaciones.append((alimento, 2, nevera, fila["Name"]))
        if not ambiente and not nevera:
            sin_datos.append((alimento, "sin días utilizables en el dataset"))

    print("=" * 78)
    print(f"Actualizaciones a generar: {len(actualizaciones)}")
    if sin_datos:
        print("\nSin dato de FoodKeeper (se conserva la estimación):")
        for a, motivo in sin_datos:
            print(f"  - {a}: {motivo}")

    # ---- Generar el SQL ----
    with open("/home/claude/actualizar_vida_util_foodkeeper.sql", "w", encoding="utf-8") as sql:
        sql.write("""-- ============================================================
-- FreshTrack — Actualización de vida útil con datos oficiales
-- Fuente: USDA FSIS FoodKeeper (data.gov, licencia CC0)
--
-- Criterio: se toma el valor MÍNIMO del rango publicado. Si FoodKeeper
-- dice que la manzana dura de 4 a 6 semanas refrigerada, se usan 4.
-- Es mejor avisarle al usuario un poco antes que un poco después.
--
-- Condición 1 = Ambiente (columnas Pantry de FoodKeeper)
-- Condición 2 = Refrigerado (columnas Refrigerate de FoodKeeper)
-- ============================================================

BEGIN;

""")
        for alimento, cond, dias, origen in actualizaciones:
            nombre_sql = alimento.replace("'", "''")
            origen_sql = origen.replace("'", "''")[:100]
            sql.write(
                f"UPDATE vida_util SET dias_estimados = {dias},\n"
                f"       fuente = 'USDA FoodKeeper — {origen_sql}'\n"
                f" WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = '{nombre_sql}')\n"
                f"   AND id_condicion = {cond};\n\n"
            )

        sql.write("""-- Arracacha no aparece en FoodKeeper (tubérculo andino que no se
-- consume en Estados Unidos). Se deja el valor estimado y se marca
-- la fuente para que quede documentado en el informe.
UPDATE vida_util SET fuente = 'Estimación propia — no disponible en FoodKeeper'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Arracacha');

COMMIT;

-- ---- Verificación ----
-- SELECT a.nombre,
--        MAX(CASE WHEN v.id_condicion = 1 THEN v.dias_estimados END) AS ambiente,
--        MAX(CASE WHEN v.id_condicion = 2 THEN v.dias_estimados END) AS nevera,
--        MIN(v.fuente) AS fuente
-- FROM   vida_util v
-- JOIN   alimento a ON a.id_alimento = v.id_alimento
-- GROUP  BY a.nombre
-- ORDER  BY a.nombre;
""")

    print("\nSQL generado en actualizar_vida_util_foodkeeper.sql")


if __name__ == "__main__":
    main()
