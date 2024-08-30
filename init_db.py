import sqlite3

def init_db():
    """Inicializa la base de datos con el esquema definido en schema.sql"""
    conn = sqlite3.connect('database.db')
    try:
        with open('schema.sql', 'r') as f:
            script = f.read()
        conn.executescript(script)
        print("Base de datos inicializada exitosamente.")
    except sqlite3.Error as e:
        print(f"Error al inicializar la base de datos: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()