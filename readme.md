

////////////////////////////////////////

{% extends "base.html" %}
{% block content %}
<div class="container-fluid px-4">
    <h1 class="text-center my-2">Sistema de Gestión de Encomiendas</h1>
    
    <div class="row g-2">
        <div class="col-md-8">
            <div class="card">
                <div class="card-header py-2">
                    <h4 class="mb-0">Estado de Estacionamientos</h4>
                </div>
                <div class="card-body">
                    <div id="estacionamientos" class="row row-cols-5 g-1 mb-2">
                        {% for estacionamiento in estacionamientos %}
                        <div class="col">
                            <div class="estacionamiento {{ estacionamiento.estado }} p-1 text-center text-white" data-id="{{ estacionamiento.id }}">
                                {{ estacionamiento.id }}
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    <div class="d-flex justify-content-center small">
                        <span class="badge bg-success me-1">Disponible</span>
                        <span class="badge bg-warning text-dark me-1">Ocupado</span>
                        <span class="badge bg-danger">Fuera de servicio</span>
                    </div>
                </div>
            </div>
            <div class="card mt-2">
                <div class="card-header py-2">
                    <h5 class="mb-0">Notificaciones</h5>
                </div>
                <div class="card-body py-2" id="notificaciones">
                    <!-- Las notificaciones se actualizarán dinámicamente aquí -->
                </div>
            </div>
        </div>
        <div class="col-md-4">
            <div class="card">
                <div class="card-header py-2">
                    <h4 class="mb-0">Consultar Encomienda</h4>
                </div>
                <div class="card-body">
                    <form id="consultaForm">
                        <div class="mb-2">
                            <input type="text" class="form-control form-control-sm" name="identificacion" placeholder="Identificación del Usuario" required>
                        </div>
                        <div class="mb-2">
                            <input type="text" class="form-control form-control-sm" name="clave_dinamica" placeholder="Clave Dinámica" required>
                        </div>
                        <button type="submit" class="btn btn-primary btn-sm">Consultar</button>
                    </form>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Modal para mostrar resultados de consulta -->
<div class="modal fade" id="resultadoConsultaModal" tabindex="-1" aria-labelledby="resultadoConsultaModalLabel" aria-hidden="true">
    <div class="modal-dialog">
        <div class="modal-content">
            <div class="modal-header">
                <h5 class="modal-title" id="resultadoConsultaModalLabel">Resultado de la Consulta</h5>
                <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
            </div>
            <div class="modal-body">
                <div id="modalMessage" class="alert d-none"></div>
                <div id="infoUsuario"></div>
                <div id="listaEncomiendas" class="mt-3">
                    <h6 class="mb-2">Encomiendas pendientes:</h6>
                    <div id="encomiendas-list"></div>
                </div>
            </div>
            <div class="modal-footer">
                <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                <button type="button" class="btn btn-primary" id="btnActivarEntrada">Activar Entrada</button>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script>
    // Función para actualizar el estado de los estacionamientos
    function actualizarEstacionamientos(estacionamientos) {
        const container = document.getElementById('estacionamientos');
        container.innerHTML = '';
        estacionamientos.forEach(estacionamiento => {
            const div = document.createElement('div');
            div.className = 'col';
            div.innerHTML = `
                <div class="estacionamiento ${estacionamiento.estado} p-1 text-center text-white" data-id="${estacionamiento.id}">
                    ${estacionamiento.id}
                </div>
            `;
            container.appendChild(div);
        });
    }

    // Función para actualizar las notificaciones
    function actualizarNotificaciones(notificaciones) {
        const container = document.getElementById('notificaciones');
        container.innerHTML = notificaciones.length > 0 
            ? notificaciones.map(n => `<div class="alert alert-info py-1 mb-1">${n}</div>`).join('') 
            : '<p class="mb-0">No hay notificaciones nuevas.</p>';
    }

    // Función para obtener actualizaciones del servidor
    function obtenerActualizaciones() {
        fetch('/get_updates')
            .then(response => response.json())
            .then(data => {
                actualizarEstacionamientos(data.garajes);
                actualizarNotificaciones(data.alertas.map(a => a.mensaje));
            })
            .catch(error => console.error('Error al obtener actualizaciones:', error));
    }

    // Manejar el envío del formulario de consulta
    document.getElementById('consultaForm').addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(this);
        fetch('/consultar_encomienda', {
            method: 'POST',
            body: formData
        })
        .then(response => response.json())
        .then(data => {
            const modal = new bootstrap.Modal(document.getElementById('resultadoConsultaModal'));
            if (data.success) {
                document.getElementById('infoUsuario').textContent = `Usuario: ${data.usuario}`;
                const encomiendasList = document.getElementById('encomiendas-list');
                encomiendasList.innerHTML = data.encomiendas.map(e => 
                    `<div class="form-check">
                        <input class="form-check-input" type="checkbox" value="${e.id}" id="encomienda${e.id}">
                        <label class="form-check-label" for="encomienda${e.id}">
                            ${e.descripcion} - Llegó: ${e.fecha}
                        </label>
                    </div>`
                ).join('');
                document.getElementById('modalMessage').classList.add('d-none');
            } else {
                document.getElementById('modalMessage').textContent = data.message;
                document.getElementById('modalMessage').classList.remove('d-none');
                document.getElementById('infoUsuario').textContent = '';
                document.getElementById('encomiendas-list').innerHTML = '';
            }
            modal.show();
        })
        .catch(error => console.error('Error:', error));
    });

    // Manejar la activación de entrada
    document.getElementById('btnActivarEntrada').addEventListener('click', function() {
        fetch('/activar_entrada', {
            method: 'POST'
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                alert(`Se ha asignado el estacionamiento ${data.garaje}`);
                obtenerActualizaciones();  // Actualizar el estado de los estacionamientos
            } else {
                alert(data.message);
            }
        })
        .catch(error => console.error('Error:', error));
    });

    // Iniciar actualizaciones automáticas
    obtenerActualizaciones();
    setInterval(obtenerActualizaciones, 30000);  // Actualizar cada 30 segundos
</script>
{% endblock %}
