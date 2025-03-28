from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit
import sqlite3

app = Flask(__name__)
socketio = SocketIO(app)

# ======= DATABASE SETUP =======
def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''
        CREATE TABLE IF NOT EXISTS groups (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL
        )
    ''')
    c.execute('''
        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            group_id INTEGER,
            status TEXT DEFAULT 'offline',
            FOREIGN KEY(group_id) REFERENCES groups(id)
        )
    ''')
    conn.commit()
    conn.close()

init_db()

# ======= ROUTES =======
@app.route('/')
def index():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT id, name FROM groups')
    groups = c.fetchall()
    conn.close()
    return render_template('index.html', groups=groups)

@app.route('/create_group', methods=['POST'])
def create_group():
    data = request.json
    name = data.get('name')
    password = data.get('password')
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    try:
        c.execute('INSERT INTO groups (name, password) VALUES (?, ?)', (name, password))
        conn.commit()
        return jsonify({'success': True})
    except sqlite3.IntegrityError:
        return jsonify({'success': False, 'message': 'Group name already exists'})
    finally:
        conn.close()

@app.route('/group/<int:group_id>')
def view_group(group_id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT name FROM groups WHERE id = ?', (group_id,))
    group = c.fetchone()
    if not group:
        return 'Group not found', 404
    c.execute('SELECT id, name, status FROM clients WHERE group_id = ?', (group_id,))
    clients = c.fetchall()
    conn.close()
    return render_template('group.html', group={'id': group_id, 'name': group[0]}, clients=clients)

@app.route('/client_action', methods=['POST'])
def client_action():
    data = request.json
    client_id = data.get('client_id')
    action = data.get('action')
    if action not in ['reset', 'shutdown', 'rename', 'delete']:
        return jsonify({'success': False, 'message': 'Invalid action'})

    conn = sqlite3.connect('data.db')
    c = conn.cursor()

    if action == 'delete':
        c.execute('DELETE FROM clients WHERE id = ?', (client_id,))
    elif action == 'rename':
        new_name = data.get('new_name')
        c.execute('UPDATE clients SET name = ? WHERE id = ?', (new_name, client_id,))
    conn.commit()
    conn.close()

    socketio.emit('client_command', {'client_id': client_id, 'action': action})
    return jsonify({'success': True})

# ======= SOCKETIO =======
@socketio.on('client_status')
def handle_client_status(data):
    client_name = data.get('name')
    group_name = data.get('group')
    status = data.get('status')

    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT id FROM groups WHERE name = ?', (group_name,))
    group = c.fetchone()
    if not group:
        conn.close()
        return

    group_id = group[0]
    c.execute('SELECT id FROM clients WHERE name = ? AND group_id = ?', (client_name, group_id))
    client = c.fetchone()
    if client:
        c.execute('UPDATE clients SET status = ? WHERE id = ?', (status, client[0]))
    else:
        c.execute('INSERT INTO clients (name, group_id, status) VALUES (?, ?, ?)', (client_name, group_id, status))
    conn.commit()
    conn.close()

    emit('update_status', {'group_id': group_id, 'client_name': client_name, 'status': status}, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
