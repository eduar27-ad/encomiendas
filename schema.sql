DROP TABLE IF EXISTS usuarios;
DROP TABLE IF EXISTS encomiendas;
DROP TABLE IF EXISTS garajes;
DROP TABLE IF EXISTS alertas;

CREATE TABLE usuarios (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    username TEXT UNIQUE NOT NULL,
    password TEXT NOT NULL,
    identificacion TEXT UNIQUE NOT NULL,
    email TEXT UNIQUE NOT NULL
);

CREATE TABLE encomiendas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    destinatario_id INTEGER NOT NULL,
    descripcion TEXT,
    fecha_llegada TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    fecha_entrega TIMESTAMP,
    garaje_id TEXT,
    FOREIGN KEY (destinatario_id) REFERENCES usuarios (id),
    FOREIGN KEY (garaje_id) REFERENCES garajes (id)
);

CREATE TABLE garajes (
    id TEXT PRIMARY KEY,
    nombre TEXT NOT NULL,
    estado TEXT NOT NULL
);

CREATE TABLE alertas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    mensaje TEXT NOT NULL,
    fecha TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Inicializar garajes
INSERT INTO garajes (id, nombre, estado) VALUES
('A1', 'Garaje A1', 'disponible'), ('A2', 'Garaje A2', 'disponible'), 
('A3', 'Garaje A3', 'disponible'), ('A4', 'Garaje A4', 'disponible'), 
('A5', 'Garaje A5', 'disponible'), ('B1', 'Garaje B1', 'disponible'), 
('B2', 'Garaje B2', 'disponible'), ('B3', 'Garaje B3', 'disponible'), 
('B4', 'Garaje B4', 'disponible'), ('B5', 'Garaje B5', 'disponible');

-- Insertar algunos usuarios de ejemplo
INSERT INTO usuarios (username, password, identificacion, email) VALUES
('EduarPila', 'macguiver15', '1003294451', 'Edupilafra22@gmail.com'),
('LedisPila', 'colombia07', '25999000', 'ledispila@gmail.com');

-- Insertar algunas encomiendas de ejemplo
INSERT INTO encomiendas (destinatario_id, descripcion, garaje_id) VALUES
(1, 'Paquete grande', 'A1'),
(2, 'Sobre urgente', 'B2');

-- Actualizar el estado de los garajes correspondientes
UPDATE garajes SET estado = 'ocupado' WHERE id IN ('A1', 'B2');