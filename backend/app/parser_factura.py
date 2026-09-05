"""
Extracción de las líneas de producto a partir del texto crudo del OCR.

El texto que devuelve Tesseract trae de todo: el nombre del almacén, el
NIT, la resolución de la DIAN, los totales, los impuestos, el mensaje de
despedida. Lo que nos interesa son solo las líneas de producto.

La estrategia es descartar por reglas (lo que sabemos que NO es un
producto) y luego validar lo que queda. Es más confiable que intentar
adivinar directamente cuál es un producto, porque los nombres de los
productos varían muchísimo entre almacenes pero los encabezados y
totales son bastante predecibles.
"""

import re
import unicodedata


# ---------------------------------------------------------------------
# Palabras que delatan que una línea NO es un producto
# ---------------------------------------------------------------------
PALABRAS_IGNORAR = {
    # Totales e impuestos
    "total", "subtotal", "sub total", "iva", "impoconsumo", "impuesto",
    "base gravable", "exento", "excluido", "descuento", "ahorro",
    # Medios de pago
    "efectivo", "cambio", "tarjeta", "credito", "debito", "aprobacion",
    "franquicia", "voucher", "propina", "bono", "puntos",
    # Datos del establecimiento
    "nit", "tel", "telefono", "direccion", "sucursal", "almacen",
    "supermercado", "s.a.", "sas", "ltda", "regimen", "contribuyente",
    # Datos de la factura
    "factura", "resolucion", "dian", "autorizacion", "prefijo",
    "consecutivo", "fecha", "hora", "caja", "cajero", "vendedor",
    "cliente", "documento", "cufe", "pos", "terminal", "transaccion",
    # Mensajes
    "gracias", "vuelva", "bienvenido", "atendido", "peticiones",
    "quejas", "reclamos", "www", "http", "com", "co", "pqrs",
    "servicio al cliente",
    # Encabezados de columna
    "descripcion", "cant", "cantidad", "vr unit", "valor", "precio",
    "articulo", "producto", "codigo",
}

# Una línea con muchos de estos caracteres suele ser un separador o ruido
CARACTERES_RUIDO = set("=*-_~#|")


# 3.900 son tres mil novecientos pesos; 1,250 es un kilo y cuarto.
PATRON_PRECIO = re.compile(r"\b\d{1,3}(?:[.\s]\d{3})+\b|\b\d{4,}\b")
PATRON_NUMERO = re.compile(r"\d+(?:[.,]\d+)*")
PATRON_UNIDAD = re.compile(
    r"\b(kg|kgs|kilo|kilos|gr|gramos|lb|lbs|libra|libras|"
    r"und|uds|unidad|unidades|manojo)\b",
    re.IGNORECASE,
)

# Una cantidad mayor a esto casi seguro no es una cantidad, sino un
# código o un precio que el OCR partió mal
CANTIDAD_MAXIMA_RAZONABLE = 100

# Normalización de unidades al código que usa la base de datos
MAPA_UNIDADES = {
    "kg": "KG", "kgs": "KG", "kilo": "KG", "kilos": "KG",
    "g": "G", "gr": "G", "gramos": "G",
    "lb": "LB", "lbs": "LB", "libra": "LB", "libras": "LB",
    "und": "UND", "un": "UND", "uds": "UND",
    "unidad": "UND", "unidades": "UND",
    "manojo": "MANOJO",
}


def normalizar(texto):
    """Pasa a minúsculas y quita tildes.

    Se usa tanto para comparar contra la lista de palabras a ignorar
    como para buscar el producto en el catálogo, porque el OCR con
    frecuencia se come las tildes.
    """
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto)


def es_ignorable(linea):
    """Decide si una línea debe descartarse por no ser un producto."""
    norm = normalizar(linea)

    if len(norm) < 4:
        return True

    # Líneas hechas casi solo de guiones, asteriscos o barras
    if norm and sum(c in CARACTERES_RUIDO for c in norm) / len(norm) > 0.3:
        return True

    # Líneas sin letras suficientes (solo números o basura del OCR)
    letras = sum(c.isalpha() for c in norm)
    if letras < 3:
        return True

    # La puntuación se cambia por espacios para que "CAJERO:" o
    # "www.exito.com" se separen en palabras y sí coincidan con la lista
    palabras = re.sub(r"[^a-z0-9ñ ]+", " ", norm)
    palabras = re.sub(r"\s+", " ", palabras).strip()

    for palabra in PALABRAS_IGNORAR:
        clave = re.sub(r"[^a-z0-9ñ ]+", " ", palabra).strip()
        # Se compara con espacios alrededor para no cortar palabras válidas:
        # así "un" no descarta "atun" ni "g" descarta "mango"
        if f" {clave} " in f" {palabras} ":
            return True

    return False


def _a_numero(texto):
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", texto):   # 4.375 / 12.500
        return float(texto.replace(".", ""))
    return float(texto.replace(",", "."))             # 1,250 / 0,5


def extraer_cantidad(linea):
    """Busca la cantidad y la unidad dentro de la línea.
    """
    numeros = PATRON_NUMERO.findall(linea)

    cantidad = 1.0
    if len(numeros) >= 2:
        # El último es el precio; el penúltimo, la cantidad
        try:
            valor = _a_numero(numeros[-2])
            if 0 < valor <= CANTIDAD_MAXIMA_RAZONABLE:
                cantidad = valor
        except ValueError:
            pass

    coincidencia = PATRON_UNIDAD.search(linea)
    unidad = MAPA_UNIDADES.get(coincidencia.group(1).lower(), "UND") if coincidencia else "UND"

    # Se limpia el texto para que quede solo el nombre del producto
    limpio = PATRON_UNIDAD.sub(" ", linea)
    limpio = PATRON_NUMERO.sub(" ", limpio)

    return cantidad, unidad, limpio.strip()


def limpiar_descripcion(texto):
    """Quita precios, códigos de barras y símbolos sueltos del nombre."""
    texto = PATRON_PRECIO.sub(" ", texto)
    texto = re.sub(r"\b\d{6,}\b", " ", texto)      # códigos de barras
    texto = re.sub(r"[$*#|=_]+", " ", texto)
    texto = re.sub(r"\s+\d+([,.]\d+)?\s*$", " ", texto)  # número final suelto
    texto = re.sub(r"\s{2,}", " ", texto)
    return texto.strip(" .,-")


def parsear_linea(linea, numero):
    """Convierte una línea de texto en un candidato a producto.

    Devuelve None si la línea no parece un producto.
    """
    if es_ignorable(linea):
        return None

    cantidad, unidad, resto = extraer_cantidad(linea)
    descripcion = limpiar_descripcion(resto)

    # Después de limpiar precios y códigos debe quedar un nombre razonable
    if len(descripcion) < 3 or sum(c.isalpha() for c in descripcion) < 3:
        return None

    return {
        "numero_linea": numero,
        "texto_crudo": linea.strip(),
        "descripcion": descripcion,
        "descripcion_normalizada": normalizar(descripcion),
        "cantidad": cantidad,
        "unidad": unidad,
    }


def parsear_factura(texto_ocr):
    """Recorre el texto completo y devuelve la lista de productos candidatos."""
    candidatos = []
    numero = 0

    for linea in texto_ocr.splitlines():
        if not linea.strip():
            continue
        numero += 1
        item = parsear_linea(linea, numero)
        if item:
            candidatos.append(item)

    return candidatos
