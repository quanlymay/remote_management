from flask import Flask, render_template, request, jsonify, send_from_directory
from flask_socketio import SocketIO, emit
import os

app = Flask(__name__)
socketio = SocketIO(app)

# Danh sách máy khách
machines = {}

@app.route('/')
def index():
    return render_template('index.html', machines=machines)

@app.route('/register', methods=['POST'])
def register():
    data = request.json
    machine_name = data.get("machine_name")
    group_name = data.get("group_name")
    password = data.get("password")

    # Kiểm tra nếu mật khẩu nhóm đúng (Giả lập)
    if group_name not in machines:
        machines[group_name] = {}

    machines[group_name][machine_name] = {"status": "online"}
    socketio.emit('update', machines)  # Cập nhật danh sách máy khách

    return jsonify({"success": True, "message": "Đăng ký thành công!"})

@app.route('/control', methods=['POST'])
def control():
    data = request.json
    machine_name = data.get("machine")
    action = data.get("action")

    # Tìm máy trong danh sách
    for group in machines.values():
        if machine_name in group:
            if action == "shutdown":
                group[machine_name]["status"] = "offline"
            elif action == "restart":
                group[machine_name]["status"] = "restarting"
            
            socketio.emit('update', machines)
            return jsonify({"success": True, "message": f"{action} executed on {machine_name}"})

    return jsonify({"success": False, "message": "Không tìm thấy máy"})

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=5000, debug=True)
