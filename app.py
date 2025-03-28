from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import json
import os

app = Flask(__name__)
socketio = SocketIO(app)

DATA_FILE = 'data.json'

# Load data
def load_data():
    if not os.path.exists(DATA_FILE):
        return {"groups": {}}
    with open(DATA_FILE, 'r') as f:
        return json.load(f)

# Save data
def save_data(data):
    with open(DATA_FILE, 'w') as f:
        json.dump(data, f)

# Routes
@app.route('/')
def index():
    data = load_data()
    return render_template('index.html', data=data)

@app.route('/create_group', methods=['POST'])
def create_group():
    data = load_data()
    group_name = request.form['group_name']
    password = request.form['password']
    if group_name not in data['groups']:
        data['groups'][group_name] = {"password": password, "clients": {}}
        save_data(data)
        return jsonify({"status": "success"})
    return jsonify({"status": "exists"})

@app.route('/get_groups', methods=['GET'])
def get_groups():
    data = load_data()
    return jsonify(data['groups'])

@app.route('/get_clients/<group>', methods=['GET'])
def get_clients(group):
    data = load_data()
    clients = data['groups'].get(group, {}).get('clients', {})
    return jsonify(clients)

@app.route('/update_client', methods=['POST'])
def update_client():
    data = load_data()
    group = request.form['group']
    client_id = request.form['client_id']
    action = request.form['action']
    if action == 'add':
        name = request.form['name']
        status = request.form['status']
        data['groups'][group]['clients'][client_id] = {"name": name, "status": status}
    elif action == 'remove':
        data['groups'][group]['clients'].pop(client_id, None)
    elif action == 'rename':
        new_name = request.form['new_name']
        data['groups'][group]['clients'][client_id]['name'] = new_name
    elif action == 'status':
        status = request.form['status']
        data['groups'][group]['clients'][client_id]['status'] = status
    save_data(data)
    return jsonify({"status": "success"})

# SocketIO
@socketio.on('command')
def handle_command(data):
    emit('command', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
