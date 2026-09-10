"""
API de FreshTrack — HU-03 · Escanear factura de mercado.

Expone el endpoint que recibe la foto de la factura, la procesa y
devuelve la lista de productos detectados para que el usuario los
confirme (eso ya es HU-04).
"""

import time

import cv2
import numpy as np
from fastapi import Cookie, Depends, FastAPI, File, HTTPException, Response, UploadFile
from pydantic import BaseModel, Field
from fastapi.responses import HTMLResponse

from .catalogo import CATALOGO_ALIAS
from .matching import asociar_catalogo
from .ocr import extraer_texto
from .parser_factura import parsear_factura
from .auth import fecha_expiracion, hash_password, usuario_actual, validar_correo, verificar_password
from .storage import conectar, crear_sesion

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


class Credenciales(BaseModel):
  correo: str
  password: str = Field(min_length=8, max_length=128)


class ItemInventario(BaseModel):
  nombre: str = Field(min_length=1, max_length=120)
  cantidad: float = Field(gt=0)


class LineaProducto(BaseModel):
  nombre: str = Field(min_length=1, max_length=120)
  cantidad: float = Field(gt=0)
  unidad: str = Field(default="UND", min_length=1, max_length=10)
  condicion: str = Field(default="fuera", pattern="^(nevera|fuera)$")


class ConfirmacionEscaneo(BaseModel):
  lineas: list[LineaProducto]


@app.post("/api/v1/auth/registro", status_code=201)
def registrar(datos: Credenciales, response: Response):
  correo = validar_correo(datos.correo)
  with conectar() as conexion:
    try:
      cursor = conexion.execute(
        "INSERT INTO usuario (correo, hash_password, nombre) VALUES (?, ?, ?)",
        (correo, hash_password(datos.password), correo.split("@")[0]),
      )
    except Exception as error:
      if "UNIQUE constraint failed" in str(error):
        raise HTTPException(status_code=409, detail="El correo ya esta registrado")
      raise
    token = crear_sesion(conexion, cursor.lastrowid, fecha_expiracion())
  response.set_cookie("token_sesion", token, max_age=30 * 86400, httponly=True, samesite="lax")
  return {"mensaje": "Cuenta creada", "correo": correo}


@app.post("/api/v1/auth/login")
def iniciar_sesion(datos: Credenciales, response: Response):
  correo = validar_correo(datos.correo)
  with conectar() as conexion:
    usuario = conexion.execute(
      "SELECT id_usuario, hash_password FROM usuario WHERE correo = ?", (correo,)
    ).fetchone()
    if usuario is None or not verificar_password(datos.password, usuario["hash_password"]):
      raise HTTPException(status_code=401, detail="Correo o contrasena incorrectos")
    token = crear_sesion(conexion, usuario["id_usuario"], fecha_expiracion())
  response.set_cookie("token_sesion", token, max_age=30 * 86400, httponly=True, samesite="lax")
  return {"mensaje": "Sesion iniciada", "correo": correo}


@app.post("/api/v1/auth/logout")
def cerrar_sesion(response: Response, token_sesion: str | None = Cookie(default=None)):
  if token_sesion:
    with conectar() as conexion:
      conexion.execute("DELETE FROM sesion WHERE token = ?", (token_sesion,))
  response.delete_cookie("token_sesion")
  return {"mensaje": "Sesion cerrada"}


@app.get("/api/v1/auth/me")
def mi_cuenta(usuario=Depends(usuario_actual)):
  return dict(usuario)


@app.get("/api/v1/inventario")
def listar_inventario(usuario=Depends(usuario_actual)):
  with conectar() as conexion:
    filas = conexion.execute(
      "SELECT id_item, nombre, cantidad, situacion FROM item_inventario "
      "WHERE id_usuario = ? ORDER BY id_item",
      (usuario["id_usuario"],),
    ).fetchall()
  return {"items": [dict(fila) for fila in filas]}


