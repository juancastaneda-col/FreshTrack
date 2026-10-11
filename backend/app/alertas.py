"""Motor de alertas de vencimiento — HU-12.

Proceso diario que revisa el inventario activo de cada usuario y genera
una notificación por cada producto que vence dentro de su ventana de
anticipación configurada. Evita duplicados mediante la restricción UNIQUE
(id_item, tipo, fecha_generada) en la tabla notificacion.
"""

import logging
import os
import smtplib
from datetime import date, timedelta
from email.mime.text import MIMEText

from .storage import conectar

logger = logging.getLogger("freshtrack.alertas")

GMAIL_USER = os.getenv("GMAIL_USER", "")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "")


def _enviar_email(destinatario: str, mensajes: list[str]):
    if not GMAIL_USER or not GMAIL_APP_PASSWORD:
        logger.warning("Email no configurado (GMAIL_USER / GMAIL_APP_PASSWORD vacíos)")
        return
    try:
        cuerpo = "Hola,\n\nEstos alimentos están por vencer:\n\n"
        cuerpo += "\n".join(f"  • {m}" for m in mensajes)
        cuerpo += "\n\n¿No sabes qué hacer con ellos? Revisa la sección de Recetario en FreshTrack y encuentra recetas para aprovecharlos antes de que se venzan.\n"
        cuerpo += "\nRevisa tu inventario en FreshTrack.\n"

        msg = MIMEText(cuerpo, "plain", "utf-8")
        msg["Subject"] = f"FreshTrack — {len(mensajes)} alimento(s) por vencer"
        msg["From"] = GMAIL_USER
        msg["To"] = destinatario

        with smtplib.SMTP("smtp.gmail.com", 587) as smtp:
            smtp.ehlo()
            smtp.starttls()
            smtp.login(GMAIL_USER, GMAIL_APP_PASSWORD)
            smtp.sendmail(GMAIL_USER, destinatario, msg.as_string())
        logger.info("Email enviado a %s (%d items)", destinatario, len(mensajes))
    except Exception:
        logger.exception("Error enviando email a %s", destinatario)


def revisar_vencimientos() -> int:
    """Revisa productos por vencer y genera notificaciones para todos los usuarios.

    Returns:
        Número de notificaciones nuevas insertadas.
    """
    hoy = date.today()
    generadas = 0
    try:
        with conectar() as conexion:
            usuarios = conexion.execute(
                "SELECT id_usuario, dias_anticipacion, notificaciones_activas FROM usuario"
            ).fetchall()

            for usuario in usuarios:
                if not usuario["notificaciones_activas"]:
                    continue
                id_usuario = usuario["id_usuario"]
                dias = usuario["dias_anticipacion"] or 3
                limite = hoy + timedelta(days=dias)

                items = conexion.execute(
                    """SELECT id_item, nombre, fecha_vencimiento_est
                       FROM item_inventario
                       WHERE id_usuario = ?
                         AND situacion = 'activo'
                         AND fecha_vencimiento_est IS NOT NULL
                         AND date(fecha_vencimiento_est) >= ?
                         AND date(fecha_vencimiento_est) <= ?""",
                    (id_usuario, hoy.isoformat(), limite.isoformat()),
                ).fetchall()

                mensajes_nuevos = []
                for item in items:
                    dias_restantes = (
                        date.fromisoformat(item["fecha_vencimiento_est"]) - hoy
                    ).days
                    if dias_restantes == 0:
                        mensaje = f"{item['nombre']} vence hoy."
                    elif dias_restantes == 1:
                        mensaje = f"{item['nombre']} vence mañana."
                    else:
                        mensaje = f"{item['nombre']} vence en {dias_restantes} días."

                    cursor = conexion.execute(
                        """INSERT OR IGNORE INTO notificacion
                           (id_usuario, id_item, tipo, mensaje, fecha_generada)
                           VALUES (?, ?, 'vencimiento_proximo', ?, ?)""",
                        (id_usuario, item["id_item"], mensaje, hoy.isoformat()),
                    )
                    if cursor.rowcount:
                        mensajes_nuevos.append(mensaje)
                        generadas += 1

                if mensajes_nuevos:
                    fila_correo = conexion.execute(
                        "SELECT correo, correo_notificaciones FROM usuario WHERE id_usuario = ?",
                        (id_usuario,),
                    ).fetchone()
                    destino = fila_correo["correo_notificaciones"] or fila_correo["correo"]
                    _enviar_email(destino, mensajes_nuevos)

        logger.info("Revisión %s completada: %d notificaciones nuevas.", hoy, generadas)
    except Exception:
        logger.exception("Error al revisar vencimientos el %s.", hoy)
        raise

    return generadas
