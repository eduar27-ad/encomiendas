import sqlite3

def init_db():
    """Inicializa la base de datos con el esquema definido en schema.sql"""
    conn = sqlite3.connect('database.db')
    with open('schema.sql') as f:
        conn.executescript(f.read())
    conn.close()
    print("Base de datos inicializada.")

if __name__ == '__main__':
    init_db()