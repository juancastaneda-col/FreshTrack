"""Persistencia local de autenticacion e inventario para el MVP."""

import os
import secrets
import sqlite3
from contextlib import contextmanager

from .catalogo import obtener
from .recetas import RECETAS


RUTA_BD = os.getenv("FRESHTRACK_DB", "freshtrack.db")


@contextmanager
def conectar():
    conexion = sqlite3.connect(RUTA_BD)
    conexion.row_factory = sqlite3.Row
    try:
        inicializar(conexion)
        yield conexion
        conexion.commit()
    finally:
        conexion.close()


def inicializar(conexion):
    conexion.executescript(
        """
        CREATE TABLE IF NOT EXISTS usuario (
            id_usuario INTEGER PRIMARY KEY AUTOINCREMENT,
            correo TEXT NOT NULL UNIQUE COLLATE NOCASE,
            hash_password TEXT NOT NULL,
            nombre TEXT NOT NULL,
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS sesion (
            token TEXT PRIMARY KEY,
            id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
            expira_en TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS item_inventario (
            id_item INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
            nombre TEXT NOT NULL,
            cantidad REAL NOT NULL CHECK (cantidad > 0),
            unidad TEXT NOT NULL DEFAULT 'UND',
            condicion TEXT NOT NULL DEFAULT 'fuera' CHECK (condicion IN ('nevera','fuera')),
            situacion TEXT NOT NULL DEFAULT 'activo',
            id_escaneo INTEGER REFERENCES escaneo_borrador(id_escaneo) ON DELETE SET NULL,
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            fecha_cierre TEXT
        );
        CREATE TABLE IF NOT EXISTS escaneo_borrador (
            id_escaneo INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
            texto_ocr TEXT,
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE TABLE IF NOT EXISTS linea_detectada (
            id_linea INTEGER PRIMARY KEY AUTOINCREMENT,
            id_escaneo INTEGER NOT NULL REFERENCES escaneo_borrador(id_escaneo) ON DELETE CASCADE,
            texto_crudo TEXT NOT NULL,
            id_alimento_sugerido INTEGER,
            nombre TEXT NOT NULL,
            cantidad REAL NOT NULL CHECK (cantidad > 0),
            unidad TEXT NOT NULL,
            confianza REAL NOT NULL DEFAULT 0,
            condicion TEXT NOT NULL DEFAULT 'fuera',
            confirmada INTEGER NOT NULL DEFAULT 0
        );
        CREATE TABLE IF NOT EXISTS correccion_alias (
            id_correccion INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
            texto_crudo TEXT NOT NULL,
            nombre_corregido TEXT NOT NULL,
            veces INTEGER NOT NULL DEFAULT 1,
            actualizado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(id_usuario, texto_crudo)
        );
        CREATE TABLE IF NOT EXISTS identificacion_camara (
            id_identificacion INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
            nombre TEXT,
            estado TEXT,
            confianza REAL NOT NULL CHECK (confianza BETWEEN 0 AND 1),
            reconocido INTEGER NOT NULL DEFAULT 0,
            clase_modelo TEXT,
            version_modelo TEXT NOT NULL,
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_sesion_usuario ON sesion(id_usuario);
        CREATE INDEX IF NOT EXISTS idx_item_usuario ON item_inventario(id_usuario);
        CREATE INDEX IF NOT EXISTS idx_escaneo_usuario ON escaneo_borrador(id_usuario);
        CREATE INDEX IF NOT EXISTS idx_linea_escaneo ON linea_detectada(id_escaneo);
        CREATE INDEX IF NOT EXISTS idx_correccion_usuario ON correccion_alias(id_usuario);
        CREATE INDEX IF NOT EXISTS idx_identificacion_usuario ON identificacion_camara(id_usuario);
        CREATE TABLE IF NOT EXISTS notificacion (
            id_notificacion INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
            id_item INTEGER NOT NULL REFERENCES item_inventario(id_item) ON DELETE CASCADE,
            tipo TEXT NOT NULL DEFAULT 'vencimiento_proximo',
            mensaje TEXT NOT NULL,
            fecha_generada TEXT NOT NULL DEFAULT CURRENT_DATE,
            leida INTEGER NOT NULL DEFAULT 0,
            UNIQUE(id_item, tipo, fecha_generada)
        );
        CREATE INDEX IF NOT EXISTS idx_notificacion_usuario ON notificacion(id_usuario);
        CREATE TABLE IF NOT EXISTS receta (
            id_receta INTEGER PRIMARY KEY,
            titulo TEXT NOT NULL,
            minutos_prep INTEGER NOT NULL CHECK (minutos_prep > 0),
            porciones INTEGER NOT NULL CHECK (porciones > 0),
            pasos TEXT NOT NULL
        );
        CREATE TABLE IF NOT EXISTS receta_ingrediente (
            id_receta INTEGER NOT NULL REFERENCES receta(id_receta) ON DELETE CASCADE,
            id_alimento INTEGER NOT NULL,
            PRIMARY KEY (id_receta, id_alimento)
        );
        CREATE TABLE IF NOT EXISTS sugerencia_receta (
            id_sugerencia INTEGER PRIMARY KEY AUTOINCREMENT,
            id_usuario INTEGER NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
            id_receta INTEGER NOT NULL REFERENCES receta(id_receta) ON DELETE CASCADE,
            accion TEXT NOT NULL CHECK (accion IN ('vista','usada','descartada')),
            creado_en TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        CREATE INDEX IF NOT EXISTS idx_sugerencia_usuario ON sugerencia_receta(id_usuario);
        """
    )
    _migrar_columnas(conexion)
    _migrar_recetas(conexion)


