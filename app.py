import io
import base64
import psycopg2
import pandas as pd
import matplotlib
matplotlib.use('Agg')
import matplotlib.pyplot as plt
import matplotlib.ticker as ticker
from flask import Flask, render_template, jsonify, request, redirect, url_for, session, send_file, flash
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
                # Convertir Decimal/float a string legible con formato monetario
                try:
                    valor = float(item)
                    # Si es la columna de precio o subtotal (índices 2 y 3), formatear con $
                    if i >= 2:
                        texto = f"${valor:,.2f}"
                    else:
                        texto = str(item)
                except (ValueError, TypeError):
                    texto = str(item)
                c.drawString(x_positions[i], y, texto)

        try:
            suma_total += float(fila[-1])
        except (ValueError, TypeError):
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
    conexion = psycopg2.connect(**DB_CONFIG); cursor = conexion.cursor()
    cursor.execute("SELECT nombre FROM categorias ORDER BY nombre ASC")
    categorias = cursor.fetchall()
    
    # IMPORTANTE: Agregamos "WHERE p.activo = TRUE"
    cursor.execute("""
        SELECT p.id_producto, p.nombre, p.precio_base, c.nombre, p.stock 
        FROM productos p
        JOIN categorias c ON p.id_categoria = c.id_categoria
        WHERE p.activo = TRUE
        ORDER BY p.id_producto ASC
    """)
    productos = cursor.fetchall()
    cursor.close(); conexion.close()
    return render_template('tienda.html', productos=productos, categorias=categorias, 
                           nombre_usuario=session.get('nombre', 'Invitado'), logueado='id_usuario' in session)
    
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
            flash("Credenciales incorrectas. Revisa tu correo o contraseña.", "danger")
            return redirect(url_for('login'))
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
        cursor.execute("INSERT INTO productos (nombre, precio_base, id_categoria, stock, activo) VALUES (%s, %s, %s, %s, TRUE)", 
                       (request.form['nombre'], request.form['precio_base'], request.form['id_categoria'], request.form['stock']))
        conexion.commit()
        return redirect(url_for('vista_productos'))

    search_query = request.args.get('search', '')
    cat_filter = request.args.get('categoria', 'todas')
    
    # Agregamos "AND p.activo = TRUE" a la consulta base
    sql = """
        SELECT p.id_producto, p.nombre, p.precio_base, c.nombre, p.stock, c.id_categoria 
        FROM productos p 
        JOIN categorias c ON p.id_categoria = c.id_categoria 
        WHERE p.activo = TRUE
    """
    parametros = []
    if search_query:
        sql += " AND p.nombre ILIKE %s"; parametros.append(f"%{search_query}%")
    if cat_filter != 'todas':
        sql += " AND p.id_categoria = %s"; parametros.append(cat_filter)
        
    sql += " ORDER BY p.id_producto DESC"
    cursor.execute(sql, tuple(parametros))
    productos = cursor.fetchall()
    
    cursor.execute("SELECT id_categoria, nombre FROM categorias")
    categorias = cursor.fetchall()
    cursor.close(); conexion.close()
    return render_template('productos.html', productos=productos, categorias=categorias, 
                           search_query=search_query, cat_filter=cat_filter)

@app.route('/ventas')
def vista_ventas():
    if 'id_usuario' not in session or session.get('rol') != 'admin':
        return redirect(url_for('login'))
    
    search_id = request.args.get('search_id', type=int)
    page = request.args.get('page', 1, type=int)
    per_page = 20
    offset = (page - 1) * per_page

    conexion = psycopg2.connect(**DB_CONFIG)
    cursor = conexion.cursor()

    if search_id:
        # CAMBIO CLAVE: Buscamos el ID y los 9 registros menores (anteriores)
        # Usamos <= para incluir el ID buscado y LIMIT 10 para completar el grupo
        cursor.execute("""
            SELECT v.id_venta, u.nombre, v.fecha::date, v.total 
            FROM ventas v JOIN usuarios u ON v.id_usuario = u.id_usuario 
            WHERE v.id_venta <= %s 
            ORDER BY v.id_venta DESC 
            LIMIT 10
        """, (search_id,))
        ventas = cursor.fetchall()
        total_ventas = len(ventas)
        total_pages = 1
    else:
        # Paginación normal (sin cambios)
        cursor.execute("SELECT COUNT(*) FROM ventas")
        total_total = cursor.fetchone()[0]
        total_pages = (total_total + per_page - 1) // per_page
        cursor.execute("""
            SELECT v.id_venta, u.nombre, v.fecha::date, v.total 
            FROM ventas v JOIN usuarios u ON v.id_usuario = u.id_usuario 
            ORDER BY v.id_venta DESC LIMIT %s OFFSET %s
        """, (per_page, offset))
        ventas = cursor.fetchall()
        total_ventas = total_total # Usamos el conteo real para el texto de arriba

    cursor.close(); conexion.close()
    return render_template('ventas.html', ventas=ventas, page=page, total_pages=total_pages, total_total=total_ventas, search_id=search_id)

