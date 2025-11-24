from flask import Flask, jsonify, request
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
import requests

app = Flask(__name__)
auth = HTTPBasicAuth()

# JWT Configuration
app.config['JWT_SECRET_KEY'] = 'your_secret_jwt_key'  # Change this to a secure secret key
jwt = JWTManager(app)

# Simulated database to store students
students = {
    # 'student_name': {'password': 'hashed_password', 'api_key': 'api_key'}
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
    current_user = auth.current_user() #create_acces_something
    # TODO: Generate a JWT access token
    # Hint: Use create_access_token(identity=current_user)
    access_token = _____(identity=current_user)
    return jsonify({'access_token': access_token}), 200

@app.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    # TODO: Get the user's identity from the JWT token
    # Hint: Use get_jwt_identity()
    current_user = _____() # get_something
    return jsonify({'profile': f'Profile information for {current_user}'}), 200

@app.route('/weather', methods=['GET'])
@jwt_required()
def weather():
    city = request.args.get('city', 'Madrid')
    api_key = 'YOUR OPENWEATHER MAP API KEY' # Register on OpenWeatherMap to get your API Key
    url = f'http://api.openweathermap.org/data/2.5/weather?q={city}&appid={api_key}&units=metric&lang=en'
    response = requests.get(url)
    if response.status_code == 200:
        data = response.json()
        weather_info = {
            'city': data['name'],
            'temperature': data['main']['temp'],
            'description': data['weather'][0]['description']
        }
        return jsonify(weather_info), 200
    else:
        return jsonify({'message': 'Could not retrieve weather information.'}), 400

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
