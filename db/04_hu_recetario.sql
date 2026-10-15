-- FreshTrack — HU-10/HU-11 · Catálogo y recomendaciones de recetas
-- Ejecutar después de 01_esquema_y_catalogo.sql.

INSERT INTO receta (id_externo, titulo, minutos_prep, porciones)
VALUES
 ('freshtrack-01', 'Batido de banano y fresa', 10, 2),
 ('freshtrack-02', 'Ensalada tropical', 15, 2),
 ('freshtrack-03', 'Avena de manzana y canela', 15, 2),
 ('freshtrack-04', 'Jugo de naranja y mandarina', 10, 3),
 ('freshtrack-05', 'Ensalada de papaya y limón', 10, 2),
 ('freshtrack-06', 'Salsa de piña y mango', 20, 4),
 ('freshtrack-07', 'Parfait de mango y yogur', 10, 2),
 ('freshtrack-08', 'Limonada de maracuyá', 10, 4),
 ('freshtrack-09', 'Ensalada de pera y uva', 15, 2),
 ('freshtrack-10', 'Guacamole fresco', 15, 4),
 ('freshtrack-11', 'Ensalada de aguacate y pepino', 15, 2),
 ('freshtrack-12', 'Pico de gallo', 15, 4),
 ('freshtrack-13', 'Gazpacho de tomate', 20, 4),
 ('freshtrack-14', 'Salteado de pimentón y zanahoria', 20, 3),
 ('freshtrack-15', 'Ensalada crocante', 15, 3),
 ('freshtrack-16', 'Crema de brócoli', 30, 4),
 ('freshtrack-17', 'Habichuelas con tomate', 25, 3),
 ('freshtrack-18', 'Repollo salteado', 20, 3),
 ('freshtrack-19', 'Patacones con hogao', 35, 4),
 ('freshtrack-20', 'Papas criollas al cilantro', 30, 4),
 ('freshtrack-21', 'Yuca con guacamole', 35, 4),
 ('freshtrack-22', 'Sopa de arracacha', 40, 4),
 ('freshtrack-23', 'Ensalada de remolacha', 30, 3),
 ('freshtrack-24', 'Sancocho de verduras', 50, 6),
 ('freshtrack-25', 'Sopa de verduras verdes', 30, 4),
 ('freshtrack-26', 'Bowl de frutas con maracuyá', 15, 2),
 ('freshtrack-27', 'Ensalada de repollo y manzana', 15, 3),
 ('freshtrack-28', 'Pimentones rellenos de verduras', 40, 4),
 ('freshtrack-29', 'Tostadas de aguacate y tomate', 15, 2),
 ('freshtrack-30', 'Salpicón de frutas', 20, 6)
ON CONFLICT (id_externo) DO NOTHING;

INSERT INTO receta_ingrediente (id_receta, id_alimento)
SELECT r.id_receta, v.id_alimento
FROM receta r
JOIN (VALUES
 ('freshtrack-01', 1), ('freshtrack-01', 8),
 ('freshtrack-02', 2), ('freshtrack-02', 3), ('freshtrack-02', 8), ('freshtrack-02', 9),
 ('freshtrack-03', 2), ('freshtrack-04', 3), ('freshtrack-04', 4), ('freshtrack-04', 13),
 ('freshtrack-05', 5), ('freshtrack-05', 13), ('freshtrack-06', 6), ('freshtrack-06', 7), ('freshtrack-06', 13),
 ('freshtrack-07', 7), ('freshtrack-07', 8), ('freshtrack-07', 9), ('freshtrack-08', 12), ('freshtrack-08', 13),
 ('freshtrack-09', 9), ('freshtrack-09', 10), ('freshtrack-09', 20),
 ('freshtrack-10', 11), ('freshtrack-10', 14), ('freshtrack-10', 18), ('freshtrack-10', 13), ('freshtrack-10', 30),
 ('freshtrack-11', 11), ('freshtrack-11', 15), ('freshtrack-11', 18), ('freshtrack-11', 13),
 ('freshtrack-12', 14), ('freshtrack-12', 18), ('freshtrack-12', 30), ('freshtrack-12', 13),
 ('freshtrack-13', 14), ('freshtrack-13', 15), ('freshtrack-13', 18), ('freshtrack-13', 13),
 ('freshtrack-14', 16), ('freshtrack-14', 17), ('freshtrack-14', 18),
 ('freshtrack-15', 15), ('freshtrack-15', 17), ('freshtrack-15', 20), ('freshtrack-15', 24),
 ('freshtrack-16', 22), ('freshtrack-16', 18), ('freshtrack-16', 17), ('freshtrack-16', 21),
 ('freshtrack-17', 23), ('freshtrack-17', 14), ('freshtrack-17', 18),  ('freshtrack-18', 24), ('freshtrack-18', 18), ('freshtrack-18', 16), ('freshtrack-18', 19),
 ('freshtrack-19', 25), ('freshtrack-19', 14), ('freshtrack-19', 18), ('freshtrack-19', 30),
 ('freshtrack-20', 26), ('freshtrack-20', 30), ('freshtrack-20', 18),
 ('freshtrack-21', 27), ('freshtrack-21', 11), ('freshtrack-21', 14), ('freshtrack-21', 13),
 ('freshtrack-22', 28), ('freshtrack-22', 17), ('freshtrack-22', 18), ('freshtrack-22', 30),
 ('freshtrack-23', 29), ('freshtrack-23', 17), ('freshtrack-23', 20), ('freshtrack-23', 13),
 ('freshtrack-24', 26), ('freshtrack-24', 27), ('freshtrack-24', 28), ('freshtrack-24', 17), ('freshtrack-24', 18), ('freshtrack-24', 30),
 ('freshtrack-25', 15), ('freshtrack-25', 22), ('freshtrack-25', 23), ('freshtrack-25', 20),
 ('freshtrack-26', 1), ('freshtrack-26', 5), ('freshtrack-26', 7), ('freshtrack-26', 12), ('freshtrack-26', 13),
 ('freshtrack-27', 2), ('freshtrack-27', 20), ('freshtrack-27', 24), ('freshtrack-27', 13),
 ('freshtrack-28', 16), ('freshtrack-28', 17), ('freshtrack-28', 22), ('freshtrack-28', 18),
 ('freshtrack-29', 11), ('freshtrack-29', 14), ('freshtrack-29', 13), ('freshtrack-29', 30),
 ('freshtrack-30', 1), ('freshtrack-30', 3), ('freshtrack-30', 4), ('freshtrack-30', 6), ('freshtrack-30', 7), ('freshtrack-30', 13)
) AS v(id_externo, id_alimento) ON TRUE
WHERE r.id_externo = v.id_externo
ON CONFLICT DO NOTHING;
