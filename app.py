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
    """Ruta principal que muestra el estado de los estacionamientos."""
    try:
        conn = get_db_connection()
        estacionamientos = conn.execute('SELECT * FROM garajes').fetchall()
        conn.close()
        return render_template('index.html', estacionamientos=estacionamientos)
    except sqlite3.Error as e:
        app.logger.error(f"Error al consultar la tabla garajes: {e}")
        return "Error al acceder a la base de datos", 500

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
    
@app.route('/activar_entrada', methods=['POST'])
def activar_entrada():
    data = request.json
    encomiendas_ids = data.get('encomiendas', [])
    
    if not encomiendas_ids:
        return jsonify({'success': False, 'message': 'No se seleccionaron encomiendas'})

    conn = get_db_connection()
    
    try:
        # Obtener el usuario_id y verificar si ya tiene un estacionamiento asignado
        usuario_id = conn.execute('SELECT destinatario_id FROM encomiendas WHERE id = ?', (encomiendas_ids[0],)).fetchone()['destinatario_id']
        estacionamiento_asignado = conn.execute('SELECT garaje_id FROM asignaciones WHERE usuario_id = ? AND fecha_salida IS NULL', (usuario_id,)).fetchone()
        
        if estacionamiento_asignado:
            # Si ya tiene un estacionamiento asignado, usamos ese
            garaje_id = estacionamiento_asignado['garaje_id']
        else:
            # Si no tiene, asignamos uno nuevo
            garajes_disponibles = conn.execute('SELECT id FROM garajes WHERE estado = "disponible"').fetchall()
            if not garajes_disponibles:
                return jsonify({'success': False, 'message': 'No hay garajes disponibles'})
            
            garaje_asignado = random.choice(garajes_disponibles)
            garaje_id = garaje_asignado['id']
            
            # Marcar el garaje como ocupado
            conn.execute('UPDATE garajes SET estado = "ocupado" WHERE id = ?', (garaje_id,))
            
            # Registrar la nueva asignación
            conn.execute('INSERT INTO asignaciones (usuario_id, garaje_id, fecha_entrada) VALUES (?, ?, ?)',
                         (usuario_id, garaje_id, datetime.now()))

        # Marcar las encomiendas seleccionadas como entregadas
        for encomienda_id in encomiendas_ids:
            conn.execute('UPDATE encomiendas SET fecha_entrega = ? WHERE id = ?', (datetime.now(), encomienda_id))

        # Actualizar la fecha de salida de la asignación si todas las encomiendas han sido entregadas
        encomiendas_pendientes = conn.execute('SELECT COUNT(*) FROM encomiendas WHERE destinatario_id = ? AND fecha_entrega IS NULL', (usuario_id,)).fetchone()[0]
        if encomiendas_pendientes == 0:
            conn.execute('UPDATE asignaciones SET fecha_salida = ? WHERE usuario_id = ? AND fecha_salida IS NULL', (datetime.now(), usuario_id))
            conn.execute('UPDATE garajes SET estado = "disponible" WHERE id = ?', (garaje_id,))

        conn.commit()
        return jsonify({'success': True, 'garaje': garaje_id})
    except sqlite3.Error as e:
        conn.rollback()
        return jsonify({'success': False, 'message': f'Error en la base de datos: {str(e)}'})
    finally:
        conn.close()

@app.route('/confirmar_entrada', methods=['POST'])
def confirmar_entrada():
    """Confirma la entrega de encomiendas adicionales en un garaje ya asignado."""
    try:
        data = request.json
        encomiendas_ids = data.get('encomiendas', [])
        
        if not encomiendas_ids:
            return jsonify({'success': False, 'message': 'No se seleccionaron encomiendas'})

        conn = get_db_connection()
        
        # Marcar las encomiendas seleccionadas como entregadas
        for encomienda_id in encomiendas_ids:
            conn.execute('UPDATE encomiendas SET fecha_entrega = ? WHERE id = ?', (datetime.now(), encomienda_id))

        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Encomiendas adicionales registradas para entrega'})
    except sqlite3.Error as e:
        app.logger.error(f"Error en confirmar_entrada: {e}")
        return jsonify({'success': False, 'message': 'Error al procesar la confirmación'})

@app.route('/dashboard')
def dashboard():
    try:
        conn = get_db_connection()
        estacionamientos = conn.execute('SELECT * FROM garajes').fetchall()
        alertas = conn.execute('SELECT * FROM alertas ORDER BY fecha DESC LIMIT 5').fetchall()
        conn.close()
        return render_template('dashboard.html', estacionamientos=estacionamientos, alertas=alertas)
    except sqlite3.Error as e:
        app.logger.error(f"Error en dashboard: {e}")
        return "Error al acceder a la base de datos", 500
    
