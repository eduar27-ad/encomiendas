
<!DOCTYPE html>
<html lang="es">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sistema de Gestión de Encomiendas</title>
    <link href="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/css/bootstrap.min.css" rel="stylesheet">
    <style>
        .estacionamiento { width: 100%; height: 50px; }
        .disponible { background-color: #28a745; }
        .ocupado { background-color: #ffc107; }
        .fuera-de-servicio { background-color: #dc3545; }
    </style>
</head>
<body>
    <div class="container">
        <h1 class="text-center mb-4">Sistema de Gestión de Encomiendas</h1>

        <h2 class="text-center mb-3">Estado de Estacionamientos</h2>
        <div id="estacionamientos" class="row justify-content-center mb-4">
            {% for estacionamiento in estacionamientos %}
            <div class="col-2 m-2">
                <div class="estacionamiento {{ estacionamiento.estado }} p-3 text-center text-white">
                    {{ estacionamiento.id }}
                </div>
            </div>
            {% endfor %}
        </div>

        <!-- Leyenda de Estados -->
        <div class="row justify-content-center mb-5">
            <div class="col-auto">
                <div class="d-flex align-items-center">
                    <div class="estacionamiento disponible me-2" style="width: 20px; height: 20px;"></div>
                    <span>Disponible</span>
                </div>
            </div>
            <div class="col-auto">
                <div class="d-flex align-items-center">
                    <div class="estacionamiento ocupado me-2" style="width: 20px; height: 20px;"></div>
                    <span>Ocupado</span>
                </div>
            </div>
            <div class="col-auto">
                <div class="d-flex align-items-center">
                    <div class="estacionamiento fuera-de-servicio me-2" style="width: 20px; height: 20px;"></div>
                    <span>Fuera de Servicio</span>
                </div>
            </div>
        </div>

        <div class="row mb-4">
            <div class="col-md-6 offset-md-3">
                <h3>Consultar Encomienda</h3>
                <form id="consultaForm">
                    <div class="mb-3">
                        <input type="text" class="form-control" name="identificacion" placeholder="Identificación del Usuario" required>
                    </div>
                    <div class="mb-3">
                        <input type="text" class="form-control" name="clave_dinamica" placeholder="Clave Dinámica" required>
                    </div>
                    <button type="submit" class="btn btn-primary">Consultar</button>
                </form>
            </div>
        </div>

        <div id="resultadoConsulta" class="row mb-4" style="display: none;">
            <div class="col-md-6 offset-md-3">
                <div class="card">
                    <div class="card-body">
                        <h5 class="card-title">Resultado de la Consulta</h5>
                        <div id="infoUsuario"></div>
                        <div id="listaEncomiendas"></div>
                        <button id="btnEntrada" class="btn btn-success mt-3" style="display: none;">Activar Entrada</button>
                    </div>
                </div>
            </div>
        </div>
    </div>

    <div id="alertaPersonalizada" class="modal fade" tabindex="-1">
        <div class="modal-dialog">
            <div class="modal-content">
                <div class="modal-header">
                    <h5 class="modal-title">Asignación de Estacionamiento</h5>
                    <button type="button" class="btn-close" data-bs-dismiss="modal" aria-label="Close"></button>
                </div>
                <div class="modal-body">
                    <p id="mensajeAlerta"></p>
                </div>
                <div class="modal-footer">
                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Cerrar</button>
                </div>
            </div>
        </div>
    </div>    

    <script src="https://cdn.jsdelivr.net/npm/bootstrap@5.1.3/dist/js/bootstrap.bundle.min.js"></script>
    <script>
        document.getElementById('consultaForm').addEventListener('submit', function(e) {
            e.preventDefault();
            // Simulación de consulta al servidor
            document.getElementById('resultadoConsulta').style.display = 'block';
            document.getElementById('infoUsuario').innerHTML = '<p>Usuario: Usuario de Prueba</p>';
            document.getElementById('listaEncomiendas').innerHTML = '<h6>Encomiendas pendientes:</h6><ul><li>Paquete 1 - Llegó: 2023-08-23</li><li>Paquete 2 - Llegó: 2023-08-24</li></ul>';
            document.getElementById('btnEntrada').style.display = 'block';
        });
        
        document.getElementById('btnEntrada').addEventListener('click', function() {
            // Simulación de asignación de estacionamiento
            const estacionamientoAsignado = 'A3'; // Esto vendría del servidor en una implementación real
            
            // Cambiar el color del estacionamiento asignado
            const estacionamientos = document.querySelectorAll('.estacionamiento');
            estacionamientos.forEach(est => {
                if (est.textContent.trim() === estacionamientoAsignado) {
                    est.classList.remove('disponible');
                    est.classList.add('ocupado');
                }
            });
        
            // Mostrar alerta personalizada
            const mensajeAlerta = `Se ha asignado el estacionamiento ${estacionamientoAsignado}.`;
            document.getElementById('mensajeAlerta').textContent = mensajeAlerta;
            const modal = new bootstrap.Modal(document.getElementById('alertaPersonalizada'));
            modal.show();
        });
        </script>
</body>
</html>