@app.route('/admin/ticket/<int:id_venta>')
def admin_descargar_ticket(id_venta):
    # Seguridad: solo el admin puede ver cualquier ticket
    if session.get('rol') != 'admin': return redirect('/')
    
    conexion = psycopg2.connect(**DB_CONFIG)
    cursor = conexion.cursor()
    
    cursor.execute("""
        SELECT p.nombre, 
               d.cantidad, 
               CAST(d.precio_unitario AS FLOAT), 
               CAST(d.subtotal AS FLOAT)
        FROM detalle_ventas d 
        JOIN productos p ON d.id_producto = p.id_producto 
        WHERE d.id_venta = %s
    """, (id_venta,))
    
    detalles = cursor.fetchall()
    cursor.close()
    conexion.close()
    
    headers = ["Producto", "Cant.", "Precio Unit.", "Subtotal"]
    return generar_pdf_documento(f"DETALLE DE VENTA #{id_venta}", headers, detalles, f"ticket_admin_{id_venta}.pdf", mostrar_total=True)

# ==========================================
# 4. RUTAS DEL CLIENTE (HISTORIAL Y TICKET)
# ==========================================
@app.route('/cliente/historial')
def historial_cliente():
    if 'id_usuario' not in session: return redirect(url_for('login'))
    conexion = psycopg2.connect(**DB_CONFIG); cursor = conexion.cursor()
    # Solo ventas con id_usuario real + que tengan al menos 1 item en detalle_ventas
    cursor.execute("""
        SELECT v.id_venta, v.fecha::date, v.total, COUNT(d.id_detalle) as items
        FROM ventas v
        JOIN detalle_ventas d ON v.id_venta = d.id_venta
        WHERE v.id_usuario = %s
        GROUP BY v.id_venta, v.fecha, v.total
        HAVING COUNT(d.id_detalle) > 0
        ORDER BY v.fecha DESC
    """, (session['id_usuario'],))
    pedidos = cursor.fetchall()
    cursor.close(); conexion.close()
    return render_template('historial.html', pedidos=pedidos, nombre_usuario=session['nombre'])

@app.route('/cliente/descargar_ticket/<int:id_venta>')
def descargar_ticket(id_venta):
    if 'id_usuario' not in session: return redirect(url_for('login'))
    conexion = psycopg2.connect(**DB_CONFIG); cursor = conexion.cursor()
    # Solo permite descargar tickets de compras propias con detalle real
    cursor.execute("""
        SELECT v.id_venta FROM ventas v
        JOIN detalle_ventas d ON v.id_venta = d.id_venta
        WHERE v.id_venta = %s AND v.id_usuario = %s
        LIMIT 1
    """, (id_venta, session['id_usuario']))
    if not cursor.fetchone():
        cursor.close(); conexion.close()
        return "Ticket no encontrado o sin permiso.", 404
    cursor.execute("""
        SELECT p.nombre, 
               d.cantidad, 
               CAST(d.precio_unitario AS FLOAT), 
               CAST(d.subtotal AS FLOAT)
        FROM detalle_ventas d 
        JOIN productos p ON d.id_producto = p.id_producto 
        WHERE d.id_venta = %s
        ORDER BY p.nombre ASC
    """, (id_venta,))
    detalles = cursor.fetchall()
    cursor.close(); conexion.close()
    headers = ["Producto", "Cant.", "Precio Unit.", "Subtotal"]
    return generar_pdf_documento(f"TICKET DE COMPRA #{id_venta}", headers, detalles, f"ticket_{id_venta}.pdf", mostrar_total=True)

