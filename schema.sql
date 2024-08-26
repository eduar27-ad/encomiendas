-- Eliminar las tablas si existen
DROP TABLE IF EXISTS usuarios;
DROP TABLE IF EXISTS encomiendas;
DROP TABLE IF EXISTS garajes;
DROP TABLE IF EXISTS alertas;
DROP TABLE IF EXISTS asignaciones;

-- Crear la tabla de usuarios
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    identificacion TEXT UNIQUE NOT NULL,
    clave_dinamica TEXT NOT NULL
);

-- Crear la tabla de encomiendas
CREATE TABLE encomiendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destinatario_id INTEGER NOT NULL,
    descripcion TEXT,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_entrega TIMESTAMP,
    FOREIGN KEY (destinatario_id) REFERENCES usuarios (id)
);

-- Crear la tabla de garajes
CREATE TABLE garajes (
    id TEXT PRIMARY KEY,
    estado TEXT NOT NULL
);

-- Crear la tabla de alertas
CREATE TABLE alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mensaje TEXT NOT NULL,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Crear la tabla de asignaciones
CREATE TABLE asignaciones (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    usuario_id INTEGER,
    garaje_id TEXT,
    fecha_entrada TIMESTAMP,
    fecha_salida TIMESTAMP,
    FOREIGN KEY (usuario_id) REFERENCES usuarios(id),
    FOREIGN KEY (garaje_id) REFERENCES garajes(id)
);

-- Inicializar los garajes
INSERT INTO garajes (id, estado) VALUES
('A1', 'disponible'), ('A2', 'disponible'), ('A3', 'disponible'), ('A4', 'disponible'), ('A5', 'disponible'),
('B1', 'disponible'), ('B2', 'disponible'), ('B3', 'disponible'), ('B4', 'disponible'), ('B5', 'disponible');

-- Insertar usuarios de ejemplo
INSERT INTO usuarios (username, password, identificacion, clave_dinamica) VALUES
('Eduar de Jesus Pila Franco', 'macguiver15', '1003294451', '2712'),
('Moises Guzman Tovar', '2704', '1003309107', '1234');

-- Insertar encomiendas de ejemplo
INSERT INTO encomiendas (destinatario_id, descripcion) VALUES
(1, 'Paquete grande'),
(1, 'Sobre urgente'),
(2, 'Caja mediana');