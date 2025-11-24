from flask import Flask, request
from flask_restx import Api, Resource, fields, Namespace
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# JWT Configuration
# WARNING: In production, use environment variables for secrets!
app.config['JWT_SECRET_KEY'] = 'super_secret_jwt_key'  # Only for educational purposes
jwt = JWTManager(app)

# TODO: Configure Flask-RESTX Api with authorization
# Hint: Add authorizations parameter for JWT Bearer token documentation
authorizations = {
    'Bearer': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': 'JWT Bearer token. Format: Bearer <your_token_here>'
    }
}

# TODO: Initialize the Api object
# Hint: You need to specify version, title, description, doc path, and authorizations
api = Api(
    app,
    version='_____',  # TODO: Add API version (e.g., '1.0')
    title='User Management API',
    description='RESTful API with JWT authentication and automatic Swagger documentation',
    doc='_____',  # TODO: Specify the Swagger UI path (e.g., '/docs')
    authorizations=authorizations
)

# Simulated database to store users
users = {}

# TODO: Create namespaces to organize endpoints
# Hint: Namespaces help group related endpoints together
auth_ns = api.namespace('_____', description='Authentication operations')  # TODO: Name this namespace 'auth'
users_ns = api.namespace('_____', description='User management operations')  # TODO: Name this namespace 'users'

# ============================================================================
# MODELS - Define the structure of request/response data
# ============================================================================

# TODO: Define model for user registration
# Hint: Use api.model() to create a model with username and password fields
user_register_model = api.model('UserRegister', {
    'username': fields.String(
        required=_____,  # TODO: Should username be required? (True/False)
        description='Username for the new account',
        example='johndoe',
        min_length=3,
        max_length=50
    ),
    'password': fields.String(
        required=_____,  # TODO: Should password be required? (True/False)
        description='Password for the account',
        example='securepass123',
        min_length=6
    )
})

# TODO: Define model for login credentials
login_model = api.model('Login', {
    'username': fields.String(required=True, description='Username', example='johndoe'),
    'password': fields.String(required=True, description='Password', example='securepass123')
})

# TODO: Define model for JWT token response
token_model = api.model('Token', {
    'access_token': fields.String(description='JWT access token',
                                  example='eyJ0eXAiOiJKV1QiLCJhbGciOiJIUzI1NiJ9...')
})

# TODO: Define model for user response (without password)
user_response_model = api.model('UserResponse', {
    'message': fields.String(description='Response message'),
    'username': fields.String(description='Username', example='johndoe')
})

# TODO: Define model for user list item
user_model = api.model('User', {
    'username': fields.String(description='Username', example='johndoe')
})

# TODO: Define model for user update
user_update_model = api.model('UserUpdate', {
    'password': fields.String(
        required=True,
        description='New password',
        example='newsecurepass456',
        min_length=6
    )
})

# TODO: Define model for error responses
error_model = api.model('Error', {
    'error': fields.String(description='Error message', example='User not found'),
    'message': fields.String(description='Detailed error description')
})

# ============================================================================
# AUTHENTICATION ENDPOINTS
# ============================================================================

@auth_ns.route('/register')
class UserRegister(Resource):
    """User registration endpoint"""

    # TODO: Document the expected request body
    # Hint: Use @auth_ns.expect() decorator with the model
    @auth_ns.expect(_____)  # TODO: Add the registration model here
    @auth_ns.response(201, 'User created successfully', user_response_model)
    @auth_ns.response(400, 'Validation error or missing data', error_model)
    @auth_ns.response(409, 'User already exists', error_model)
    def post(self):
        """
        Register a new user

        Creates a new user account with a hashed password.
        Returns success message and username if registration is successful.
        """
        # TODO: Get the JSON payload from the request
        # Hint: Use api.payload to get validated data from Flask-RESTX
        data = _____  # TODO: Get the request data

        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return {'error': 'Username and password are required'}, 400

        if username in users:
            return {'error': 'User already exists'}, 409

        # Hash the password before storing
        users[username] = {
            'password': generate_password_hash(password)
        }

        return {
            'message': 'User registered successfully',
            'username': username
        }, 201


@auth_ns.route('/login')
class UserLogin(Resource):
    """User login endpoint"""

    # TODO: Document expected request and response
    @auth_ns.expect(login_model)
    @auth_ns.response(200, 'Login successful', token_model)
    @auth_ns.response(401, 'Invalid credentials', error_model)
    @auth_ns.response(400, 'Missing username or password', error_model)
    def post(self):
        """
        Login and receive JWT token

        Authenticates user credentials and returns a JWT access token
        that can be used to access protected endpoints.
        """
        data = api.payload
        username = data.get('username')
        password = data.get('password')

        if not username or not password:
            return {'error': 'Username and password are required'}, 400

        user = users.get(username)

        # TODO: Verify password and create JWT token
        # Hint: Use check_password_hash() and create_access_token()
        if user and check_password_hash(user['password'], password):
            access_token = _____(identity=username)  # TODO: Create JWT token
            return {'access_token': access_token}, 200

        return {'error': 'Invalid username or password'}, 401

