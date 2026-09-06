"""Persistencia local de autenticacion e inventario para el MVP."""

import os
import secrets
import sqlite3
from contextlib import contextmanager


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
            situacion TEXT NOT NULL DEFAULT 'activo'
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
        CREATE INDEX IF NOT EXISTS idx_sesion_usuario ON sesion(id_usuario);
        CREATE INDEX IF NOT EXISTS idx_item_usuario ON item_inventario(id_usuario);
        CREATE INDEX IF NOT EXISTS idx_escaneo_usuario ON escaneo_borrador(id_usuario);
        CREATE INDEX IF NOT EXISTS idx_linea_escaneo ON linea_detectada(id_escaneo);
        """
    )


def crear_sesion(conexion, id_usuario, expira_en):
    token = secrets.token_urlsafe(32)
    conexion.execute(
        "INSERT INTO sesion (token, id_usuario, expira_en) VALUES (?, ?, ?)",
        (token, id_usuario, expira_en),
    )
    return token