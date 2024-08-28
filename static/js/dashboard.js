document.addEventListener('DOMContentLoaded', function() {
    const parkingSpots = document.querySelectorAll('.parking-spot');
    const parkingDetailModal = new bootstrap.Modal(document.getElementById('parkingDetailModal'));
    const outOfServiceModal = new bootstrap.Modal(document.getElementById('outOfServiceModal'));

    // Añadir evento de clic a cada estacionamiento
    parkingSpots.forEach(spot => {
        spot.addEventListener('click', function() {
            const spotId = this.dataset.id;
            showParkingDetails(spotId);
        });
    });

    function showParkingDetails(spotId) {
        // Aquí deberías hacer una llamada AJAX para obtener los detalles del estacionamiento
        // Por ahora, usaremos datos de ejemplo
        const spotDetails = {
            id: spotId,
            status: 'ocupado',
            currentUser: 'Juan Pérez',
            entryTime: '2023-08-26 14:30',
            lastUse: '2023-08-25 10:15',
            lastDuration: '2h 30m',
            lastUser: 'María García'
        };

        document.getElementById('parking-id').textContent = spotDetails.id;
        document.getElementById('parking-status').textContent = spotDetails.status;

        const occupiedInfo = document.getElementById('occupied-info');
        if (spotDetails.status === 'ocupado') {
            occupiedInfo.style.display = 'block';
            document.getElementById('current-user').textContent = spotDetails.currentUser;
            document.getElementById('entry-time').textContent = spotDetails.entryTime;
            document.getElementById('duration').textContent = calculateDuration(spotDetails.entryTime);
            document.getElementById('release-btn').style.display = 'inline-block';
        } else {
            occupiedInfo.style.display = 'none';
            document.getElementById('release-btn').style.display = 'none';
        }

        document.getElementById('last-use').textContent = spotDetails.lastUse;
        document.getElementById('last-duration').textContent = spotDetails.lastDuration;
        document.getElementById('last-user').textContent = spotDetails.lastUser;

        parkingDetailModal.show();
    }

    function calculateDuration(entryTime) {
        const entry = new Date(entryTime);
        const now = new Date();
        const diff = now - entry;
        const hours = Math.floor(diff / 3600000);
        const minutes = Math.floor((diff % 3600000) / 60000);
        return `${hours}h ${minutes}m`;
    }

    // Aquí puedes añadir más funciones para manejar otras interacciones,
    // como liberar estacionamientos, marcar como fuera de servicio, etc.

    // Ejemplo de cómo actualizar las estadísticas
    function updateStatistics() {
        document.getElementById('occupied-count').textContent = document.querySelectorAll('.parking-spot.ocupado').length;
        document.getElementById('available-count').textContent = document.querySelectorAll('.parking-spot.disponible').length;
        document.getElementById('out-of-service-count').textContent = document.querySelectorAll('.parking-spot.fuera-de-servicio').length;
    }

    updateStatistics();

    // Aquí puedes añadir código para inicializar y actualizar el gráfico de ocupación usando Chart.js
});
