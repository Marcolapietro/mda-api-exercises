from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity

app = Flask(__name__)
auth = HTTPBasicAuth()

# JWT Configuration
# WARNING: In production, use environment variables for secrets!
# Example: app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY')
app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'  # Hint: Change this to a secure secret key (only for educational purposes)
jwt = _____(app)  # Hint: Initialize JWTManager with the app, check the library documentation.

# Simulated database to store students
students = {
    # 'student_name': {'password': 'hashed_password'}
}

@auth.verify_password
def verify_password(username, password):
    if username in students and check_password_hash(students.get(username)['password'], password):
        return username
    return None

@app.route('/students', methods=['POST'])
def register_student():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required.'}), 400
    if username in students:
        return jsonify({'message': 'User already exists.'}), 400

    # Hash the password before storing it
    students[username] = {
        'password': generate_password_hash(password)
    }
    return jsonify({'message': 'User registered successfully.'}), 201

@app.route('/login', methods=['POST'])
@auth.login_required
def login():
    current_user = _____()  # Hint: Retrieve the currently authenticated user. Use a method from the 'auth' object.
    access_token = _____(identity=current_user)  # Hint: Generate a JWT token. Use one of the functions from flask_jwt_extended imported above.
    return jsonify({'access_token': access_token}), 200

@app.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    current_user = _____()  # Hint: Get the user's identity from the JWT token.
    return jsonify({'profile': f'Profile information for {current_user}'}), 200

@app.route('/students', methods=['GET'])
@auth.login_required
def get_students():
    return jsonify({'students': list(students.keys())}), 200

@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Resource not found.'}), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({'error': 'Method not allowed.'}), 405

if __name__ == '__main__':
    app.run(debug=True)
