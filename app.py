from flask import Flask, render_template, request, redirect, url_for, jsonify
from flask_socketio import SocketIO, emit
import eventlet

eventlet.monkey_patch()

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

clients = {}

@app.route('/')
def index():
    return render_template('index.html', clients=clients)

@socketio.on('client_connect')
def handle_client_connect(data):
    client_id = data.get('client_id')
    group = data.get('group')
    clients[client_id] = {'status': 'online', 'group': group}
    emit('update_clients', clients, broadcast=True)

@socketio.on('client_disconnect')
def handle_client_disconnect(data):
    client_id = data.get('client_id')
    if client_id in clients:
        del clients[client_id]
    emit('update_clients', clients, broadcast=True)

@socketio.on('send_command')
def handle_send_command(data):
    client_id = data.get('client_id')
    command = data.get('command')
    emit('execute_command', {'command': command}, room=client_id)

@socketio.on('register')
def handle_register():
    emit('register_ack', {'message': 'Registered successfully'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
