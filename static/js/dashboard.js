console.log("Dashboard script iniciado");

document.addEventListener('DOMContentLoaded', function() {
    console.log("DOM completamente cargado y analizado");

    const parkingSpots = document.querySelectorAll('.parking-spot');
    const parkingDetailModal = new bootstrap.Modal(document.getElementById('parkingDetailModal'));
    const releaseBtn = document.getElementById('release-btn');
    const outOfServiceBtn = document.getElementById('out-of-service-btn');
    const confirmOutOfServiceBtn = document.getElementById('confirm-out-of-service');
    let currentSpotId = null;

    console.log("Número de parking spots encontrados:", parkingSpots.length);

    parkingSpots.forEach(spot => {
        console.log("Añadiendo event listener a spot:", spot.dataset.id);
        spot.addEventListener('click', function() {
            console.log("Spot clicked:", this.dataset.id);
            currentSpotId = this.dataset.id;
            showParkingDetails(this.dataset.id);
        });
    });
    

    function showParkingDetails(spotId) {
        console.log("Intentando mostrar detalles para el estacionamiento:", spotId);
        fetch(`/api/parking-spot/${spotId}`)
            .then(response => {
                console.log("Respuesta recibida:", response);
                if (!response.ok) {
                    throw new Error(`HTTP error! status: ${response.status}`);
                }
                return response.json();
            })
            .then(data => {
                console.log("Detalles del estacionamiento recibidos:", data);
                updateModalWithParkingDetails(data);
                parkingDetailModal.show();
            })
            .catch(error => {
                console.error('Error al obtener detalles del estacionamiento:', error);
                alert('Hubo un error al cargar los detalles del estacionamiento.');
            });
    }

    function updateModalWithParkingDetails(spotDetails) {
        console.log("Actualizando modal con detalles:", spotDetails);
        document.getElementById('parking-id').textContent = spotDetails.id;
        document.getElementById('parking-status').textContent = spotDetails.estado;

        const occupiedInfo = document.getElementById('occupied-info');
        const outOfServiceInfo = document.getElementById('out-of-service-info');

        if (spotDetails.estado === 'ocupado') {
            occupiedInfo.style.display = 'block';
            outOfServiceInfo.style.display = 'none';
            document.getElementById('current-user').textContent = spotDetails.usuario_actual || 'N/A';
            document.getElementById('entry-time').textContent = spotDetails.hora_entrada || 'N/A';
            document.getElementById('duration').textContent = calculateDuration(spotDetails.hora_entrada);
            releaseBtn.style.display = 'inline-block';
            outOfServiceBtn.style.display = 'none';
        } else if (spotDetails.estado === 'fuera-de-servicio') {
            occupiedInfo.style.display = 'none';
            outOfServiceInfo.style.display = 'block';
            document.getElementById('out-of-service-reason').textContent = spotDetails.razon || 'No especificada';
            releaseBtn.style.display = 'none';
            outOfServiceBtn.textContent = 'Volver a Servicio';
            outOfServiceBtn.style.display = 'inline-block';
        } else {
            occupiedInfo.style.display = 'none';
            outOfServiceInfo.style.display = 'none';
            releaseBtn.style.display = 'none';
            outOfServiceBtn.textContent = 'Marcar Fuera de Servicio';
            outOfServiceBtn.style.display = 'inline-block';
        }

        const lastUseInfo = spotDetails.ultimo_uso;
        if (lastUseInfo && lastUseInfo.usuario) {
            document.getElementById('last-use').textContent = lastUseInfo.salida || 'N/A';
            document.getElementById('last-duration').textContent = calculateDuration(lastUseInfo.entrada, lastUseInfo.salida);
            document.getElementById('last-user').textContent = lastUseInfo.usuario;
        } else {
            document.getElementById('last-use').textContent = 'N/A';
            document.getElementById('last-duration').textContent = 'N/A';
            document.getElementById('last-user').textContent = 'N/A';
        }
    }

    if (releaseBtn) {
        releaseBtn.addEventListener('click', function() {
            releaseParking(currentSpotId);
        });
    }

    if (outOfServiceBtn) {
        outOfServiceBtn.addEventListener('click', function() {
            if (outOfServiceBtn.textContent === 'Volver a Servicio') {
                returnToService(currentSpotId);
            } else {
                const outOfServiceModal = new bootstrap.Modal(document.getElementById('outOfServiceModal'));
                outOfServiceModal.show();
            }
        });
    }

    if (confirmOutOfServiceBtn) {
        confirmOutOfServiceBtn.addEventListener('click', function() {
            const reason = document.getElementById('out-of-service-reason-select').value;
            markOutOfService(currentSpotId, reason);
            const outOfServiceModal = bootstrap.Modal.getInstance(document.getElementById('outOfServiceModal'));
            outOfServiceModal.hide();
        });
    }

    function releaseParking(spotId) {
        console.log(`Intentando liberar estacionamiento: ${spotId}`);
        fetch(`/api/release-parking/${spotId}`, { 
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
        })
            .then(response => {
                console.log(`Respuesta recibida: ${response.status} ${response.statusText}`);
                if (!response.ok) {
                    return response.text().then(text => {
                        throw new Error(`HTTP error! status: ${response.status}, body: ${text}`);
                    });
                }
                return response.json();
            })
            .then(data => {
                console.log('Datos recibidos:', data);
                if (data.success) {
                    alert(data.message);
                    updateParkingSpotStatus(spotId, 'disponible');
                    parkingDetailModal.hide();
                    updateStatistics();
                    actualizarEstadoEstacionamientos();
                } else {
                    alert(data.message);
                }
            })
            .catch(error => {
                console.error('Error detallado:', error);
                alert(`Error al liberar el estacionamiento: ${error.message}`);
            });
    }

    function markOutOfService(spotId, reason) {
        fetch(`/api/mark-out-of-service/${spotId}`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ reason: reason })
        })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateParkingSpotStatus(spotId, 'fuera-de-servicio');
                    parkingDetailModal.hide();
                    updateStatistics();
                } else {
                    alert(data.message);
                }
            })
            .catch(error => console.error('Error:', error));
    }

    function returnToService(spotId) {
        fetch(`/api/return-to-service/${spotId}`, { method: 'POST' })
            .then(response => response.json())
            .then(data => {
                if (data.success) {
                    updateParkingSpotStatus(spotId, 'disponible');
                    parkingDetailModal.hide();
                    updateStatistics();
                } else {
                    alert(data.message);
                }
            })
            .catch(error => console.error('Error:', error));
    }

    function updateParkingSpotStatus(spotId, newStatus) {
        const spot = document.querySelector(`.parking-spot[data-id="${spotId}"]`);
        spot.classList.remove('disponible', 'ocupado', 'fuera-de-servicio');
        spot.classList.add(newStatus);
    }

    function updateStatistics() {
        document.getElementById('occupied-count').textContent = document.querySelectorAll('.parking-spot.ocupado').length;
        document.getElementById('available-count').textContent = document.querySelectorAll('.parking-spot.disponible').length;
        document.getElementById('out-of-service-count').textContent = document.querySelectorAll('.parking-spot.fuera-de-servicio').length;
    }

    function calculateDuration(startTime, endTime = new Date()) {
        const start = new Date(startTime);
        const end = endTime instanceof Date ? endTime : new Date(endTime);
        const diff = end - start;
        const hours = Math.floor(diff / 3600000);
        const minutes = Math.floor((diff % 3600000) / 60000);
        return `${hours}h ${minutes}m`;
    }

    updateStatistics();
    console.log("Estadísticas actualizadas");

    // Implementar el gráfico de ocupación
    const ctx = document.getElementById('occupationChart').getContext('2d');
    const occupationChart = new Chart(ctx, {
        type: 'pie',
        data: {
            labels: ['Disponibles', 'Ocupados', 'Fuera de Servicio'],
            datasets: [{
                data: [
                    document.querySelectorAll('.parking-spot.disponible').length,
                    document.querySelectorAll('.parking-spot.ocupado').length,
                    document.querySelectorAll('.parking-spot.fuera-de-servicio').length
                ],
                backgroundColor: [
                    'rgba(40, 167, 69, 0.8)',  // Verde para disponibles
                    'rgba(255, 193, 7, 0.8)',  // Amarillo para ocupados
                    'rgba(220, 53, 69, 0.8)'   // Rojo para fuera de servicio
                ]
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false
        }
    });

    // Función para actualizar el gráfico
    function updateOccupationChart() {
        occupationChart.data.datasets[0].data = [
            document.querySelectorAll('.parking-spot.disponible').length,
            document.querySelectorAll('.parking-spot.ocupado').length,
            document.querySelectorAll('.parking-spot.fuera-de-servicio').length
        ];
        occupationChart.update();
    }

    // Actualizar estadísticas y gráfico cada 30 segundos
    setInterval(() => {
        updateStatistics();
        updateOccupationChart();
    }, 30000);

    // Manejar acciones rápidas
    document.getElementById('refreshButton').addEventListener('click', function() {
        fetch('/api/refresh-dashboard')
            .then(response => response.json())
            .then(data => {
                updateDashboard(data);
            })
            .catch(error => console.error('Error:', error));
    });

    document.getElementById('generateReportButton').addEventListener('click', function() {
        // Aquí iría la lógica para generar el reporte
        console.log("Generando reporte...");
        alert("Funcionalidad de generación de reporte aún no implementada");
    });

    function updateDashboard(data) {
        // Actualizar estacionamientos
        data.estacionamientos.forEach(est => {
            updateParkingSpotStatus(est.id, est.estado);
        });

        // Actualizar estadísticas
        updateStatistics();

        // Actualizar gráfico
        updateOccupationChart();

        // Actualizar alertas
        const alertList = document.getElementById('alertList');
        alertList.innerHTML = '';
        data.alertas.forEach(alerta => {
            const li = document.createElement('li');
            li.className = 'list-group-item';
            li.textContent = `${alerta.mensaje} - ${alerta.fecha}`;
            alertList.appendChild(li);
        });

        // Actualizar entregas del día
        document.getElementById('daily-deliveries').textContent = data.entregasDelDia;
    }

    function actualizarEstadoEstacionamientos() {
        fetch('/api/estado-estacionamientos')
            .then(response => response.json())
            .then(data => {
                data.estacionamientos.forEach(est => {
                    updateParkingSpotStatus(est.id, est.estado);
                });
                updateStatistics();
                updateOccupationChart();
            })
            .catch(error => console.error('Error al actualizar estacionamientos:', error));
    }

    // Llamar a esta función periódicamente
    setInterval(actualizarEstadoEstacionamientos, 30000);

    // Y también llamarla inmediatamente al cargar la página
    actualizarEstadoEstacionamientos();

    console.log("Configuración del dashboard completada");
});