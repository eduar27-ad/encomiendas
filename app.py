from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3
import re
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import string
import os
import logging
from flask import session

logging.basicConfig(level=logging.DEBUG)

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'  # Clave secreta para sesiones y flash messages

def get_db_connection():
    """Establece y retorna una conexión a la base de datos."""
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

app.config['CARPETA_USUARIOS_ACTIVOS'] = os.path.join(app.root_path, 'usuarios_activos')
if not os.path.exists(app.config['CARPETA_USUARIOS_ACTIVOS']):
    os.makedirs(app.config['CARPETA_USUARIOS_ACTIVOS'])

def crear_archivo_validacion(cedula):
    caracteres_aleatorios = ''.join(random.choices(string.ascii_uppercase + string.digits, k=10))
    contenido = f"{cedula}{caracteres_aleatorios}"
    nombre_archivo = f"cedula_{cedula}.txt"
    ruta_completa = os.path.join(app.config['CARPETA_USUARIOS_ACTIVOS'], nombre_archivo)
    
    with open(ruta_completa, 'w') as archivo:
        archivo.write(contenido)
    
    return True

def validar_usuario(cedula):
    nombre_archivo = f"cedula_{cedula}.txt"
    ruta_completa = os.path.join(app.config['CARPETA_USUARIOS_ACTIVOS'], nombre_archivo)
    
    if os.path.exists(ruta_completa):
        with open(ruta_completa, 'r') as archivo:
            contenido = archivo.read()
        
        if contenido.startswith(cedula):
            os.remove(ruta_completa)  # Eliminar el archivo después de la validación exitosa
            return True
    
    return False

@app.route('/')
def index():
    """Ruta principal que muestra el estado de los estacionamientos y usuarios."""
    conn = get_db_connection()
    estacionamientos = conn.execute('SELECT * FROM garajes').fetchall()
    usuarios_en_camino = conn.execute('SELECT * FROM usuarios WHERE estado = "en_camino"').fetchall()
    usuarios_en_estacionamiento = conn.execute('SELECT * FROM usuarios WHERE estado = "en_estacionamiento"').fetchall()
    conn.close()
    return render_template('index.html', 
                           estacionamientos=estacionamientos, 
                           usuarios_en_camino=usuarios_en_camino,
                           usuarios_en_estacionamiento=usuarios_en_estacionamiento)

                           
@app.route('/api/usuarios_en_camino')
def api_usuarios_en_camino():
    conn = get_db_connection()
    usuarios = conn.execute('SELECT id, username, identificacion FROM usuarios WHERE estado = "en_camino"').fetchall()
    conn.close()
    return jsonify([dict(usuario) for usuario in usuarios])

@app.route('/api/usuarios_en_estacionamiento')
def api_usuarios_en_estacionamiento():
    conn = get_db_connection()
    usuarios = conn.execute('SELECT id, username, identificacion FROM usuarios WHERE estado = "en_estacionamiento"').fetchall()
    conn.close()
    return jsonify([dict(usuario) for usuario in usuarios])

@app.route('/api/usuario/<int:id>')
def api_usuario(id):
    conn = get_db_connection()
    usuario = conn.execute('SELECT id, username, identificacion, estado FROM usuarios WHERE id = ?', (id,)).fetchone()
    if usuario:
        encomiendas = conn.execute('SELECT descripcion FROM encomiendas WHERE destinatario_id = ? AND fecha_entrega IS NULL', (id,)).fetchall()
        usuario_dict = dict(usuario)
        usuario_dict['encomiendas'] = [e['descripcion'] for e in encomiendas]
        conn.close()
        return jsonify(usuario_dict)
    conn.close()
    return jsonify({'error': 'Usuario no encontrado'}), 404


@app.route('/api/notificar_llegada', methods=['POST'])
def notificar_llegada():
    data = request.json
    cedula = data.get('cedula')
    if cedula:
        conn = get_db_connection()
        conn.execute('UPDATE usuarios SET estado = "en_camino" WHERE identificacion = ?', (cedula,))
        conn.commit()
        conn.close()
        logging.debug(f"Usuario con cédula {cedula} notificó su llegada")
        if crear_archivo_validacion(cedula):
            logging.debug(f"Archivo de validación creado para cédula {cedula}")
            return jsonify({'success': True, 'message': 'Llegada notificada con éxito'})
    logging.error(f"Error al notificar llegada para cédula {cedula}")
    return jsonify({'success': False, 'message': 'Error al notificar llegada'}), 400


