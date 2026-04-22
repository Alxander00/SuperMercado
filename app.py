import io
import base64
import psycopg2
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, send_file
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors

app = Flask(__name__)
app.secret_key = 'super_secreto_123'

DB_CONFIG = {
    "host": "localhost",
    "database": "supermercado",
    "user": "postgres",
    "password": "123" 
}

# Esto es para que el HTML pueda usar max() y min() en la paginación
@app.context_processor
def utility_processor():
    return dict(max=max, min=min)

# --- FUNCIÓN MAESTRA PARA GENERAR PDF ---
def generar_pdf_documento(titulo, encabezados, filas, nombre_archivo, mostrar_total=False):
    buffer = io.BytesIO()
    c = canvas.Canvas(buffer, pagesize=letter)
    width, height = letter

    # 1. Encabezado Estilizado
    c.setFillColor(colors.HexColor("#16a34a"))
    c.rect(0, height - 80, width, 80, fill=1, stroke=0)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 20)
    c.drawString(50, height - 50, "MERCADO FRESCO EL SALVADOR")
    
    c.setFillColor(colors.black)
    c.setFont("Helvetica-Bold", 14)
    c.drawString(50, height - 110, titulo)
    c.setFont("Helvetica", 10)
    c.drawString(50, height - 125, f"Fecha de emisión: {pd.Timestamp.now().strftime('%d/%m/%Y %H:%M')}")

    # 2. Tabla de datos
    y = height - 170
    c.setFont("Helvetica-Bold", 11)
    
    x_positions = [50, 150, 320, 470]
    for i, header in enumerate(encabezados):
        if i < len(x_positions):
            c.drawString(x_positions[i], y, str(header))
    
    y -= 10
    c.setLineWidth(1)
    c.line(50, y, width - 50, y)
    y -= 25
    
    c.setFont("Helvetica", 10)
    suma_total = 0 

    for fila in filas:
        for i, item in enumerate(fila):
            if i < len(x_positions):
                c.drawString(x_positions[i], y, str(item))
        
        try:
            suma_total += float(fila[-1])
        except:
            pass

        y -= 20
        if y < 100:
            c.showPage()
            y = height - 50
            c.setFont("Helvetica", 10)

    if mostrar_total:
        y -= 20
        c.setLineWidth(2)
        c.setStrokeColor(colors.HexColor("#16a34a"))
        c.line(300, y+15, width - 50, y+15)
        
        c.setFont("Helvetica-Bold", 12)
        c.drawString(320, y, "TOTAL GENERAL:")
        c.setFillColor(colors.HexColor("#f97316"))
        c.drawString(470, y, f"${suma_total:,.2f}")
        
        c.setFillColor(colors.lightgrey)
        c.setFont("Helvetica-Oblique", 8)
        c.drawCentredString(width/2, 30, "Este documento es un reporte generado automáticamente por el sistema de gestión.")

    c.save()
    buffer.seek(0)
    return send_file(buffer, as_attachment=True, download_name=nombre_archivo, mimetype='application/pdf')

# ==========================================
# 1. RUTAS DEL CLIENTE (PORTADA Y TIENDA)
# ==========================================
@app.route('/')
def portada():
    nombre = session.get('nombre', 'Invitado')
    esta_logueado = 'id_usuario' in session 
    return render_template('portada.html', nombre_usuario=nombre, logueado=esta_logueado)

@app.route('/tienda')
def catalogo_cliente():
    conexion = psycopg2.connect(**DB_CONFIG)
    cursor = conexion.cursor()
    cursor.execute("SELECT nombre FROM categorias ORDER BY nombre ASC")
    categorias = cursor.fetchall()
    
    cursor.execute("""
        SELECT p.id_producto, p.nombre, p.precio_base, c.nombre, p.stock 
        FROM productos p
        JOIN categorias c ON p.id_categoria = c.id_categoria
        ORDER BY p.id_producto ASC
    """)
    productos = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    nombre = session.get('nombre', 'Invitado')
    esta_logueado = 'id_usuario' in session 
    return render_template('tienda.html', productos=productos, categorias=categorias, nombre_usuario=nombre, logueado=esta_logueado)

