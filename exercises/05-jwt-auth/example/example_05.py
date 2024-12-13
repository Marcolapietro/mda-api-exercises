from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)
auth = HTTPBasicAuth()

# Configuración de JWT
app.config['JWT_SECRET_KEY'] = 'clave_super_secreta_jwt'  # Cambia esto por una clave secreta segura
jwt = JWTManager(app)

# Base de datos simulada para almacenar usuarios
usuarios = {
    # 'nombre_usuario': {'password': 'hashed_password', 'api_key': 'api_key'}
}

@auth.verify_password
def verify_password(username, password):
    if username in usuarios and check_password_hash(usuarios.get(username)['password'], password):
        return username
    return None

@app.route('/usuarios', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Username and password are required.'}), 400
    if username in usuarios:
        return jsonify({'message': 'User already exists.'}), 400
    
    # Hashear la contraseña antes de almacenarla
    usuarios[username] = {
        'password': generate_password_hash(password),
        'api_key': 'api_key_placeholder'  # Implementa la generación de API Key si aplica
    }
    return jsonify({'message': 'User registered successfully.'}), 201

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

@app.route('/usuarios', methods=['GET'])
@auth.login_required
def get_users():
    return jsonify({'users': list(usuarios.keys())}), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found.'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed.'}), 405

if __name__ == '__main__':
    app.run(debug=True)