@app.route('/api/validar_usuario', methods=['POST'])
def validar_usuario_api():
    data = request.json
    cedula = data.get('cedula')
    if cedula:
        if validar_usuario(cedula):
            conn = get_db_connection()
            # Asignar estacionamiento aleatoriamente
            garajes_disponibles = conn.execute('SELECT id FROM garajes WHERE estado = "disponible"').fetchall()
            if garajes_disponibles:
                garaje_asignado = random.choice(garajes_disponibles)
                conn.execute('UPDATE usuarios SET estado = "en_estacionamiento" WHERE identificacion = ?', (cedula,))
                conn.execute('UPDATE garajes SET estado = "ocupado" WHERE id = ?', (garaje_asignado['id'],))
                conn.commit()
                conn.close()
                logging.debug(f"Usuario con cédula {cedula} validado y movido a estacionamiento {garaje_asignado['id']}")
                return jsonify({'success': True, 'message': 'Usuario validado con éxito', 'garaje': garaje_asignado['id']})
            else:
                conn.close()
                return jsonify({'success': False, 'message': 'No hay estacionamientos disponibles'}), 400
    logging.error(f"Validación fallida para cédula {cedula}")
    return jsonify({'success': False, 'message': 'Validación fallida'}), 400


@app.route('/test')
def test_page():
    return render_template('test.html')

@app.route('/api/estacionamiento/<string:id>')
def api_estacionamiento(id):
    conn = get_db_connection()
    try:
        garaje = conn.execute('SELECT * FROM garajes WHERE id = ?', (id,)).fetchone()
        
        if not garaje:
            return jsonify({'error': 'Estacionamiento no encontrado'}), 404
        
        resultado = {
            'id': garaje['id'],
            'estado': garaje['estado'],
            'ultimoUso': None
        }
        
        if garaje['estado'] == 'ocupado':
            encomienda = conn.execute('''
                SELECT e.*, u.username
                FROM encomiendas e
                JOIN usuarios u ON e.destinatario_id = u.id
                WHERE e.fecha_entrega IS NULL
                ORDER BY e.fecha DESC
                LIMIT 1
            ''').fetchone()
            
            if encomienda:
                resultado.update({
                    'usuarioActual': encomienda['username'],
                    'horaInicio': encomienda['fecha'],
                    'encomiendas': [encomienda['descripcion']],
                    'ultimoUso': encomienda['fecha']
                })
        
        return jsonify(resultado)
    
    except sqlite3.Error as e:
        return jsonify({'error': str(e)}), 500
    finally:
        conn.close()

@app.route('/buscar_destinatario')
def buscar_destinatario():
    query = request.args.get('query', '')
    
    conn = get_db_connection()
    if query:
        usuarios = conn.execute('''
            SELECT id, username, identificacion 
            FROM usuarios 
            WHERE username LIKE ? OR identificacion LIKE ?
            LIMIT 10
        ''', (f'%{query}%', f'%{query}%')).fetchall()
    else:
        usuarios = conn.execute('SELECT id, username, identificacion FROM usuarios LIMIT 10').fetchall()
    conn.close()

    return jsonify([{
        'id': usuario['id'],
        'username': usuario['username'],
        'identificacion': usuario['identificacion']
    } for usuario in usuarios])

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
            return jsonify({'success': False, 'message': 'El nombre de usuario debe tener entre 3 y 50 caracteres.'})
        
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$', password):
            return jsonify({'success': False, 'message': 'La contraseña debe tener al menos 8 caracteres, incluir una mayúscula, una minúscula y un número.'})
        
        if not re.match(r'^\d{4}$', clave_dinamica):
            return jsonify({'success': False, 'message': 'La clave dinámica debe ser exactamente 4 dígitos.'})
        
        if not re.match(r'^\d{5,20}$', identificacion):
            return jsonify({'success': False, 'message': 'La identificación debe ser solo números, entre 5 y 20 dígitos.'})
        
        conn = get_db_connection()
        try:
            existing_user = conn.execute('SELECT * FROM usuarios WHERE username = ? OR identificacion = ? OR clave_dinamica = ?', 
                                         (username, identificacion, clave_dinamica)).fetchone()
            if existing_user:
                if existing_user['username'] == username:
                    return jsonify({'success': False, 'message': 'Error: El nombre de usuario ya existe'})
                elif existing_user['identificacion'] == identificacion:
                    return jsonify({'success': False, 'message': 'Error: La identificación ya está registrada'})
                elif existing_user['clave_dinamica'] == clave_dinamica:
                    return jsonify({'success': False, 'message': 'Error: La clave dinámica ya está en uso'})
            
            hashed_password = generate_password_hash(password)
            
            conn.execute('INSERT INTO usuarios (username, password, identificacion, clave_dinamica, estado) VALUES (?, ?, ?, ?, ?)',
                         (username, hashed_password, identificacion, clave_dinamica, 'normal'))
            conn.commit()
            return jsonify({'success': True, 'message': 'Usuario registrado exitosamente'})
        except sqlite3.Error as e:
            return jsonify({'success': False, 'message': f'Error al registrar el usuario: {str(e)}'})
        finally:
            conn.close()
    
    return render_template('register.html')