@app.post("/api/v1/inventario", status_code=201)
def agregar_inventario(item: ItemInventario, usuario=Depends(usuario_actual)):
  with conectar() as conexion:
    fila = conexion.execute(
      "INSERT INTO item_inventario (id_usuario, nombre, cantidad) VALUES (?, ?, ?) "
      "RETURNING id_item, nombre, cantidad, situacion",
      (usuario["id_usuario"], item.nombre.strip(), item.cantidad),
    ).fetchone()
  return dict(fila)


def _linea_dict(fila):
  return {
    "id_linea": fila["id_linea"],
    "texto_crudo": fila["texto_crudo"],
    "id_alimento_sugerido": fila["id_alimento_sugerido"],
    "nombre": fila["nombre"],
    "cantidad": fila["cantidad"],
    "unidad": fila["unidad"],
    "confianza": fila["confianza"],
    "condicion": fila["condicion"],
    "confirmada": bool(fila["confirmada"]),
  }


def _obtener_escaneo(conexion, id_escaneo, id_usuario):
  escaneo = conexion.execute(
    "SELECT id_escaneo FROM escaneo_borrador WHERE id_escaneo = ? AND id_usuario = ?",
    (id_escaneo, id_usuario),
  ).fetchone()
  if escaneo is None:
    raise HTTPException(status_code=404, detail="Escaneo no encontrado")
  return escaneo


@app.get("/api/v1/escaneos/{id_escaneo}")
def ver_escaneo(id_escaneo: int, usuario=Depends(usuario_actual)):
  with conectar() as conexion:
    _obtener_escaneo(conexion, id_escaneo, usuario["id_usuario"])
    filas = conexion.execute(
      "SELECT * FROM linea_detectada WHERE id_escaneo = ? ORDER BY id_linea", (id_escaneo,)
    ).fetchall()
  return {"id_escaneo": id_escaneo, "lineas": [_linea_dict(fila) for fila in filas]}


@app.put("/api/v1/escaneos/{id_escaneo}/lineas/{id_linea}")
def editar_linea(id_escaneo: int, id_linea: int, cambios: LineaProducto,
                 usuario=Depends(usuario_actual)):
  with conectar() as conexion:
    _obtener_escaneo(conexion, id_escaneo, usuario["id_usuario"])
    cursor = conexion.execute(
      """UPDATE linea_detectada SET nombre = ?, cantidad = ?, unidad = ?, condicion = ?,
         confirmada = 0 WHERE id_linea = ? AND id_escaneo = ?""",
      (cambios.nombre.strip(), cambios.cantidad, cambios.unidad.upper(),
       cambios.condicion, id_linea, id_escaneo),
    )
    if cursor.rowcount == 0:
      raise HTTPException(status_code=404, detail="Linea no encontrada")
    fila = conexion.execute("SELECT * FROM linea_detectada WHERE id_linea = ?", (id_linea,)).fetchone()
  return _linea_dict(fila)


@app.delete("/api/v1/escaneos/{id_escaneo}/lineas/{id_linea}", status_code=204)
def eliminar_linea(id_escaneo: int, id_linea: int, usuario=Depends(usuario_actual)):
  with conectar() as conexion:
    _obtener_escaneo(conexion, id_escaneo, usuario["id_usuario"])
    cursor = conexion.execute(
      "DELETE FROM linea_detectada WHERE id_linea = ? AND id_escaneo = ?", (id_linea, id_escaneo)
    )
    if cursor.rowcount == 0:
      raise HTTPException(status_code=404, detail="Linea no encontrada")
  return Response(status_code=204)


@app.post("/api/v1/escaneos/{id_escaneo}/lineas", status_code=201)
def agregar_linea(id_escaneo: int, linea: LineaProducto, usuario=Depends(usuario_actual)):
  with conectar() as conexion:
    _obtener_escaneo(conexion, id_escaneo, usuario["id_usuario"])
    fila = conexion.execute(
      """INSERT INTO linea_detectada
         (id_escaneo, texto_crudo, nombre, cantidad, unidad, condicion)
         VALUES (?, ?, ?, ?, ?, ?) RETURNING *""",
      (id_escaneo, linea.nombre, linea.nombre.strip(), linea.cantidad,
       linea.unidad.upper(), linea.condicion),
    ).fetchone()
  return _linea_dict(fila)


