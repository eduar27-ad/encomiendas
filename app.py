from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
import sqlite3
import re
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import random
import string
import os

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

@app.route('/api/notificar_llegada', methods=['POST'])
def notificar_llegada():
    data = request.json
    cedula = data.get('cedula')
    if cedula:
        if crear_archivo_validacion(cedula):
            return jsonify({'success': True, 'message': 'Llegada notificada con éxito'})
    return jsonify({'success': False, 'message': 'Error al notificar llegada'}), 400

@app.route('/api/validar_usuario', methods=['POST'])
def validar_usuario_api():
    data = request.json
    cedula = data.get('cedula')
    if cedula:
        if validar_usuario(cedula):
            return jsonify({'success': True, 'message': 'Usuario validado con éxito'})
    return jsonify({'success': False, 'message': 'Validación fallida'}), 400

@app.route('/api/estacionamiento/<string:id>')
def api_estacionamiento(id):
    conn = get_db_connection()
    try:
        # Obtener detalles del estacionamiento
        garaje = conn.execute('SELECT * FROM garajes WHERE id = ?', (id,)).fetchone()
        
        if not garaje:
            return jsonify({'error': 'Estacionamiento no encontrado'}), 404
        
        resultado = {
            'id': garaje['id'],
            'estado': garaje['estado'],
            'ultimoUso': None  # Inicialmente None, se actualizará si está ocupado
        }
        
        # Si está ocupado, obtener información adicional
        if garaje['estado'] == 'ocupado':
            # Obtener la última encomienda asociada a este garaje (asumiendo que existe una relación)
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

@app.route('/')
def index():
    """Ruta principal que muestra el estado de los estacionamientos."""
    conn = get_db_connection()
    estacionamientos = conn.execute('SELECT * FROM garajes').fetchall()
    conn.close()
    return render_template('index.html', estacionamientos=estacionamientos)

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
            return jsonify({'success': False, 'message': 'El nombre de usuario debe tener entre 3 y 50 caracteres.'})
        
        if not re.match(r'^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)[a-zA-Z\d]{8,}$', password):
            return jsonify({'success': False, 'message': 'La contraseña debe tener al menos 8 caracteres, incluir una mayúscula, una minúscula y un número.'})
        
        if not re.match(r'^\d{4}$', clave_dinamica):
            return jsonify({'success': False, 'message': 'La clave dinámica debe ser exactamente 4 dígitos.'})
        
        if not re.match(r'^\d{5,20}$', identificacion):
            return jsonify({'success': False, 'message': 'La identificación debe ser solo números, entre 5 y 20 dígitos.'})
        
        conn = get_db_connection()
        try:
            # Verificar si el usuario, la identificación o la clave dinámica ya existen
            existing_user = conn.execute('SELECT * FROM usuarios WHERE username = ? OR identificacion = ? OR clave_dinamica = ?', 
                                         (username, identificacion, clave_dinamica)).fetchone()
            if existing_user:
                if existing_user['username'] == username:
                    return jsonify({'success': False, 'message': 'Error: El nombre de usuario ya existe'})
                elif existing_user['identificacion'] == identificacion:
                    return jsonify({'success': False, 'message': 'Error: La identificación ya está registrada'})
                elif existing_user['clave_dinamica'] == clave_dinamica:
                    return jsonify({'success': False, 'message': 'Error: La clave dinámica ya está en uso'})
            
            # Hash de la contraseña
            hashed_password = generate_password_hash(password)
            
            conn.execute('INSERT INTO usuarios (username, password, identificacion, clave_dinamica) VALUES (?, ?, ?, ?)',
                         (username, hashed_password, identificacion, clave_dinamica))
            conn.commit()
            return jsonify({'success': True, 'message': 'Usuario registrado exitosamente'})
        except sqlite3.Error as e:
            return jsonify({'success': False, 'message': f'Error al registrar el usuario: {str(e)}'})
        finally:
            conn.close()
    
    return render_template('register.html')

@app.route('/encomienda', methods=['GET', 'POST'])
def encomienda():
    """Maneja el registro de nuevas encomiendas."""
    if request.method == 'POST':
        destinatario_id = request.form['destinatario_id']
        descripcion = request.form['descripcion']
        peso = request.form['peso']
        dimensiones = request.form.get('dimensiones', '')  # Campo opcional
        fecha_llegada = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        conn = get_db_connection()
        try:
            # Insertar la nueva encomienda
            cursor = conn.execute('''
                INSERT INTO encomiendas (destinatario_id, descripcion, peso, dimensiones, fecha)
                VALUES (?, ?, ?, ?, ?)
            ''', (destinatario_id, descripcion, peso, dimensiones, fecha_llegada))
            
            # Obtener el nombre del destinatario
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
    app.run(host='0.0.0.0', port=8080, debug=True)