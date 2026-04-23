import psycopg2
import random
from datetime import datetime, timedelta

DB_CONFIG = {
    "host": "localhost",
    "database": "supermercado",
    "user": "postgres",
    "password": "1234567890"
}

def poblar():
    try:
        conn = psycopg2.connect(**DB_CONFIG)
        cur = conn.cursor()
        
        # Primero limpiamos para no duplicar si lo corres de nuevo
        cur.execute("TRUNCATE detalle_ventas, ventas, productos, categorias RESTART IDENTITY CASCADE")
        
        # Categorías y Productos
        cats = ['Lácteos', 'Carnes', 'Frutas', 'Limpieza', 'Bebidas']
        for c in cats:
            cur.execute("INSERT INTO categorias (nombre) VALUES (%s)", (c,))
            
        cur.execute("INSERT INTO productos (nombre, precio_base, id_categoria) VALUES ('Leche', 1.50, 1), ('Carne', 7.00, 2), ('Manzana', 0.50, 3), ('Jabón', 1.20, 4), ('Soda', 1.50, 5)")
        
        # Ventas Cabecera
        for i in range(1, 5001):
            cur.execute("INSERT INTO ventas (cliente) VALUES (%s)", (f"Cliente {i}",))
            
        # Detalles (Los 20,000 registros)
        detalles = []
        for _ in range(20000):
            id_v = random.randint(1, 5000)
            id_p = random.randint(1, 5)
            cant = random.randint(1, 10)
            pu = random.uniform(0.5, 10.0)
            detalles.append((id_v, id_p, cant, pu, cant * pu))
            
        cur.executemany("INSERT INTO detalle_ventas (id_venta, id_producto, cantidad, precio_unitario, subtotal) VALUES (%s,%s,%s,%s,%s)", detalles)
        
        conn.commit()
        print("¡20,000 registros insertados!")
        cur.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    poblar()