@app.route('/whatsapp-sim')
def whatsapp_sim():
       return render_template('whatsapp_sim_advanced.html')


@app.route('/api/whatsapp-interaction', methods=['POST'])
def whatsapp_interaction():
    data = request.json
    message = data.get('message')
    state = data.get('state')
    user_data = data.get('userData', {})  # Obtenemos los datos del usuario del request
    
    response = process_whatsapp_message(message, state, user_data)
    return jsonify(response)

def process_whatsapp_message(message, state, user_data=None):
    if state == 'initial':
        if message.lower() == 'iniciar sesion':
            return {
                'message': 'Por favor, ingresa tu nombre de usuario:',
                'new_state': 'esperando_usuario'
            }
        else:
            return {
                'message': 'Para comenzar, escribe "iniciar sesion"',
                'new_state': 'initial'
            }
    elif state == 'esperando_usuario':
        return {
            'message': 'Ahora, ingresa tu contraseña:',
            'new_state': 'esperando_password',
            'username': message
        }
    elif state == 'esperando_password':
        username = user_data.get('username') if user_data else None
        if username and authenticate_user(username, message):
            return {
                'message': 'Inicio de sesión exitoso. ¿Qué deseas hacer?\n1. Ver paquetes\n2. Notificar llegada\n3. Ver estado\n4. Cerrar sesión',
                'new_state': 'menu_principal',
                'logged_in': True
            }
        else:
            return {
                'message': 'Usuario o contraseña incorrectos. Por favor, intenta de nuevo.',
                'new_state': 'initial'
            }
    elif state == 'menu_principal':
        if message == '1':
            return submenu_ver_paquetes()
        elif message == '2':
            return submenu_notificar_llegada()
        elif message == '3':
            return submenu_ver_estado()
        elif message == '4':
            return {
                'message': 'Has cerrado sesión. ¡Hasta pronto!',
                'new_state': 'initial',
                'logged_out': True
            }
        else:
            return {
                'message': 'Opción no válida. Por favor, elige una opción del 1 al 4.',
                'new_state': 'menu_principal'
            }
    elif state.startswith('submenu_'):
        return handle_submenu(state, message, user_data)
    return {
        'message': 'Lo siento, no entendí eso. ¿Puedes intentar de nuevo?',
        'new_state': state
    }

def submenu_ver_paquetes():
    return {
        'message': 'Submenú Ver Paquetes:\n1. Ver todos los paquetes\n2. Buscar paquete por ID\n3. Volver al menú principal',
        'new_state': 'submenu_ver_paquetes'
    }

def submenu_notificar_llegada():
    return {
        'message': 'Submenú Notificar Llegada:\n1. Notificar llegada ahora\n2. Programar llegada\n3. Volver al menú principal',
        'new_state': 'submenu_notificar_llegada'
    }

def submenu_ver_estado():
    return {
        'message': 'Submenú Ver Estado:\n1. Estado de paquetes\n2. Estado de llegada\n3. Volver al menú principal',
        'new_state': 'submenu_ver_estado'
    }

def handle_submenu(state, message, user_data):
    if message == '3':  # Opción para volver al menú principal en todos los submenús
        return {
            'message': '¿Qué deseas hacer?\n1. Ver paquetes\n2. Notificar llegada\n3. Ver estado\n4. Cerrar sesión',
            'new_state': 'menu_principal'
        }
    
    if state == 'submenu_ver_paquetes':
        if message == '1':
            return get_user_packages(user_data.get('username'))
        elif message == '2':
            return {
                'message': 'Por favor, ingresa el ID del paquete:',
                'new_state': 'esperando_id_paquete'
            }
    elif state == 'submenu_notificar_llegada':
        if message == '1':
            return notify_arrival(user_data.get('username'))
        elif message == '2':
            return {
                'message': 'Funcionalidad de programar llegada aún no implementada.',
                'new_state': state
            }
    elif state == 'submenu_ver_estado':
        if message == '1':
            return get_package_status(user_data.get('username'))
        elif message == '2':
            return {
                'message': 'Funcionalidad de ver estado de llegada aún no implementada.',
                'new_state': state
            }
    
    return {
        'message': 'Opción no válida. Por favor, intenta de nuevo.',
        'new_state': state
    }

