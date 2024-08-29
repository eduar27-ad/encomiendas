from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3
from datetime import datetime
import random

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'  # Clave secreta para sesiones y flash messages

def get_db_connection():
    """Establece y retorna una conexión a la base de datos."""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    """Ruta principal que muestra el estado de los estacionamientos."""
    conn = get_db_connection()
    estacionamientos = conn.execute('SELECT * FROM garajes').fetchall()
    conn.close()
    return render_template('index.html', estacionamientos=estacionamientos)

@app.route('/consultar_encomienda', methods=['POST'])
def consultar_encomienda():
    """Maneja la consulta de encomiendas para un usuario."""
    identificacion = request.form['identificacion']
    clave_dinamica = request.form['clave_dinamica']
    conn = get_db_connection()
    usuario = conn.execute('SELECT * FROM usuarios WHERE identificacion = ? AND clave_dinamica = ?', 
                           (identificacion, clave_dinamica)).fetchone()
    if usuario:
        encomiendas = conn.execute('SELECT * FROM encomiendas WHERE destinatario_id = ? AND fecha_entrega IS NULL', 
                                   (usuario['id'],)).fetchall()
        conn.close()
        return jsonify({
            'success': True,
            'usuario': usuario['username'],
            'encomiendas': [{'id': e['id'], 'descripcion': e['descripcion'], 'fecha': e['fecha']} for e in encomiendas]
        })
    conn.close()
    return jsonify({'success': False, 'message': 'Usuario no encontrado o clave incorrecta'})

@app.route('/activar_entrada', methods=['POST'])
def activar_entrada():
    """Asigna un estacionamiento disponible aleatoriamente."""
    conn = get_db_connection()
    garajes_disponibles = conn.execute('SELECT id FROM garajes WHERE estado = "disponible"').fetchall()
    if garajes_disponibles:
        garaje_asignado = random.choice(garajes_disponibles)
        conn.execute('UPDATE garajes SET estado = "ocupado" WHERE id = ?', (garaje_asignado['id'],))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'garaje': garaje_asignado['id']})
    conn.close()
    return jsonify({'success': False, 'message': 'No hay garajes disponibles'})

@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    garajes = conn.execute('SELECT * FROM garajes').fetchall()
    alertas = conn.execute('SELECT * FROM alertas ORDER BY fecha DESC LIMIT 5').fetchall()
    
    # Contar estacionamientos por estado
    estados_estacionamientos = {
        'disponible': 0,
        'ocupado': 0,
        'fuera_de_servicio': 0
    }
    for garaje in garajes:
        estado = garaje['estado']
        if estado in estados_estacionamientos:
            estados_estacionamientos[estado] += 1
        else:
            estados_estacionamientos['fuera_de_servicio'] += 1
    
    print("Estados de estacionamientos:", estados_estacionamientos)  # Print de depuración
    
    conn.close()
    
    context = {
        'garajes': garajes,
        'alertas': alertas,
        'estados_estacionamientos': estados_estacionamientos
    }
    print("Contexto completo:", context)  # Print de depuración
    
    return render_template('dashboard.html', **context)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Maneja el registro de nuevos usuarios."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        identificacion = request.form['identificacion']
        clave_dinamica = request.form['clave_dinamica']
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO usuarios (username, password, identificacion, clave_dinamica) VALUES (?, ?, ?, ?)',
                         (username, password, identificacion, clave_dinamica))
            conn.commit()
            flash('Usuario registrado exitosamente')
            return redirect(url_for('index'))
        except sqlite3.IntegrityError:
            flash('Error: El nombre de usuario o identificación ya existe')
        finally:
            conn.close()
    return render_template('register.html')

@app.route('/encomienda', methods=['GET', 'POST'])
def encomienda():
    """Maneja el registro de nuevas encomiendas."""
    if request.method == 'POST':
        destinatario_id = request.form['destinatario_id']
        descripcion = request.form['descripcion']
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO encomiendas (destinatario_id, descripcion) VALUES (?, ?)',
                         (destinatario_id, descripcion))
            conn.commit()
            flash('Encomienda registrada exitosamente')
            return redirect(url_for('dashboard'))
        except sqlite3.Error as e:
            flash(f'Error al registrar la encomienda: {str(e)}')
        finally:
            conn.close()
    conn = get_db_connection()
    usuarios = conn.execute('SELECT id, username FROM usuarios').fetchall()
    conn.close()
    return render_template('encomienda.html', usuarios=usuarios)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)