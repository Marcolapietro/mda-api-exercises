import os
from flask import Flask, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_principal import Principal, Permission, RoleNeed, identity_loaded, UserNeed, Identity, AnonymousIdentity
import math
import random
import string
import secrets

app = Flask(__name__)

# JWT configuration for token-based authentication
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY') or secrets.token_hex(32)  # from env; random per run if unset
jwt = JWTManager(app)

# Flask-Principal configuration for role and permission management
app.config['SECRET_KEY'] = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)  # from env; random per run if unset
# use_sessions=False: the identity comes from the JWT on every request, never from a session cookie
principals = Principal(app, use_sessions=False)

VALID_ROLES = ('admin', 'student')


@principals.identity_loader
def load_identity_from_jwt():
    """Builds the Flask-Principal identity from the JWT sent in the Authorization header."""
    try:
        verify_jwt_in_request(optional=True)
        username = get_jwt_identity()
    except Exception:
        username = None
    return Identity(username) if username else AnonymousIdentity()

# Role and permission definitions
admin_permission = Permission(RoleNeed('admin'))  # Permission for administrators
student_permission = Permission(RoleNeed('student'))  # Permission for students

# Simulated database for storing users
users = {}

# Generate test users
def generate_users(users, total):
    """Generates test users with random roles"""
    roles = ['admin', 'student']
    # These users only exist to have data to list (nobody logs in with them).
    # Hashing one random password once keeps start-up fast: hashing 100 passwords
    # one by one takes many seconds.
    unusable_hash = generate_password_hash(secrets.token_hex(16))
    for _ in range(total):
        username = ''.join(random.choices(string.ascii_letters, k=8))
        role = random.choice(roles)
        users[username] = {
            'password': unusable_hash,
            'api_key': secrets.token_hex(16),
            'role': role
        }

def create_admin_user():
    """Bootstraps one admin account so the admin-only endpoints can be tested.

    The password comes from the ADMIN_PASSWORD environment variable; if it is not set,
    a random one is generated and printed once in the console.
    """
    password = os.environ.get('ADMIN_PASSWORD') or secrets.token_urlsafe(12)
    users['admin'] = {
        'password': generate_password_hash(password),
        'api_key': secrets.token_hex(16),
        'role': 'admin'
    }
    if not os.environ.get('ADMIN_PASSWORD'):
        print(f"Admin user created -> username: admin  password: {password}")

@app.route('/register', methods=['POST'])
def register_user():
    """Registers a new user. New users are ALWAYS students.

    Security: the role is never taken from the request body. Accepting it would let anyone
    register as admin (a "mass assignment" vulnerability). Only an admin can change roles
    via PUT /users/<username>.
    """
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required.'}), 400
    if username in users:
        return jsonify({'message': 'User already exists.'}), 409

    users[username] = {
        'password': generate_password_hash(password),
        'api_key': secrets.token_hex(16),
        'role': 'student'
    }
    return jsonify({'message': 'User registered successfully.', 'role': 'student'}), 201

@app.route('/login', methods=['POST'])
def login():
    """Authenticates a user and generates a JWT token that includes the role as a claim"""
    data = request.get_json(silent=True) or {}
    username = data.get('username')
    password = data.get('password')

    if not username or not password:
        return jsonify({'message': 'Username and password are required.'}), 400

    user = users.get(username)
    if user and check_password_hash(user['password'], password):
        access_token = create_access_token(identity=username, additional_claims={'role': user['role']})
        return jsonify({'access_token': access_token}), 200

    return jsonify({'message': 'Invalid username or password.'}), 401

@app.route('/profile', methods=['GET'])
@jwt_required()
def profile():
    """Returns the authenticated user's profile"""
    current_user = get_jwt_identity()
    return jsonify({'profile': f'Profile information for {current_user}'}), 200

@identity_loaded.connect_via(app)
def on_identity_loaded(sender, identity):
    """Loads permissions and roles for the authenticated user"""
    identity.user = identity.id
    identity.provides.add(UserNeed(identity.id))

    if identity.id in users:
        role = users[identity.id].get('role')
        if role:
            identity.provides.add(RoleNeed(role))

@app.route('/users', methods=['GET'])
@jwt_required()
def get_users():
    """Returns a list of users with pagination"""
    page = request.args.get('page', 1, type=int)
    per_page = min(max(request.args.get('per_page', 10, type=int), 1), 100)  # clamp to 1..100

    total_users = len(users)
    total_pages = math.ceil(total_users / per_page)

    if page > total_pages or page < 1:
        return jsonify({'message': 'Page not found.'}), 404

    start = (page - 1) * per_page
    end = start + per_page
    users_list = list(users.keys())[start:end]

    return jsonify({
        'users': users_list,
        'total_pages': total_pages,
        'current_page': page
    }), 200

@app.route('/users/<username>', methods=['PUT'])
@jwt_required()
def update_user(username):
    """Updates an existing user's information (admins only)"""
    # Check permission BEFORE looking the user up: answering 404 to a non-admin
    # would reveal which usernames exist
    if not admin_permission.can():
        return jsonify({'message': 'Permission denied.'}), 403

    if username not in users:
        return jsonify({'message': 'User not found.'}), 404

    data = request.get_json(silent=True) or {}
    password = data.get('password')
    role = data.get('role')

    if role is not None and role not in VALID_ROLES:
        return jsonify({'message': f'Invalid role. Allowed: {", ".join(VALID_ROLES)}.'}), 400

    if password:
        users[username]['password'] = generate_password_hash(password)
    if role:
        users[username]['role'] = role

    return jsonify({'message': 'User updated successfully.'}), 200

@app.route('/users/<username>', methods=['DELETE'])
@jwt_required()
@admin_permission.require(http_exception=403)
def delete_user(username):
    """Deletes a user if the requester has administrator permissions"""
    if username not in users:
        return jsonify({'message': 'User not found.'}), 404

    users.pop(username)
    return jsonify({'message': 'User deleted successfully.'}), 200

@app.route('/admin/dashboard', methods=['GET'])
@jwt_required()
@admin_permission.require(http_exception=403)
def admin_dashboard():
    """Returns the dashboard exclusive to administrators"""
    return jsonify({'message': f'Welcome to the admin dashboard, {get_jwt_identity()}.'}), 200

@app.route('/student/data', methods=['GET'])
@jwt_required()
@student_permission.require(http_exception=403)
def student_data():
    """Returns specific data for the authenticated student"""
    return jsonify({'message': f'Student data for {get_jwt_identity()}.'}), 200

if __name__ == '__main__':
    debug = os.getenv("FLASK_DEBUG") == "1"
    # In debug mode the reloader runs this file twice: a watcher process and the process
    # that actually serves requests (WERKZEUG_RUN_MAIN == 'true'). Create the data only in
    # the serving process, so the admin password printed is the one that works.
    if not debug or os.environ.get('WERKZEUG_RUN_MAIN') == 'true':
        # Generate 100 test users with random roles for testing, plus one known admin
        generate_users(users, 100)
        create_admin_user()
    app.run(debug=debug)
