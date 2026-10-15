"""Catálogo local de recetas para aprovechar los alimentos del inventario."""

RECETAS = [
    (1, "Batido de banano y fresa", [1, 8], 10, 2, "Licúa el banano y la fresa con agua o leche hasta obtener una mezcla homogénea."),
    (2, "Ensalada tropical", [2, 3, 8, 9], 15, 2, "Corta las frutas, mezcla y sirve fría con unas gotas de limón."),
    (3, "Avena de manzana y canela", [2], 15, 2, "Cocina la manzana en cubos con avena, agua y canela hasta ablandar."),
    (4, "Jugo de naranja y mandarina", [3, 4, 13], 10, 3, "Exprime las frutas, mezcla sus jugos y ajusta con agua al gusto."),
    (5, "Ensalada de papaya y limón", [5, 13], 10, 2, "Corta la papaya y aliña con limón antes de servir."),
    (6, "Salsa de piña y mango", [6, 7, 13], 20, 4, "Pica las frutas, cocina cinco minutos y deja enfriar para acompañar."),
    (7, "Parfait de mango y yogur", [7, 8, 9], 10, 2, "Alterna mango, fresa y yogur en vasos y refrigera."),
    (8, "Limonada de maracuyá", [12, 13], 10, 4, "Extrae la pulpa, mezcla con limón, agua y endulzante."),
    (9, "Ensalada de pera y uva", [9, 10, 20], 15, 2, "Corta la pera, agrega uvas y lechuga, y mezcla con vinagreta."),
    (10, "Guacamole fresco", [11, 14, 18, 13, 30], 15, 4, "Tritura el aguacate y mezcla con tomate, cebolla, limón y cilantro."),
    (11, "Ensalada de aguacate y pepino", [11, 15, 18, 13], 15, 2, "Corta todos los ingredientes y aliña con limón y sal."),
    (12, "Pico de gallo", [14, 18, 30, 13], 15, 4, "Pica tomate, cebolla y cilantro; termina con jugo de limón."),
    (13, "Gazpacho de tomate", [14, 15, 18, 13], 20, 4, "Licúa los vegetales, enfría y sirve con un hilo de aceite."),
    (14, "Salteado de pimentón y zanahoria", [16, 17, 18], 20, 3, "Saltea los vegetales en tiras hasta que estén tiernos pero firmes."),
    (15, "Ensalada crocante", [15, 17, 20, 24], 15, 3, "Corta pepino, zanahoria, lechuga y repollo; mezcla y aliña."),
    (16, "Crema de brócoli", [22, 18, 17, 21], 30, 4, "Cocina los vegetales, licúa con caldo y vuelve a calentar."),
    (17, "Habichuelas con tomate", [23, 14, 18], 25, 3, "Cocina las habichuelas y termina con un guiso de tomate y cebolla."),
    (18, "Repollo salteado", [24, 18, 16, 19], 20, 3, "Corta el repollo y saltéalo con cebolla y pimentón."),
    (19, "Patacones con hogao", [25, 14, 18, 30], 35, 4, "Fríe y aplasta el plátano; acompaña con hogao de tomate y cebolla."),
    (20, "Papas criollas al cilantro", [26, 30, 18], 30, 4, "Cocina las papas y saltéalas con cebolla y cilantro."),
    (21, "Yuca con guacamole", [27, 11, 14, 13], 35, 4, "Hierve la yuca y acompaña con guacamole fresco."),
    (22, "Sopa de arracacha", [28, 17, 18, 30], 40, 4, "Cocina los tubérculos con cebolla, licúa y termina con cilantro."),
    (23, "Ensalada de remolacha", [29, 17, 20, 13], 30, 3, "Cocina la remolacha, corta en cubos y mezcla con zanahoria y limón."),
    (24, "Sancocho de verduras", [26, 27, 28, 17, 18, 30], 50, 6, "Cocina los tubérculos y verduras en caldo hasta que estén suaves."),
    (25, "Sopa de verduras verdes", [15, 22, 23, 20], 30, 4, "Cocina y licúa las verduras; ajusta la textura con caldo."),
    (26, "Bowl de frutas con maracuyá", [1, 5, 7, 12, 13], 15, 2, "Corta las frutas y cubre con pulpa de maracuyá y limón."),
    (27, "Ensalada de repollo y manzana", [2, 20, 24, 13], 15, 3, "Corta fino, mezcla y aliña con limón."),
    (28, "Pimentones rellenos de verduras", [16, 17, 22, 18], 40, 4, "Asa los pimentones, rellena con verduras salteadas y gratina."),
    (29, "Tostadas de aguacate y tomate", [11, 14, 13, 30], 15, 2, "Aplasta el aguacate sobre pan y cubre con tomate, limón y cilantro."),
    (30, "Salpicón de frutas", [1, 3, 4, 6, 7, 13], 20, 6, "Pica las frutas, mezcla y refrigera antes de servir."),
]


def obtener_catalogo():
    return [
        {
            "id_receta": rid,
            "titulo": titulo,
            "ingredientes": ingredientes,
            "minutos_prep": minutos,
            "porciones": porciones,
            "pasos": pasos,
        }
        for rid, titulo, ingredientes, minutos, porciones, pasos in RECETAS
    ]