def get_user_packages(username):
    conn = get_db_connection()
    user = conn.execute('SELECT id FROM usuarios WHERE username = ?', (username,)).fetchone()
    if user:
        packages = conn.execute('SELECT descripcion, fecha FROM encomiendas WHERE destinatario_id = ? AND fecha_entrega IS NULL', (user['id'],)).fetchall()
        conn.close()
        if packages:
            message = "Tus paquetes pendientes son:\n"
            for package in packages:
                message += f"- {package['descripcion']} (Llegó el: {package['fecha']})\n"
        else:
            message = "No tienes paquetes pendientes en este momento."
    else:
        message = "No se pudo encontrar información de tus paquetes."
    return {
        'message': message,
        'new_state': 'menu_principal'
    }

def notify_arrival(username):
    conn = get_db_connection()
    user = conn.execute('SELECT identificacion FROM usuarios WHERE username = ?', (username,)).fetchone()
    if user:
        conn.execute('UPDATE usuarios SET estado = "en_camino" WHERE username = ?', (username,))
        conn.commit()
        conn.close()
        crear_archivo_validacion(user['identificacion'])
        message = "Has notificado tu llegada. Por favor, dirígete al área de recogida."
    else:
        message = "No se pudo notificar tu llegada. Por favor, intenta más tarde."
    return {
        'message': message,
        'new_state': 'menu_principal'
    }

def get_package_status(username):
    conn = get_db_connection()
    user = conn.execute('SELECT id FROM usuarios WHERE username = ?', (username,)).fetchone()
    if user:
        packages = conn.execute('SELECT estado, COUNT(*) as count FROM encomiendas WHERE destinatario_id = ? GROUP BY estado', (user['id'],)).fetchall()
        conn.close()
        if packages:
            message = "Estado de tus paquetes:\n"
            for package in packages:
                message += f"- {package['count']} paquete(s) en estado: {package['estado']}\n"
        else:
            message = "No tienes paquetes registrados en el sistema."
    else:
        message = "No se pudo obtener el estado de tus paquetes."
    return {
        'message': message,
        'new_state': 'menu_principal'
    }

def authenticate_user(username, password):
    conn = get_db_connection()
    user = conn.execute('SELECT * FROM usuarios WHERE username = ?', (username,)).fetchone()
    conn.close()
    
    if user and check_password_hash(user['password'], password):
        return True
    return False

@app.route('/encomienda', methods=['GET', 'POST'])
def encomienda():
    """Maneja el registro de nuevas encomiendas."""
    if request.method == 'POST':
        destinatario_id = request.form['destinatario_id']
        descripcion = request.form['descripcion']
        peso = request.form['peso']
        dimensiones = request.form.get('dimensiones', '')
        fecha_llegada = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = get_db_connection()
        try:
            cursor = conn.execute('''
                INSERT INTO encomiendas (destinatario_id, descripcion, peso, dimensiones, fecha)
                VALUES (?, ?, ?, ?, ?)
            ''', (destinatario_id, descripcion, peso, dimensiones, fecha_llegada))
            
            destinatario = conn.execute('SELECT username FROM usuarios WHERE id = ?', (destinatario_id,)).fetchone()
            
            conn.commit()
            
            return jsonify({
                'success': True,
                'message': 'Encomienda registrada exitosamente',
                'destinatario': destinatario['username'],
                'descripcion': descripcion,
                'fecha': fecha_llegada
            })
        except sqlite3.Error as e:
            conn.rollback()
            return jsonify({'success': False, 'message': f'Error al registrar la encomienda: {str(e)}'})
        finally:
            conn.close()
    
    # Si es una solicitud GET, obtener la lista de usuarios para el formulario
    conn = get_db_connection()
    usuarios = conn.execute('SELECT id, username, identificacion FROM usuarios').fetchall()
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
     app.run(host='127.0.0.1', port=8080, debug=True)