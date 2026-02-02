// ═══════════════════════════════════════════════════════════════════════════
// NAVEGACIÓN ENTRE SECCIONES
// ═══════════════════════════════════════════════════════════════════════════
let map;
let marker;

function mostrarSeccion(nombre) {
    // Hide all sections
    document.querySelectorAll('.seccion').forEach(s => {
        s.classList.remove('active');
    });
    
    // Show the requested section
    const seccion = document.getElementById(`seccion-${nombre}`);
    if (seccion) {
        seccion.classList.add('active');
    }
    
    // If showing the map section, initialize/update the map
    if (nombre === 'crear') {
        // Small delay to ensure DOM is updated
        setTimeout(() => {
            initMap();
            if (map) {
                setTimeout(() => {
                    map.invalidateSize(true);
                }, 50);
            }
        }, 50);
    }
    
    // Load reports if showing list section
    if (nombre === 'lista') {
        cargarReportes();
    }
    
    // Load analytics if showing analytics section
    if (nombre === 'analiticas') {
        cargarAnaliticas();
    }
}

function initMap() {
    // Don't initialize if map already exists
    if (map) return;
    
    // Ensure map container exists and is visible
    const mapContainer = document.getElementById('map');
    if (!mapContainer || mapContainer.offsetParent === null) {
        return;
    }
    
    map = L.map('map').setView([-25.5095, -54.6110], 13);

    L.tileLayer('https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png', {
        attribution: '&copy; OpenStreetMap contributors',
        maxZoom: 19,
        minZoom: 2
    }).addTo(map);

    map.on('click', function (e) {
        const { lat, lng } = e.latlng;

        if (marker) {
            marker.setLatLng(e.latlng);
        } else {
            marker = L.marker(e.latlng).addTo(map);
        }

        document.getElementById('lat').value = lat;
        document.getElementById('lng').value = lng;
    });
    
    // Force redraw after initialization
    setTimeout(() => {
        map.invalidateSize(true);
    }, 100);
}

// Initialize on page load
document.addEventListener('DOMContentLoaded', function() {
    // Show first section
    mostrarSeccion('crear');
    
    // Initialize filters
    const filtroEstado = document.getElementById('filtro-estado');
    if (filtroEstado) {
        filtroEstado.addEventListener('change', cargarReportes);
    }
});

// ═══════════════════════════════════════════════════════════════════════════
// CREAR REPORTE
// ═══════════════════════════════════════════════════════════════════════════

document.addEventListener('DOMContentLoaded', function() {
    const formCrear = document.getElementById('form-crear-reporte');
    if (formCrear) {
        formCrear.addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const mensajeDiv = document.getElementById('mensaje-crear');
            const btnSubmit = this.querySelector('button[type="submit"]');
            
            // Validaciones del lado del cliente
            const direccion = document.getElementById('direccion').value.trim();
            const comentario = document.getElementById('comentario').value.trim();
            const foto = document.getElementById('foto').files[0];
            
            if (direccion.length < 5) {
                mostrarMensaje(mensajeDiv, 'La dirección debe tener al menos 5 caracteres', 'error');
                return;
            }
            
            if (comentario.length < 10) {
                mostrarMensaje(mensajeDiv, 'El comentario debe tener al menos 10 caracteres', 'error');
                return;
            }
            
            if (!foto) {
                mostrarMensaje(mensajeDiv, 'Debes seleccionar una foto', 'error');
                return;
            }
            
            // Validar tamaño de archivo (5MB)
            if (foto.size > 5 * 1024 * 1024) {
                mostrarMensaje(mensajeDiv, 'La foto no debe superar los 5MB', 'error');
                return;
            }
            
            // Preparar FormData
            const formData = new FormData(this);
            
            // Deshabilitar botón mientras se envía
            btnSubmit.disabled = true;
            btnSubmit.textContent = 'Enviando...';
            
            try {
                const response = await fetch('/api/reportes', {
                    method: 'POST',
                    body: formData
                });
                
                const data = await response.json();
                
                if (response.ok) {
                    mostrarMensaje(mensajeDiv, '✅ ' + data.message, 'exito');
                    // Limpiar formulario
                    this.reset();
                    // Después de 2 segundos, ir a ver reportes
                    setTimeout(() => {
                        mostrarSeccion('lista');
                    }, 2000);
                } else {
                    mostrarMensaje(mensajeDiv, '❌ ' + data.error, 'error');
                }
            } catch (error) {
                mostrarMensaje(mensajeDiv, '❌ Error al conectar con el servidor', 'error');
            } finally {
                btnSubmit.disabled = false;
                btnSubmit.textContent = 'Enviar Reporte';
            }
        });
    }
});