@app.post("/api/v1/escaneos/{id_escaneo}/confirmar")
def confirmar_escaneo(id_escaneo: int, datos: ConfirmacionEscaneo,
                      usuario=Depends(usuario_actual)):
  with conectar() as conexion:
    _obtener_escaneo(conexion, id_escaneo, usuario["id_usuario"])
    existentes = conexion.execute(
      "SELECT id_linea FROM linea_detectada WHERE id_escaneo = ? ORDER BY id_linea", (id_escaneo,)
    ).fetchall()
    if len(existentes) != len(datos.lineas):
      raise HTTPException(status_code=400, detail="La lista de confirmacion no coincide con el escaneo")
    for fila, linea in zip(existentes, datos.lineas):
      conexion.execute(
        "UPDATE linea_detectada SET nombre = ?, cantidad = ?, unidad = ?, condicion = ?, confirmada = 1 "
        "WHERE id_linea = ?",
        (linea.nombre.strip(), linea.cantidad, linea.unidad.upper(), linea.condicion, fila["id_linea"]),
      )
  return {"mensaje": "Productos confirmados", "id_escaneo": id_escaneo, "total": len(datos.lineas)}


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


@app.get("/registro", response_class=HTMLResponse)
def pagina_registro():
  """Formulario independiente para crear una cuenta."""
  return """
<!DOCTYPE html>
<html lang="es">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>FreshTrack — Crear cuenta</title>
  <style>
    body { font-family: system-ui, sans-serif; margin: 0; padding: 20px;
           background: #f5f6f8; color: #1a1a1a; }
    h1 { font-size: 20px; }
    .caja { max-width: 480px; background: #fff; border-radius: 12px; padding: 16px;
            margin: 0 auto 14px; box-shadow: 0 1px 3px rgba(0,0,0,.08); }
    button { width: 100%; padding: 14px; font-size: 16px; border: 0;
             border-radius: 10px; background: #1a4fd6; color: #fff; }
    button:disabled { background: #9aa5b8; }
    label { display: block; font-size: 13px; margin: 10px 0 4px; }
    input { box-sizing: border-box; width: 100%; padding: 12px;
            border: 1px solid #c8ceda; border-radius: 8px; font-size: 16px; }
    .secundario { display: block; box-sizing: border-box; background: #e5e9f2;
                  color: #1a1a1a; margin-top: 8px; text-align: center;
                  text-decoration: none; }
    .error { color: #b3261e; margin-top: 10px; }
  </style>
</head>
<body>
  <div class="caja">
    <h1>FreshTrack</h1>
    <h2>Crear cuenta</h2>
    <label for="correo">Correo electronico</label>
    <input type="email" id="correo" autocomplete="email" required>
    <label for="password">Contrasena</label>
    <input type="password" id="password" minlength="8" autocomplete="new-password" required>
    <button id="crear">Crear cuenta</button>
    <a class="secundario" href="/">Volver a iniciar sesion</a>
    <div class="error" id="error-registro" role="alert"></div>
  </div>

<script>
const botonCrear = document.getElementById('crear');
const errorRegistro = document.getElementById('error-registro');

botonCrear.onclick = async () => {
  errorRegistro.textContent = '';
  botonCrear.disabled = true;
  try {
    const respuesta = await fetch('/api/v1/auth/registro', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({correo: document.getElementById('correo').value,
                            password: document.getElementById('password').value})
    });
    const json = await respuesta.json();
    if (!respuesta.ok) throw new Error(json.detail || 'No fue posible crear la cuenta');
    window.location.href = '/';
  } catch (error) {
    errorRegistro.textContent = error.message;
    botonCrear.disabled = false;
  }
};
</script>
</body>
</html>
"""