# ============================================================================
# USER MANAGEMENT ENDPOINTS
# ============================================================================

@users_ns.route('/')
class UserList(Resource):
    """User list endpoint"""

    # TODO: Document that this endpoint requires authentication
    # Hint: Use @users_ns.doc(security='Bearer') decorator
    @users_ns.doc(security='_____')  # TODO: Add security requirement
    @users_ns.marshal_list_with(user_model)  # Documents that response is a list
    @users_ns.response(200, 'Success', [user_model])
    @users_ns.response(401, 'Authentication required', error_model)
    @jwt_required()
    def get(self):
        """
        Get list of all users (requires authentication)

        Returns a list of all registered usernames.
        Requires valid JWT token in Authorization header.
        """
        current_user = get_jwt_identity()
        user_list = [{'username': username} for username in users.keys()]
        return user_list, 200


@users_ns.route('/<string:username>')
@users_ns.param('username', 'The username identifier')
class UserDetail(Resource):
    """User detail endpoint"""

    # TODO: Document PUT endpoint for updating user
    @users_ns.doc(security='Bearer')
    @users_ns.expect(_____)  # TODO: Add the update model
    @users_ns.response(200, 'User updated successfully', user_response_model)
    @users_ns.response(404, 'User not found', error_model)
    @users_ns.response(401, 'Authentication required', error_model)
    @jwt_required()
    def put(self, username):
        """
        Update user password (requires authentication)

        Updates the password for the specified user.
        Any authenticated user can update their own password.
        """
        if username not in users:
            return {'error': 'User not found'}, 404

        data = api.payload
        password = data.get('password')

        if not password:
            return {'error': 'Password is required'}, 400

        # TODO: Update user password with hashed version
        users[username]['password'] = _____(password)  # TODO: Hash the password

        return {
            'message': 'User updated successfully',
            'username': username
        }, 200

    # TODO: Document DELETE endpoint
    @users_ns.doc(security='_____')  # TODO: Add security requirement
    @users_ns.response(200, 'User deleted successfully', user_response_model)
    @users_ns.response(404, 'User not found', error_model)
    @users_ns.response(401, 'Authentication required', error_model)
    @jwt_required()
    def delete(self, username):
        """
        Delete a user (requires authentication)

        Permanently removes a user from the system.
        """
        if username not in users:
            return {'error': 'User not found'}, 404

        # TODO: Delete the user
        del users[username]

        return {
            'message': 'User deleted successfully',
            'username': username
        }, 200


@users_ns.route('/profile')
class UserProfile(Resource):
    """Current user profile endpoint"""

    @users_ns.doc(security='Bearer')
    @users_ns.response(200, 'Success', user_model)
    @users_ns.response(401, 'Authentication required', error_model)
    @jwt_required()
    def get(self):
        """
        Get current user profile (requires authentication)

        Returns the profile information for the currently authenticated user
        based on the JWT token.
        """
        # TODO: Get the current user from JWT token
        current_user = _____()  # TODO: Get user identity from JWT

        return {
            'username': current_user,
            'message': f'Profile information for {current_user}'
        }, 200

# ============================================================================
# ERROR HANDLERS
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 Not Found errors"""
    return {'error': 'Resource not found', 'message': str(error)}, 404

@app.errorhandler(405)
def method_not_allowed(error):
    """Handle 405 Method Not Allowed errors"""
    return {'error': 'Method not allowed', 'message': str(error)}, 405

@app.errorhandler(500)
def internal_error(error):
    """Handle 500 Internal Server Error"""
    app.logger.error(f'Internal server error: {str(error)}')
    return {'error': 'Internal server error', 'message': 'An unexpected error occurred'}, 500

# ============================================================================
# RUN APPLICATION
# ============================================================================

if __name__ == '__main__':
    print("\n" + "="*70)
    print("🚀 Flask-RESTX API with Swagger Documentation")
    print("="*70)
    print(f"📚 Swagger UI available at: http://127.0.0.1:5000/docs")
    print(f"📄 OpenAPI JSON spec at: http://127.0.0.1:5000/swagger.json")
    print("="*70 + "\n")

    # Run the application in debug mode
    # WARNING: Do not use debug=True in production!
    app.run(debug=True)
