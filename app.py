from flask import Flask, render_template, request, redirect, url_for, flash
import sqlite3
from datetime import datetime

app = Flask(__name__)
app.secret_key = 'tu_clave_secreta_aqui'

def get_db_connection():
    conn = sqlite3.connect('database.db')
    conn.row_factory = sqlite3.Row
    return conn

@app.route('/')
def index():
    conn = get_db_connection()
    garajes = conn.execute('SELECT * FROM garajes').fetchall()
    conn.close()
    return render_template('index.html', garajes=garajes)

@app.route('/dashboard')
def dashboard():
    conn = get_db_connection()
    garajes = conn.execute('SELECT * FROM garajes').fetchall()
    alertas = conn.execute('SELECT * FROM alertas ORDER BY fecha DESC LIMIT 5').fetchall()
    conn.close()
    return render_template('dashboard.html', garajes=garajes, alertas=alertas)

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        identificacion = request.form['identificacion']
        email = request.form['email']
        conn = get_db_connection()
        try:
            conn.execute('INSERT INTO usuarios (username, password, identificacion, email) VALUES (?, ?, ?, ?)',
                         (username, password, identificacion, email))
            conn.commit()
            flash('Usuario registrado exitosamente')
        except sqlite3.IntegrityError:
            flash('Error: El nombre de usuario, identificación o email ya existe')
        finally:
            conn.close()
        return redirect(url_for('index'))
    return render_template('register.html')

@app.route('/encomienda', methods=['GET', 'POST'])
def encomienda():
    if request.method == 'POST':
        destinatario_id = request.form['destinatario_id']
        descripcion = request.form['descripcion']
        conn = get_db_connection()
        try:
            garaje = conn.execute('SELECT id FROM garajes WHERE estado = "disponible" LIMIT 1').fetchone()
            if garaje:
                conn.execute('INSERT INTO encomiendas (destinatario_id, descripcion, garaje_id) VALUES (?, ?, ?)',
                             (destinatario_id, descripcion, garaje['id']))
                conn.execute('UPDATE garajes SET estado = "ocupado" WHERE id = ?', (garaje['id'],))
                conn.execute('INSERT INTO alertas (mensaje) VALUES (?)',
                             (f"Nueva encomienda para usuario {destinatario_id} asignada al garaje {garaje['id']}",))
                conn.commit()
                flash(f'Encomienda registrada y asignada al garaje {garaje["id"]}')
            else:
                flash('No hay garajes disponibles en este momento')
        except sqlite3.Error as e:
            flash(f'Error al registrar la encomienda: {str(e)}')
        finally:
            conn.close()
        return redirect(url_for('dashboard'))
    conn = get_db_connection()
    usuarios = conn.execute('SELECT id, username FROM usuarios').fetchall()
    conn.close()
    return render_template('encomienda.html', usuarios=usuarios)

@app.route('/garaje/<string:id>', methods=['GET', 'POST'])
def garaje_detalle(id):
    conn = get_db_connection()
    garaje = conn.execute('SELECT * FROM garajes WHERE id = ?', (id,)).fetchone()
    encomienda = conn.execute('SELECT e.*, u.username FROM encomiendas e JOIN usuarios u ON e.destinatario_id = u.id WHERE e.garaje_id = ? AND e.fecha_entrega IS NULL', (id,)).fetchone()
    
    if request.method == 'POST':
        if encomienda:
            conn.execute('UPDATE encomiendas SET fecha_entrega = ? WHERE id = ?', (datetime.now(), encomienda['id']))
            conn.execute('UPDATE garajes SET estado = "disponible" WHERE id = ?', (id,))
            conn.execute('INSERT INTO alertas (mensaje) VALUES (?)', (f"Encomienda entregada en garaje {id}",))
            conn.commit()
            flash('Encomienda marcada como entregada y garaje liberado')
        else:
            flash('No hay encomienda pendiente en este garaje')
    
    conn.close()
    return render_template('garaje_detalle.html', garaje=garaje, encomienda=encomienda)

if __name__ == '__main__':
    app.run(debug=True)