// ═══════════════════════════════════════════════════════════════════════════
// CARGAR Y MOSTRAR REPORTES
// ═══════════════════════════════════════════════════════════════════════════

async function cargarReportes() {
    const estado = document.getElementById('filtro-estado').value;
    const container = document.getElementById('lista-reportes');
    
    container.innerHTML = '<p class="cargando">Cargando reportes...</p>';
    
    try {
        const url = estado === 'Todos' 
            ? '/api/reportes' 
            : `/api/reportes?estado=${encodeURIComponent(estado)}`;
            
        const response = await fetch(url);
        const reportes = await response.json();
        
        if (reportes.length === 0) {
            container.innerHTML = '<p class="cargando">No hay reportes para mostrar.</p>';
            return;
        }
        
        // Renderizar reportes
        container.innerHTML = '';
        reportes.forEach(reporte => {
            const card = crearTarjetaReporte(reporte);
            container.appendChild(card);
        });
        
    } catch (error) {
        container.innerHTML = '<p class="cargando">Error al cargar reportes.</p>';
    }
}

function crearTarjetaReporte(reporte) {
    const card = document.createElement('div');
    card.className = 'reporte-card';
    card.onclick = () => verDetalleReporte(reporte.id);
    
    const estadoClass = `estado-${reporte.estado.toLowerCase()}`;
    
    card.innerHTML = `
        <img src="/static/uploads/${reporte.foto}" alt="Foto del reporte" class="reporte-imagen" onerror="this.src='data:image/svg+xml,%3Csvg xmlns=%22http://www.w3.org/2000/svg%22 width=%22300%22 height=%22200%22%3E%3Crect fill=%22%23ddd%22 width=%22300%22 height=%22200%22/%3E%3Ctext x=%2250%25%22 y=%2250%25%22 font-size=%2218%22 text-anchor=%22middle%22 fill=%22%23999%22%3ESin imagen%3C/text%3E%3C/svg%3E'">
        <div class="reporte-contenido">
            <div class="reporte-direccion">${escapeHtml(reporte.direccion)}</div>
            <div class="reporte-comentario">${escapeHtml(reporte.comentario)}</div>
            <div class="reporte-footer">
                <span class="reporte-estado ${estadoClass}">${reporte.estado}</span>
                <span class="reporte-fecha">${formatearFecha(reporte.fecha_creacion)}</span>
            </div>
        </div>
    `;
    
    return card;
}

// ═══════════════════════════════════════════════════════════════════════════
// MODAL - VER DETALLE DE REPORTE
// ═══════════════════════════════════════════════════════════════════════════

