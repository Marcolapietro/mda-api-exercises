
### **Solución Opcional (`ejercicios/04-autenticacion-api-key/solucion/app.py`)**

from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import uuid
from functools import wraps

app = Flask(__name__)
auth = HTTPBasicAuth()

# Base de datos simulada con estructura más detallada
usuarios = {
    # 'nombre_usuario': {'password': 'hashed_password', 'api_key': 'api_key'}
}

@auth.verify_password
def verificar_usuario(nombre, contrasena):
    if nombre in usuarios and check_password_hash(usuarios.get(nombre)['password'], contrasena):
        return nombre
    return None

def api_key_requerida(f):
    @wraps(f)
    def decorado(*args, **kwargs):
        api_key = request.headers.get('x-api-key')
        if not api_key:
            return jsonify({'message': 'API Key faltante.'}), 401
        # Verifica si la API Key existe
        for usuario, info in usuarios.items():
            if info.get('api_key') == api_key:
                return f(*args, **kwargs)
        return jsonify({'message': 'API Key inválida.'}), 401
    return decorado

@app.route('/usuarios', methods=['POST'])
def registrar_usuario():
    datos = request.get_json()
    nombre = datos.get('username')
    contrasena = datos.get('password')
    
    if not nombre or not contrasena:
        return jsonify({'message': 'Username y password son requeridos.'}), 400
    if nombre in usuarios:
        return jsonify({'message': 'El usuario ya está registrado.'}), 400
    
    # Generar y almacenar la API Key
    api_key = str(uuid.uuid4())
    usuarios[nombre] = {
        'password': generate_password_hash(contrasena),
        'api_key': api_key
    }
    
    return jsonify({'message': 'Usuario registrado exitosamente.', 'api_key': api_key}), 201

@app.route('/usuarios', methods=['GET'])
@auth.login_required
@api_key_requerida
def obtener_usuarios():
    lista_usuarios = list(usuarios.keys())
    return jsonify({'usuarios': lista_usuarios}), 200

@app.errorhandler(404)
def recurso_no_encontrado(error):
    return jsonify({'error': 'Recurso no encontrado.'}), 404

@app.errorhandler(405)
def metodo_no_permitido(error):
    return jsonify({'error': 'Método no permitido.'}), 405

if __name__ == '__main__':
    app.run(debug=True)
