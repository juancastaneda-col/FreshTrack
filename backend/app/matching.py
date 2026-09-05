"""
Asociación de cada línea detectada con un alimento del catálogo.

La factura dice "TOMATE CHONTO KG" y el catálogo tiene "Tomate". Este
módulo hace ese puente usando la tabla alias_alimento que se cargó en
HU-01, más una comparación por similitud para los casos que el OCR
leyó con errores ("platanoo", "zanahona").

En producción la similitud la calcula PostgreSQL con pg_trgm. Aquí se
incluye además una implementación en Python para poder probar el
pipeline sin base de datos conectada.
"""

from difflib import SequenceMatcher

from .parser_factura import normalizar


# Umbral minimo de parecido para aceptar una sugerencia automatica.
UMBRAL_SUGERENCIA = 0.70

# Si supera este valor consideramos la coincidencia confiable y la
# marcamos previamente como confirmada en la interfaz.
UMBRAL_ALTA_CONFIANZA = 0.85


def similitud(a, b):
    """Parecido entre dos textos, de 0 a 1."""
    return SequenceMatcher(None, a, b).ratio()


def _mejor_por_contencion(texto, alias_norm):
    """Da puntaje alto si el alias aparece completo dentro del texto.

    "tomate chonto kg" contiene "tomate chonto" y también "tomate".
    Preferimos el alias más largo que esté contenido, porque es el más
    específico.
    """
    if alias_norm in texto:
        # Cuanto más largo el alias respecto al texto, más confiable
        return 0.80 + 0.20 * (len(alias_norm) / max(len(texto), 1))
    return 0.0


def buscar_alimento(descripcion_normalizada, catalogo_alias):
    """Encuentra el alimento más probable para una descripción.

    catalogo_alias es una lista de diccionarios con las llaves
    id_alimento, nombre y texto_normalizado.

    Devuelve (id_alimento, nombre, confianza) o (None, None, 0.0).
    """
    if not descripcion_normalizada:
        return None, None, 0.0

    mejor_id = None
    mejor_nombre = None
    mejor_puntaje = 0.0

    for alias in catalogo_alias:
        alias_norm = alias["texto_normalizado"]

        puntaje = max(
            _mejor_por_contencion(descripcion_normalizada, alias_norm),
            similitud(descripcion_normalizada, alias_norm),
        )

        if puntaje > mejor_puntaje:
            mejor_puntaje = puntaje
            mejor_id = alias["id_alimento"]
            mejor_nombre = alias["nombre"]

    if mejor_puntaje < UMBRAL_SUGERENCIA:
        return None, None, round(mejor_puntaje, 3)

    return mejor_id, mejor_nombre, round(min(mejor_puntaje, 1.0), 3)


def asociar_catalogo(candidatos, catalogo_alias):
    """Agrega la sugerencia de alimento a cada línea detectada."""
    resultado = []

    for item in candidatos:
        id_alimento, nombre, confianza = buscar_alimento(
            item["descripcion_normalizada"], catalogo_alias
        )

        item = dict(item)
        item["id_alimento_sugerido"] = id_alimento
        item["nombre_sugerido"] = nombre
        item["confianza"] = confianza
        item["confirmado"] = confianza >= UMBRAL_ALTA_CONFIANZA
        resultado.append(item)

    return resultado


# ---------------------------------------------------------------------
# Consulta equivalente en PostgreSQL, para cuando el backend esté conectado
# ---------------------------------------------------------------------
SQL_BUSCAR_ALIAS = """
SELECT a.id_alimento,
       a.nombre,
       similarity(al.texto_normalizado, %(texto)s) AS confianza
FROM   alias_alimento al
JOIN   alimento a ON a.id_alimento = al.id_alimento
WHERE  similarity(al.texto_normalizado, %(texto)s) > %(umbral)s
ORDER  BY confianza DESC
LIMIT  1;
"""