# ==========================================
# 2. RUTAS DE AUTENTICACIÓN
# ==========================================
@app.route('/registro', methods=['GET', 'POST'])
def registro():
    if request.method == 'POST':
        nombre = request.form['nombre']
        correo = request.form['correo']
        password = request.form['password']
        conexion = psycopg2.connect(**DB_CONFIG)
        cursor = conexion.cursor()
        try:
            cursor.execute("INSERT INTO usuarios (nombre, correo, password, rol) VALUES (%s, %s, %s, 'cliente')", (nombre, correo, password))
            conexion.commit()
            return redirect(url_for('login'))
        except Exception as e:
            conexion.rollback()
            return f"Error: {e}"
        finally:
            cursor.close()
            conexion.close()
    return render_template('registro.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        correo = request.form['correo']
        password = request.form['password']
        conexion = psycopg2.connect(**DB_CONFIG)
        cursor = conexion.cursor()
        cursor.execute("SELECT id_usuario, nombre, rol FROM usuarios WHERE correo = %s AND password = %s", (correo, password))
        usuario = cursor.fetchone()
        cursor.close()
        conexion.close()
        
        if usuario:
            session['id_usuario'] = usuario[0]
            session['nombre'] = usuario[1]
            session['rol'] = usuario[2]
            return redirect(url_for('index' if usuario[2] == 'admin' else 'portada'))
        else:
            return "Credenciales incorrectas. <a href='/login'>Intentar de nuevo</a>"
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('portada'))

# ==========================================
# 3. RUTAS DEL ADMINISTRADOR
# ==========================================
@app.route('/admin')
def index():
    if 'id_usuario' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
    return render_template('index.html')

@app.route('/admin/reporte/<periodo>')
def reporte_ventas_pdf(periodo):
    if session.get('rol') != 'admin': return redirect('/')
    intervalos = {"dia": "1 day", "semana": "7 days", "mes": "1 month"}
    intervalo = intervalos.get(periodo, "1 day")
    conexion = psycopg2.connect(**DB_CONFIG)
    cursor = conexion.cursor()
    cursor.execute(f"""
        SELECT c.nombre as categoria, SUM(d.cantidad) as unidades_vendidas, SUM(d.subtotal) as total_categoria
        FROM ventas v
        JOIN detalle_ventas d ON v.id_venta = d.id_venta
        JOIN productos p ON d.id_producto = p.id_producto
        JOIN categorias c ON p.id_categoria = c.id_categoria
        WHERE v.fecha >= CURRENT_DATE - INTERVAL '{intervalo}'
        GROUP BY c.nombre ORDER BY total_categoria DESC
    """)
    resumen_categorias = cursor.fetchall()
    cursor.close(); conexion.close()
    headers = ["Categoría", "Unidades Vendidas", "Total Ingresos ($)"]
    return generar_pdf_documento(f"RESUMEN DE VENTAS: {periodo.upper()}", headers, resumen_categorias, f"resumen_{periodo}.pdf", mostrar_total=True)

@app.route('/productos', methods=['GET', 'POST'])
def vista_productos():
    if session.get('rol') != 'admin': return redirect('/')
    conexion = psycopg2.connect(**DB_CONFIG); cursor = conexion.cursor()
    if request.method == 'POST':
        cursor.execute("INSERT INTO productos (nombre, precio_base, id_categoria, stock) VALUES (%s, %s, %s, %s)", 
                       (request.form['nombre'], request.form['precio_base'], request.form['id_categoria'], request.form['stock']))
        conexion.commit()
        return redirect(url_for('vista_productos'))
    cursor.execute("SELECT p.id_producto, p.nombre, p.precio_base, c.nombre, p.stock FROM productos p JOIN categorias c ON p.id_categoria = c.id_categoria ORDER BY p.id_producto DESC")
    productos = cursor.fetchall()
    cursor.execute("SELECT id_categoria, nombre FROM categorias")
    categorias = cursor.fetchall()
    cursor.close(); conexion.close()
    return render_template('productos.html', productos=productos, categorias=categorias)

@app.route('/ventas')
def vista_ventas():
    if 'id_usuario' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page
    conexion = psycopg2.connect(**DB_CONFIG); cursor = conexion.cursor()
    cursor.execute("SELECT COUNT(*) FROM ventas")
    total_ventas = cursor.fetchone()[0]
    total_pages = (total_ventas + per_page - 1) // per_page
    cursor.execute("""
        SELECT v.id_venta, u.nombre, v.fecha::date, v.total 
        FROM ventas v JOIN usuarios u ON v.id_usuario = u.id_usuario 
        ORDER BY v.id_venta DESC LIMIT %s OFFSET %s
    """, (per_page, offset))
    ventas = cursor.fetchall()
    cursor.close(); conexion.close()
    return render_template('ventas.html', ventas=ventas, page=page, total_pages=total_pages, total_total=total_ventas)

# ==========================================
# 4. RUTAS DEL CLIENTE (HISTORIAL Y TICKET)
# ==========================================
@app.route('/cliente/historial')
def historial_cliente():
    if 'id_usuario' not in session: return redirect(url_for('login'))
    conexion = psycopg2.connect(**DB_CONFIG); cursor = conexion.cursor()
    cursor.execute("SELECT id_venta, fecha::date, total FROM ventas WHERE id_usuario = %s ORDER BY fecha DESC", (session['id_usuario'],))
    pedidos = cursor.fetchall()
    cursor.close(); conexion.close()
    return render_template('historial.html', pedidos=pedidos, nombre_usuario=session['nombre'])

