// ==========================================
// 1. ADMIN (DASHBOARD)
// ==========================================
function cargarNumeros() {
    if (document.getElementById('kpi-registros')) {
        fetch('/api/resumen_ventas')
            .then(response => response.json())
            .then(data => {
                if(data.mensaje === 'Éxito') {
                    document.getElementById('kpi-registros').innerText = data.datos.total_registros.toLocaleString();
                    document.getElementById('kpi-ingresos').innerText = '$' + data.datos.ingresos_totales.toLocaleString(undefined, {minimumFractionDigits: 2});
                    document.getElementById('kpi-promedio').innerText = '$' + data.datos.precio_promedio.toLocaleString(undefined, {minimumFractionDigits: 2});
                }
            });
    }
}

function renderizarGrafico(tipo) {
    const contenedor = document.getElementById('contenedor-grafico');
    if (!contenedor) return;
    contenedor.innerHTML = `<div class="p-5 text-muted"><i class="fas fa-spinner fa-spin fa-2x mb-2 text-success"></i><p>Calculando matrices...</p></div>`;
    fetch(`/api/grafico_tendencias?tipo=${tipo}`)
        .then(response => response.json())
        .then(data => {
            if(data.mensaje === 'Éxito') {
                contenedor.innerHTML = `<img src="data:image/png;base64,${data.imagen}" class="img-fluid" style="max-height: 350px;" alt="Gráfico">`;
            } else {
                contenedor.innerHTML = `<p class="text-danger">Error: ${data.error}</p>`;
            }
        });
}

// ==========================================
// 2. CARRITO Y COMPRAS (CON CANTIDADES)
// ==========================================
// ==========================================
// 2. CARRITO Y COMPRAS (CON LÍMITE DE STOCK)
// ==========================================
// ==========================================
// 2. CARRITO Y COMPRAS (ACTUALIZACIÓN EN VIVO)
// ==========================================
let carrito = [];

function mostrarToast(mensaje, tipo = 'success') {
    const toastEl = document.getElementById('toastCarrito');
    const mensajeEl = document.getElementById('toast-mensaje');
    
    // Cambiar el color de la notificación según si es éxito o error
    toastEl.className = `toast align-items-center text-bg-${tipo} border-0 shadow-lg animate__animated animate__fadeInUp`;
    mensajeEl.innerText = mensaje;
    
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
}

// NUEVO: Lee el stock directamente de la tarjeta en tiempo real
function obtenerStockActual(id) {
    const input = document.getElementById(`cant-${id}`);
    if (!input) return 0;
    return parseInt(input.closest('.tarjeta-producto').getAttribute('data-stock'));
}

function cambiarCantidad(id, delta) {
    let input = document.getElementById(`cant-${id}`);
    if (!input) return;
    
    let maxStock = obtenerStockActual(id); // Calculamos el stock al instante
    let nueva = parseInt(input.value) + delta;
    
    if (nueva >= 1 && nueva <= maxStock) {
        input.value = nueva;
    } else if (nueva > maxStock) {
        mostrarToast(`¡Solo tenemos ${maxStock} unidades disponibles!`, 'warning');
    }
}

function agregarAlCarrito(id, nombre, precio) {
    let inputCant = document.getElementById(`cant-${id}`);
    let maxStock = obtenerStockActual(id);
    let cantidadAAgregar = inputCant ? parseInt(inputCant.value) : 1;

    let productoExistente = carrito.find(item => item.id === id);
    let cantidadTotalDeseada = productoExistente ? productoExistente.cantidad + cantidadAAgregar : cantidadAAgregar;

    // Validación estricta
    if (cantidadTotalDeseada > maxStock) {
        mostrarToast(`No puedes agregar ${cantidadAAgregar} más. Stock límite: ${maxStock}`, 'danger');
        return;
    }

    if (productoExistente) {
        productoExistente.cantidad += cantidadAAgregar;
        productoExistente.subtotal = productoExistente.cantidad * productoExistente.precio;
    } else {
        carrito.push({ id: id, nombre: nombre, precio: parseFloat(precio), cantidad: cantidadAAgregar, subtotal: parseFloat(precio) * cantidadAAgregar });
    }
    
    actualizarVistaCarrito();
    mostrarToast(`Agregaste ${cantidadAAgregar}x ${nombre}`, 'success');

    // Animar el ícono del carrito en el Navbar
    const botonCarrito = document.getElementById('btn-carrito-nav');
    if(botonCarrito) {
        botonCarrito.classList.remove('animate__animated', 'animate__rubberBand');
        setTimeout(() => botonCarrito.classList.add('animate__animated', 'animate__rubberBand'), 10);
    }

    if (inputCant) inputCant.value = 1; 
}

function actualizarVistaCarrito() {
    const lista = document.getElementById('lista-carrito');
    if (!lista) return; 

    lista.innerHTML = ''; 
    let granTotal = 0, cantidadTotal = 0;

    if (carrito.length === 0) {
        lista.innerHTML = '<li class="list-group-item text-center text-muted border-0 py-4">El carrito está vacío</li>';
    } else {
        carrito.forEach((item) => {
            granTotal += item.subtotal;
            cantidadTotal += item.cantidad;
            lista.innerHTML += `
                <li class="list-group-item d-flex justify-content-between align-items-center px-0 py-3">
                    <div>
                        <h6 class="my-0 fw-bold">${item.nombre}</h6>
                        <small class="text-success fw-bold">${item.cantidad} x $${item.precio.toFixed(2)}</small>
                    </div>
                    <span class="text-dark fw-bold fs-5">$${item.subtotal.toFixed(2)}</span>
                </li>`;
        });
    }
    
    const contador = document.getElementById('contador-carrito');
    if (contador) contador.innerText = cantidadTotal;
    
    const totalTexto = document.getElementById('total-carrito');
    if (totalTexto) totalTexto.innerText = '$' + granTotal.toFixed(2);
}

