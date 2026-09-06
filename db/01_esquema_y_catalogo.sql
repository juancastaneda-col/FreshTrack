-- ============================================================
-- FreshTrack — HU-01 · Base de datos del proyecto
-- Motor: PostgreSQL 15+
-- Contenido: DDL + catálogo de 30 alimentos + vida útil + datos de prueba
-- ============================================================

CREATE EXTENSION IF NOT EXISTS pg_trgm;   -- búsqueda tolerante a errores de escritura

-- ============================================================
-- PARTE 1 — TABLAS
-- ============================================================

-- ---------- Usuarios ----------
CREATE TABLE usuario (
    id_usuario     BIGSERIAL     PRIMARY KEY,
    correo         VARCHAR(255)  NOT NULL UNIQUE,
    hash_password  VARCHAR(255)  NOT NULL,
    nombre         VARCHAR(120)  NOT NULL,
    dias_aviso     SMALLINT      NOT NULL DEFAULT 3
                                 CHECK (dias_aviso BETWEEN 1 AND 14),
    creado_en      TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- Evita duplicados como Usuario@correo.com y usuario@correo.com.
CREATE UNIQUE INDEX uq_usuario_correo_normalizado ON usuario (LOWER(correo));

CREATE TABLE dispositivo (
    id_dispositivo BIGSERIAL     PRIMARY KEY,
    id_usuario     BIGINT        NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    token_push     VARCHAR(255)  NOT NULL UNIQUE,
    plataforma     VARCHAR(10)   NOT NULL CHECK (plataforma IN ('android','ios')),
    activo         BOOLEAN       NOT NULL DEFAULT TRUE,
    registrado_en  TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ---------- Catálogo de alimentos ----------
CREATE TABLE categoria (
    id_categoria   SMALLSERIAL   PRIMARY KEY,
    nombre         VARCHAR(50)   NOT NULL UNIQUE
);

CREATE TABLE unidad_medida (
    id_unidad      SMALLSERIAL   PRIMARY KEY,
    codigo         VARCHAR(10)   NOT NULL UNIQUE,
    descripcion    VARCHAR(50)   NOT NULL
);

CREATE TABLE alimento (
    id_alimento       SERIAL      PRIMARY KEY,
    nombre            VARCHAR(80) NOT NULL UNIQUE,
    id_categoria      SMALLINT    NOT NULL REFERENCES categoria(id_categoria),
    id_unidad_default SMALLINT    NOT NULL REFERENCES unidad_medida(id_unidad),
    etiqueta_modelo   VARCHAR(60) UNIQUE   -- clase del modelo de visión; NULL = no reconocible por cámara
);

-- Alias: traduce el texto de la factura al catálogo.
-- 'BANANO CRIOLLO X KG' -> Banano
CREATE TABLE alias_alimento (
    id_alias          SERIAL       PRIMARY KEY,
    id_alimento       INT          NOT NULL REFERENCES alimento(id_alimento) ON DELETE CASCADE,
    texto_alias       VARCHAR(120) NOT NULL,
    texto_normalizado VARCHAR(120) NOT NULL UNIQUE
);

CREATE INDEX idx_alias_trgm ON alias_alimento USING GIN (texto_normalizado gin_trgm_ops);

-- ---------- Vida útil y madurez ----------
CREATE TABLE condicion_almacenamiento (
    id_condicion   SMALLSERIAL   PRIMARY KEY,
    nombre         VARCHAR(30)   NOT NULL UNIQUE
);

-- La vida útil depende del PAR (alimento, condición): un banano dura
-- distinto en la nevera que fuera de ella. Por eso va en tabla propia
-- con clave compuesta, y no como columnas dentro de 'alimento'.
CREATE TABLE vida_util (
    id_alimento    INT        NOT NULL REFERENCES alimento(id_alimento) ON DELETE CASCADE,
    id_condicion   SMALLINT   NOT NULL REFERENCES condicion_almacenamiento(id_condicion),
    dias_estimados SMALLINT   NOT NULL CHECK (dias_estimados > 0),
    fuente         VARCHAR(120),
    PRIMARY KEY (id_alimento, id_condicion)
);

CREATE TABLE estado_madurez (
    id_estado      SMALLSERIAL  PRIMARY KEY,
    nombre         VARCHAR(30)  NOT NULL UNIQUE,
    factor_ajuste  NUMERIC(3,2) NOT NULL CHECK (factor_ajuste >= 0)
);

-- ---------- Compras y facturas ----------
CREATE TABLE compra (
    id_compra       BIGSERIAL    PRIMARY KEY,
    id_usuario      BIGINT       NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    fecha_compra    DATE         NOT NULL,
    establecimiento VARCHAR(120),
    origen          VARCHAR(20)  NOT NULL CHECK (origen IN ('ocr','manual','camara')),
    creado_en       TIMESTAMPTZ  NOT NULL DEFAULT NOW()
);

CREATE TABLE escaneo_factura (
    id_escaneo       BIGSERIAL    PRIMARY KEY,
    id_usuario       BIGINT       NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    id_compra        BIGINT       UNIQUE REFERENCES compra(id_compra) ON DELETE SET NULL,
    ruta_imagen      VARCHAR(255) NOT NULL,
    texto_ocr        TEXT,
    estado_proc      VARCHAR(20)  NOT NULL DEFAULT 'pendiente'
                                  CHECK (estado_proc IN ('pendiente','procesado','fallido')),
    procesado_en     TIMESTAMPTZ
);

CREATE TABLE linea_detectada (
    id_linea             BIGSERIAL     PRIMARY KEY,
    id_escaneo           BIGINT        NOT NULL REFERENCES escaneo_factura(id_escaneo) ON DELETE CASCADE,
    numero_linea         SMALLINT      NOT NULL,
    texto_crudo          VARCHAR(255)  NOT NULL,
    id_alimento_sugerido INT           REFERENCES alimento(id_alimento),
    cantidad_detectada   NUMERIC(10,3),
    id_unidad            SMALLINT      REFERENCES unidad_medida(id_unidad),
    id_condicion         SMALLINT      REFERENCES condicion_almacenamiento(id_condicion),
    confianza            NUMERIC(4,3)  CHECK (confianza BETWEEN 0 AND 1),
    confirmado           BOOLEAN       NOT NULL DEFAULT FALSE,
    UNIQUE (id_escaneo, numero_linea)
);

-- ---------- Inventario ----------
CREATE TABLE item_inventario (
    id_item               BIGSERIAL     PRIMARY KEY,
    id_usuario            BIGINT        NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    id_alimento           INT           NOT NULL REFERENCES alimento(id_alimento),
    id_compra             BIGINT        REFERENCES compra(id_compra) ON DELETE SET NULL,
    id_condicion          SMALLINT      NOT NULL REFERENCES condicion_almacenamiento(id_condicion),
    id_estado_inicial     SMALLINT      REFERENCES estado_madurez(id_estado),
    cantidad              NUMERIC(10,3) NOT NULL CHECK (cantidad > 0),
    id_unidad             SMALLINT      NOT NULL REFERENCES unidad_medida(id_unidad),
    fecha_registro        DATE          NOT NULL DEFAULT CURRENT_DATE,
    fecha_vencimiento_est DATE          NOT NULL,
    situacion             VARCHAR(20)   NOT NULL DEFAULT 'activo'
                                        CHECK (situacion IN ('activo','consumido','desechado')),
    fecha_cierre          DATE,
    CHECK (fecha_vencimiento_est >= fecha_registro),
    CHECK ((situacion = 'activo' AND fecha_cierre IS NULL)
        OR (situacion <> 'activo' AND fecha_cierre IS NOT NULL))
);

CREATE INDEX idx_item_vencimiento
    ON item_inventario (id_usuario, fecha_vencimiento_est)
    WHERE situacion = 'activo';

-- ---------- Visión artificial ----------
CREATE TABLE inferencia_vision (
    id_inferencia         BIGSERIAL     PRIMARY KEY,
    id_usuario            BIGINT        NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    id_item               BIGINT        REFERENCES item_inventario(id_item) ON DELETE SET NULL,
    ruta_imagen           VARCHAR(255)  NOT NULL,
    id_alimento_pred      INT           REFERENCES alimento(id_alimento),
    id_estado_pred        SMALLINT      REFERENCES estado_madurez(id_estado),
    confianza             NUMERIC(4,3)  NOT NULL CHECK (confianza BETWEEN 0 AND 1),
    version_modelo        VARCHAR(30)   NOT NULL,
    corregido_por_usuario BOOLEAN       NOT NULL DEFAULT FALSE,
    creado_en             TIMESTAMPTZ   NOT NULL DEFAULT NOW()
);

-- ---------- Notificaciones ----------
CREATE TABLE notificacion (
    id_notificacion  BIGSERIAL    PRIMARY KEY,
    id_usuario       BIGINT       NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    id_item          BIGINT       NOT NULL REFERENCES item_inventario(id_item) ON DELETE CASCADE,
    tipo             VARCHAR(20)  NOT NULL CHECK (tipo IN ('por_vencer','vencido')),
    fecha_programada DATE         NOT NULL,
    estado           VARCHAR(15)  NOT NULL DEFAULT 'pendiente'
                                  CHECK (estado IN ('pendiente','enviada','fallida')),
    enviada_en       TIMESTAMPTZ,
    UNIQUE (id_item, tipo, fecha_programada)   -- evita avisos duplicados
);

-- ---------- Recetas ----------
CREATE TABLE receta (
    id_receta     BIGSERIAL     PRIMARY KEY,
    id_externo    VARCHAR(60)   UNIQUE,
    titulo        VARCHAR(200)  NOT NULL,
    url           VARCHAR(500),
    minutos_prep  SMALLINT      CHECK (minutos_prep > 0),
    porciones     SMALLINT      CHECK (porciones > 0)
);

CREATE TABLE receta_ingrediente (
    id_receta   BIGINT        NOT NULL REFERENCES receta(id_receta) ON DELETE CASCADE,
    id_alimento INT           NOT NULL REFERENCES alimento(id_alimento) ON DELETE CASCADE,
    cantidad    NUMERIC(10,3),
    id_unidad   SMALLINT      REFERENCES unidad_medida(id_unidad),
    PRIMARY KEY (id_receta, id_alimento)
);

CREATE TABLE sugerencia_receta (
    id_sugerencia BIGSERIAL    PRIMARY KEY,
    id_usuario    BIGINT       NOT NULL REFERENCES usuario(id_usuario) ON DELETE CASCADE,
    id_item       BIGINT       NOT NULL REFERENCES item_inventario(id_item) ON DELETE CASCADE,
    id_receta     BIGINT       NOT NULL REFERENCES receta(id_receta) ON DELETE CASCADE,
    sugerida_en   TIMESTAMPTZ  NOT NULL DEFAULT NOW(),
    accion        VARCHAR(15)  CHECK (accion IN ('vista','usada','descartada')),
    UNIQUE (id_item, id_receta)
);

-- ============================================================
-- PARTE 2 — DATOS SEMILLA
-- ============================================================

INSERT INTO categoria (nombre) VALUES
    ('Fruta'), ('Verdura'), ('Tubérculo'), ('Hierba');

INSERT INTO unidad_medida (codigo, descripcion) VALUES
    ('UND','Unidad'), ('KG','Kilogramo'), ('G','Gramo'),
    ('LB','Libra'), ('MANOJO','Manojo');

INSERT INTO condicion_almacenamiento (nombre) VALUES
    ('Ambiente'), ('Refrigerado'), ('Congelado');

INSERT INTO estado_madurez (nombre, factor_ajuste) VALUES
    ('Verde', 1.30), ('Fresco', 1.00), ('Maduro', 0.50), ('Dañado', 0.00);

-- ---------- Catálogo de 30 alimentos ----------
-- etiqueta_modelo: solo los 8 que el modelo del Sprint 2 podrá reconocer por cámara
INSERT INTO alimento (nombre, id_categoria, id_unidad_default, etiqueta_modelo) VALUES
    -- Frutas
    ('Banano',           1, 1, 'banana'),
    ('Manzana',          1, 1, 'apple'),
    ('Naranja',          1, 1, 'orange'),
    ('Mandarina',        1, 1, NULL),
    ('Papaya',           1, 1, NULL),
    ('Piña',             1, 1, NULL),
    ('Mango',            1, 1, NULL),
    ('Fresa',            1, 3, NULL),
    ('Uva',              1, 3, NULL),
    ('Pera',             1, 1, NULL),
    ('Aguacate',         1, 1, NULL),
    ('Maracuyá',         1, 1, NULL),
    ('Limón',            1, 1, NULL),
    -- Verduras
    ('Tomate',           2, 1, 'tomato'),
    ('Pepino',           2, 1, 'cucumber'),
    ('Pimentón',         2, 1, 'capsicum'),
    ('Zanahoria',        2, 1, 'carrot'),
    ('Cebolla cabezona', 2, 1, NULL),
    ('Cebolla larga',    2, 5, NULL),
    ('Lechuga',          2, 1, NULL),
    ('Espinaca',         2, 5, NULL),
    ('Brócoli',          2, 1, NULL),
    ('Habichuela',       2, 3, NULL),
    ('Repollo',          2, 1, NULL),
    ('Plátano',          2, 1, NULL),
    -- Tubérculos
    ('Papa',             3, 2, 'potato'),
    ('Yuca',             3, 2, NULL),
    ('Arracacha',        3, 2, NULL),
    ('Remolacha',        3, 1, NULL),
    -- Hierbas
    ('Cilantro',         4, 5, NULL);

-- ---------- Vida útil (días) ----------
-- Condición 1 = Ambiente, 2 = Refrigerado
-- Valores de referencia; ajustar contra USDA FoodKeeper antes de la entrega final.
INSERT INTO vida_util (id_alimento, id_condicion, dias_estimados, fuente)
SELECT a.id_alimento, v.cond, v.dias, 'Referencia USDA FoodKeeper (aprox.)'
FROM (VALUES
    ('Banano',            1,  5), ('Banano',            2,  9),
    ('Manzana',           1,  7), ('Manzana',           2, 30),
    ('Naranja',           1,  7), ('Naranja',           2, 21),
    ('Mandarina',         1,  7), ('Mandarina',         2, 14),
    ('Papaya',            1,  4), ('Papaya',            2,  7),
    ('Piña',              1,  3), ('Piña',              2,  5),
    ('Mango',             1,  5), ('Mango',             2,  7),
    ('Fresa',             1,  2), ('Fresa',             2,  5),
    ('Uva',               1,  3), ('Uva',               2,  7),
    ('Pera',              1,  5), ('Pera',              2, 14),
    ('Aguacate',          1,  4), ('Aguacate',          2,  7),
    ('Maracuyá',          1,  7), ('Maracuyá',          2, 21),
    ('Limón',             1, 10), ('Limón',             2, 30),
    ('Tomate',            1,  5), ('Tomate',            2, 10),
    ('Pepino',            1,  4), ('Pepino',            2,  7),
    ('Pimentón',          1,  5), ('Pimentón',          2, 14),
    ('Zanahoria',         1, 14), ('Zanahoria',         2, 30),
    ('Cebolla cabezona',  1, 30), ('Cebolla cabezona',  2, 60),
    ('Cebolla larga',     1,  7), ('Cebolla larga',     2, 14),
    ('Lechuga',           1,  2), ('Lechuga',           2,  7),
    ('Espinaca',          1,  2), ('Espinaca',          2,  5),
    ('Brócoli',           1,  3), ('Brócoli',           2,  7),
    ('Habichuela',        1,  3), ('Habichuela',        2,  7),
    ('Repollo',           1,  7), ('Repollo',           2, 30),
    ('Plátano',           1,  7), ('Plátano',           2, 10),
    ('Papa',              1, 21), ('Papa',              2, 60),
    ('Yuca',              1,  4), ('Yuca',              2, 10),
    ('Arracacha',         1,  7), ('Arracacha',         2, 14),
    ('Remolacha',         1,  7), ('Remolacha',         2, 21),
    ('Cilantro',          1,  2), ('Cilantro',          2,  7)
) AS v(nombre, cond, dias)
JOIN alimento a ON a.nombre = v.nombre;

-- ---------- Alias para el OCR ----------
-- Se cargan variantes reales que aparecen en las facturas colombianas.
INSERT INTO alias_alimento (id_alimento, texto_alias, texto_normalizado)
SELECT a.id_alimento, v.alias, v.norm
FROM (VALUES
    ('Banano',           'BANANO CRIOLLO',      'banano criollo'),
    ('Banano',           'BANANO URABA',        'banano uraba'),
    ('Banano',           'BANANO',              'banano'),
    ('Manzana',          'MANZANA ROJA',        'manzana roja'),
    ('Manzana',          'MANZANA VERDE',       'manzana verde'),
    ('Manzana',          'MANZANA',             'manzana'),
    ('Tomate',           'TOMATE CHONTO',       'tomate chonto'),
    ('Tomate',           'TOMATE LARGA VIDA',   'tomate larga vida'),
    ('Tomate',           'TOMATE',              'tomate'),
    ('Papa',             'PAPA PASTUSA',        'papa pastusa'),
    ('Papa',             'PAPA CRIOLLA',        'papa criolla'),
    ('Papa',             'PAPA',                'papa'),
    ('Cebolla cabezona', 'CEBOLLA CABEZONA',    'cebolla cabezona'),
    ('Cebolla cabezona', 'CEBOLLA BLANCA',      'cebolla blanca'),
    ('Cebolla larga',    'CEBOLLA LARGA',       'cebolla larga'),
    ('Cebolla larga',    'CEBOLLA JUNCA',       'cebolla junca'),
    ('Aguacate',         'AGUACATE HASS',       'aguacate hass'),
    ('Aguacate',         'AGUACATE',            'aguacate'),
    ('Plátano',          'PLATANO VERDE',       'platano verde'),
    ('Plátano',          'PLATANO MADURO',      'platano maduro'),
    ('Plátano',          'PLATANO',             'platano'),
    ('Zanahoria',        'ZANAHORIA',           'zanahoria'),
    ('Lechuga',          'LECHUGA BATAVIA',     'lechuga batavia'),
    ('Lechuga',          'LECHUGA CRESPA',      'lechuga crespa'),
    ('Naranja',          'NARANJA VALENCIA',    'naranja valencia'),
    ('Limón',            'LIMON TAHITI',        'limon tahiti'),
    ('Limón',            'LIMON MANDARINO',     'limon mandarino'),
    ('Cilantro',         'CILANTRO',            'cilantro'),
    ('Pimentón',         'PIMENTON ROJO',       'pimenton rojo'),
    ('Fresa',            'FRESA',               'fresa')
) AS v(nombre, alias, norm)
JOIN alimento a ON a.nombre = v.nombre;

-- ============================================================
-- PARTE 3 — DATOS DE PRUEBA
-- ============================================================

INSERT INTO usuario (correo, hash_password, nombre, dias_aviso) VALUES
    ('prueba@freshtrack.co', '$2b$12$hashDeEjemploNoUsarEnProduccion', 'Usuario de Prueba', 3);

INSERT INTO compra (id_usuario, fecha_compra, establecimiento, origen) VALUES
    (1, CURRENT_DATE - 2, 'Éxito Robledo', 'ocr');

-- Inserta 5 productos calculando la fecha de vencimiento con la fórmula del proyecto:
--   fecha_registro + ROUND(dias_estimados * factor_ajuste)
INSERT INTO item_inventario
    (id_usuario, id_alimento, id_compra, id_condicion, id_estado_inicial,
     cantidad, id_unidad, fecha_registro, fecha_vencimiento_est)
SELECT
    1,
    a.id_alimento,
    1,
    p.cond,
    e.id_estado,
    p.cant,
    a.id_unidad_default,
    CURRENT_DATE - 2,
    (CURRENT_DATE - 2) + ROUND(vu.dias_estimados * e.factor_ajuste)::INT
FROM (VALUES
    ('Banano',    1, 'Verde',  6),
    ('Tomate',    2, 'Fresco', 4),
    ('Lechuga',   2, 'Fresco', 1),
    ('Aguacate',  1, 'Maduro', 2),
    ('Zanahoria', 2, 'Fresco', 5)
) AS p(nombre, cond, estado, cant)
JOIN alimento       a  ON a.nombre = p.nombre
JOIN estado_madurez e  ON e.nombre = p.estado
JOIN vida_util      vu ON vu.id_alimento = a.id_alimento AND vu.id_condicion = p.cond;

-- ============================================================
-- PARTE 4 — CONSULTAS DE VERIFICACIÓN
-- ============================================================

-- 1. Confirmar que el catálogo quedó completo (debe dar 30)
-- SELECT COUNT(*) FROM alimento;

-- 2. Ningún alimento puede quedar sin vida útil (debe dar 0 filas)
-- SELECT a.nombre FROM alimento a
-- LEFT JOIN vida_util v ON v.id_alimento = a.id_alimento
-- WHERE v.id_alimento IS NULL;

-- 3. Inventario del usuario ordenado por urgencia
-- SELECT a.nombre, i.cantidad, u.codigo AS unidad,
--        c.nombre AS lugar, e.nombre AS estado,
--        i.fecha_vencimiento_est,
--        (i.fecha_vencimiento_est - CURRENT_DATE) AS dias_restantes
-- FROM   item_inventario i
-- JOIN   alimento a                 ON a.id_alimento  = i.id_alimento
-- JOIN   unidad_medida u            ON u.id_unidad    = i.id_unidad
-- JOIN   condicion_almacenamiento c ON c.id_condicion = i.id_condicion
-- LEFT JOIN estado_madurez e        ON e.id_estado    = i.id_estado_inicial
-- WHERE  i.id_usuario = 1 AND i.situacion = 'activo'
-- ORDER  BY i.fecha_vencimiento_est;

-- 4. Buscar un alimento aunque venga mal escrito en la factura
-- SELECT a.nombre, similarity(al.texto_normalizado, 'platanoo') AS parecido
-- FROM   alias_alimento al
-- JOIN   alimento a ON a.id_alimento = al.id_alimento
-- WHERE  similarity(al.texto_normalizado, 'platanoo') > 0.3
-- ORDER  BY parecido DESC;
