import sqlite3

def init_db():
    """Inicializa la base de datos con el esquema definido en schema.sql"""
    conn = sqlite3.connect('database.db')
    try:
        with open('schema.sql', 'r') as f:
            script = f.read()

        # Dividir el script en instrucciones individuales
        instructions = script.split(';')

        for instruction in instructions:
            # Ignorar líneas vacías o comentarios
            if instruction.strip() and not instruction.strip().startswith('--'):
                try:
                    conn.execute(instruction)
                    print(f"Ejecutada con éxito: {instruction[:50]}...") # Imprime las primeras 50 caracteres de la instrucción
                except sqlite3.OperationalError as e:
                    print(f"Error ejecutando instrucción: {instruction[:50]}...")
                    print(f"Error completo: {e}")

        conn.commit()
        print("Base de datos inicializada correctamente.")
    except Exception as e:
        print(f"Ocurrió un error: {e}")
    finally:
        conn.close()

if __name__ == '__main__':
    init_db()