async function verDetalleReporte(id) {
    try {
        const response = await fetch(`/api/reportes/${id}`);
        const reporte = await response.json();
        
        if (!response.ok) {
            alert('Error al cargar el reporte');
            return;
        }
        
        const estadoClass = `estado-${reporte.estado.toLowerCase()}`;
        
        let contenido = `
            <h2>Detalle del Reporte #${reporte.id}</h2>
            
            <img src="/static/uploads/${reporte.foto}" alt="Foto del reporte" class="modal-imagen" onerror="this.style.display='none'">
            
            <div class="modal-info">
                <strong>📍 Dirección:</strong>
                <p>${escapeHtml(reporte.direccion)}</p>
            </div>
            
            <div class="modal-info">
                <strong>💬 Descripción:</strong>
                <p>${escapeHtml(reporte.comentario)}</p>
            </div>
            
            <div class="modal-info">
                <strong>📅 Fecha de creación:</strong>
                <p>${formatearFecha(reporte.fecha_creacion)}</p>
            </div>
            
            ${reporte.email ? `
            <div class="modal-info">
                <strong>📧 Email de contacto:</strong>
                <p>${escapeHtml(reporte.email)}</p>
            </div>
            ` : ''}
            
            <div class="modal-info">
                <strong>📊 Estado actual:</strong>
                <p><span class="reporte-estado ${estadoClass}">${reporte.estado}</span></p>
            </div>
            
            ${reporte.razon_rechazo ? `
            <div class="modal-info">
                <strong>❌ Razón de rechazo:</strong>
                <p>${escapeHtml(reporte.razon_rechazo)}</p>
            </div>
            ` : ''}
        `;
        
        // Si es admin, agregar botones para cambiar estado
        if (esAdmin()) {
            contenido += `
                <div class="admin-acciones">
                    <h4>Acciones de Administrador</h4>
                    <div class="admin-botones">
                        <button class="btn btn-warning btn-small" onclick="cambiarEstado(${reporte.id}, 'Pendiente')">Pendiente</button>
                        <button class="btn btn-primary btn-small" onclick="cambiarEstado(${reporte.id}, 'Verificando')">Verificando</button>
                        <button class="btn btn-success btn-small" onclick="cambiarEstado(${reporte.id}, 'Solucionado')">Solucionado</button>
                        <button class="btn btn-danger btn-small" onclick="rechazarReporte(${reporte.id})">Rechazar</button>
                    </div>
                </div>
            `;
        }
        
        abrirModal(contenido);
        
    } catch (error) {
        alert('Error al cargar el reporte');
    }
}

async function cambiarEstado(id, nuevoEstado) {
    if (!confirm(`¿Cambiar estado a "${nuevoEstado}"?`)) {
        return;
    }
    
    try {
        const response = await fetch(`/api/reportes/${id}/estado`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ estado: nuevoEstado })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('✅ ' + data.message);
            cerrarModal();
            cargarReportes(); // Recargar lista
            if (document.getElementById('seccion-analiticas')?.classList.contains('active')) {
                cargarAnaliticas(); // Actualizar analíticas si está visible
            }
        } else {
            alert('❌ ' + data.error);
        }
    } catch (error) {
        alert('❌ Error al cambiar el estado');
    }
}

function rechazarReporte(id) {
    const razon = prompt('Ingresa la razón del rechazo (mínimo 10 caracteres):');
    
    if (!razon) {
        return; // Cancelado
    }
    
    if (razon.trim().length < 10) {
        alert('❌ La razón debe tener al menos 10 caracteres');
        return rechazarReporte(id); // Volver a preguntar
    }
    
    cambiarEstadoConRazon(id, 'Rechazado', razon);
}

async function cambiarEstadoConRazon(id, nuevoEstado, razon) {
    try {
        const response = await fetch(`/api/reportes/${id}/estado`, {
            method: 'PUT',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify({ 
                estado: nuevoEstado,
                razon_rechazo: razon
            })
        });
        
        const data = await response.json();
        
        if (response.ok) {
            alert('✅ ' + data.message);
            cerrarModal();
            cargarReportes();
            if (document.getElementById('seccion-analiticas')?.classList.contains('active')) {
                cargarAnaliticas();
            }
        } else {
            alert('❌ ' + data.error);
        }
    } catch (error) {
        alert('❌ Error al cambiar el estado');
    }
}

// ═══════════════════════════════════════════════════════════════════════════
// ANALÍTICAS (SOLO ADMIN)
// ═══════════════════════════════════════════════════════════════════════════

