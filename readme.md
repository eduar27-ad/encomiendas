{% extends "base.html" %}
{% block content %}

<div class="container-fluid px-4">
    <h1 class="text-center my-3">Dashboard de Gestión</h1>

    <div id="loadingIndicator" class="alert alert-info" style="display: none;">
        Cargando datos...
    </div>

    <div id="errorMessage" class="alert alert-danger" style="display: none;">
    </div>

    <!-- Fila principal con dos columnas -->
    <div class="row mb-4">
        <!-- Columna izquierda: Mapa de Estacionamientos -->
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h2 class="h5 mb-0">Mapa de Estacionamientos</h2>
                </div>
                <div class="card-body">
                    <div id="mapaEstacionamientos" class="row row-cols-5 g-2">
                        {% for garaje in garajes %}
                        <div class="col">
                            <div class="estacionamiento {{ garaje['estado'] }} p-2 text-center text-white" data-id="{{ garaje['id'] }}">
                                {{ garaje['id'] }}
                            </div>
                        </div>
                        {% endfor %}
                    </div>
                    <div class="mt-3">
                        <span class="badge bg-success">Disponible</span>
                        <span class="badge bg-warning text-dark">Ocupado</span>
                        <span class="badge bg-danger">Fuera de servicio</span>
                    </div>
                </div>
            </div>
        </div>
        <!-- Columna derecha: Gráfico de Distribución de Estados -->
        <div class="col-md-6">
            <div class="card">
                <div class="card-header">
                    <h2 class="h5 mb-0">Distribución de Estados</h2>
                </div>
                <div class="card-body">
                    <canvas id="estadosChart"></canvas>
                </div>
            </div>
        </div>
    </div>

    <!-- Fila de Conteo de Estados -->
    <div class="row mb-4">
        <div class="col-12">
            <div class="card">
                <div class="card-header">
                    <h2 class="h5 mb-0">Conteo de Estados</h2>
                </div>
                <div class="card-body">
                    <ul class="list-group" id="conteo-estados">
                    {% for estado, cantidad in estados_estacionamientos.items() %}
                        <li class="list-group-item d-flex justify-content-between align-items-center">
                            {{ estado | capitalize }}
                            <span class="badge bg-{{ 'success' if estado == 'disponible' else 'warning' if estado == 'ocupado' else 'danger' }} rounded-pill">{{ cantidad }}</span>
                        </li>
                    {% endfor %}
                    </ul>
                </div>
            </div>
        </div>
    </div>

    <!-- Fila de Últimas Alertas -->
    <div class="row">
        <div class="col-12">
            <div class="card">
                <div class="card-header d-flex justify-content-between align-items-center">
                    <h2 class="h5 mb-0">Últimas Alertas</h2>
                    <span class="badge bg-danger" id="alertas-no-leidas">0</span>
                </div>
                <div class="card-body">
                    <div class="mb-3">
                        <label for="filtroTipoAlerta" class="form-label">Tipo de Alerta:</label>
                        <select class="form-select" id="filtroTipoAlerta">
                            <option value="todas">Todas</option>
                            <option value="error">Error</option>
                            <option value="advertencia">Advertencia</option>
                            <option value="info">Información</option>
                        </select>
                    </div>
                    <div class="mb-3">
                        <label for="filtroFechaAlerta" class="form-label">Fecha:</label>
                        <input type="date" class="form-control" id="filtroFechaAlerta">
                    </div>
                    <ul class="list-group" id="lista-alertas">
                        {% for alerta in alertas %}
                        <li class="list-group-item d-flex justify-content-between align-items-center" data-tipo="{{ alerta['tipo'] }}" data-fecha="{{ alerta['fecha'] }}">
                            <span>
                                <strong>{{ alerta['fecha'] }}:</strong> {{ alerta['mensaje'] }}
                            </span>
                            <button class="btn btn-sm btn-outline-secondary marcar-leida" data-id="{{ alerta['id'] }}">Marcar como leída</button>
                        </li>
                        {% endfor %}
                    </ul>
                </div>
            </div>
        </div>
    </div>
</div>

<!-- Modal de detalles del estacionamiento -->
<div class="modal fade" id="estacionamientoModal" tabindex="-1" aria-labelledby="estacionamientoModalLabel" aria-hidden="true">
    <div class="modal-dialog">
      <div class="modal-content">
        <div class="modal-header">
          <h5 class="modal-title" id="estacionamientoModalLabel">Detalles del Estacionamiento</h5>
          <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
        </div>
        <div class="modal-body">
          <p><strong>ID:</strong> <span id="estacionamientoId"></span></p>
          <p><strong>Estado:</strong> <span id="estacionamientoEstado"></span></p>
          <p><strong>Última vez de uso:</strong> <span id="estacionamientoUltimoUso"></span></p>
          <div id="infoOcupado" style="display: none;">
            <p><strong>Usuario actual:</strong> <span id="estacionamientoUsuario"></span></p>
            <p><strong>Tiempo de ocupación:</strong> <span id="estacionamientoTiempoOcupacion"></span></p>
          </div>
        </div>
        <div class="modal-footer">
          <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
          <button type="button" class="btn btn-primary" id="btnLiberar" style="display: none;">Liberar Estacionamiento</button>
          <button type="button" class="btn btn-success" id="btnCambiarEstado">Poner Fuera de Servicio</button>
        </div>
      </div>
    </div>
  </div>

