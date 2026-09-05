-- ============================================================
-- FreshTrack — Actualización de vida útil con datos oficiales
-- Fuente: USDA FSIS FoodKeeper (data.gov, licencia CC0)
--
-- Criterio: se toma el valor MÍNIMO del rango publicado. Si FoodKeeper
-- dice que la manzana dura de 4 a 6 semanas refrigerada, se usan 4.
--
-- Condición 1 = Ambiente (columnas Pantry de FoodKeeper)
-- Condición 2 = Refrigerado (columnas Refrigerate de FoodKeeper)
-- ============================================================

BEGIN;

UPDATE vida_util SET dias_estimados = 3,
       fuente = 'USDA FoodKeeper — Bananas'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Banano')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 21,
       fuente = 'USDA FoodKeeper — Apples'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Manzana')
   AND id_condicion = 1;

UPDATE vida_util SET dias_estimados = 28,
       fuente = 'USDA FoodKeeper — Apples'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Manzana')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 10,
       fuente = 'USDA FoodKeeper — Citrus fruit'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Naranja')
   AND id_condicion = 1;

UPDATE vida_util SET dias_estimados = 10,
       fuente = 'USDA FoodKeeper — Citrus fruit'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Naranja')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 10,
       fuente = 'USDA FoodKeeper — Citrus fruit'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Mandarina')
   AND id_condicion = 1;

UPDATE vida_util SET dias_estimados = 10,
       fuente = 'USDA FoodKeeper — Citrus fruit'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Mandarina')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 3,
       fuente = 'USDA FoodKeeper — Papaya, mango, feijoa, passionfruit, casaha melon'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Papaya')
   AND id_condicion = 1;

UPDATE vida_util SET dias_estimados = 7,
       fuente = 'USDA FoodKeeper — Papaya, mango, feijoa, passionfruit, casaha melon'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Papaya')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 5,
       fuente = 'USDA FoodKeeper — Pineapple'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Piña')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 3,
       fuente = 'USDA FoodKeeper — Papaya, mango, feijoa, passionfruit, casaha melon'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Mango')
   AND id_condicion = 1;

UPDATE vida_util SET dias_estimados = 7,
       fuente = 'USDA FoodKeeper — Papaya, mango, feijoa, passionfruit, casaha melon'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Mango')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 2,
       fuente = 'USDA FoodKeeper — Strawberries'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Fresa')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 1,
       fuente = 'USDA FoodKeeper — Grapes'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Uva')
   AND id_condicion = 1;

UPDATE vida_util SET dias_estimados = 7,
       fuente = 'USDA FoodKeeper — Grapes'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Uva')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 3,
       fuente = 'USDA FoodKeeper — Peaches, nectarines, plums, pears, sapote'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Pera')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 3,
       fuente = 'USDA FoodKeeper — Avocados'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Aguacate')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 3,
       fuente = 'USDA FoodKeeper — Papaya, mango, feijoa, passionfruit, casaha melon'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Maracuyá')
   AND id_condicion = 1;

UPDATE vida_util SET dias_estimados = 7,
       fuente = 'USDA FoodKeeper — Papaya, mango, feijoa, passionfruit, casaha melon'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Maracuyá')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 10,
       fuente = 'USDA FoodKeeper — Citrus fruit'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Limón')
   AND id_condicion = 1;

UPDATE vida_util SET dias_estimados = 10,
       fuente = 'USDA FoodKeeper — Citrus fruit'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Limón')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 7,
       fuente = 'USDA FoodKeeper — Tomatoes'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Tomate')
   AND id_condicion = 1;

UPDATE vida_util SET dias_estimados = 4,
       fuente = 'USDA FoodKeeper — Cucumbers'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Pepino')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 4,
       fuente = 'USDA FoodKeeper — Peppers'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Pimentón')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 14,
       fuente = 'USDA FoodKeeper — Carrots, parsnips'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Zanahoria')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 30,
       fuente = 'USDA FoodKeeper — Onions'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Cebolla cabezona')
   AND id_condicion = 1;

UPDATE vida_util SET dias_estimados = 60,
       fuente = 'USDA FoodKeeper — Onions'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Cebolla cabezona')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 30,
       fuente = 'USDA FoodKeeper — Onions'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Cebolla larga')
   AND id_condicion = 1;

UPDATE vida_util SET dias_estimados = 7,
       fuente = 'USDA FoodKeeper — Onions'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Cebolla larga')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 7,
       fuente = 'USDA FoodKeeper — Lettuce'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Lechuga')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 3,
       fuente = 'USDA FoodKeeper — Lettuce'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Espinaca')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 3,
       fuente = 'USDA FoodKeeper — Broccoli and broccoli raab (rapini)'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Brócoli')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 3,
       fuente = 'USDA FoodKeeper — Beans and peas'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Habichuela')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 7,
       fuente = 'USDA FoodKeeper — Cabbage'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Repollo')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 3,
       fuente = 'USDA FoodKeeper — Plantains'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Plátano')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 30,
       fuente = 'USDA FoodKeeper — Potatoes'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Papa')
   AND id_condicion = 1;

UPDATE vida_util SET dias_estimados = 7,
       fuente = 'USDA FoodKeeper — Potatoes'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Papa')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 7,
       fuente = 'USDA FoodKeeper — Yuca/cassava'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Yuca')
   AND id_condicion = 1;

UPDATE vida_util SET dias_estimados = 3,
       fuente = 'USDA FoodKeeper — Yuca/cassava'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Yuca')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 1,
       fuente = 'USDA FoodKeeper — Beets'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Remolacha')
   AND id_condicion = 1;

UPDATE vida_util SET dias_estimados = 7,
       fuente = 'USDA FoodKeeper — Beets'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Remolacha')
   AND id_condicion = 2;

UPDATE vida_util SET dias_estimados = 7,
       fuente = 'USDA FoodKeeper — Cilantro'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Cilantro')
   AND id_condicion = 1;

UPDATE vida_util SET dias_estimados = 14,
       fuente = 'USDA FoodKeeper — Cilantro'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Cilantro')
   AND id_condicion = 2;

-- Arracacha no aparece en FoodKeeper (tubérculo andino que no se
-- consume en Estados Unidos). Se deja el valor estimado y se marca
-- la fuente para que quede documentado en el informe.
UPDATE vida_util SET fuente = 'Estimación propia — no disponible en FoodKeeper'
 WHERE id_alimento = (SELECT id_alimento FROM alimento WHERE nombre = 'Arracacha');

COMMIT;

-- ---- Verificación ----
-- SELECT a.nombre,
--        MAX(CASE WHEN v.id_condicion = 1 THEN v.dias_estimados END) AS ambiente,
--        MAX(CASE WHEN v.id_condicion = 2 THEN v.dias_estimados END) AS nevera,
--        MIN(v.fuente) AS fuente
-- FROM   vida_util v
-- JOIN   alimento a ON a.id_alimento = v.id_alimento
-- GROUP  BY a.nombre
-- ORDER  BY a.nombre;