@app.route('/api/parking-spot/<spot_id>')
def get_parking_spot_details(spot_id):
    try:
        conn = get_db_connection()
        spot = conn.execute('SELECT * FROM garajes WHERE id = ?', (spot_id,)).fetchone()
        if spot:
            # Obtener información adicional si está ocupado
            if spot['estado'] == 'ocupado':
                asignacion = conn.execute('''
                    SELECT u.username, a.fecha_entrada
                    FROM asignaciones a
                    JOIN usuarios u ON a.usuario_id = u.id
                    WHERE a.garaje_id = ? AND a.fecha_salida IS NULL
                ''', (spot_id,)).fetchone()
                
                ultimo_uso = conn.execute('''
                    SELECT u.username, a.fecha_entrada, a.fecha_salida
                    FROM asignaciones a
                    JOIN usuarios u ON a.usuario_id = u.id
                    WHERE a.garaje_id = ? AND a.fecha_salida IS NOT NULL
                    ORDER BY a.fecha_salida DESC LIMIT 1
                ''', (spot_id,)).fetchone()
                
                conn.close()
                return jsonify({
                    'id': spot['id'],
                    'estado': spot['estado'],
                    'usuario_actual': asignacion['username'] if asignacion else None,
                    'hora_entrada': asignacion['fecha_entrada'] if asignacion else None,
                    'ultimo_uso': {
                        'usuario': ultimo_uso['username'] if ultimo_uso else None,
                        'entrada': ultimo_uso['fecha_entrada'] if ultimo_uso else None,
                        'salida': ultimo_uso['fecha_salida'] if ultimo_uso else None
                    }
                })
            else:
                conn.close()
                return jsonify({
                    'id': spot['id'],
                    'estado': spot['estado']
                })
        else:
            conn.close()
            return jsonify({'error': 'Estacionamiento no encontrado'}), 404
    except sqlite3.Error as e:
        app.logger.error(f"Error al obtener detalles del estacionamiento: {e}")
        return jsonify({'error': 'Error en la base de datos'}), 500

@app.route('/api/release-parking/<spot_id>', methods=['POST'])
def release_parking(spot_id):
    try:
        conn = get_db_connection()
        # Verificar si el estacionamiento está ocupado
        spot = conn.execute('SELECT estado FROM garajes WHERE id = ?', (spot_id,)).fetchone()
        if spot and spot['estado'] == 'ocupado':
            # Liberar el estacionamiento
            conn.execute('UPDATE garajes SET estado = "disponible" WHERE id = ?', (spot_id,))
            # Actualizar la asignación
            conn.execute('''
                UPDATE asignaciones 
                SET fecha_salida = ? 
                WHERE garaje_id = ? AND fecha_salida IS NULL
            ''', (datetime.now(), spot_id))
            conn.commit()
            conn.close()
            return jsonify({'success': True, 'message': 'Estacionamiento liberado exitosamente'})
        else:
            conn.close()
            return jsonify({'success': False, 'message': 'El estacionamiento no está ocupado'}), 400
    except sqlite3.Error as e:
        app.logger.error(f"Error al liberar estacionamiento: {e}")
        return jsonify({'success': False, 'message': 'Error en la base de datos'}), 500

@app.route('/api/mark-out-of-service/<spot_id>', methods=['POST'])
def mark_out_of_service(spot_id):
    try:
        data = request.json
        reason = data.get('reason', 'No especificada')
        conn = get_db_connection()
        conn.execute('UPDATE garajes SET estado = "fuera-de-servicio" WHERE id = ?', (spot_id,))
        # Aquí podrías añadir un registro en una tabla de mantenimiento si lo deseas
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Estacionamiento marcado como fuera de servicio'})
    except sqlite3.Error as e:
        app.logger.error(f"Error al marcar estacionamiento como fuera de servicio: {e}")
        return jsonify({'success': False, 'message': 'Error en la base de datos'}), 500

@app.route('/api/return-to-service/<spot_id>', methods=['POST'])
def return_to_service(spot_id):
    try:
        conn = get_db_connection()
        conn.execute('UPDATE garajes SET estado = "disponible" WHERE id = ?', (spot_id,))
        conn.commit()
        conn.close()
        return jsonify({'success': True, 'message': 'Estacionamiento vuelto a poner en servicio'})
    except sqlite3.Error as e:
        app.logger.error(f"Error al volver a poner estacionamiento en servicio: {e}")
        return jsonify({'success': False, 'message': 'Error en la base de datos'}), 500

@app.route('/api/refresh-dashboard')
def refresh_dashboard():
    try:
        conn = get_db_connection()
        estacionamientos = conn.execute('SELECT * FROM garajes').fetchall()
        alertas = conn.execute('SELECT * FROM alertas ORDER BY fecha DESC LIMIT 5').fetchall()
        entregas_del_dia = conn.execute('SELECT COUNT(*) FROM encomiendas WHERE DATE(fecha_entrega) = DATE("now")').fetchone()[0]
        conn.close()
        return jsonify({
            'estacionamientos': [dict(e) for e in estacionamientos],
            'alertas': [dict(a) for a in alertas],
            'entregasDelDia': entregas_del_dia
        })
    except sqlite3.Error as e:
        app.logger.error(f"Error al refrescar el dashboard: {e}")
        return jsonify({'error': 'Error en la base de datos'}), 500


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
        except sqlite3.Error as e:
            app.logger.error(f"Error en register: {e}")
            flash('Error al registrar el usuario')
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
            app.logger.error(f"Error al registrar la encomienda: {e}")
            flash(f'Error al registrar la encomienda: {str(e)}')
        finally:
            conn.close()
    conn = get_db_connection()
    usuarios = conn.execute('SELECT id, username FROM usuarios').fetchall()
    conn.close()
    return render_template('encomienda.html', usuarios=usuarios)

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)