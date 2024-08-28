from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3
from datetime import datetime
import random
import logging

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'  # Clave secreta para sesiones y flash messages

# Configuración de logging
logging.basicConfig(level=logging.DEBUG)

def get_db_connection():
    """Establece y retorna una conexión a la base de datos."""
    try:
        conn = sqlite3.connect('database.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.Error as e:
        app.logger.error(f"Error al conectar con la base de datos: {e}")
        raise

@app.route('/')
def index():
    """Ruta principal que muestra el estado detallado de los estacionamientos."""
    try:
        conn = get_db_connection()
        estacionamientos = conn.execute('''
            SELECT g.id, g.estado, 
                   CASE WHEN a.id IS NOT NULL THEN u.username ELSE NULL END as usuario_actual
            FROM garajes g
            LEFT JOIN asignaciones a ON g.id = a.garaje_id AND a.fecha_salida IS NULL
            LEFT JOIN usuarios u ON a.usuario_id = u.id
        ''').fetchall()
        conn.close()
        return render_template('index.html', estacionamientos=estacionamientos)
    except sqlite3.Error as e:
        app.logger.error(f"Error al consultar la tabla garajes: {e}")
        return "Error al acceder a la base de datos", 500

@app.route('/api/estado-estacionamientos')
def estado_estacionamientos():
    try:
        conn = get_db_connection()
        estacionamientos = conn.execute('''
            SELECT g.id, g.estado, 
                   CASE WHEN a.id IS NOT NULL THEN u.username ELSE NULL END as usuario_actual
            FROM garajes g
            LEFT JOIN asignaciones a ON g.id = a.garaje_id AND a.fecha_salida IS NULL
            LEFT JOIN usuarios u ON a.usuario_id = u.id
        ''').fetchall()
        conn.close()
        
        resultado = {
            'estacionamientos': [
                {'id': e['id'], 'estado': e['estado'], 'usuario_actual': e['usuario_actual']}
                for e in estacionamientos
            ]
        }
        app.logger.info(f"Estado de estacionamientos enviado: {resultado}")
        return jsonify(resultado)
    except sqlite3.Error as e:
        app.logger.error(f"Error al consultar el estado de los estacionamientos: {e}")
        return jsonify({'error': 'Error en la base de datos'}), 500

@app.route('/consultar_encomienda', methods=['POST'])
def consultar_encomienda():
    identificacion = request.form['identificacion']
    clave_dinamica = request.form['clave_dinamica']
    conn = get_db_connection()
    try:
        usuario = conn.execute('SELECT * FROM usuarios WHERE identificacion = ? AND clave_dinamica = ?', 
                               (identificacion, clave_dinamica)).fetchone()
        if usuario:
            encomiendas = conn.execute('''
                SELECT e.id, e.descripcion, e.fecha, e.fecha_entrega, 
                       CASE WHEN a.id IS NOT NULL THEN a.garaje_id ELSE NULL END as garaje_asignado
                FROM encomiendas e
                LEFT JOIN asignaciones a ON e.destinatario_id = a.usuario_id AND a.fecha_salida IS NULL
                WHERE e.destinatario_id = ?
                ORDER BY e.fecha_entrega IS NULL DESC, e.fecha ASC
            ''', (usuario['id'],)).fetchall()
            
            conn.close()
            return jsonify({
                'success': True,
                'usuario': usuario['username'],
                'encomiendas': [{
                    'id': e['id'],
                    'descripcion': e['descripcion'],
                    'fecha': e['fecha'],
                    'entregada': e['fecha_entrega'] is not None,
                    'garaje_asignado': e['garaje_asignado']
                } for e in encomiendas]
            })
        conn.close()
        return jsonify({'success': False, 'message': 'Usuario no encontrado o clave incorrecta'})
    except sqlite3.Error as e:
        conn.close()
        return jsonify({'success': False, 'message': f'Error en la base de datos: {str(e)}'})