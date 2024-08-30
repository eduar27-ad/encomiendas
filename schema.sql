-- Elimina las tablas si existen para evitar conflictos
DROP TABLE IF EXISTS usuarios;
DROP TABLE IF EXISTS encomiendas;
DROP TABLE IF EXISTS garajes;
DROP TABLE IF EXISTS alertas;

-- Crea la tabla de usuarios
CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    identificacion TEXT UNIQUE NOT NULL,
    clave_dinamica TEXT NOT NULL
);

-- Crea la tabla de encomiendas
CREATE TABLE encomiendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destinatario_id INTEGER NOT NULL,
    descripcion TEXT NOT NULL,
    peso REAL NOT NULL,
    dimensiones TEXT,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_entrega TIMESTAMP,
    FOREIGN KEY (destinatario_id) REFERENCES usuarios (id)
);

-- Crea la tabla de garajes
CREATE TABLE garajes (
    id TEXT PRIMARY KEY,
    estado TEXT NOT NULL
);

-- Crea la tabla de alertas
CREATE TABLE alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mensaje TEXT NOT NULL,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Inicializa los garajes
INSERT INTO garajes (id, estado) VALUES
('A1', 'disponible'), ('A2', 'disponible'), ('A3', 'disponible'), ('A4', 'disponible'), ('A5', 'disponible'),
('B1', 'disponible'), ('B2', 'disponible'), ('B3', 'disponible'), ('B4', 'disponible'), ('B5', 'disponible');

-- Inserta usuarios de ejemplo
INSERT INTO usuarios (username, password, identificacion, clave_dinamica) VALUES
('Eduar de Jesus Pila Franco', 'macguiver15', '1003294451', '2712'),
('Moises Guzman Tovar', '2704', '1003309107', '1234');

-- Inserta encomiendas de ejemplo
INSERT INTO encomiendas (destinatario_id, descripcion, peso) VALUES
(1, 'Paquete grande', 5.0),
(1, 'Sobre urgente', 0.5),
(2, 'Caja mediana', 3.0);