@app.post("/api/v1/facturas/escanear")
async def escanear_factura(archivo: UploadFile = File(...), usuario=Depends(usuario_actual)):
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

    with conectar() as conexion:
      escaneo = conexion.execute(
        "INSERT INTO escaneo_borrador (id_usuario, texto_ocr) VALUES (?, ?) RETURNING id_escaneo",
        (usuario["id_usuario"], resultado_ocr["texto"]),
      ).fetchone()
      id_escaneo = escaneo["id_escaneo"]
      for producto in productos:
        conexion.execute(
          """INSERT INTO linea_detectada
             (id_escaneo, texto_crudo, id_alimento_sugerido, nombre, cantidad, unidad, confianza)
             VALUES (?, ?, ?, ?, ?, ?, ?)""",
          (id_escaneo, producto["texto_crudo"], producto["id_alimento_sugerido"],
           producto["nombre_sugerido"] or producto["descripcion"], producto["cantidad"],
           producto["unidad"], producto["confianza"]),
        )

    return {
      "id_escaneo": id_escaneo,
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
  <title>FreshTrack — Mi inventario</title>
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
    .fila { display: grid; grid-template-columns: 1fr 90px 90px; gap: 8px; align-items: center; margin: 8px 0; }
    .fila input, .fila select { min-width: 0; padding: 9px; border: 1px solid #c8ceda; border-radius: 6px; }
    .fila button { padding: 9px; font-size: 13px; }
    .acciones { display: flex; gap: 8px; margin-top: 12px; }
    .acciones button { flex: 1; }
    .aviso { background: #fff4e5; border-left: 4px solid #e08b00;
             padding: 10px; border-radius: 6px; margin-bottom: 12px; }
    .oculto { display: none; }
    .error { color: #b3261e; margin-top: 10px; }
    .secundario { background: #e5e9f2; color: #1a1a1a; margin-top: 8px; }
    label { display: block; font-size: 13px; margin: 10px 0 4px; }
    input[type=email], input[type=password] { box-sizing: border-box; width: 100%;
      padding: 12px; border: 1px solid #c8ceda; border-radius: 8px; font-size: 16px; }
  </style>
</head>
<body>
  <h1>FreshTrack</h1>

  <div class="caja" id="acceso">
    <h2>Tu inventario, solo tuyo</h2>
    <label for="correo">Correo electronico</label>
    <input type="email" id="correo" autocomplete="email">
    <label for="password">Contrasena</label>
    <input type="password" id="password" minlength="8" autocomplete="current-password">
    <button id="iniciar">Iniciar sesion</button>
    <button class="secundario" id="registrar">Crear cuenta</button>
    <div class="error" id="error-acceso" role="alert"></div>
  </div>

  <div class="caja oculto" id="cuenta">
    <b id="usuario"></b>
    <button class="secundario" id="salir">Cerrar sesion</button>
  </div>

  <div class="caja oculto" id="escaneo">
    <h2>Escanear factura</h2>
    <input type="file" id="archivo" accept="image/*" capture="environment">
    <button id="enviar">Procesar factura</button>
  </div>

  <div id="salida"></div>

<script>
const boton = document.getElementById('enviar');
const entrada = document.getElementById('archivo');
const salida = document.getElementById('salida');
const acceso = document.getElementById('acceso');
const cuenta = document.getElementById('cuenta');
const escaneo = document.getElementById('escaneo');
const errorAcceso = document.getElementById('error-acceso');

async function autenticar(ruta) {
  errorAcceso.textContent = '';
  const respuesta = await fetch(ruta, {
    method: 'POST', headers: {'Content-Type': 'application/json'},
    body: JSON.stringify({correo: document.getElementById('correo').value,
                          password: document.getElementById('password').value})
  });
  const json = await respuesta.json();
  if (!respuesta.ok) throw new Error(json.detail || 'No fue posible autenticarte');
  mostrarSesion(json.correo);
}

function mostrarSesion(correo) {
  acceso.classList.add('oculto');
  cuenta.classList.remove('oculto');
  escaneo.classList.remove('oculto');
  document.getElementById('usuario').textContent = correo;
}

document.getElementById('iniciar').onclick = () => autenticar('/api/v1/auth/login')
  .catch(error => errorAcceso.textContent = error.message);
document.getElementById('registrar').onclick = () => window.location.href = '/registro';
document.getElementById('salir').onclick = async () => {
  await fetch('/api/v1/auth/logout', {method: 'POST'});
  window.location.reload();
};

fetch('/api/v1/auth/me').then(respuesta => {
  if (respuesta.ok) return respuesta.json();
  throw new Error();
}).then(usuario => mostrarSesion(usuario.correo)).catch(() => {});

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

    const escaneo = await (await fetch('/api/v1/escaneos/' + json.id_escaneo)).json();
    renderizarEscaneo(json, escaneo.lineas);

  } catch (e) {
    salida.innerHTML = '<div class="caja">Error de conexión: ' + e.message + '</div>';
  } finally {
    boton.disabled = false;
    boton.textContent = 'Procesar factura';
  }
};

function renderizarEscaneo(resumen, lineas) {
  let html = '';
  if (resumen.advertencia) html += '<div class="aviso">' + resumen.advertencia + '</div>';
  html += '<div class="caja"><b>Revisa tus productos</b> · confianza OCR ' +
          (resumen.confianza_ocr * 100).toFixed(0) + '% · ' + resumen.segundos + 's</div>';
  html += '<div class="caja"><div id="lineas">';
  for (const linea of lineas) {
    const clase = linea.confianza >= 0.85 ? 'alta' : (linea.confianza >= 0.55 ? 'baja' : 'nula');
    html += '<div class="item fila" data-linea="' + linea.id_linea + '" data-unidad="' + linea.unidad + '">' +
      '<input class="nombre" value="' + linea.nombre.replace(/"/g, '&quot;') + '">' +
      '<input class="cantidad" type="number" min="0.001" step="0.001" value="' + linea.cantidad + '">' +
      '<select class="condicion"><option value="fuera" ' + (linea.condicion === 'fuera' ? 'selected' : '') + '>Fuera</option>' +
      '<option value="nevera" ' + (linea.condicion === 'nevera' ? 'selected' : '') + '>Nevera</option></select>' +
      '<button class="eliminar" type="button">Eliminar</button>' +
      '<div class="crudo">Detectado: ' + linea.texto_crudo + ' · ' +
      '<span class="conf ' + clase + '">' + (linea.confianza * 100).toFixed(0) + '%</span></div></div>';
  }
  html += '</div><button id="agregar" class="secundario" type="button">Agregar producto</button>' +
          '<button id="confirmar" type="button">Confirmar productos</button><div id="mensaje"></div></div>';
  salida.innerHTML = html;
  const idEscaneo = resumen.id_escaneo;
  document.querySelectorAll('.eliminar').forEach(boton => boton.onclick = async () => {
    const fila = boton.closest('[data-linea]');
    await fetch('/api/v1/escaneos/' + idEscaneo + '/lineas/' + fila.dataset.linea, {method: 'DELETE'});
    fila.remove();
  });
  document.getElementById('agregar').onclick = async () => {
    const respuesta = await fetch('/api/v1/escaneos/' + idEscaneo + '/lineas', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      body: JSON.stringify({nombre: 'Nuevo producto', cantidad: 1, unidad: 'UND', condicion: 'fuera'})
    });
    if (respuesta.ok) { const actualizado = await (await fetch('/api/v1/escaneos/' + idEscaneo)).json(); renderizarEscaneo(resumen, actualizado.lineas); }
  };
  document.getElementById('confirmar').onclick = async () => {
    const lineasActuales = [...document.querySelectorAll('[data-linea]')].map(fila => ({
      nombre: fila.querySelector('.nombre').value, cantidad: Number(fila.querySelector('.cantidad').value),
      unidad: fila.dataset.unidad || 'UND', condicion: fila.querySelector('.condicion').value
    }));
    const respuesta = await fetch('/api/v1/escaneos/' + idEscaneo + '/confirmar', {
      method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({lineas: lineasActuales})
    });
    document.getElementById('mensaje').textContent = respuesta.ok ? 'Productos confirmados' : 'No se pudieron confirmar los productos';
  };
}
</script>
</body>
</html>
"""
