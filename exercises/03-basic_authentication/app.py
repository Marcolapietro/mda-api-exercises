from flask import Flask, request, jsonify
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
auth = HTTPBasicAuth()

# In-memory database for this example
users = {
    "admin": generate_password_hash("admin123")  # We are creating a test user here
}

# Verify the provided credentials
@auth.verify_password
def verify_password(username, password):
    # Check if the user is in the database and if the password is correct
    if username in users and check_password_hash(users[username], password):
        return username
    return None

# Route to register new users
@app.route('/users', methods=['   '])
def register_user():
    data = request.get_json()
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return jsonify({"error": "Required data is missing"}), 400

    if username in users:
        return jsonify({"error": "User already exists"}), 400

    # Hint: Use generate_password_hash from Werkzeug library to store the password securely
    users[username] = _____(password)
    return jsonify({"message": "User registered successfully"}), 201

# Protected route to get the list of users
@app.route('/users', methods=['   '])
@auth.login_required
def get_users():
    # Hint: Return the list of registered users
    return jsonify({"users": list(users.keys())}), 200

# Custom error handlers
@app.errorhandler(404)
def not_found(e):
    # Customize the message for routes not found
    return jsonify({"error": "Route not found", "detail": str(e)}), 404  # Here we pass the captured error detail

@app.errorhandler(405)
def method_not_allowed(e):
    # Customize the message for HTTP methods not allowed
    return jsonify({"error": "Method not allowed"}), 405

if __name__ == '__main__':
    # Run the application in debug mode to facilitate testing
    # Do not use this in production!!
    app.run(debug=True)
