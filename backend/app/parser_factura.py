"""
Extracción de las líneas de producto a partir del texto crudo del OCR.

El texto que devuelve Tesseract trae de todo: el nombre del almacén, el
NIT, la resolución de la DIAN, los totales, los impuestos, el mensaje de
despedida. Lo que nos interesa son solo las líneas de producto.

La estrategia es:
  1. Para facturas del Éxito (y similares con formato PLU/KGM), detectar
     la sección de productos y parsear solo esa zona.
  2. Para cualquier otra factura, descartar por reglas lo que NO es producto
     y validar lo que queda.
"""

import re
import unicodedata


# ---------------------------------------------------------------------
# Palabras que delatan que una línea NO es un producto
# ---------------------------------------------------------------------
PALABRAS_IGNORAR = {
    # Totales e impuestos
    "total", "subtotal", "sub total", "iva", "impoconsumo", "impuesto",
    "base gravable", "exento", "excluido", "descuento", "ahorro", "ahorra",
    # Medios de pago
    "efectivo", "cambio", "tarjeta", "credito", "debito", "aprobacion",
    "franquicia", "voucher", "propina", "bono", "puntos", "contado",
    "forma", "pago",
    # Datos del establecimiento
    "nit", "tel", "telefono", "direccion", "sucursal", "almacen",
    "supermercado", "s.a.", "sas", "ltda", "regimen", "contribuyente",
    "retenedor",
    # Datos de la factura
    "factura", "resolucion", "dian", "autorizacion", "prefijo",
    "consecutivo", "fecha", "hora", "caja", "cajero", "vendedor",
    "cliente", "documento", "cufe", "pos", "terminal", "transaccion",
    "identificacion", "identif", "expedicion", "rango",
    # Impuestos y tarifas
    "discriminacion", "tarifa", "tarifas",
    # Encabezados de columna (incluye formato Éxito)
    "descripcion", "cant", "cantidad", "vr unit", "valor", "precio",
    "articulo", "producto", "codigo", "plu", "detalle", "detalles",
    # Mensajes
    "gracias", "vuelva", "bienvenido", "atendido", "peticiones",
    "quejas", "reclamos", "www", "http", "com", "co", "pqrs",
    "servicio al cliente",
}

# Una línea con muchos de estos caracteres suele ser un separador o ruido
CARACTERES_RUIDO = set("=*-_~#|")


# 3.900 son tres mil novecientos pesos; 1,250 es un kilo y cuarto.
PATRON_PRECIO = re.compile(r"\b\d{1,3}(?:[.\s]\d{3})+\b|\b\d{4,}\b")
PATRON_NUMERO = re.compile(r"\d+(?:[.,]\d+)*")
PATRON_UNIDAD = re.compile(
    r"\b(kgm|kg|kgs|kilo|kilos|gr|gramos|lb|lbs|libra|libras|"
    r"und|uds|unidad|unidades|manojo)\b",
    re.IGNORECASE,
)

# Líneas de peso en facturas del Éxito: "1 0.775/KGM × 4.680 V.Ahorro 0"
# El OCR puede leer "." como "-" o "," y "KGM" como "KGH", "KGA", etc.
# No ponemos \b al final porque el OCR a veces pega un guión/underscore: "KGM_x".
PATRON_KGM = re.compile(r"(\d+[-.,]\d+)\s*/\s*KG", re.IGNORECASE)

# "V.Ahorro" / "V.Ahorra" identifica líneas de peso del Éxito incluso cuando
# el OCR arruinó la parte "/KGM" (p.ej. la lee como "S x" por una arruga).
# Usamos solo el stem "Ahorr" porque "Ahorra?" no matchea "Ahorro" (termina en o).
PATRON_AHORRO = re.compile(r"\bAhorr", re.IGNORECASE)

# Fin de sección de productos en facturas del Éxito
PATRON_FIN_SECCION = re.compile(r"\bTotal\s+Item\b", re.IGNORECASE)

# Una cantidad mayor a esto casi seguro no es una cantidad, sino un
# código o un precio que el OCR partió mal
CANTIDAD_MAXIMA_RAZONABLE = 100

# Normalización de unidades al código que usa la base de datos
MAPA_UNIDADES = {
    "kg": "KG", "kgs": "KG", "kilo": "KG", "kilos": "KG", "kgm": "KG",
    "g": "G", "gr": "G", "gramos": "G",
    "lb": "LB", "lbs": "LB", "libra": "LB", "libras": "LB",
    "und": "UND", "un": "UND", "uds": "UND",
    "unidad": "UND", "unidades": "UND",
    "manojo": "MANOJO",
}


def normalizar(texto):
    """Pasa a minúsculas y quita tildes."""
    texto = texto.lower().strip()
    texto = unicodedata.normalize("NFD", texto)
    texto = "".join(c for c in texto if unicodedata.category(c) != "Mn")
    return re.sub(r"\s+", " ", texto)