async function cargarAnaliticas() {
    try {
        // Cargar estadísticas
        const statsResponse = await fetch('/api/estadisticas');
        const stats = await statsResponse.json();
        
        // Actualizar tarjetas de estadísticas
        document.getElementById('stat-total').textContent = stats.Total;
        document.getElementById('stat-pendiente').textContent = stats.Pendiente;
        document.getElementById('stat-verificando').textContent = stats.Verificando;
        document.getElementById('stat-solucionado').textContent = stats.Solucionado;
        document.getElementById('stat-rechazado').textContent = stats.Rechazado;
        
        // Actualizar gráfico de barras
        const total = stats.Total || 1; // Evitar división por cero
        
        actualizarBarra('pendiente', stats.Pendiente, total);
        actualizarBarra('verificando', stats.Verificando, total);
        actualizarBarra('solucionado', stats.Solucionado, total);
        actualizarBarra('rechazado', stats.Rechazado, total);
        
        // Cargar reportes recientes
        const reportesResponse = await fetch('/api/reportes');
        const reportes = await reportesResponse.json();
        
        const container = document.getElementById('reportes-recientes');
        if (reportes.length === 0) {
            container.innerHTML = '<p class="cargando">No hay reportes aún.</p>';
        } else {
            container.innerHTML = '';
            // Mostrar solo los 6 más recientes
            reportes.slice(0, 6).forEach(reporte => {
                const card = crearTarjetaReporte(reporte);
                container.appendChild(card);
            });
        }
        
    } catch (error) {
        console.error('Error al cargar analíticas:', error);
    }
}

function actualizarBarra(estado, valor, total) {
    const porcentaje = total > 0 ? (valor / total) * 100 : 0;
    
    document.getElementById(`barra-${estado}`).style.width = `${porcentaje}%`;
    document.getElementById(`valor-${estado}`).textContent = valor;
}

// ═══════════════════════════════════════════════════════════════════════════
// MODAL - FUNCIONES GENERALES
// ═══════════════════════════════════════════════════════════════════════════

function abrirModal(contenido) {
    document.getElementById('modal-body').innerHTML = contenido;
    document.getElementById('modal-reporte').classList.remove('oculto');
}

function cerrarModal() {
    document.getElementById('modal-reporte').classList.add('oculto');
}

// Cerrar modal al hacer clic fuera
document.addEventListener('click', function(e) {
    const modal = document.getElementById('modal-reporte');
    if (e.target === modal) {
        cerrarModal();
    }
});

// ═══════════════════════════════════════════════════════════════════════════
// FUNCIONES AUXILIARES
// ═══════════════════════════════════════════════════════════════════════════

function mostrarMensaje(elemento, texto, tipo) {
    elemento.textContent = texto;
    elemento.className = `mensaje ${tipo}`;
    elemento.classList.remove('oculto');
    
    // Ocultar después de 5 segundos
    setTimeout(() => {
        elemento.classList.add('oculto');
    }, 5000);
}

function formatearFecha(fechaString) {
    const fecha = new Date(fechaString);
    const ahora = new Date();
    const diferencia = ahora - fecha;
    
    const minutos = Math.floor(diferencia / 60000);
    const horas = Math.floor(diferencia / 3600000);
    const dias = Math.floor(diferencia / 86400000);
    
    if (minutos < 1) return 'Hace un momento';
    if (minutos < 60) return `Hace ${minutos} min`;
    if (horas < 24) return `Hace ${horas} h`;
    if (dias < 7) return `Hace ${dias} días`;
    
    return fecha.toLocaleDateString('es-ES', {
        day: '2-digit',
        month: '2-digit',
        year: 'numeric'
    });
}

function escapeHtml(text) {
    const map = {
        '&': '&amp;',
        '<': '&lt;',
        '>': '&gt;',
        '"': '&quot;',
        "'": '&#039;'
    };
    return text.replace(/[&<>"']/g, m => map[m]);
}

function esAdmin() {
    // Verificar si el elemento de analíticas existe (solo visible para admin)
    return document.getElementById('seccion-analiticas') !== null;
}