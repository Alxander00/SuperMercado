-- ============================================================
-- CATEGORÍAS Y PRODUCTOS PARA MERCADO FRESCO EL SALVADOR
-- ============================================================

-- 1. CATEGORÍAS
INSERT INTO categorias (nombre) VALUES
    ('Frutas y Verduras'),
    ('Carnes y Embutidos'),
    ('Lácteos y Huevos'),
    ('Panadería y Tortillería'),
    ('Abarrotes'),
    ('Bebidas'),
    ('Limpieza y Hogar'),
    ('Higiene Personal');

-- 2. PRODUCTOS (usando el nombre de categoría para buscar el id)
INSERT INTO productos (nombre, precio_base, id_categoria, stock) VALUES

-- Frutas y Verduras
('Tomate (lb)',          0.75, (SELECT id_categoria FROM categorias WHERE nombre='Frutas y Verduras'), 200),
('Cebolla blanca (lb)', 0.60, (SELECT id_categoria FROM categorias WHERE nombre='Frutas y Verduras'), 200),
('Papa (lb)',            0.55, (SELECT id_categoria FROM categorias WHERE nombre='Frutas y Verduras'), 300),
('Zanahoria (lb)',       0.50, (SELECT id_categoria FROM categorias WHERE nombre='Frutas y Verduras'), 250),
('Repollo (unidad)',     1.25, (SELECT id_categoria FROM categorias WHERE nombre='Frutas y Verduras'), 100),
('Chile verde (lb)',     1.00, (SELECT id_categoria FROM categorias WHERE nombre='Frutas y Verduras'), 150),
('Plátano maduro (lb)', 0.45, (SELECT id_categoria FROM categorias WHERE nombre='Frutas y Verduras'), 200),
('Aguacate (unidad)',    0.80, (SELECT id_categoria FROM categorias WHERE nombre='Frutas y Verduras'), 120),
('Limón (bolsa 6)',      0.50, (SELECT id_categoria FROM categorias WHERE nombre='Frutas y Verduras'), 180),
('Güisquil (unidad)',    0.40, (SELECT id_categoria FROM categorias WHERE nombre='Frutas y Verduras'), 150),

-- Carnes y Embutidos
('Pollo entero (lb)',            2.50, (SELECT id_categoria FROM categorias WHERE nombre='Carnes y Embutidos'), 100),
('Carne molida de res (lb)',     3.25, (SELECT id_categoria FROM categorias WHERE nombre='Carnes y Embutidos'), 100),
('Chuleta de cerdo (lb)',        2.80, (SELECT id_categoria FROM categorias WHERE nombre='Carnes y Embutidos'), 80),
('Chorizo salvadoreño (lb)',     3.00, (SELECT id_categoria FROM categorias WHERE nombre='Carnes y Embutidos'), 90),
('Mortadela (lb)',               2.20, (SELECT id_categoria FROM categorias WHERE nombre='Carnes y Embutidos'), 80),
('Salchicha (paquete)',          1.75, (SELECT id_categoria FROM categorias WHERE nombre='Carnes y Embutidos'), 120),
('Costilla de res (lb)',         3.50, (SELECT id_categoria FROM categorias WHERE nombre='Carnes y Embutidos'), 70),
('Hígado de res (lb)',           2.00, (SELECT id_categoria FROM categorias WHERE nombre='Carnes y Embutidos'), 60),

-- Lácteos y Huevos
('Huevos (cartón 30)',   4.50, (SELECT id_categoria FROM categorias WHERE nombre='Lácteos y Huevos'), 150),
('Huevos (cartón 12)',   1.90, (SELECT id_categoria FROM categorias WHERE nombre='Lácteos y Huevos'), 200),
('Leche entera (litro)', 1.10, (SELECT id_categoria FROM categorias WHERE nombre='Lácteos y Huevos'), 200),
('Queso duro (lb)',      3.75, (SELECT id_categoria FROM categorias WHERE nombre='Lácteos y Huevos'), 100),
('Queso fresco (lb)',    3.25, (SELECT id_categoria FROM categorias WHERE nombre='Lácteos y Huevos'), 100),
('Crema (bolsa 500ml)',  1.50, (SELECT id_categoria FROM categorias WHERE nombre='Lácteos y Huevos'), 120),
('Mantequilla (200g)',   1.80, (SELECT id_categoria FROM categorias WHERE nombre='Lácteos y Huevos'), 100),
('Yogur natural (500ml)',1.60, (SELECT id_categoria FROM categorias WHERE nombre='Lácteos y Huevos'), 90),

-- Panadería y Tortillería
('Tortillas maíz (paquete 30)', 1.25, (SELECT id_categoria FROM categorias WHERE nombre='Panadería y Tortillería'), 200),
('Pan francés (unidad)',         0.15, (SELECT id_categoria FROM categorias WHERE nombre='Panadería y Tortillería'), 500),
('Pan molde blanco',             1.50, (SELECT id_categoria FROM categorias WHERE nombre='Panadería y Tortillería'), 150),
('Pan dulce (lb)',               1.20, (SELECT id_categoria FROM categorias WHERE nombre='Panadería y Tortillería'), 200),
('Pupusas (unidad)',             0.50, (SELECT id_categoria FROM categorias WHERE nombre='Panadería y Tortillería'), 300),

