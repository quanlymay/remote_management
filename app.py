from flask import Flask, render_template, request, jsonify
from flask_socketio import SocketIO, emit

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

clients = {}

@app.route('/')
def index():
    return render_template('index.html', clients=clients)

@socketio.on('client_connect')
def handle_client_connect(data):
    client_id = data.get('client_id')
    group = data.get('group')
    if client_id:
        clients[client_id] = {'status': 'online', 'group': group}
        emit('update_clients', clients, broadcast=True)

@socketio.on('client_disconnect')
def handle_client_disconnect(data):
    client_id = data.get('client_id')
    if client_id and client_id in clients:
        clients.pop(client_id)
        emit('update_clients', clients, broadcast=True)

@app.route('/shutdown', methods=['POST'])
def shutdown():
    client_id = request.json.get('client_id')
    emit('shutdown', {'client_id': client_id}, broadcast=True)
    return jsonify({'message': 'Shutdown signal sent'})

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000)