@app.route('/cliente/descargar_ticket/<int:id_venta>')
def descargar_ticket(id_venta):
    if 'id_usuario' not in session: return redirect(url_for('login'))
    conexion = psycopg2.connect(**DB_CONFIG); cursor = conexion.cursor()
    cursor.execute("""
        SELECT p.nombre, d.cantidad, d.precio_unitario, d.subtotal 
        FROM detalle_ventas d JOIN productos p ON d.id_producto = p.id_producto 
        WHERE d.id_venta = %s
    """, (id_venta,))
    detalles = cursor.fetchall()
    cursor.close(); conexion.close()
    headers = ["Producto", "Cant.", "Precio U.", "Subtotal"]
    return generar_pdf_documento(f"TICKET DE COMPRA #{id_venta}", headers, detalles, f"ticket_{id_venta}.pdf")

# ==========================================
# 5. RUTAS API (DATOS Y GRÁFICOS)
# ==========================================
@app.route('/api/resumen_ventas')
def resumen_ventas():
    try:
        conexion = psycopg2.connect(**DB_CONFIG); cursor = conexion.cursor()
        cursor.execute("SELECT COUNT(*) as total_filas, SUM(total) as gran_total, AVG(total) as precio_promedio FROM ventas")
        res = cursor.fetchone()
        cursor.close(); conexion.close()
        return jsonify({'mensaje': 'Éxito', 'datos': {
            'total_registros': res[0], 
            'ingresos_totales': float(res[1]) if res[1] else 0, 
            'precio_promedio': round(float(res[2]), 2) if res[2] else 0
        }})
    except Exception as e:
        return jsonify({'mensaje': 'Error', 'error': str(e)})

@app.route('/api/comprar', methods=['POST'])
def procesar_compra():
    if 'id_usuario' not in session: return jsonify({'mensaje': 'Error', 'error': 'Inicia sesión'})
    carrito = request.get_json()
    if not carrito: return jsonify({'mensaje': 'Error', 'error': 'Carrito vacío'})
    try:
        total_v = sum(item['subtotal'] for item in carrito)
        conexion = psycopg2.connect(**DB_CONFIG); cursor = conexion.cursor()
        cursor.execute("INSERT INTO ventas (cliente, id_usuario, total) VALUES (%s, %s, %s) RETURNING id_venta", 
                       (session['nombre'], session['id_usuario'], total_v))
        id_venta = cursor.fetchone()[0]
        for item in carrito:
            cursor.execute("INSERT INTO detalle_ventas (id_venta, id_producto, cantidad, precio_unitario, subtotal) VALUES (%s, %s, %s, %s, %s)",
                (id_venta, item['id'], item['cantidad'], item['precio'], item['subtotal']))
            cursor.execute("UPDATE productos SET stock = stock - %s WHERE id_producto = %s", (item['cantidad'], item['id']))
        conexion.commit()
        cursor.close(); conexion.close()
        return jsonify({'mensaje': 'Éxito', 'id_venta': id_venta})
    except Exception as e:
        return jsonify({'mensaje': 'Error', 'error': str(e)})

@app.route('/api/grafico_tendencias')
def grafico_tendencias():
    tipo = request.args.get('tipo', 'barras')
    try:
        conexion = psycopg2.connect(**DB_CONFIG); cursor = conexion.cursor()
        cursor.execute("""
            SELECT c.nombre as categoria, SUM(d.subtotal) as total_ventas
            FROM detalle_ventas d JOIN productos p ON d.id_producto = p.id_producto 
            JOIN categorias c ON p.id_categoria = c.id_categoria GROUP BY c.nombre ORDER BY total_ventas DESC
        """)
        datos = cursor.fetchall()
        df = pd.DataFrame(datos, columns=['categoria', 'total_ventas'])
        cursor.close(); conexion.close()
        plt.rcParams['font.family'] = 'sans-serif'
        fig, ax = plt.subplots(figsize=(8, 4.5))
        colores = ['#16a34a', '#22c55e', '#4ade80', '#f97316', '#fb923c']
        if tipo == 'pastel':
            ax.pie(df['total_ventas'], labels=df['categoria'], autopct='%1.1f%%', colors=colores, startangle=90)
        else:
            ax.bar(df['categoria'], df['total_ventas'], color=colores[:len(df)])
            ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('${x:,.0f}'))
        plt.tight_layout()
        img = io.BytesIO(); plt.savefig(img, format='png', transparent=True); img.seek(0); plt.close()
        return jsonify({'mensaje': 'Éxito', 'imagen': base64.b64encode(img.getvalue()).decode('utf8')})
    except Exception as e:
        return jsonify({'mensaje': 'Error', 'error': str(e)})

if __name__ == '__main__':
    app.run(debug=True, port=5000)