-- Abarrotes
('Arroz blanco (lb)',            0.65, (SELECT id_categoria FROM categorias WHERE nombre='Abarrotes'), 400),
('Frijoles rojos (lb)',          0.90, (SELECT id_categoria FROM categorias WHERE nombre='Abarrotes'), 400),
('Aceite vegetal (litro)',       2.50, (SELECT id_categoria FROM categorias WHERE nombre='Abarrotes'), 200),
('Azúcar (lb)',                  0.55, (SELECT id_categoria FROM categorias WHERE nombre='Abarrotes'), 400),
('Sal (lb)',                     0.30, (SELECT id_categoria FROM categorias WHERE nombre='Abarrotes'), 300),
('Harina de maíz (lb)',         0.60, (SELECT id_categoria FROM categorias WHERE nombre='Abarrotes'), 300),
('Pasta espagueti (500g)',       1.10, (SELECT id_categoria FROM categorias WHERE nombre='Abarrotes'), 200),
('Consomé de pollo (caja)',      1.25, (SELECT id_categoria FROM categorias WHERE nombre='Abarrotes'), 250),
('Salsa de tomate (lata)',       0.95, (SELECT id_categoria FROM categorias WHERE nombre='Abarrotes'), 200),
('Atún en lata',                 1.50, (SELECT id_categoria FROM categorias WHERE nombre='Abarrotes'), 250),
('Frijoles molidos (lata)',      1.20, (SELECT id_categoria FROM categorias WHERE nombre='Abarrotes'), 200),
('Mayonesa (frasco 400g)',       2.25, (SELECT id_categoria FROM categorias WHERE nombre='Abarrotes'), 150),

-- Bebidas
('Agua purificada (500ml)',      0.50, (SELECT id_categoria FROM categorias WHERE nombre='Bebidas'), 400),
('Agua purificada (1.5L)',       0.90, (SELECT id_categoria FROM categorias WHERE nombre='Bebidas'), 300),
('Refresco cola (2L)',           1.50, (SELECT id_categoria FROM categorias WHERE nombre='Bebidas'), 200),
('Refresco naranja (2L)',        1.50, (SELECT id_categoria FROM categorias WHERE nombre='Bebidas'), 200),
('Jugo de naranja (1L)',         1.75, (SELECT id_categoria FROM categorias WHERE nombre='Bebidas'), 150),
('Café molido (200g)',           2.50, (SELECT id_categoria FROM categorias WHERE nombre='Bebidas'), 150),
('Té en bolsitas (caja 20)',     1.20, (SELECT id_categoria FROM categorias WHERE nombre='Bebidas'), 120),

-- Limpieza y Hogar
('Detergente en polvo (1kg)',    3.50, (SELECT id_categoria FROM categorias WHERE nombre='Limpieza y Hogar'), 150),
('Jabón de lavar (pastilla)',    0.75, (SELECT id_categoria FROM categorias WHERE nombre='Limpieza y Hogar'), 300),
('Cloro (litro)',                1.25, (SELECT id_categoria FROM categorias WHERE nombre='Limpieza y Hogar'), 200),
('Escoba (unidad)',              3.00, (SELECT id_categoria FROM categorias WHERE nombre='Limpieza y Hogar'), 80),
('Trapeador (unidad)',           4.50, (SELECT id_categoria FROM categorias WHERE nombre='Limpieza y Hogar'), 60),
('Bolsas basura (paquete)',      1.75, (SELECT id_categoria FROM categorias WHERE nombre='Limpieza y Hogar'), 200),
('Papel higiénico (4 rollos)',   2.25, (SELECT id_categoria FROM categorias WHERE nombre='Limpieza y Hogar'), 250),

-- Higiene Personal
('Jabón de baño (pastilla)',     0.90, (SELECT id_categoria FROM categorias WHERE nombre='Higiene Personal'), 300),
('Shampoo (400ml)',              3.25, (SELECT id_categoria FROM categorias WHERE nombre='Higiene Personal'), 150),
('Pasta dental (100ml)',         1.50, (SELECT id_categoria FROM categorias WHERE nombre='Higiene Personal'), 200),
('Cepillo dental (unidad)',      1.25, (SELECT id_categoria FROM categorias WHERE nombre='Higiene Personal'), 200),
('Desodorante (roll-on)',        2.75, (SELECT id_categoria FROM categorias WHERE nombre='Higiene Personal'), 150),
('Toallas sanitarias (paquete)', 2.50, (SELECT id_categoria FROM categorias WHERE nombre='Higiene Personal'), 150),
('Pañales (paquete 20)',         6.50, (SELECT id_categoria FROM categorias WHERE nombre='Higiene Personal'), 100);

-- Verificación
SELECT c.nombre AS categoria, COUNT(p.id_producto) AS productos
FROM categorias c
LEFT JOIN productos p ON c.id_categoria = p.id_categoria
GROUP BY c.nombre
ORDER BY c.nombre;
