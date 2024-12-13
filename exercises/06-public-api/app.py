from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import requests

app = Flask(__name__)
auth = HTTPBasicAuth()

# Configuración de JWT
app.config['JWT_SECRET_KEY'] = 'tu_clave_secreta_jwt'  # Cambia esto por una clave secreta segura
jwt = JWTManager(app)

# Base de datos simulada para almacenar estudiantes
estudiantes = {
    # 'nombre_estudiante': {'password': 'hashed_password', 'api_key': 'api_key'}
}

@auth.verify_password
def verify_password(username, password):
    if username in estudiantes and check_password_hash(estudiantes.get(username)['password'], password):
        return username
    return None

@app.route('/estudiantes', methods=['POST'])
def register_student():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')
    
    if not username or not password:
        return jsonify({'message': 'Username and password are required.'}), 400
    if username in estudiantes:
        return jsonify({'message': 'User already exists.'}), 400
    
    # Hashear la contraseña antes de almacenarla
    estudiantes[username] = {
        'password': generate_password_hash(password),
        'api_key': 'api_key_placeholder'  # Implementa la generación de API Key si aplica. Pista: No.
    }
    return jsonify({'message': 'User registered successfully.'}), 201

@app.route('/login', methods=['POST'])
@auth.login_required
def login():
    current_user = auth.current_user() #create_acces_something
    access_token = _____(identity=current_user)
    return jsonify({'access_token': access_token}), 200

@app.route('/perfil', methods=['GET'])
@jwt_required()
def perfil():
    current_user = _____() # get_something
    return jsonify({'perfil': f'Información del perfil de {current_user}'}), 200

@app.route('/clima', methods=['GET'])
@jwt_required()
def clima():
    ciudad = request.args.get('ciudad', 'Madrid')
    api_key = 'TU API KEY DE OPENWEATHER MAP' #Regístrate en OpenWeatherMap para conseguir tu API Key
    url = f'http://api.openweathermap.org/data/2.5/weather?q={ciudad}&appid={api_key}&units=metric&lang=es'
    respuesta = requests.get(url)
    if respuesta.status_code == 200:
        datos = respuesta.json()
        clima_info = {
            'ciudad': datos['name'],
            'temperatura': datos['main']['temp'],
            'descripcion': datos['weather'][0]['description']
        }
        return jsonify(clima_info), 200
    else:
        return jsonify({'message': 'No se pudo obtener la información del clima.'}), 400

@app.route('/estudiantes', methods=['GET'])
@auth.login_required
def get_students():
    return jsonify({'students': list(estudiantes.keys())}), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found.'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed.'}), 405

if __name__ == '__main__':
    app.run(debug=True)