function procesarCompra() {
    if (carrito.length === 0) return alert("Tu carrito está vacío.");
    
    fetch('/api/comprar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(carrito) 
    })
    .then(r => r.json())
    .then(data => {
        if(data.mensaje === 'Éxito') {
            
            // ¡MAGIA VISUAL!: RESTAR EL STOCK DE LA PANTALLA
            carrito.forEach(item => {
                let tarjeta = document.getElementById(`cant-${item.id}`)?.closest('.tarjeta-producto');
                if(tarjeta) {
                    let stockActual = parseInt(tarjeta.getAttribute('data-stock'));
                    let nuevoStock = stockActual - item.cantidad;

                    // 1. Actualizamos el dato oculto
                    tarjeta.setAttribute('data-stock', nuevoStock);

                    // 2. Actualizamos el texto de "Stock: XX"
                    let badgeStock = document.getElementById(`disp-${item.id}`);
                    if(badgeStock) badgeStock.innerText = nuevoStock;

                    // 3. Ajustamos el límite del botón "+"
                    let inputCant = document.getElementById(`cant-${item.id}`);
                    if(inputCant) inputCant.setAttribute('max', nuevoStock);

                    // 4. Si llegó a Cero, transformamos los botones en el letrero de "¡Agotado!"
                    if(nuevoStock <= 0) {
                        let controlesDiv = inputCant.closest('.mt-auto');
                        if(controlesDiv) {
                            controlesDiv.innerHTML = `
                                <div class="alert alert-danger py-2 mb-0 fw-bold rounded-pill" role="alert">
                                    <i class="fas fa-times-circle me-1"></i> ¡Agotado!
                                </div>
                            `;
                        }
                    }
                }
            });

            alert(`¡Compra Exitosa! Ticket #${data.id_venta}`);
            carrito = []; 
            actualizarVistaCarrito();
            bootstrap.Modal.getInstance(document.getElementById('carritoModal')).hide();
        } else { alert("Error: " + data.error); }
    });
}

// ==========================================
// 3. FILTROS EN LA BARRA LATERAL
// ==========================================
function limpiarFiltros() {
    if(document.getElementById('filtro-texto')) document.getElementById('filtro-texto').value = '';
    if(document.getElementById('filtro-categoria')) document.getElementById('filtro-categoria').value = 'todas';
    if(document.getElementById('filtro-precio')) document.getElementById('filtro-precio').value = 200;
    aplicarFiltros();
}

function aplicarFiltros() {
    const textoElemento = document.getElementById('filtro-texto');
    const selectCat = document.getElementById('filtro-categoria');
    const inputPrecio = document.getElementById('filtro-precio');

    if (!textoElemento || !selectCat || !inputPrecio) return;

    const texto = textoElemento.value.toLowerCase().trim();
    const categoriaActiva = selectCat.value;
    const precioMax = parseFloat(inputPrecio.value);

    const labelPrecio = document.getElementById('label-precio');
    if(labelPrecio) labelPrecio.innerText = `$${precioMax.toFixed(2)}`;

    let visibles = 0;
    
    document.querySelectorAll('.tarjeta-producto').forEach(tarjeta => {
        const tNombre = (tarjeta.getAttribute('data-nombre') || "").toLowerCase();
        const tCategoria = tarjeta.getAttribute('data-categoria') || "";
        const tPrecio = parseFloat(tarjeta.getAttribute('data-precio') || "0");

        const coincideTexto = tNombre.includes(texto);
        const coincideCat = (categoriaActiva === 'todas' || tCategoria === categoriaActiva);
        const coincidePrecio = tPrecio <= precioMax;

        if (coincideTexto && coincideCat && coincidePrecio) {
            tarjeta.style.display = 'block';
            tarjeta.classList.add('animate__animated', 'animate__fadeIn');
            visibles++;
        } else {
            tarjeta.style.display = 'none';
            tarjeta.classList.remove('animate__animated', 'animate__fadeIn');
        }
    });

    const contador = document.getElementById('contador-productos');
    if (contador) contador.innerText = `${visibles} productos encontrados`;
}

// ==========================================
// 4. INICIALIZADOR
// ==========================================
document.addEventListener('DOMContentLoaded', () => {
    cargarNumeros();
    if(document.getElementById('contenedor-grafico')) renderizarGrafico('barras');
    const selector = document.getElementById('tipo-grafico');
    if (selector) selector.addEventListener('change', (e) => renderizarGrafico(e.target.value));

    actualizarVistaCarrito();
    
    // Asignar eventos a la barra lateral
    const buscador = document.getElementById('filtro-texto');
    const comboCat = document.getElementById('filtro-categoria');
    const rangoPrecio = document.getElementById('filtro-precio');

    if (buscador) buscador.addEventListener('input', aplicarFiltros);
    if (comboCat) comboCat.addEventListener('change', aplicarFiltros);
    if (rangoPrecio) rangoPrecio.addEventListener('input', aplicarFiltros);
});