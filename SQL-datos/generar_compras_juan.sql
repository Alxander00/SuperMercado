-- ============================================================
-- GENERADOR DE 20,000 COMPRAS REALES PARA JUAN PÉREZ
-- Versión corregida: valida productos antes de insertar
-- ============================================================

DO $$
DECLARE
    i               INT;
    v_id_venta      INT;
    v_id_usuario    INT;
    v_num_items     INT;
    j               INT;
    v_id_producto   INT;
    v_precio        DECIMAL(10,2);
    v_cantidad      INT;
    v_subtotal      DECIMAL(10,2);
    v_total         DECIMAL(10,2);
    v_fecha         TIMESTAMP;
    v_total_prods   INT;
BEGIN
    -- 1. Verificar que existen productos
    SELECT COUNT(*) INTO v_total_prods FROM productos;
    IF v_total_prods = 0 THEN
        RAISE EXCEPTION 'La tabla productos está vacía. Agrega productos antes de correr este script.';
    END IF;

    -- 2. Obtener el id de Juan Pérez
    SELECT id_usuario INTO v_id_usuario
    FROM usuarios
    WHERE correo = 'juan@gmail.com'
    LIMIT 1;

    IF v_id_usuario IS NULL THEN
        RAISE EXCEPTION 'No se encontró el usuario juan@gmail.com';
    END IF;

    RAISE NOTICE 'Generando compras para id_usuario=%, con % productos disponibles...', v_id_usuario, v_total_prods;

    FOR i IN 1..20000 LOOP

        -- Fecha aleatoria dentro del último año
        v_fecha := NOW() - (RANDOM() * INTERVAL '365 days');

        -- Número de productos por compra: entre 1 y 5
        v_num_items := (RANDOM() * 4 + 1)::INT;
        v_total := 0;

        -- Insertar cabecera (total se actualiza al final)
        INSERT INTO ventas (cliente, id_usuario, total, fecha)
        VALUES ('Juan Perez', v_id_usuario, 0, v_fecha)
        RETURNING id_venta INTO v_id_venta;

        FOR j IN 1..v_num_items LOOP

            -- Obtener producto con precio válido (no nulo)
            SELECT id_producto, precio_base
            INTO v_id_producto, v_precio
            FROM productos
            WHERE precio_base IS NOT NULL
            ORDER BY RANDOM()
            LIMIT 1;

            -- Skip si por alguna razón no encontró producto
            CONTINUE WHEN v_id_producto IS NULL OR v_precio IS NULL;

            v_cantidad := (RANDOM() * 4 + 1)::INT;
            v_subtotal := v_precio * v_cantidad;
            v_total    := v_total + v_subtotal;

            INSERT INTO detalle_ventas
                (id_venta, id_producto, cantidad, precio_unitario, subtotal)
            VALUES
                (v_id_venta, v_id_producto, v_cantidad, v_precio, v_subtotal);

        END LOOP;

        -- Si la venta quedó sin items (todos los productos eran NULL), eliminarla
        IF v_total = 0 THEN
            DELETE FROM ventas WHERE id_venta = v_id_venta;
            CONTINUE;
        END IF;

        -- Actualizar el total real
        UPDATE ventas SET total = v_total WHERE id_venta = v_id_venta;

    END LOOP;

    RAISE NOTICE '¡Listo! Compras generadas para id_usuario=%', v_id_usuario;
END $$;

-- ============================================================
-- Verificación: resumen de las compras de Juan
-- ============================================================
SELECT
    COUNT(DISTINCT v.id_venta)              AS total_ventas,
    COUNT(d.id_detalle)                     AS total_items,
    ROUND(AVG(v.total)::NUMERIC, 2)         AS ticket_promedio,
    ROUND(MIN(v.total)::NUMERIC, 2)         AS ticket_minimo,
    ROUND(MAX(v.total)::NUMERIC, 2)         AS ticket_maximo
FROM ventas v
JOIN detalle_ventas d ON v.id_venta = d.id_venta
WHERE v.id_usuario = (SELECT id_usuario FROM usuarios WHERE correo = 'juan@gmail.com');
