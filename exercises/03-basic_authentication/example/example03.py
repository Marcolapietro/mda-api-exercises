from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
auth = HTTPBasicAuth()

usuarios = {}

@auth.verify_password
def verify_password(username, password):
    if username in usuarios and check_password_hash(usuarios[username], password):
        return username
    return None

@app.route('/usuarios', methods=['POST'])
def registrar_usuario():
    datos = request.get_json()
    username = datos.get("username")
    password = datos.get("password")

    if not username or not password:
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    if username in usuarios:
        return jsonify({"error": "El usuario ya existe"}), 400

    usuarios[username] = generate_password_hash(password)
    return jsonify({"mensaje": "Usuario registrado exitosamente"}), 201

@app.route('/usuarios', methods=['GET'])
@auth.login_required
def obtener_usuarios():
    return jsonify({"usuarios": list(usuarios.keys())}), 200

@app.errorhandler(404)
def no_encontrado(e):
    return jsonify({"error": "Ruta no encontrada"}), 404

@app.errorhandler(405)
def metodo_no_permitido(e):
    return jsonify({"error": "Método no permitido", "detalle": str(e)}), 405

if __name__ == '__main__':
    app.run(debug=True)