# ==========================================
# 5. RUTAS API (DATOS Y GRÁFICOS)
# ==========================================
@app.route('/api/mis_pedidos')
def api_mis_pedidos():
    """Endpoint que usa el modal de historial en la tienda (main.js)."""
    if 'id_usuario' not in session:
        return jsonify({'mensaje': 'Error', 'error': 'No autenticado'}), 401
    page = request.args.get('page', 1, type=int)
    per_page = 10
    offset = (page - 1) * per_page
    try:
        conexion = psycopg2.connect(**DB_CONFIG); cursor = conexion.cursor()
        # Total de pedidos reales con detalle
        cursor.execute("""
            SELECT COUNT(DISTINCT v.id_venta)
            FROM ventas v
            JOIN detalle_ventas d ON v.id_venta = d.id_venta
            WHERE v.id_usuario = %s
        """, (session['id_usuario'],))
        total = cursor.fetchone()[0]
        # Pedidos paginados con conteo de items
        cursor.execute("""
            SELECT v.id_venta, v.fecha::date, v.total, COUNT(d.id_detalle) as items
            FROM ventas v
            JOIN detalle_ventas d ON v.id_venta = d.id_venta
            WHERE v.id_usuario = %s
            GROUP BY v.id_venta, v.fecha, v.total
            ORDER BY v.fecha DESC
            LIMIT %s OFFSET %s
        """, (session['id_usuario'], per_page, offset))
        filas = cursor.fetchall()
        cursor.close(); conexion.close()
        pedidos = [
            {'id': f[0], 'fecha': str(f[1]), 'total': float(f[2]), 'items': f[3]}
            for f in filas
        ]
        return jsonify({
            'mensaje': 'Éxito',
            'pedidos': pedidos,
            'total': total,
            'pagina': page,
            'total_paginas': (total + per_page - 1) // per_page if total > 0 else 1
        })
    except Exception as e:
        return jsonify({'mensaje': 'Error', 'error': str(e)}), 500


