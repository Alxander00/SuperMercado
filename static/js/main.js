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

    // Mensajes de carga según tipo de gráfico
    const mensajes = {
        'barras':        'Calculando ventas por categoría...',
        'pastel':        'Preparando distribución...',
        'lineal':        'Trazando tendencia de 30 días...',
        'top_productos': 'Buscando los productos estrella...',
        'calor':         'Construyendo mapa de calor...'
    };
    const msg = mensajes[tipo] || 'Cargando gráfico...';

    contenedor.innerHTML = `
        <div class="p-5 text-center text-muted">
            <i class="fas fa-spinner fa-spin fa-2x mb-2 text-success"></i>
            <p>${msg}</p>
        </div>`;

    fetch(`/api/grafico_tendencias?tipo=${tipo}`)
        .then(response => response.json())
        .then(data => {
            if (data.mensaje === 'Éxito') {
                // Altura dinámica según tipo
                const alturas = { 'calor': '420px', 'top_productos': '380px' };
                const altura = alturas[tipo] || '350px';
                contenedor.innerHTML = `<img src="data:image/png;base64,${data.imagen}" class="img-fluid w-100" style="max-height:${altura}; object-fit:contain;" alt="Gráfico">`;
            } else {
                contenedor.innerHTML = `<p class="text-danger text-center py-4"><i class="fas fa-exclamation-circle me-2"></i>Error: ${data.error}</p>`;
            }
        })
        .catch(() => {
            contenedor.innerHTML = `<p class="text-danger text-center py-4">No se pudo conectar con el servidor.</p>`;
        });
}

// ==========================================
// 2. CARRITO Y COMPRAS (CON LÍMITE DE STOCK)
// ==========================================
let carrito = [];

function mostrarToast(mensaje, tipo = 'success') {
    const toastEl = document.getElementById('toastCarrito');
    const mensajeEl = document.getElementById('toast-mensaje');
    toastEl.className = `toast align-items-center text-bg-${tipo} border-0 shadow-lg animate__animated animate__fadeInUp`;
    mensajeEl.innerText = mensaje;
    const toast = new bootstrap.Toast(toastEl, { delay: 3000 });
    toast.show();
}

function obtenerStockActual(id) {
    const input = document.getElementById(`cant-${id}`);
    if (!input) return 0;
    return parseInt(input.closest('.tarjeta-producto').getAttribute('data-stock'));
}

function cambiarCantidad(id, delta) {
    let input = document.getElementById(`cant-${id}`);
    if (!input) return;
    let maxStock = obtenerStockActual(id);
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

// ==========================================
// DESCARGA AUTOMÁTICA DEL TICKET PDF
// ==========================================
function descargarTicketAutomatico(idVenta) {
    // Crear un enlace invisible, dispararlo y eliminarlo
    const enlace = document.createElement('a');
    enlace.href = `/cliente/descargar_ticket/${idVenta}`;
    enlace.download = `ticket_${idVenta}.pdf`;
    document.body.appendChild(enlace);
    enlace.click();
    document.body.removeChild(enlace);
}

function mostrarModalExito(idVenta) {
    // Rellenar datos del modal de éxito
    const numTicket = document.getElementById('modal-num-ticket');
    const btnDescargar = document.getElementById('btn-descargar-ticket');

    if (numTicket) numTicket.innerText = `#${idVenta}`;
    if (btnDescargar) btnDescargar.href = `/cliente/descargar_ticket/${idVenta}`;

    // Ocultar modal del carrito y mostrar modal de éxito
    const modalCarrito = bootstrap.Modal.getInstance(document.getElementById('carritoModal'));
    if (modalCarrito) modalCarrito.hide();

    const modalExito = new bootstrap.Modal(document.getElementById('modalCompraExitosa'));
    modalExito.show();
}

function procesarCompra() {
    if (carrito.length === 0) return alert("Tu carrito está vacío.");

    // Deshabilitar botón para evitar doble clic
    const btnPagar = document.getElementById('btn-pagar');
    if (btnPagar) {
        btnPagar.disabled = true;
        btnPagar.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Procesando...';
    }

    fetch('/api/comprar', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(carrito)
    })
    .then(r => r.json())
    .then(data => {
        if (data.mensaje === 'Éxito') {

            // Actualizar stock visual en las tarjetas
            carrito.forEach(item => {
                let tarjeta = document.getElementById(`cant-${item.id}`)?.closest('.tarjeta-producto');
                if (tarjeta) {
                    let stockActual = parseInt(tarjeta.getAttribute('data-stock'));
                    let nuevoStock = stockActual - item.cantidad;

                    tarjeta.setAttribute('data-stock', nuevoStock);

                    let badgeStock = document.getElementById(`disp-${item.id}`);
                    if (badgeStock) badgeStock.innerText = nuevoStock;

                    let inputCant = document.getElementById(`cant-${item.id}`);
                    if (inputCant) inputCant.setAttribute('max', nuevoStock);

                    if (nuevoStock <= 0) {
                        let controlesDiv = inputCant?.closest('.mt-auto');
                        if (controlesDiv) {
                            controlesDiv.innerHTML = `
                                <div class="alert alert-danger py-2 mb-0 fw-bold rounded-pill" role="alert">
                                    <i class="fas fa-times-circle me-1"></i> ¡Agotado!
                                </div>
                            `;
                        }
                    }
                }
            });

            // ✅ DESCARGA AUTOMÁTICA DEL TICKET PDF
            descargarTicketAutomatico(data.id_venta);

            // Limpiar carrito
            carrito = [];
            actualizarVistaCarrito();

            // Mostrar modal de compra exitosa
            mostrarModalExito(data.id_venta);

        } else {
            alert("Error al procesar la compra: " + data.error);
            if (btnPagar) {
                btnPagar.disabled = false;
                btnPagar.innerHTML = '<i class="fas fa-credit-card me-2"></i>Pagar';
            }
        }
    })
    .catch(() => {
        alert("Error de conexión. Intenta nuevamente.");
        if (btnPagar) {
            btnPagar.disabled = false;
            btnPagar.innerHTML = '<i class="fas fa-credit-card me-2"></i>Pagar';
        }
    });
}