def _tiene_palabra_sustancial(texto_norm):
    """True si hay al menos una palabra de 4+ letras (descarta líneas de puro ruido)."""
    return bool(re.search(r'\b[a-zn]{4,}\b', texto_norm))


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

    # Líneas sin ninguna palabra de 4+ letras: "q N DB", "An Ms", "i / + A hs"
    if not _tiene_palabra_sustancial(norm):
        return True

    # La puntuación se cambia por espacios para que "CAJERO:" o
    # "www.exito.com" se separen en palabras y sí coincidan con la lista
    palabras = re.sub(r"[^a-z0-9n ]+", " ", norm)
    palabras = re.sub(r"\s+", " ", palabras).strip()

    for palabra in PALABRAS_IGNORAR:
        clave = re.sub(r"[^a-z0-9n ]+", " ", palabra).strip()
        if f" {clave} " in f" {palabras} ":
            return True

    return False


def _a_numero(texto):
    if re.fullmatch(r"\d{1,3}(?:\.\d{3})+", texto):   # 4.375 / 12.500
        return float(texto.replace(".", ""))
    return float(texto.replace(",", "."))             # 1,250 / 0,5


def extraer_cantidad(linea):
    """Busca la cantidad y la unidad dentro de la línea."""
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
    texto = re.sub(r"\b\d{6,}\b", " ", texto)           # códigos de barras
    texto = re.sub(r'[$*#|=_%"<>§]+', " ", texto)       # símbolos y ruido OCR
    texto = re.sub(r"\s+\d+([,.]\d+)?\s*$", " ", texto) # número final suelto
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


def _es_linea_peso_exito(linea):
    """Detecta líneas de peso del Éxito: contiene /KG o 'V.Ahorro'.

    El OCR puede arruinar '/KGM' por completo en zonas arrugadas, pero
    'V.Ahorro' casi siempre se lee bien y es exclusivo de estas líneas.
    """
    return bool(PATRON_KGM.search(linea)) or bool(PATRON_AHORRO.search(linea))


def _extraer_peso_exito(linea):
    """Devuelve (cantidad_kg, 'KG') de una línea de peso Éxito.

    Estrategia 1 — patrón /KG: funciona cuando el OCR leyó bien esa parte.
    Estrategia 2 — decimal antes de ×: el OCR a veces lee '×' como 'x' o '>'.
    Fallback — (1.0, 'KG'): al menos la unidad queda correcta para que el
    usuario solo tenga que corregir el número, no también la unidad.
    """
    # Estrategia 1: número antes de /KG
    m = PATRON_KGM.search(linea)
    if m:
        try:
            return float(m.group(1).replace(",", ".").replace("-", ".")), "KG"
        except ValueError:
            pass

    # Estrategia 2: buscar decimal antes del símbolo de multiplicación
    m_mult = re.search(r"[×xX>]", linea)
    if m_mult:
        antes = linea[:m_mult.start()]
        for num in reversed(re.findall(r"\d+[-.,]\d+", antes)):
            try:
                peso = float(num.replace(",", ".").replace("-", "."))
                if 0.05 <= peso <= 30.0:
                    return peso, "KG"
            except ValueError:
                pass

    return 1.0, "KG"


def _rango_seccion_kgm(lineas):
    """Para facturas con formato KGM (Éxito), devuelve (inicio, fin) de la sección.

    Busca la primera línea de peso (con /KG o V.Ahorro) y arranca 2 líneas
    antes para no perder el primer producto. Termina en 'Total Item'.
    Si no hay líneas de peso, devuelve (0, len) para parsear todo.
    """
    primera_peso = None
    fin = len(lineas)

    for i, linea in enumerate(lineas):
        if primera_peso is None and _es_linea_peso_exito(linea):
            primera_peso = i
        if PATRON_FIN_SECCION.search(linea):
            fin = i + 1
            break

    if primera_peso is None:
        return 0, fin

    return max(0, primera_peso - 2), fin


def parsear_factura(texto_ocr):
    """Recorre el texto completo y devuelve la lista de productos candidatos.

    Para facturas del Éxito detecta la sección PLU/KGM y parsea solo esa
    zona, eliminando el encabezado, los datos del cliente y el pie de página.

    Dentro de la sección entiende el formato de dos líneas del Éxito:
      línea 1 — peso: "1 0.775/KGM × 4.680 V.Ahorro 0"
      línea 2 — nombre: "1297    Cebolla Blanca G    3.627"
    La cantidad y unidad de la línea 1 se transfieren al producto de la línea 2.
    """
    candidatos = []
    numero = 0
    cantidad_kgm_pendiente = None
    unidad_kgm_pendiente = None

    lineas = [l for l in texto_ocr.splitlines() if l.strip()]
    inicio, fin = _rango_seccion_kgm(lineas)

    for linea in lineas[inicio:fin]:
        numero += 1

        if _es_linea_peso_exito(linea):
            cantidad_kgm_pendiente, unidad_kgm_pendiente = _extraer_peso_exito(linea)
            continue

        item = parsear_linea(linea, numero)
        if item:
            if cantidad_kgm_pendiente is not None:
                item["cantidad"] = cantidad_kgm_pendiente
                item["unidad"] = unidad_kgm_pendiente
                cantidad_kgm_pendiente = None
                unidad_kgm_pendiente = None
            candidatos.append(item)

    return candidatos