@app.route('/api/resumen_ventas')
def resumen_ventas():
    try:
        conexion = psycopg2.connect(**DB_CONFIG); cursor = conexion.cursor()
        cursor.execute("""
            SELECT 
                COUNT(*) as total_ventas,
                SUM(total) as gran_total,
                AVG(total) as precio_promedio,
                COUNT(*) FILTER (WHERE id_usuario IS NOT NULL) as ventas_reales,
                COUNT(*) FILTER (WHERE id_usuario IS NULL) as ventas_simuladas
            FROM ventas
        """)
        res = cursor.fetchone()
        cursor.close(); conexion.close()
        return jsonify({'mensaje': 'Éxito', 'datos': {
            'total_registros': res[0],
            'ingresos_totales': float(res[1]) if res[1] else 0,
            'precio_promedio': round(float(res[2]), 2) if res[2] else 0,
            'ventas_reales': res[3],
            'ventas_simuladas': res[4]
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
        colores = ['#16a34a', '#22c55e', '#4ade80', '#f97316', '#fb923c',
                   '#16a34a', '#22c55e', '#4ade80', '#f97316', '#fb923c']

        if tipo == 'pastel':
            # --- PASTEL: leyenda lateral, sin labels solapados ---
            fig, ax = plt.subplots(figsize=(9, 5))
            wedges, texts, autotexts = ax.pie(
                df['total_ventas'], labels=None,
                autopct='%1.1f%%', colors=colores[:len(df)],
                startangle=90, pctdistance=0.75
            )
            ax.legend(wedges, df['categoria'],
                      loc='center left', bbox_to_anchor=(1, 0, 0.4, 1), fontsize=9)

        elif tipo == 'lineal':
            # --- LINEAL: ingresos diarios últimos 30 días ---
            fig, ax = plt.subplots(figsize=(10, 5))
            conexion2 = psycopg2.connect(**DB_CONFIG); cursor2 = conexion2.cursor()
            cursor2.execute("""
                SELECT DATE(v.fecha) as dia, SUM(d.subtotal) as total_dia
                FROM ventas v
                JOIN detalle_ventas d ON v.id_venta = d.id_venta
                WHERE v.fecha >= CURRENT_DATE - INTERVAL '30 days'
                GROUP BY dia ORDER BY dia ASC
            """)
            datos_linea = cursor2.fetchall()
            cursor2.close(); conexion2.close()
            if datos_linea:
                df_linea = pd.DataFrame(datos_linea, columns=['dia', 'total_dia'])
                ax.plot(df_linea['dia'], df_linea['total_dia'],
                        color='#16a34a', linewidth=2.5, marker='o', markersize=4)
                ax.fill_between(df_linea['dia'], df_linea['total_dia'], alpha=0.15, color='#16a34a')
                ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('${x:,.0f}'))
                ax.set_xlabel('Fecha', fontsize=9)
                ax.set_title('Ingresos diarios - últimos 30 días', fontsize=10, pad=10)
                ax.grid(axis='y', linestyle='--', alpha=0.4)
                plt.xticks(rotation=45, ha='right', fontsize=8)
            else:
                ax.text(0.5, 0.5, 'Sin datos en los últimos 30 días',
                        ha='center', va='center', transform=ax.transAxes, fontsize=11)

        elif tipo == 'top_productos':
            # --- TOP 10 PRODUCTOS MÁS VENDIDOS (barras horizontales) ---
            fig, ax = plt.subplots(figsize=(10, 6))
            conexion2 = psycopg2.connect(**DB_CONFIG); cursor2 = conexion2.cursor()
            cursor2.execute("""
                SELECT p.nombre, SUM(d.cantidad) as total_unidades
                FROM detalle_ventas d
                JOIN productos p ON d.id_producto = p.id_producto
                GROUP BY p.nombre
                ORDER BY total_unidades DESC
                LIMIT 10
            """)
            datos_top = cursor2.fetchall()
            cursor2.close(); conexion2.close()
            if datos_top:
                df_top = pd.DataFrame(datos_top, columns=['producto', 'unidades'])
                df_top = df_top.sort_values('unidades', ascending=True)  # invertir para que el mayor quede arriba
                bars = ax.barh(df_top['producto'], df_top['unidades'],
                               color=colores[:len(df_top)], height=0.6, zorder=2)
                # Etiqueta de valor al final de cada barra
                for bar, val in zip(bars, df_top['unidades']):
                    ax.text(bar.get_width() + (bar.get_width() * 0.01),
                            bar.get_y() + bar.get_height() / 2,
                            f'{int(val):,}', va='center', fontsize=8, color='#333')
                ax.set_xlabel('Unidades vendidas', fontsize=9)
                ax.set_title('Top 10 productos más vendidos', fontsize=10, pad=10)
                ax.grid(axis='x', linestyle='--', alpha=0.4, zorder=1)
                ax.set_axisbelow(True)
                ax.tick_params(axis='y', labelsize=9)
                ax.xaxis.set_major_formatter(ticker.StrMethodFormatter('{x:,.0f}'))

        elif tipo == 'calor':
            # --- MAPA DE CALOR: ventas por día de semana y hora ---
            import numpy as np
            fig, ax = plt.subplots(figsize=(11, 5))
            conexion2 = psycopg2.connect(**DB_CONFIG); cursor2 = conexion2.cursor()
            cursor2.execute("""
                SELECT EXTRACT(DOW FROM v.fecha)::INT  as dia_semana,
                       EXTRACT(HOUR FROM v.fecha)::INT as hora,
                       COUNT(*) as num_ventas
                FROM ventas v
                WHERE v.fecha >= CURRENT_DATE - INTERVAL '90 days'
                GROUP BY dia_semana, hora
                ORDER BY dia_semana, hora
            """)
            datos_calor = cursor2.fetchall()
            cursor2.close(); conexion2.close()
            if datos_calor:
                # Construir matriz 7 dias x 24 horas
                matriz = np.zeros((7, 24))
                for dia, hora, cnt in datos_calor:
                    if 0 <= dia <= 6 and 0 <= hora <= 23:
                        matriz[dia][hora] = cnt
                dias_labels = ['Dom', 'Lun', 'Mar', 'Mié', 'Jue', 'Vie', 'Sáb']
                im = ax.imshow(matriz, cmap='Greens', aspect='auto')
                ax.set_xticks(range(24))
                ax.set_xticklabels([f'{h:02d}h' for h in range(24)], fontsize=7, rotation=45)
                ax.set_yticks(range(7))
                ax.set_yticklabels(dias_labels, fontsize=9)
                ax.set_title('Mapa de calor: ventas por día y hora (últimos 90 días)', fontsize=10, pad=10)
                ax.set_xlabel('Hora del día', fontsize=9)
                plt.colorbar(im, ax=ax, label='Nº ventas', shrink=0.8)
            else:
                ax.text(0.5, 0.5, 'Sin datos suficientes',
                        ha='center', va='center', transform=ax.transAxes, fontsize=11)

        else:  # barras (default)
            # --- BARRAS VERTICALES POR CATEGORÍA ---
            fig, ax = plt.subplots(figsize=(10, 5))
            ax.bar(range(len(df)), df['total_ventas'], color=colores[:len(df)], width=0.6, zorder=2)
            ax.set_xticks(range(len(df)))
            ax.set_xticklabels(df['categoria'], rotation=40, ha='right', fontsize=9)
            ax.yaxis.set_major_formatter(ticker.StrMethodFormatter('${x:,.0f}'))
            ax.grid(axis='y', linestyle='--', alpha=0.4, zorder=1)
            ax.set_axisbelow(True)

        plt.tight_layout()
        img = io.BytesIO()
        plt.savefig(img, format='png', transparent=True, bbox_inches='tight', dpi=110)
        img.seek(0); plt.close()
        return jsonify({'mensaje': 'Éxito', 'imagen': base64.b64encode(img.getvalue()).decode('utf8')})
    except Exception as e:
        return jsonify({'mensaje': 'Error', 'error': str(e)})
    
    # --- ELIMINAR PRODUCTO ---
@app.route('/productos/eliminar/<int:id>')
def eliminar_producto(id):
    if session.get('rol') != 'admin': return redirect(url_for('login'))
    
    conexion = psycopg2.connect(**DB_CONFIG)
    cursor = conexion.cursor()
    try:
        # En lugar de DELETE, usamos UPDATE
        cursor.execute("UPDATE productos SET activo = FALSE WHERE id_producto = %s", (id,))
        conexion.commit()
    except Exception as e:
        print(f"Error al desactivar: {e}")
        conexion.rollback()
    finally:
        cursor.close(); conexion.close()
    
    return redirect(url_for('vista_productos'))

# --- EDITAR PRODUCTO (VISTA Y LÓGICA) ---
@app.route('/productos/editar/<int:id>', methods=['GET', 'POST'])
def editar_producto(id):
    if session.get('rol') != 'admin': return redirect(url_for('login'))
    
    conexion = psycopg2.connect(**DB_CONFIG)
    cursor = conexion.cursor()

    if request.method == 'POST':
        # Capturamos los nuevos datos del formulario
        nombre = request.form['nombre']
        precio = request.form['precio_base']
        stock = request.form['stock']
        id_cat = request.form['id_categoria']
        
        cursor.execute("""
            UPDATE productos 
            SET nombre = %s, precio_base = %s, stock = %s, id_categoria = %s 
            WHERE id_producto = %s
        """, (nombre, precio, stock, id_cat, id))
        conexion.commit()
        cursor.close()
        conexion.close()
        return redirect(url_for('vista_productos'))

    # Si es GET, buscamos los datos actuales para llenar el formulario
    cursor.execute("SELECT * FROM productos WHERE id_producto = %s", (id,))
    producto = cursor.fetchone()
    
    cursor.execute("SELECT * FROM categorias")
    categorias = cursor.fetchall()
    
    cursor.close()
    conexion.close()
    return render_template('editar_producto.html', producto=producto, categorias=categorias)

if __name__ == '__main__':
    app.run(debug=True, port=5000)