// ==========================================
// HISTORIAL DE PEDIDOS EN MODAL
// ==========================================
function cargarHistorialModal() {
    const cuerpo = document.getElementById('cuerpo-pedidos-modal');
    if (!cuerpo) return;

    cuerpo.innerHTML = `
        <div class="text-center py-5">
            <i class="fas fa-spinner fa-spin fa-2x text-success mb-3"></i>
            <p class="text-muted">Cargando tus pedidos...</p>
        </div>`;

    fetch('/api/mis_pedidos')
        .then(r => r.json())
        .then(data => {
            if (data.mensaje === 'Éxito' && data.pedidos.length > 0) {
                let html = '<div class="row g-3">';
                data.pedidos.forEach(p => {
                    html += `
                        <div class="col-12">
                            <div class="card border-0 shadow-sm rounded-4 p-3">
                                <div class="d-flex justify-content-between align-items-center">
                                    <div>
                                        <span class="badge bg-success-subtle text-success border border-success-subtle mb-1">Pedido #${p.id}</span>
                                        <h6 class="fw-bold mb-0">${p.fecha}</h6>
                                        <span class="text-success fw-bold fs-5">$${parseFloat(p.total).toFixed(2)}</span>
                                    </div>
                                    <a href="/cliente/descargar_ticket/${p.id}" class="btn btn-dark btn-sm rounded-pill px-3 shadow-sm">
                                        <i class="fas fa-file-pdf me-1 text-danger"></i> Ticket PDF
                                    </a>
                                </div>
                            </div>
                        </div>`;
                });
                html += '</div>';
                cuerpo.innerHTML = html;
            } else {
                cuerpo.innerHTML = `
                    <div class="text-center py-5">
                        <i class="fas fa-receipt fa-4x text-muted opacity-25 mb-3"></i>
                        <h5 class="text-muted">Aún no has realizado ninguna compra.</h5>
                        <p class="text-muted small">¡Tus próximos tickets aparecerán aquí!</p>
                    </div>`;
            }
        })
        .catch(() => {
            cuerpo.innerHTML = `<p class="text-danger text-center py-4">No se pudo cargar el historial.</p>`;
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

    const buscador = document.getElementById('filtro-texto');
    const comboCat = document.getElementById('filtro-categoria');
    const rangoPrecio = document.getElementById('filtro-precio');

    if (buscador) buscador.addEventListener('input', aplicarFiltros);
    if (comboCat) comboCat.addEventListener('change', aplicarFiltros);
    if (rangoPrecio) rangoPrecio.addEventListener('input', aplicarFiltros);

    // Cargar historial cuando se abre el modal de pedidos
    const modalPedidos = document.getElementById('pedidosModal');
    if (modalPedidos) {
        modalPedidos.addEventListener('show.bs.modal', cargarHistorialModal);
    }

    // Re-habilitar botón pagar al cerrar el modal del carrito
    const modalCarrito = document.getElementById('carritoModal');
    if (modalCarrito) {
        modalCarrito.addEventListener('hidden.bs.modal', () => {
            const btnPagar = document.getElementById('btn-pagar');
            if (btnPagar) {
                btnPagar.disabled = false;
                btnPagar.innerHTML = '<i class="fas fa-credit-card me-2"></i>Pagar';
            }
        });
    }
});
