from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
from flask_principal import Principal, Permission, RoleNeed, identity_loaded, UserNeed, Identity, identity_changed
import math
import random
import string
import secrets
from urllib.parse import urlencode

app = Flask(__name__)

# Configuración de JWT para manejar autenticación basada en tokens
app.config['JWT_SECRET_KEY'] = 'clave_super_secreta_jwt'
jwt = JWTManager(app)

# Configuración de Flask-Principal para manejar roles y permisos
app.config['SECRET_KEY'] = 'clave_secreta_flask' 
principals = Principal(app)

# Definición de roles y permisos
admin_permission = Permission(RoleNeed('admin'))  # Permiso para administradores
student_permission = Permission(RoleNeed('student'))  # Permiso para estudiantes

# Base de datos simulada para almacenar usuarios
usuarios = {}

# Generar usuarios de prueba
def generate_users(usuarios, total):
    """Genera usuarios de prueba con roles aleatorios"""
    roles = ['admin', 'student']
    for _ in range(total):
        username = ''.join(random.choices(string.ascii_letters, k=8))
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        role = random.choice(roles)
        usuarios[username] = {
            'password': generate_password_hash(password),
            'api_key': secrets.token_hex(16),
            'role': role
        }

@app.route('/register', methods=['POST'])
def register_user():
    """Registra un nuevo usuario con un rol predeterminado o personalizado"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    role = data.get('role', 'student')

    if not username or not password:
        return jsonify({'message': 'Username and password are required.'}), 400
    if username in usuarios:
        return jsonify({'message': 'User already exists.'}), 400

    usuarios[username] = {
        'password': generate_password_hash(password),
        'api_key': secrets.token_hex(16),
        'role': role
    }
    return jsonify({'message': 'User registered successfully.', 'role': role}), 201

@app.route('/login', methods=['POST'])
def login():
    """Autentica a un usuario y genera un token JWT"""
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required.'}), 400

    user = usuarios.get(username)
    if user and check_password_hash(user['password'], password):
        access_token = create_access_token(identity=username)  # Genera un token JWT para el usuario autenticado
        identity_changed.send(app, identity=Identity(username))
        return jsonify({'access_token': access_token}), 200

    return jsonify({'message': 'Invalid username or password.'}), 401

@app.route('/perfil', methods=['GET'])
@jwt_required()
def perfil():
    """Retorna el perfil del usuario autenticado"""
    current_user = get_jwt_identity()
    return jsonify({'perfil': f'Información del perfil de {current_user}'}), 200

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    """Carga los permisos y roles del usuario autenticado"""
    identity.user = identity.id  # Pista: Asocia el usuario autenticado con la identidad
    identity.provides.add(UserNeed(identity.id))  # Pista: Agrega permiso basado en el ID del usuario

    if identity.id in usuarios:
        role = usuarios[identity.id].get('role')  # Pista: Recupera el rol del usuario autenticado
        if role:
            identity.provides.add(____Need(role))  # Pista: Agrega el rol como un permiso

@app.route('/usuarios', methods=['GET'])
@jwt_required()
def obtener_usuarios():
    """Retorna una lista de usuarios con paginación"""
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    total_users = len(usuarios)
    total_pages = math.ceil(total_users / per_page)

    if page > total_pages or page < 1:
        return jsonify({'message': 'Page not found.'}), 404

    start = (page - 1) * per_page
    end = start + per_page
    users_list = list(usuarios.keys())[start:end]

    return jsonify({
        'users': users_list,
        'total_pages': total_pages,
        'current_page': page
    }), 200

@app.route('/usuarios/<username>', methods=['PUT'])
@jwt_required()
def actualizar_usuario(username):
    """Actualiza la información de un usuario existente"""
    current_user = get_jwt_identity()

    if username not in usuarios:
        return jsonify({'message': 'User not found.'}), 404

    if not admin_permission.can():
        return jsonify({'message': 'Permission denied.'}), 403

    data = request.get_json()
    password = data.get('password')
    role = data.get('role')

    if password:
        usuarios[username]['password'] = generate_password_hash(password)  # Pista: Actualiza la contraseña del usuario
    if role:
        usuarios[username]['____'] = role  # Pista: Actualiza el rol del usuario

    return jsonify({'message': 'User updated successfully.'}), 200

@app.route('/usuarios/<username>', methods=['DELETE'])
@jwt_required()
@admin_permission.require(http_exception=403)
def eliminar_usuario(username):
    """Elimina a un usuario si el solicitante tiene permisos de administrador"""
    if username not in usuarios:
        return jsonify({'message': 'User not found.'}), 404

    ___ usuarios[username]  # Pista: Elimina al usuario de la base de datos. ¿Como se dice borrar en inglés? Una palabra, es de Python, no tiene que ver con el framework.
    return jsonify({'message': 'User deleted successfully.'}), 200

@app.route('/admin/dashboard', methods=['GET'])
@jwt_required()
@admin_permission.require(http_exception=403)
def admin_dashboard():
    """Retorna el dashboard exclusivo para administradores"""
    return jsonify({'message': f'Bienvenido al dashboard de admin, {get_jwt_identity()}.'}), 200

@app.route('/student/data', methods=['GET'])
@jwt_required()
@student_permission.require(http_exception=403)
def student_data():
    """Retorna datos específicos del estudiante autenticado"""
    return jsonify({'message': f'Datos del estudiante {get_jwt_identity()}.'}), 200

if __name__ == '__main__':
    generate_users(usuarios, 100)  # Pista: Genera usuarios de prueba con roles aleatorios
    app.run(debug=True)
