from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
app.config['SECRET_KEY'] = 'secret!'
socketio = SocketIO(app, async_mode='eventlet')

# Dữ liệu lưu nhóm và máy
groups = {}

@app.route('/')
def index():
    return render_template('index.html', groups=groups)

@app.route('/create_group', methods=['POST'])
def create_group():
    data = request.json
    group_name = data.get('group_name')
    password = data.get('password')
    if group_name not in groups:
        groups[group_name] = {
            'password': password,
            'clients': []
        }
    return jsonify({'success': True})

@app.route('/get_groups')
def get_groups():
    return jsonify(groups)

@app.route('/remove_client', methods=['POST'])
def remove_client():
    data = request.json
    group_name = data.get('group')
    client_name = data.get('client')
    if group_name in groups:
        groups[group_name]['clients'] = [
            c for c in groups[group_name]['clients'] if c['name'] != client_name
        ]
    return jsonify({'success': True})

@socketio.on('register_client')
def handle_register_client(data):
    group_name = data.get('group')
    password = data.get('password')
    client_name = data.get('name')
    if group_name in groups and groups[group_name]['password'] == password:
        client_info = {'name': client_name, 'status': 'online'}
        groups[group_name]['clients'].append(client_info)
        emit('client_list_updated', groups, broadcast=True)
    else:
        emit('register_failed')

@socketio.on('client_disconnect')
def handle_client_disconnect(data):
    group_name = data.get('group')
    client_name = data.get('name')
    if group_name in groups:
        groups[group_name]['clients'] = [
            c for c in groups[group_name]['clients'] if c['name'] != client_name
        ]
        emit('client_list_updated', groups, broadcast=True)

@socketio.on('control_command')
def handle_control_command(data):
    emit('execute_command', data, broadcast=True)

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
