from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash
import math
import random
import string
import secrets
from urllib.parse import urlencode

app = Flask(__name__)

# Configuración de JWT
app.config['JWT_SECRET_KEY'] = 'clave_super_secreta_jwt'
jwt = JWTManager(app)

# Base de datos simulada para almacenar estudiantes
estudiantes = {}

# Generar usuarios de prueba
def generate_users(estudiantes, total):
    """Genera usuarios de prueba con nombres aleatorios"""
    for _ in range(total):
        username = ''.join(random.choices(string.ascii_letters, k=8))
        password = ''.join(random.choices(string.ascii_letters + string.digits, k=12))
        estudiantes[username] = {
            'password': generate_password_hash(password),
            'api_key': secrets.token_hex(16)
        }

@app.route('/register', methods=['POST'])
def register_student():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required.'}), 400
    if username in estudiantes:
        return jsonify({'message': 'User already exists.'}), 400

    estudiantes[username] = {
        'password': generate_password_hash(password),
        'api_key': secrets.token_hex(16)
    }
    return jsonify({'message': 'User registered successfully.', 'api_key': estudiantes[username]['api_key']}), 201

@app.route('/login', methods=['POST'])
def login():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required.'}), 400

    user = estudiantes.get(username)
    if user and check_password_hash(user['password'], password):
        access_token = create_access_token(identity=username)
        return jsonify({'access_token': access_token}), 200

    return jsonify({'message': 'Invalid username or password.'}), 401

@app.route('/perfil', methods=['GET'])
@jwt_required()
def perfil():
    current_user = get_jwt_identity()
    return jsonify({'perfil': f'Información del perfil de {current_user}'}), 200

@app.route('/estudiantes', methods=['GET'])
@jwt_required()
def obtener_estudiantes():
    try:
        # Obtener los parámetros de consulta 'page' y 'per_page' con valores predeterminados
        page = request.args.get('page', 1, type=int)  # Página actual
        per_page = request.args.get('per_page', 10, type=int)  # Estudiantes por página

        # Validar el valor de 'per_page'
        if per_page <= 0 or per_page > 100:
            return jsonify({'message': 'per_page debe ser entre 1 y 100.'}), 400

        # Calcular el número total de estudiantes y páginas
        total_students = len(estudiantes)  # Total de estudiantes registrados
        total_pages = math.ceil(total_students / per_page)  # Número total de páginas

        # Validar el rango de la página solicitada
        if page < 1 or page > total_pages:
            return jsonify({'message': 'Página no encontrada.'}), 404

        # Determinar los índices de inicio y fin de la lista de estudiantes
        start = (page - 1) * per_page  # Índice inicial
        end = start + per_page  # Índice final
        students_list = list(estudiantes.keys())[start:end]  # Subconjunto de estudiantes

        # Construir enlaces para navegar entre páginas
        base_url = request.base_url  # URL base de la solicitud
        query_params = request.args.to_dict()  # Parámetros de consulta actuales

        def build_url(new_page):
            # Construye una URL con el número de página actualizado
            query_params['page'] = new_page
            return f"{base_url}?{urlencode(query_params)}"

        # Crear enlaces de navegación (prev y next)
        links = {}
        if page > 1:
            links['prev'] = build_url(page - 1)  # Enlace a la página anterior
        if page < total_pages:
            links['next'] = build_url(page + 1)  # Enlace a la página siguiente

        # Retornar la respuesta con datos paginados
        return jsonify({
            'students': students_list,  # Lista de estudiantes en la página actual
            'total_pages': total_pages,  # Número total de páginas
            'current_page': page,  # Página actual
            'per_page': per_page,  # Número de estudiantes por página
            'total_students': total_students,  # Total de estudiantes registrados
            'links': links  # Enlaces de navegación
        }), 200

    except Exception as e:
        # Manejo de errores generales
        return jsonify({'error': 'Ocurrió un error al procesar la solicitud.', 'details': str(e)}), 500

if __name__ == '__main__':
    # Generar usuarios de prueba al inicio
    generate_users(estudiantes, 500)  # Generar 500 usuarios para probar la paginación
    app.run(debug=True)
