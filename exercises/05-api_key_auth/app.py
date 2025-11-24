from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
import _____  # Hint: Import the necessary library to generate API Keys
from functools import wraps

app = Flask(__name__)
auth = HTTPBasicAuth()

# Simulated database with more detailed structure
users = {
    # 'username': {'password': 'hashed_password', 'api_key': 'api_key'}
}

@auth.verify_password
def verify_user(username, password):
    if username in users and check_password_hash(users.get(username)['password'], password):
        return username
    return None

def api_key_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('x-api-key')
        if not api_key:
            return jsonify({'message': 'API Key missing.'}), 401
        # Verify if the API Key exists
        for user, info in users.items():
            if info.get('api_key') == api_key:
                return f(*args, **kwargs)
        return jsonify({'message': 'Invalid API Key.'}), 401
    return decorated

@app.route('/users', methods=['POST'])
def register_user():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required.'}), 400
    if username in users:
        return jsonify({'message': 'User is already registered.'}), 400

    # Generate and store the API Key
    api_key = str(_____)  # Hint: Use a function to generate a unique API Key (use a method from the imported library)
    users[username] = {
        'password': generate_password_hash(password),
        'api_key': api_key
    }

    return jsonify({'message': 'User registered successfully.', 'api_key': api_key}), 201

@app.route('/users', methods=['_____'])  # Hint: Indicate the correct HTTP method
@auth.login_required
@api_key_required
def get_users():
    user_list = list(users.keys())
    return jsonify({'users': user_list}), 200

@app.errorhandler(404)
def resource_not_found(error):
    return jsonify({'error': 'Resource not found.'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed.'}), 405

if __name__ == '__main__':
    app.run(debug=True)
