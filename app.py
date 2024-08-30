from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3
import re
from werkzeug.security import generate_password_hash, check_password_hash
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

@app.route('/actualizar_estacionamiento', methods=['POST'])
def actualizar_estacionamiento():
    id = request.json['id']
    nuevo_estado = request.json['estado']
    conn = get_db_connection()
    conn.execute('UPDATE garajes SET estado = ? WHERE id = ?', (nuevo_estado, id))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

@app.route('/marcar_alerta_leida', methods=['POST'])
def marcar_alerta_leida():
    id = request.json['id']
    conn = get_db_connection()
    conn.execute('UPDATE alertas SET leida = 1 WHERE id = ?', (id,))
    conn.commit()
    conn.close()
    return jsonify({'success': True})

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
    
    conn.close()
    
    return render_template('dashboard.html', 
                           garajes=garajes, 
                           alertas=alertas, 
                           estados_estacionamientos=estados_estacionamientos)

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Maneja el registro de nuevos usuarios."""
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        identificacion = request.form['identificacion']
        clave_dinamica = request.form['clave_dinamica']
        
        # Validaciones del lado del servidor
        if len(username) < 3 or len(username) > 50:
            flash('El nombre de usuario debe tener entre 3 y 50 caracteres.')
            return redirect(url_for('register'))
        
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$', password):
            flash('La contraseña debe tener al menos 8 caracteres, incluir una mayúscula, una minúscula y un número.')
            return redirect(url_for('register'))
        
        if len(clave_dinamica) < 4 or len(clave_dinamica) > 8:
            flash('La clave dinámica debe tener entre 4 y 8 caracteres.')
            return redirect(url_for('register'))
        
        conn = get_db_connection()
        try:
            # Verificar si el usuario o la identificación ya existen
            existing_user = conn.execute('SELECT * FROM usuarios WHERE username = ? OR identificacion = ?', 
                                         (username, identificacion)).fetchone()
            if existing_user:
                flash('Error: El nombre de usuario o identificación ya existe')
                return redirect(url_for('register'))
            
            # Hash de la contraseña
            hashed_password = generate_password_hash(password)
            
            conn.execute('INSERT INTO usuarios (username, password, identificacion, clave_dinamica) VALUES (?, ?, ?, ?)',
                         (username, hashed_password, identificacion, clave_dinamica))
            conn.commit()
            flash('Usuario registrado exitosamente', 'success')
            return redirect(url_for('index'))
        except sqlite3.Error as e:
            flash(f'Error al registrar el usuario: {str(e)}', 'error')
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


@app.route('/get_updates')
def get_updates():
    conn = get_db_connection()
    garajes = conn.execute('SELECT * FROM garajes').fetchall()
    alertas = conn.execute('SELECT * FROM alertas ORDER BY fecha DESC LIMIT 5').fetchall()
    
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
    
    conn.close()
    
    return jsonify({
        'garajes': [dict(garaje) for garaje in garajes],
        'alertas': [dict(alerta) for alerta in alertas],
        'estados_estacionamientos': estados_estacionamientos
    })

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)