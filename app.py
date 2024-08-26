from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3
from datetime import datetime
import random
import json

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
        encomiendas = conn.execute('SELECT id, descripcion, fecha FROM encomiendas WHERE destinatario_id = ? AND fecha_entrega IS NULL', 
                                   (usuario['id'],)).fetchall()
        conn.close()
        return jsonify({
            'success': True,
            'usuario': usuario['username'],
            'encomiendas': [{
                'id': e['id'], 
                'descripcion': e['descripcion'], 
                'fecha': e['fecha']
            } for e in encomiendas]
        })
    conn.close()
    return jsonify({'success': False, 'message': 'Usuario no encontrado o clave incorrecta'})

@app.route('/activar_entrada', methods=['POST'])
def activar_entrada():
    """Asigna un estacionamiento disponible para las encomiendas seleccionadas."""
    data = request.json
    encomiendas_ids = data.get('encomiendas', [])
    
    if not encomiendas_ids:
        return jsonify({'success': False, 'message': 'No se seleccionaron encomiendas'})

    conn = get_db_connection()
    
    # Verificar si el usuario ya tiene un estacionamiento asignado
    usuario_id = conn.execute('SELECT destinatario_id FROM encomiendas WHERE id = ?', (encomiendas_ids[0],)).fetchone()['destinatario_id']
    estacionamiento_asignado = conn.execute('SELECT garaje_id FROM asignaciones WHERE usuario_id = ? AND fecha_salida IS NULL', (usuario_id,)).fetchone()
    
    if estacionamiento_asignado:
        # Si ya tiene un estacionamiento asignado, usamos ese
        garaje_id = estacionamiento_asignado['garaje_id']
    else:
        # Si no tiene, asignamos uno nuevo
        garajes_disponibles = conn.execute('SELECT id FROM garajes WHERE estado = "disponible"').fetchall()
        if not garajes_disponibles:
            conn.close()
            return jsonify({'success': False, 'message': 'No hay garajes disponibles'})
        
        garaje_asignado = random.choice(garajes_disponibles)
        garaje_id = garaje_asignado['id']
        
        # Marcar el garaje como ocupado
        conn.execute('UPDATE garajes SET estado = "ocupado" WHERE id = ?', (garaje_id,))
        
        # Registrar la asignación
        conn.execute('INSERT INTO asignaciones (usuario_id, garaje_id, fecha_entrada) VALUES (?, ?, ?)',
                     (usuario_id, garaje_id, datetime.now()))

    # Marcar las encomiendas seleccionadas como entregadas
    for encomienda_id in encomiendas_ids:
        conn.execute('UPDATE encomiendas SET fecha_entrega = ? WHERE id = ?', (datetime.now(), encomienda_id))

    conn.commit()
    conn.close()
    return jsonify({'success': True, 'garaje': garaje_id})

# ... (el resto del código permanece igual) ...

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)