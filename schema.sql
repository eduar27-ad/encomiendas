DROP TABLE IF EXISTS usuarios;
DROP TABLE IF EXISTS encomiendas;
DROP TABLE IF EXISTS garajes;

CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    identificacion TEXT UNIQUE NOT NULL,
    clave_dinamica TEXT NOT NULL
);

CREATE TABLE encomiendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destinatario_id INTEGER NOT NULL,
    descripcion TEXT,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_entrega TIMESTAMP,
    FOREIGN KEY (destinatario_id) REFERENCES usuarios (id)
);

CREATE TABLE garajes (
    id TEXT PRIMARY KEY,
    estado TEXT NOT NULL
);

-- Inicializar garajes
INSERT INTO garajes (id, estado) VALUES
('A1', 'disponible'), ('A2', 'disponible'), ('A3', 'disponible'), ('A4', 'disponible'), ('A5', 'disponible'),
('B1', 'disponible'), ('B2', 'disponible'), ('B3', 'disponible'), ('B4', 'disponible'), ('B5', 'disponible');

-- Insertar algunos usuarios de ejemplo
INSERT INTO usuarios (username, password, identificacion, clave_dinamica) VALUES
('usuario1', 'password1', 'ID001', '1234'),
('usuario2', 'password2', 'ID002', '5678');

-- Insertar algunas encomiendas de ejemplo
INSERT INTO encomiendas (destinatario_id, descripcion) VALUES
(1, 'Paquete grande'),
(1, 'Sobre urgente'),
(2, 'Caja mediana');