# app.py
from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'  # Necesito esto para usar flash messages

# Esta función me ayuda a conectarme a la base de datos
def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

# Ruta para la página principal
@app.route('/')
def index():
    conn = get_db_connection()
    estacionamientos = conn.execute('SELECT * FROM garajes').fetchall()
    conn.close()
    return render_template('index.html', estacionamientos=estacionamientos)

@app.route('/validar_encomienda', methods=['POST'])
def validar_encomienda():
    id_encomienda = request.form['id_encomienda']
    id_usuario = request.form['id_usuario']
    # Aquí deberías agregar la lógica para validar la encomienda
    # Por ahora, solo mostraremos un mensaje flash
    flash(f'Validando encomienda {id_encomienda} para el usuario {id_usuario}')
    return redirect(url_for('index'))

# Ruta para el dashboard
@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    garajes = conn.execute('SELECT * FROM garajes').fetchall()
    alertas = conn.execute('SELECT * FROM alertas ORDER BY fecha DESC LIMIT 5').fetchall()
    conn.close()
    return render_template('dashboard.html', garajes=garajes, alertas=alertas)

# Ruta para registrar usuarios
@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        conn = get_db_connection()
        conn.execute('INSERT INTO usuarios (username, password) VALUES (?, ?)',
                     (username, password))
        conn.commit()
        conn.close()
        flash('Usuario registrado exitosamente')
        return redirect(url_for('index'))
    return render_template('register.html')

# Ruta para registrar encomiendas
@app.route('/encomienda', methods=['GET', 'POST'])
def encomienda():
    if request.method == 'POST':
        destinatario = request.form['destinatario']
        descripcion = request.form['descripcion']
        conn = get_db_connection()
        conn.execute('INSERT INTO encomiendas (destinatario, descripcion, fecha) VALUES (?, ?, ?)',
                     (destinatario, descripcion, datetime.now()))
        conn.commit()
        
        # Aquí asigno un garaje disponible
        garaje = conn.execute('SELECT id FROM garajes WHERE estado = "disponible" LIMIT 1').fetchone()
        if garaje:
            conn.execute('UPDATE garajes SET estado = "ocupado" WHERE id = ?', (garaje['id'],))
            conn.execute('INSERT INTO alertas (mensaje, fecha) VALUES (?, ?)',
                         (f"Encomienda para {destinatario} asignada al garaje {garaje['id']}", datetime.now()))
            conn.commit()
            flash(f'Encomienda registrada y asignada al garaje {garaje["id"]}')
        else:
            flash('Encomienda registrada, pero no hay garajes disponibles')
        
        conn.close()
        return redirect(url_for('dashboard'))
    return render_template('encomienda.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)