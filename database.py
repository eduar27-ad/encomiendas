import sqlite3

def crear_tablas():
    conn = sqlite3.connect('parqueadero.db')
    c = conn.cursor()
    
    # Crear tabla de garajes
    c.execute('''CREATE TABLE IF NOT EXISTS garajes
                 (id INTEGER PRIMARY KEY,
                  estado TEXT,
                  tiempo_limite TEXT)''')
    
    # Crear tabla de encomiendas
    c.execute('''CREATE TABLE IF NOT EXISTS encomiendas
                 (id INTEGER PRIMARY KEY AUTOINCREMENT,
                  cliente TEXT,
                  tipo TEXT,
                  garaje_asignado INTEGER,
                  tiempo_ingreso TEXT,
                  FOREIGN KEY(garaje_asignado) REFERENCES garajes(id))''')
    
    conn.commit()
    conn.close()

def inicializar_garajes():
    conn = sqlite3.connect('parqueadero.db')
    c = conn.cursor()
    
    # Verificar si ya existen garajes
    c.execute("SELECT COUNT(*) FROM garajes")
    if c.fetchone()[0] == 0:
        # Si no hay garajes, crear 5 iniciales
        for i in range(1, 6):
            c.execute("INSERT INTO garajes (id, estado) VALUES (?, ?)", (i, "disponible"))
    
    conn.commit()
    conn.close()

if __name__ == "__main__":
    crear_tablas()
    inicializar_garajes()
    print("Base de datos inicializada correctamente.")