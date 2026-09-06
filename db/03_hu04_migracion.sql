-- FreshTrack — HU-04 · Migracion para bases PostgreSQL existentes
-- Ejecutar despues de 01_esquema_y_catalogo.sql y 02_vida_util_foodkeeper.sql.

ALTER TABLE linea_detectada
    ADD COLUMN IF NOT EXISTS id_condicion SMALLINT
    REFERENCES condicion_almacenamiento(id_condicion);

CREATE INDEX IF NOT EXISTS idx_linea_detectada_escaneo
    ON linea_detectada (id_escaneo);