{% endblock %}

{% block extra_css %}
<style>
    .estacionamiento {
        height: 60px;
        border-radius: 4px;
        border: 1px solid #ddd;
        cursor: pointer;
        font-size: 1.2em;
        font-weight: bold;
        display: flex;
        align-items: center;
        justify-content: center;
    }
    .disponible { background-color: #28a745; }
    .ocupado { background-color: #ffc107; color: #212529; }
    .fuera_de_servicio { background-color: #dc3545; }
</style>
{% endblock %}

{% block extra_js %}
<script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
<script>
    // Datos del gráfico pasados desde Python
    var estadosEstacionamientos = JSON.parse('{{ estados_estacionamientos | tojson | safe }}');

    // Configuración del gráfico circular
    const ctx = document.getElementById('estadosChart').getContext('2d');
    const estadosChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Disponible', 'Ocupado', 'Fuera de servicio'],
            datasets: [{
                data: [
                    estadosEstacionamientos['disponible'] || 0,
                    estadosEstacionamientos['ocupado'] || 0,
                    estadosEstacionamientos['fuera_de_servicio'] || 0
                ],
                backgroundColor: ['#28a745', '#ffc107', '#dc3545']
            }]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'bottom',
                }
            }
        }
    });

    // Función para actualizar el estado de un estacionamiento
    function actualizarEstacionamiento(id, nuevoEstado) {
        const estacionamiento = document.querySelector(`.estacionamiento[data-id="${id}"]`);
        if (estacionamiento && estacionamiento.classList[1] !== nuevoEstado) {
            estacionamiento.className = `estacionamiento ${nuevoEstado} p-2 text-center text-white`;
            
            // Actualizar el conteo y el gráfico solo si ha habido un cambio
            actualizarConteoEstados();
            actualizarGrafico();
        }
    }

    // Función para actualizar el conteo de estados
    function actualizarConteoEstados() {
        const conteoEstados = {
            disponible: document.querySelectorAll('.estacionamiento.disponible').length,
            ocupado: document.querySelectorAll('.estacionamiento.ocupado').length,
            fuera_de_servicio: document.querySelectorAll('.estacionamiento.fuera_de_servicio').length
        };
        
        const conteoList = document.getElementById('conteo-estados');
        conteoList.innerHTML = '';
        for (const [estado, cantidad] of Object.entries(conteoEstados)) {
            conteoList.innerHTML += `
                <li class="list-group-item d-flex justify-content-between align-items-center">
                    ${estado.charAt(0).toUpperCase() + estado.slice(1)}
                    <span class="badge bg-${estado === 'disponible' ? 'success' : estado === 'ocupado' ? 'warning' : 'danger'} rounded-pill">${cantidad}</span>
                </li>
            `;
        }
    }

    // Función para actualizar el gráfico
    function actualizarGrafico() {
        const conteoEstados = {
            disponible: document.querySelectorAll('.estacionamiento.disponible').length,
            ocupado: document.querySelectorAll('.estacionamiento.ocupado').length,
            fuera_de_servicio: document.querySelectorAll('.estacionamiento.fuera_de_servicio').length
        };
        
        estadosChart.data.datasets[0].data = [
            conteoEstados.disponible,
            conteoEstados.ocupado,
            conteoEstados.fuera_de_servicio
        ];
        estadosChart.update();
    }

    // Función para mostrar el indicador de carga
    function mostrarCargando() {
        document.getElementById('loadingIndicator').style.display = 'block';
    }

    // Función para ocultar el indicador de carga
    function ocultarCargando() {
        document.getElementById('loadingIndicator').style.display = 'none';
    }

    // Función para mostrar mensajes de error
    function mostrarError(mensaje) {
        const errorDiv = document.getElementById('errorMessage');
        errorDiv.textContent = mensaje;
        errorDiv.style.display = 'block';
        setTimeout(() => {
            errorDiv.style.display = 'none';
        }, 5000);  // El mensaje de error desaparecerá después de 5 segundos
    }

    // Función para actualizar alertas
    function actualizarAlertas(alertas) {
        const listaAlertas = document.getElementById('lista-alertas');
        listaAlertas.innerHTML = '';
        alertas.forEach(alerta => {
            listaAlertas.innerHTML += `
                <li class="list-group-item d-flex justify-content-between align-items-center" data-tipo="${alerta.tipo}" data-fecha="${alerta.fecha}">
                    <span>
                        <strong>${alerta.fecha}:</strong> ${alerta.mensaje}
                    </span>
                    <button class="btn btn-sm btn-outline-secondary marcar-leida" data-id="${alerta.id}">Marcar como leída</button>
                </li>
            `;
        });
        actualizarContadorAlertas();
    }

    // Función para actualizar el contador de alertas
    function actualizarContadorAlertas() {
        const alertasNoLeidas = document.querySelectorAll('#lista-alertas li').length;
        document.getElementById('alertas-no-leidas').textContent = alertasNoLeidas;
    }

    function obtenerActualizaciones() {
        mostrarCargando();
        fetch('/get_updates')
            .then(response => {
                if (!response.ok) {
                    throw new Error('Error en la respuesta del servidor');
                }
                return response.json();
            })
            .then(data => {
                data.garajes.forEach(garaje => {
                    actualizarEstacionamiento(garaje.id, garaje.estado);
                });
                actualizarAlertas(data.alertas);
            })
            .catch(error => {
                console.error('Error al obtener actualizaciones:', error);
                mostrarError('Hubo un problema al actualizar los datos. Por favor, intente de nuevo más tarde.');
            })
            .finally(() => {
                ocultarCargando();
            });
    }

    // Event listeners para los estacionamientos
    document.querySelectorAll('.estacionamiento').forEach(item => {
        item.addEventListener('click', event => {
            const id = event.target.dataset.id;
            const estado = event.target.classList[1];
            
            // Aquí deberías hacer una llamada al servidor para obtener los detalles del estacionamiento
            // Por ahora, simularemos algunos datos
            const detalles = {
                id: id,
                estado: estado,
                ultimoUso: '2023-08-29 15:30',
                usuario: 'Juan Pérez',
                tiempoOcupacion: '2 horas 15 minutos'
            };
            
            mostrarDetallesEstacionamiento(detalles);
        });
    });

    // Función para mostrar detalles del estacionamiento
    function mostrarDetallesEstacionamiento(detalles) {
        document.getElementById('estacionamientoId').textContent = detalles.id;
        document.getElementById('estacionamientoEstado').textContent = detalles.estado;
        document.getElementById('estacionamientoUltimoUso').textContent = detalles.ultimoUso;
        
        const infoOcupado = document.getElementById('infoOcupado');
        const btnLiberar = document.getElementById('btnLiberar');
        const btnCambiarEstado = document.getElementById('btnCambiarEstado');

        if (detalles.estado === 'fuera_de_servicio') {
            btnCambiarEstado.textContent = 'Poner en Servicio';
            btnCambiarEstado.classList.remove('btn-danger');
            btnCambiarEstado.classList.add('btn-success');
        } else {
            btnCambiarEstado.textContent = 'Poner Fuera de Servicio';
            btnCambiarEstado.classList.remove('btn-success');
            btnCambiarEstado.classList.add('btn-danger');
        }

        new bootstrap.Modal(document.getElementById('estacionamientoModal')).show();
    }

    // Event listener para el botón de liberar
    document.getElementById('btnLiberar').addEventListener('click', () => {
        const id = document.getElementById('estacionamientoId').textContent;
        mostrarCargando();
        fetch('/actualizar_estacionamiento', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({id: id, estado: 'disponible'})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                actualizarEstacionamiento(id, 'disponible');
                bootstrap.Modal.getInstance(document.getElementById('estacionamientoModal')).hide();
            } else {
                throw new Error('No se pudo liberar el estacionamiento');
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarError('No se pudo liberar el estacionamiento. Por favor, intente de nuevo.');
        })
        .finally(() => {
            ocultarCargando();
        });
    });

    // Event listener para el botón de poner fuera de servicio
    document.getElementById('btnCambiarEstado').addEventListener('click', () => {
        const id = document.getElementById('estacionamientoId').textContent;
        const estadoActual = document.getElementById('estacionamientoEstado').textContent;
        const nuevoEstado = estadoActual === 'fuera_de_servicio' ? 'disponible' : 'fuera_de_servicio';
        
        mostrarCargando();
        fetch('/actualizar_estacionamiento', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({id: id, estado: nuevoEstado})
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                actualizarEstacionamiento(id, nuevoEstado);
                const btn = document.getElementById('btnCambiarEstado');
                if (nuevoEstado === 'fuera_de_servicio') {
                    btn.textContent = 'Poner en Servicio';
                    btn.classList.remove('btn-danger');
                    btn.classList.add('btn-success');
                } else {
                    btn.textContent = 'Poner Fuera de Servicio';
                    btn.classList.remove('btn-success');
                    btn.classList.add('btn-danger');
                }
                document.getElementById('estacionamientoEstado').textContent = nuevoEstado;
            } else {
                throw new Error(`No se pudo cambiar el estado del estacionamiento a ${nuevoEstado}`);
            }
        })
        .catch(error => {
            console.error('Error:', error);
            mostrarError(`No se pudo actualizar el estado del estacionamiento. Por favor, intente de nuevo.`);
        })
        .finally(() => {
            ocultarCargando();
        });
    });

    // Inicializar las actualizaciones
    obtenerActualizaciones();
    setInterval(obtenerActualizaciones, 10000);  // Actualizar cada 10 segundos
</script>
{% endblock %}
