"""Hash de contrasenas y dependencias de autenticacion HTTP."""

import base64
import hashlib
import hmac
import os
import re
from datetime import datetime, timedelta, timezone

from fastapi import Cookie, HTTPException

from .storage import conectar


CORREO_VALIDO = re.compile(r"^[^@\s]+@[^@\s]+\.[^@\s]+$")
SESION_DIAS = 30


def validar_correo(correo):
    correo = correo.strip().lower()
    if len(correo) > 255 or not CORREO_VALIDO.fullmatch(correo):
        raise HTTPException(status_code=422, detail="Ingrese un correo electronico valido")
    return correo


def hash_password(password):
    salt = os.urandom(16)
    derivada = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, 310_000)
    return "pbkdf2_sha256$310000${}${}".format(
        base64.b64encode(salt).decode(), base64.b64encode(derivada).decode()
    )


def verificar_password(password, guardada):
    try:
        algoritmo, rondas, sal, digest = guardada.split("$")
        if algoritmo != "pbkdf2_sha256":
            return False
        calculada = hashlib.pbkdf2_hmac(
            "sha256", password.encode(), base64.b64decode(sal), int(rondas)
        )
        return hmac.compare_digest(base64.b64encode(calculada).decode(), digest)
    except (ValueError, TypeError):
        return False


def fecha_expiracion():
    return (datetime.now(timezone.utc) + timedelta(days=SESION_DIAS)).isoformat()


def usuario_actual(token_sesion: str | None = Cookie(default=None)):
    if not token_sesion:
        raise HTTPException(status_code=401, detail="Debe iniciar sesion")

    with conectar() as conexion:
        usuario = conexion.execute(
            """
            SELECT u.id_usuario, u.correo, u.nombre
            FROM sesion s JOIN usuario u ON u.id_usuario = s.id_usuario
            WHERE s.token = ? AND s.expira_en > ?
            """,
            (token_sesion, datetime.now(timezone.utc).isoformat()),
        ).fetchone()
    if usuario is None:
        raise HTTPException(status_code=401, detail="La sesion no es valida o ha expirado")
    return usuario