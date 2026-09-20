"""
API de FreshTrack — HU-03 · Escanear factura de mercado.

Expone el endpoint que recibe la foto de la factura, la procesa y
devuelve la lista de productos detectados para que el usuario los
confirme (eso ya es HU-04).
"""

import time
from datetime import date

import cv2
import numpy as np
from fastapi import Cookie, Depends, FastAPI, File, HTTPException, Response, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from . import catalogo
from .catalogo import CATALOGO_ALIAS
from .matching import asociar_catalogo
from .ocr import extraer_texto
from .parser_factura import parsear_factura
from .prototipo import router as prototipo_router
from .auth import fecha_expiracion, hash_password, usuario_actual, validar_correo, verificar_password
from .storage import conectar, crear_sesion

app = FastAPI(
    title="FreshTrack — OCR de facturas",
    description="HU-03 · Escanear factura de mercado",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http://localhost:\d+",  # permite cualquier puerto local (Expo web)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(prototipo_router)

TAMANO_MAXIMO = 10 * 1024 * 1024          # 10 MB
FORMATOS_VALIDOS = {"image/jpeg", "image/png", "image/webp"}

# Si el OCR lee con menos confianza que esto, probablemente la foto
# está muy mala y es mejor pedirle al usuario que la repita.
CONFIANZA_MINIMA_ACEPTABLE = 0.40


class Credenciales(BaseModel):
  correo: str
  password: str = Field(min_length=8, max_length=128)

class ActualizacionCuenta(BaseModel):
  nombre: str | None = Field(default=None, min_length=1, max_length=120)
  password_actual: str | None = None
  nueva_password: str | None = Field(default=None, min_length=8, max_length=128)

class ItemInventario(BaseModel):
  id_alimento: int | None = None
  nombre: str = Field(min_length=1, max_length=120)
  cantidad: float = Field(gt=0)
  unidad: str = Field(default="UND", min_length=1, max_length=10)
  condicion: str = Field(default="fuera", pattern="^(nevera|fuera)$")


class CambioSituacion(BaseModel):
  situacion: str = Field(pattern="^(consumido|desechado)$")


class LineaProducto(BaseModel):
  id_alimento: int | None = None
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

@app.patch("/api/v1/auth/me")
def actualizar_cuenta(datos: ActualizacionCuenta, usuario=Depends(usuario_actual)):
  with conectar() as conexion:
    if datos.nueva_password:
      if not datos.password_actual:
        raise HTTPException(status_code=422, detail="Debe ingresar su contrasena actual")
      fila = conexion.execute(
        "SELECT hash_password FROM usuario WHERE id_usuario = ?", (usuario["id_usuario"],)
      ).fetchone()
      if not verificar_password(datos.password_actual, fila["hash_password"]):
        raise HTTPException(status_code=401, detail="La contrasena actual no es correcta")
      conexion.execute(
        "UPDATE usuario SET hash_password = ? WHERE id_usuario = ?",
        (hash_password(datos.nueva_password), usuario["id_usuario"]),
      )
    if datos.nombre:
      conexion.execute(
        "UPDATE usuario SET nombre = ? WHERE id_usuario = ?",
        (datos.nombre.strip(), usuario["id_usuario"]),
      )
    fila = conexion.execute(
      "SELECT id_usuario, correo, nombre FROM usuario WHERE id_usuario = ?",
      (usuario["id_usuario"],),
    ).fetchone()
  return dict(fila)

@app.get("/api/v1/inventario")
def listar_inventario(usuario=Depends(usuario_actual)):
  with conectar() as conexion:
    filas = conexion.execute(
      "SELECT id_item, id_alimento, nombre, cantidad, unidad, condicion, situacion, "
      "fecha_vencimiento_est FROM item_inventario "
      "WHERE id_usuario = ? AND situacion = 'activo' "
      "ORDER BY fecha_vencimiento_est IS NULL, fecha_vencimiento_est, id_item DESC",
      (usuario["id_usuario"],),
    ).fetchall()
  return {"items": [dict(fila) for fila in filas]}


@app.get("/api/v1/catalogo")
def buscar_catalogo(q: str, usuario=Depends(usuario_actual)):
  return {"resultados": catalogo.buscar(q)}


@app.post("/api/v1/inventario", status_code=201)
def agregar_inventario(item: ItemInventario, usuario=Depends(usuario_actual)):
  hoy = date.today()
  aviso = None
  vencimiento = None
  info = None
  if item.id_alimento is not None:
    info = catalogo.obtener(item.id_alimento)
    if info is None:
      raise HTTPException(status_code=404, detail="El alimento no esta en el catalogo")
    vencimiento = catalogo.calcular_vencimiento(item.id_alimento, item.condicion, hoy)
  else:
    aviso = ("Este producto no esta en el catalogo, no se pudo calcular "
             "una fecha de vencimiento estimada.")
  nombre = info["nombre"] if info else item.nombre.strip()
  vencimiento_iso = vencimiento.isoformat() if vencimiento else None
  with conectar() as conexion:
    fila = conexion.execute(
      "INSERT INTO item_inventario "
      "(id_usuario, id_alimento, nombre, cantidad, unidad, condicion, fecha_vencimiento_est) "
      "VALUES (?, ?, ?, ?, ?, ?, ?) "
      "RETURNING id_item, id_alimento, nombre, cantidad, unidad, condicion, "
      "situacion, fecha_vencimiento_est",
      (usuario["id_usuario"], item.id_alimento, nombre, item.cantidad,
       item.unidad.upper(), item.condicion, vencimiento_iso),
    ).fetchone()
  resultado = dict(fila)
  if aviso:
    resultado["aviso"] = aviso
  return resultado


@app.patch("/api/v1/inventario/{id_item}")
def cambiar_situacion(id_item: int, cambio: CambioSituacion,
                      usuario=Depends(usuario_actual)):
  with conectar() as conexion:
    cursor = conexion.execute(
      "UPDATE item_inventario SET situacion = ?, fecha_cierre = CURRENT_DATE "
      "WHERE id_item = ? AND id_usuario = ? AND situacion = 'activo'",
      (cambio.situacion, id_item, usuario["id_usuario"]),
    )
    if cursor.rowcount == 0:
      raise HTTPException(status_code=404, detail="Producto no encontrado o ya cerrado")
    fila = conexion.execute(
      "SELECT id_item, nombre, cantidad, unidad, condicion, situacion, fecha_vencimiento_est "
      "FROM item_inventario WHERE id_item = ?", (id_item,)
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
    "en_catalogo": fila["id_alimento_sugerido"] is not None,
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
      "SELECT id_linea, texto_crudo, id_alimento_sugerido FROM linea_detectada "
      "WHERE id_escaneo = ? ORDER BY id_linea",
      (id_escaneo,),
    ).fetchall()
    if len(existentes) != len(datos.lineas):
      raise HTTPException(status_code=400, detail="La lista de confirmacion no coincide con el escaneo")
    items_creados = 0
    for fila, linea in zip(existentes, datos.lineas):
      nombre = linea.nombre.strip()
      unidad = linea.unidad.upper()
      id_alimento = linea.id_alimento or fila["id_alimento_sugerido"]
      if id_alimento is not None and catalogo.obtener(id_alimento) is None:
        raise HTTPException(status_code=404, detail="El alimento no esta en el catalogo")
      vencimiento = (catalogo.calcular_vencimiento(id_alimento, linea.condicion, date.today())
                     if id_alimento is not None else None)
      conexion.execute(
        "UPDATE linea_detectada SET nombre = ?, cantidad = ?, unidad = ?, condicion = ?, confirmada = 1 "
        "WHERE id_linea = ?",
        (nombre, linea.cantidad, unidad, linea.condicion, fila["id_linea"]),
      )
      conexion.execute(
        "INSERT INTO item_inventario "
        "(id_usuario, id_alimento, nombre, cantidad, unidad, condicion, "
        "fecha_vencimiento_est, id_escaneo) VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
        (usuario["id_usuario"], id_alimento, nombre, linea.cantidad, unidad,
         linea.condicion, vencimiento.isoformat() if vencimiento else None, id_escaneo),
      )
      items_creados += 1
      _guardar_correccion(conexion, usuario["id_usuario"], fila["texto_crudo"], nombre)
  return {"mensaje": "Productos confirmados", "id_escaneo": id_escaneo,
          "total": len(datos.lineas), "items_creados": items_creados}


def _cargar_correcciones(conexion, id_usuario):
  """Devuelve {texto_crudo: nombre_corregido} para aplicar a nuevos escaneos."""
  filas = conexion.execute(
    "SELECT texto_crudo, nombre_corregido FROM correccion_alias WHERE id_usuario = ?",
    (id_usuario,),
  ).fetchall()
  return {fila["texto_crudo"]: fila["nombre_corregido"] for fila in filas}


def _guardar_correccion(conexion, id_usuario, texto_crudo, nombre_final):
  """Aprende que este texto de factura corresponde a este producto para el usuario."""
  texto = (texto_crudo or "").strip()
  nombre = (nombre_final or "").strip()
  if not texto or not nombre:
    return
  conexion.execute(
    """INSERT INTO correccion_alias (id_usuario, texto_crudo, nombre_corregido)
       VALUES (?, ?, ?)
       ON CONFLICT(id_usuario, texto_crudo) DO UPDATE SET
         nombre_corregido = excluded.nombre_corregido,
         veces = correccion_alias.veces + 1,
         actualizado_en = CURRENT_TIMESTAMP""",
    (id_usuario, texto, nombre),
  )


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
      correcciones = _cargar_correcciones(conexion, usuario["id_usuario"])
      escaneo = conexion.execute(
        "INSERT INTO escaneo_borrador (id_usuario, texto_ocr) VALUES (?, ?) RETURNING id_escaneo",
        (usuario["id_usuario"], resultado_ocr["texto"]),
      ).fetchone()
      id_escaneo = escaneo["id_escaneo"]
      for producto in productos:
        aprendida = correcciones.get((producto["texto_crudo"] or "").strip())
        if aprendida:
          producto["nombre_sugerido"] = aprendida
          producto["confianza"] = max(producto["confianza"], 0.95)
          producto["confirmado"] = True
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
                "en_catalogo": p["id_alimento_sugerido"] is not None,
            }
            for p in productos
        ],
    }
