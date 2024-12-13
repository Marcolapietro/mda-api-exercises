from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
auth = HTTPBasicAuth()

# Base de datos en memoria para este ejemplo
usuarios = {
    "admin": generate_password_hash("admin123") # nosotros aqui estamos creando ya un usuario de prueba
}

# Verifica las credenciales proporcionadas
@auth.verify_password
def verify_password(username, password):
    # Verifica si el usuario está en la base de datos y si la contraseña es correcta
    if username in usuarios and check_password_hash(usuarios[username], password):
        return username
    return None

# Ruta para registrar nuevos usuarios
@app.route('/usuarios', methods=['   '])
def registrar_usuario():
    datos = request.get_json()
    username = datos.get("username")
    password = datos.get("password")

    if not username or not password:
        return jsonify({"error": "Faltan datos obligatorios"}), 400

    if username in usuarios:
        return jsonify({"error": "El usuario ya existe"}), 400

    # Pista: Usa generate_password_hash de la lbrería Werkzeug para almacenar la contraseña de forma segura
    usuarios[username] = _____(password)
    return jsonify({"mensaje": "Usuario registrado exitosamente"}), 201

# Ruta protegida para obtener la lista de usuarios
@app.route('/usuarios', methods=['   '])
@auth.login_required
def obtener_usuarios():
    # Pista: Devuelve la lista de usuarios registrados
    return jsonify({"usuarios": list(usuarios.keys())}), 200

# Manejo de errores personalizados
@app.errorhandler(404)
def no_encontrado(e):
    #  Personaliza el mensaje para rutas no encontradas
    return jsonify({"error": "Ruta no encontrada", "detalle": str(e)}), 404 # aquí pasamos el detalle del error capturado

@app.errorhandler(405)
def metodo_no_permitido(e):
    #Personaliza el mensaje para métodos HTTP no permitidos
    return jsonify({"error": "Método no permitido"}), 405

if __name__ == '__main__':
    # Ejecuta la aplicación en modo debug para facilitar pruebas
    # en producción no se debe poner!!
    app.run(debug=True)
