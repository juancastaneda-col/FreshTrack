"""
API de FreshTrack — HU-03 · Escanear factura de mercado.

Expone el endpoint que recibe la foto de la factura, la procesa y
devuelve la lista de productos detectados para que el usuario los
confirme (eso ya es HU-04).
"""

import time

import cv2
import numpy as np
from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.responses import HTMLResponse

from .catalogo import CATALOGO_ALIAS
from .matching import asociar_catalogo
from .ocr import extraer_texto
from .parser_factura import parsear_factura

app = FastAPI(
    title="FreshTrack — OCR de facturas",
    description="HU-03 · Escanear factura de mercado",
    version="1.0.0",
)

TAMANO_MAXIMO = 10 * 1024 * 1024          # 10 MB
FORMATOS_VALIDOS = {"image/jpeg", "image/png", "image/webp"}

# Si el OCR lee con menos confianza que esto, probablemente la foto
# está muy mala y es mejor pedirle al usuario que la repita.
CONFIANZA_MINIMA_ACEPTABLE = 0.40


def _leer_imagen(contenido):
    """Convierte los bytes recibidos en una imagen de OpenCV."""
    arreglo = np.frombuffer(contenido, np.uint8)
    imagen = cv2.imdecode(arreglo, cv2.IMREAD_COLOR)
    if imagen is None:
        raise HTTPException(status_code=400, detail="La imagen no se pudo leer o está dañada")
    return imagen


@app.get("/salud")
def salud():
    """Verifica que el servicio esté arriba."""
    return {"estado": "ok"}


@app.post("/api/v1/facturas/escanear")
async def escanear_factura(archivo: UploadFile = File(...)):
    """Recibe la foto de una factura y devuelve los productos detectados."""
    if archivo.content_type not in FORMATOS_VALIDOS:
        raise HTTPException(
            status_code=400,
            detail=f"Formato no soportado: {archivo.content_type}. Use JPG, PNG o WEBP.",
        )

    contenido = await archivo.read()
    if len(contenido) > TAMANO_MAXIMO:
        raise HTTPException(status_code=413, detail="La imagen supera los 10 MB")
    if not contenido:
        raise HTTPException(status_code=400, detail="El archivo llegó vacío")

    inicio = time.time()

    imagen = _leer_imagen(contenido)
    resultado_ocr = extraer_texto(imagen)
    candidatos = parsear_factura(resultado_ocr["texto"])
    productos = asociar_catalogo(candidatos, CATALOGO_ALIAS)

    duracion = round(time.time() - inicio, 2)

    # Aviso para la app: si la lectura salió mala, conviene repetir la foto
    advertencia = None
    if resultado_ocr["confianza"] < CONFIANZA_MINIMA_ACEPTABLE:
        advertencia = "La foto se leyó con dificultad. Intente de nuevo con mejor luz."
    elif not productos:
        advertencia = "No se detectaron productos en la factura."

    return {
        "confianza_ocr": resultado_ocr["confianza"],
        "variante_usada": resultado_ocr["variante"],
        "segundos": duracion,
        "total_detectados": len(productos),
        "advertencia": advertencia,
        "productos": [
            {
                "numero_linea": p["numero_linea"],
                "texto_crudo": p["texto_crudo"],
                "id_alimento_sugerido": p["id_alimento_sugerido"],
                "nombre_sugerido": p["nombre_sugerido"],
                "cantidad": p["cantidad"],
                "unidad": p["unidad"],
                "confianza": p["confianza"],
                "confirmado": p["confirmado"],
            }
            for p in productos
        ],
    }


@app.get("/", response_class=HTMLResponse)
def pagina_prueba():
    """Página mínima para probar el escaneo desde el celular.

    No es la app final: sirve para que el equipo valide el OCR con
    facturas reales antes de integrarlo al frontend móvil.
    """
    return """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FreshTrack — Probar OCR</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 0; padding: 20px;
           background: #f5f6f8; color: #1a1a1a; }
    h1 { font-size: 20px; }
    .caja { background: #fff; border-radius: 12px; padding: 16px;
            margin-bottom: 14px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
    button { width: 100%; padding: 14px; font-size: 16px; border: 0;
             border-radius: 10px; background: #1a4fd6; color: #fff; }
    button:disabled { background: #9aa5b8; }
    input[type=file] { width: 100%; margin-bottom: 12px; }
    .item { border-bottom: 1px solid #eee; padding: 10px 0; }
    .item:last-child { border-bottom: 0; }
    .nombre { font-weight: 600; }
    .crudo { color: #777; font-size: 12px; }
    .conf { font-size: 12px; }
    .alta { color: #1a7f37; } .baja { color: #b35c00; } .nula { color: #b3261e; }
    .aviso { background: #fff4e5; border-left: 4px solid #e08b00;
             padding: 10px; border-radius: 6px; margin-bottom: 12px; }
  </style>
</head>
<body>
  <h1>Escanear factura</h1>

  <div class="caja">
    <input type="file" id="archivo" accept="image/*" capture="environment">
    <button id="enviar">Procesar factura</button>
  </div>

  <div id="salida"></div>

<script>
const boton = document.getElementById('enviar');
const entrada = document.getElementById('archivo');
const salida = document.getElementById('salida');

boton.onclick = async () => {
  if (!entrada.files.length) { alert('Seleccione una foto primero'); return; }

  boton.disabled = true;
  boton.textContent = 'Procesando...';
  salida.innerHTML = '';

  const datos = new FormData();
  datos.append('archivo', entrada.files[0]);

  try {
    const respuesta = await fetch('/api/v1/facturas/escanear', {
      method: 'POST', body: datos
    });
    const json = await respuesta.json();

    if (!respuesta.ok) {
      salida.innerHTML = '<div class="caja">Error: ' + (json.detail || 'desconocido') + '</div>';
      return;
    }

    let html = '';
    if (json.advertencia) {
      html += '<div class="aviso">' + json.advertencia + '</div>';
    }
    html += '<div class="caja">' +
            '<b>' + json.total_detectados + ' productos</b> · ' +
            'confianza OCR ' + (json.confianza_ocr * 100).toFixed(0) + '% · ' +
            json.segundos + 's</div>';

    html += '<div class="caja">';
    for (const p of json.productos) {
      let clase = p.confianza >= 0.85 ? 'alta' : (p.confianza >= 0.55 ? 'baja' : 'nula');
      let nombre = p.nombre_sugerido || 'Sin identificar';
      html += '<div class="item">' +
              '<div class="nombre">' + nombre + ' — ' + p.cantidad + ' ' + p.unidad + '</div>' +
              '<div class="crudo">' + p.texto_crudo + '</div>' +
              '<div class="conf ' + clase + '">confianza ' +
              (p.confianza * 100).toFixed(0) + '%</div>' +
              '</div>';
    }
    html += '</div>';
    salida.innerHTML = html;

  } catch (e) {
    salida.innerHTML = '<div class="caja">Error de conexión: ' + e.message + '</div>';
  } finally {
    boton.disabled = false;
    boton.textContent = 'Procesar factura';
  }
};
</script>
</body>
</html>
"""
