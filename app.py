from flask import Flask, render_template, request, redirect, url_for, session, flash
import sqlite3
import os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'no-compartir-esta-clave-en-produccion'

UPLOAD_FOLDER = 'static/images'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 5 * 1024 * 1024
DATABASE = 'database.db'

ADMIN_PASSWORD = '2009241030'

def get_db():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    with get_db() as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS services
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             name TEXT NOT NULL,
             description TEXT,
             price REAL NOT NULL,
             image TEXT)''')
        conn.execute('''CREATE TABLE IF NOT EXISTS requests
            (id INTEGER PRIMARY KEY AUTOINCREMENT,
             service_id INTEGER,
             service_name TEXT,
             username TEXT NOT NULL,
             contact TEXT NOT NULL,
             roblox_user TEXT,
             message TEXT,
             created_at TEXT DEFAULT (datetime('now','localtime')))''')

init_db()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/store')
def store():
    with get_db() as conn:
        servicios = conn.execute('SELECT * FROM services ORDER BY id DESC').fetchall()
    return render_template('store.html', services=servicios)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if not session.get('admin'):
        if request.method == 'POST':
            if request.form.get('password') == ADMIN_PASSWORD:
                session['admin'] = True
                flash('Acceso correcto', 'success')
                return redirect('/admin')
            flash('Clave incorrecta', 'error')
        return render_template('admin_login.html')

    mensaje = None
    if request.method == 'POST':
        if 'add' in request.form:
            nombre = request.form.get('name', '').strip()
            desc = request.form.get('description', '').strip()
            try:
                precio = float(request.form.get('price', 0))
            except:
                precio = 0
            imagen = ''
            archivo = request.files.get('image_file')
            if archivo and archivo.filename:
                nombre_archivo = secure_filename(archivo.filename)
                archivo.save(os.path.join(UPLOAD_FOLDER, nombre_archivo))
                imagen = nombre_archivo

            if nombre and precio > 0:
                with get_db() as conn:
                    conn.execute('INSERT INTO services (name, description, price, image) VALUES (?,?,?,?)',
                                 (nombre, desc, precio, imagen))
                mensaje = 'Servicio agregado'
            else:
                mensaje = 'Faltan datos'

    with get_db() as conn:
        servicios = conn.execute('SELECT * FROM services ORDER BY id DESC').fetchall()
        solicitudes = conn.execute('SELECT * FROM requests ORDER BY created_at DESC LIMIT 30').fetchall()

    return render_template('admin.html', services=servicios, requests=solicitudes, mensaje=mensaje)

@app.route('/admin/logout')
def logout():
    session.pop('admin', None)
    return redirect('/admin')

if __name__ == '__main__':
    from os import environ
    port = int(environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
