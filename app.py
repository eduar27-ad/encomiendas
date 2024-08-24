from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
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
    estacionamientos = conn.execute('SELECT * FROM garajes').fetchall()
    conn.close()
    return render_template('index.html', estacionamientos=estacionamientos)

@app.route('/consultar_encomienda', methods=['POST'])
def consultar_encomienda():
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
            'usuario': usuario['username'],
            'encomiendas': [{'descripcion': e['descripcion'], 'fecha': e['fecha']} for e in encomiendas]
        })
    conn.close()
    return jsonify({'error': 'Usuario no encontrado o clave incorrecta'}), 404

@app.route('/activar_entrada', methods=['POST'])
def activar_entrada():
    conn = get_db_connection()
    estacionamiento = conn.execute('SELECT id FROM garajes WHERE estado = "disponible" LIMIT 1').fetchone()
    if estacionamiento:
        conn.execute('UPDATE garajes SET estado = "ocupado" WHERE id = ?', (estacionamiento['id'],))
        conn.commit()
        conn.close()
        return jsonify({'estacionamiento': estacionamiento['id']})
    conn.close()
    return jsonify({'error': 'No hay estacionamientos disponibles'}), 404


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=8080, debug=True)