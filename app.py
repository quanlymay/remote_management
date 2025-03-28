from flask import Flask, render_template, request, redirect, jsonify
from flask_socketio import SocketIO, emit
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app)

groups = {}  # {group_name: {'password': 'xxx', 'clients': [{'name': 'PC01', 'status': 'online'}]}}

@app.route('/')
def index():
    return render_template('index.html', groups=groups)

@app.route('/create_group', methods=['POST'])
def create_group():
    data = request.json
    name = data.get('name')
    password = data.get('password')
    if name in groups:
        return jsonify({'status': 'error', 'message': 'Group already exists'}), 400
    groups[name] = {'password': password, 'clients': []}
    return jsonify({'status': 'success'})

@app.route('/get_clients/<group_name>')
def get_clients(group_name):
    if group_name not in groups:
        return jsonify([])
    return jsonify(groups[group_name]['clients'])

@app.route('/action', methods=['POST'])
def action():
    data = request.json
    group = data['group']
    client = data['client']
    command = data['command']
    socketio.emit('control', {'client': client, 'command': command}, broadcast=True)
    return jsonify({'status': 'success'})

@app.route('/rename', methods=['POST'])
def rename():
    data = request.json
    group = data['group']
    old_name = data['old_name']
    new_name = data['new_name']
    for c in groups[group]['clients']:
        if c['name'] == old_name:
            c['name'] = new_name
            break
    return jsonify({'status': 'success'})

@socketio.on('connect_client')
def connect_client(data):
    group = data.get('group')
    password = data.get('password')
    name = data.get('name')
    if group not in groups or groups[group]['password'] != password:
        emit('auth_failed')
        return
    client = {'name': name, 'status': 'online'}
    groups[group]['clients'].append(client)
    emit('update', broadcast=True)

@socketio.on('disconnect_client')
def disconnect_client(data):
    group = data.get('group')
    name = data.get('name')
    if group in groups:
        groups[group]['clients'] = [c for c in groups[group]['clients'] if c['name'] != name]
    emit('update', broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