def _migrar_recetas(conexion):
    """Alinea el catálogo local con el esquema actual de recetas."""
    columnas = {fila["name"] for fila in conexion.execute("PRAGMA table_info(receta)")}
    columnas_ingrediente = {
        fila["name"] for fila in conexion.execute("PRAGMA table_info(receta_ingrediente)")
    }
    if "pasos" not in columnas:
        conexion.execute("ALTER TABLE receta ADD COLUMN pasos TEXT NOT NULL DEFAULT ''")
        columnas.add("pasos")

    existentes = conexion.execute("SELECT COUNT(*) AS total FROM receta").fetchone()["total"]
    if existentes == len(RECETAS) and "pasos" in columnas:
        return

    ids_actuales = tuple(receta[0] for receta in RECETAS)
    marcadores = ",".join("?" for _ in ids_actuales)
    conexion.execute(
        f"DELETE FROM sugerencia_receta WHERE id_receta NOT IN ({marcadores})",
        ids_actuales,
    )
    conexion.execute(
        f"DELETE FROM receta_ingrediente WHERE id_receta NOT IN ({marcadores})",
        ids_actuales,
    )
    conexion.execute(
        f"DELETE FROM receta WHERE id_receta NOT IN ({marcadores})",
        ids_actuales,
    )

    for rid, titulo, ingredientes, minutos, porciones, pasos in RECETAS:
        if "id_externo" in columnas:
            conexion.execute(
                """INSERT INTO receta
                     (id_receta, id_externo, titulo, minutos_prep, porciones, pasos, fuente)
                   VALUES (?, ?, ?, ?, ?, ?, ?)
                   ON CONFLICT(id_receta) DO UPDATE SET
                     titulo = excluded.titulo,
                     minutos_prep = excluded.minutos_prep,
                     porciones = excluded.porciones,
                     pasos = excluded.pasos,
                     fuente = excluded.fuente""",
                (rid, f"freshtrack-{rid:02d}", titulo, minutos, porciones, pasos, "FreshTrack"),
            )
        else:
            conexion.execute(
                """INSERT INTO receta (id_receta, titulo, minutos_prep, porciones, pasos)
                   VALUES (?, ?, ?, ?, ?)
                   ON CONFLICT(id_receta) DO UPDATE SET
                     titulo = excluded.titulo,
                     minutos_prep = excluded.minutos_prep,
                     porciones = excluded.porciones,
                     pasos = excluded.pasos""",
                (rid, titulo, minutos, porciones, pasos),
            )
        conexion.execute("DELETE FROM receta_ingrediente WHERE id_receta = ?", (rid,))
        if "nombre" in columnas_ingrediente:
            conexion.executemany(
                "INSERT INTO receta_ingrediente (id_receta, id_alimento, nombre, posicion) VALUES (?, ?, ?, ?)",
                [
                    (rid, ingrediente, _nombre_alimento(ingrediente), posicion)
                    for posicion, ingrediente in enumerate(ingredientes, start=1)
                ],
            )
        else:
            conexion.executemany(
                "INSERT INTO receta_ingrediente (id_receta, id_alimento) VALUES (?, ?)",
                [(rid, ingrediente) for ingrediente in ingredientes],
            )


def _nombre_alimento(id_alimento):
    """Obtiene el nombre del catálogo sin importar el módulo desde storage."""
    return obtener(id_alimento)["nombre"]


def _migrar_columnas(conexion):
    col_item = {fila["name"] for fila in conexion.execute("PRAGMA table_info(item_inventario)")}
    if "unidad" not in col_item:
        conexion.execute("ALTER TABLE item_inventario ADD COLUMN unidad TEXT NOT NULL DEFAULT 'UND'")
    if "condicion" not in col_item:
        conexion.execute("ALTER TABLE item_inventario ADD COLUMN condicion TEXT NOT NULL DEFAULT 'fuera'")
    if "id_escaneo" not in col_item:
        conexion.execute("ALTER TABLE item_inventario ADD COLUMN id_escaneo INTEGER")
    if "creado_en" not in col_item:
        conexion.execute("ALTER TABLE item_inventario ADD COLUMN creado_en TEXT")
    if "id_alimento" not in col_item:
        conexion.execute("ALTER TABLE item_inventario ADD COLUMN id_alimento INTEGER")
    if "fecha_vencimiento_est" not in col_item:
        conexion.execute("ALTER TABLE item_inventario ADD COLUMN fecha_vencimiento_est TEXT")
    if "fecha_cierre" not in col_item:
        conexion.execute("ALTER TABLE item_inventario ADD COLUMN fecha_cierre TEXT")

    col_usuario = {fila["name"] for fila in conexion.execute("PRAGMA table_info(usuario)")}
    if "dias_anticipacion" not in col_usuario:
        conexion.execute("ALTER TABLE usuario ADD COLUMN dias_anticipacion INTEGER NOT NULL DEFAULT 3")
    if "correo_notificaciones" not in col_usuario:
        conexion.execute("ALTER TABLE usuario ADD COLUMN correo_notificaciones TEXT")
    if "notificaciones_activas" not in col_usuario:
        conexion.execute("ALTER TABLE usuario ADD COLUMN notificaciones_activas INTEGER NOT NULL DEFAULT 1")


def crear_sesion(conexion, id_usuario, expira_en):
    token = secrets.token_urlsafe(32)
    conexion.execute(
        "INSERT INTO sesion (token, id_usuario, expira_en) VALUES (?, ?, ?)",
        (token, id_usuario, expira_en),
    )
    return token