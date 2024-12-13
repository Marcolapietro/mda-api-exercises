from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import requests

app = Flask(__name__)
auth = HTTPBasicAuth()

# Configuración de JWT
app.config['JWT_SECRET_KEY'] = 'clave_super_secreta_jwt'
jwt = JWTManager(app)

# Base de datos simulada para almacenar usuarios
usuarios = {}

@auth.verify_password
def verify_password(username, password):
    if username in usuarios and check_password_hash(usuarios.get(username)['password'], password):
        return username
    return None

@app.route('/usuarios', methods=['POST'])
def register_user():
    try:
        data = request.get_json()
        print("Datos recibidos:", data)  # Debug print
        
        if not data:
            return jsonify({'message': 'No se recibieron datos JSON.'}), 400
            
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({'message': 'Se requieren username y password.'}), 400
            
        if username in usuarios:
            return jsonify({'message': 'El usuario ya existe.'}), 400
        
        usuarios[username] = {
            'password': generate_password_hash(password),
            'api_key': 'api_key_placeholder'
        }
        return jsonify({'message': 'Usuario registrado exitosamente.'}), 201
        
    except Exception as e:
        print("Error:", str(e))  # Debug print
        return jsonify({'message': f'Error al procesar la solicitud: {str(e)}'}), 400

@app.route('/login', methods=['POST'])
@auth.login_required
def login():
    current_user = auth.current_user()
    access_token = create_access_token(identity=current_user)
    return jsonify({'access_token': access_token}), 200

@app.route('/perfil', methods=['GET'])
@jwt_required()
def perfil():
    current_user = get_jwt_identity()
    return jsonify({'perfil': f'Información del perfil de {current_user}'}), 200

@app.route('/usuarios/admin', methods=['POST'])
@jwt_required()
def crear_usuario_admin():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Se requieren username y password.'}), 400
        
    if username in usuarios:
        return jsonify({'message': 'El usuario ya existe.'}), 400
    
    usuarios[username] = {
        'password': generate_password_hash(password),
        'api_key': 'api_key_placeholder'
    }
    return jsonify({'message': 'Usuario creado exitosamente.'}), 201

@app.route('/usuarios', methods=['GET'])
@jwt_required()
def obtener_usuarios():
    return jsonify({'users': list(usuarios.keys())}), 200

@app.route('/usuarios/<username>', methods=['PUT'])
@jwt_required()
def actualizar_usuario(username):
    if username not in usuarios:
        return jsonify({'message': 'Usuario no encontrado.'}), 404
    
    data = request.get_json()
    password = data.get('password')
    
    if password:
        usuarios[username]['password'] = generate_password_hash(password)
        return jsonify({'message': 'Usuario actualizado exitosamente.'}), 200
    else:
        return jsonify({'message': 'No hay datos para actualizar.'}), 400

@app.route('/usuarios/<username>', methods=['DELETE'])
@jwt_required()
def eliminar_usuario(username):
    if username not in usuarios:
        return jsonify({'message': 'Usuario no encontrado.'}), 404
    
    del usuarios[username]
    return jsonify({'message': 'Usuario eliminado exitosamente.'}), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Recurso no encontrado.'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Método no permitido.'}), 405

if __name__ == '__main__':
    app.run(debug=True)