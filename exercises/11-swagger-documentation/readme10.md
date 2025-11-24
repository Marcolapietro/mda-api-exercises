# Exercise 11: Automatic API Documentation with Swagger

## Introduction

In this exercise, you'll learn how to automatically generate professional, interactive API documentation using **Flask-RESTX** and **Swagger UI**. Instead of manually writing documentation, Flask-RESTX automatically creates a beautiful web interface where users can explore and test your API endpoints directly in their browser.

## Why API Documentation Matters

**Good API documentation is essential because:**
- Developers can understand how to use your API without reading the code
- Teams can collaborate more effectively
- Testing becomes easier with interactive documentation
- It demonstrates professionalism and improves API adoption
- Reduces support requests and onboarding time

**Industry Standard:** Companies like Stripe, GitHub, Twitter, and Google all provide Swagger/OpenAPI documentation for their APIs.

## Learning Objectives

By the end of this exercise, you will be able to:

1. Install and configure Flask-RESTX for automatic documentation
2. Convert standard Flask routes to Flask-RESTX Resources
3. Define API models for request and response validation
4. Document authentication requirements (JWT Bearer tokens)
5. Add descriptions, examples, and response codes
6. Organize endpoints using namespaces
7. Generate interactive Swagger UI accessible at `/docs`

## Prerequisites

Before starting this exercise, you should have completed:
- **Exercise 06**: JWT Authentication (understanding JWT tokens)
- **Exercise 08**: CRUD Operations (understanding REST endpoints)
- **Exercise 10**: Roles & Permissions (optional, but helpful)

## What is Flask-RESTX?

**Flask-RESTX** is a Flask extension that:
- Automatically generates Swagger/OpenAPI documentation
- Provides request/response validation
- Organizes APIs using namespaces
- Creates interactive Swagger UI
- Follows REST best practices

**What is Swagger UI?**
An interactive web interface that:
- Lists all your API endpoints
- Shows request/response formats
- Allows testing APIs directly in the browser
- Displays authentication requirements
- Provides examples and descriptions

## Installation

You'll need to install Flask-RESTX:

```bash
pip install Flask Flask-RESTX Flask-JWT-Extended Werkzeug
```

## Quick Start

```bash
cd exercises/11-swagger-documentation
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Core Concepts

### 1. Api Object
The main object that creates the Swagger documentation:

```python
from flask import Flask
from flask_restx import Api

app = Flask(__name__)
api = Api(app,
    version='1.0',
    title='My API',
    description='API with automatic documentation',
    doc='/docs'  # Swagger UI will be at http://localhost:5000/docs
)
```

### 2. Namespaces
Organize related endpoints together:

```python
# Create a namespace for user-related endpoints
users_ns = api.namespace('users', description='User operations')
```

### 3. Models
Define the structure of request/response data:

```python
# Define what a User looks like in the API
user_model = api.model('User', {
    'username': fields.String(required=True, description='Username', example='johndoe'),
    'password': fields.String(required=True, description='Password', example='secret123')
})
```

### 4. Resources
Replace Flask routes with Resource classes:

**Before (standard Flask):**
```python
@app.route('/users', methods=['POST'])
def register_user():
    # Implementation
    pass
```

**After (Flask-RESTX):**
```python
@users_ns.route('/')
class UserList(Resource):
    @users_ns.expect(user_model)  # Documents request body
    def post(self):
        '''Register a new user'''
        # Implementation
        pass
```

### 5. Documentation Decorators

- `@ns.doc()` - Add general documentation
- `@ns.expect()` - Document request body/parameters
- `@ns.marshal_with()` - Document response format
- `@ns.response()` - Document specific response codes

## Exercise Structure

This exercise has **5 parts** that progressively build a documented API:

1. **Part 1**: Basic setup and first endpoint
2. **Part 2**: Request/response models
3. **Part 3**: JWT authentication documentation
4. **Part 4**: CRUD operations with full documentation
5. **Part 5**: Advanced features (pagination, error handling)

## Getting Started

### Step 1: Review the Starter Code

Open `app.py` and review the structure. You'll see:
- Import statements with some blanks
- API initialization with blanks
- Model definitions to complete
- Endpoints to document

### Step 2: Fill in the Blanks

Look for `_____` markers and complete them using:
- **Hints** in comments above each blank
- **Examples** in this README
- **Flask-RESTX documentation** (links at the end)

### Step 3: Run the Application

```bash
python app.py
```

### Step 4: View the Documentation

Open your browser and visit:
```
http://127.0.0.1:5000/docs
```

You should see the **Swagger UI** with your API documentation!

### Step 5: Test in Swagger UI

The Swagger UI allows you to:
1. Click "Try it out" on any endpoint
2. Fill in parameters/body
3. Click "Execute"
4. See the response

## Part 1: Basic Setup (20 minutes)

### Task 1.1: Import Flask-RESTX
Complete the import statement in `app.py`:

```python
from flask import Flask, jsonify, request
from flask_restx import _____, Resource, fields  # Import Api
```

**Hint:** You need to import the main class that creates the API documentation.

### Task 1.2: Initialize the Api
Create the Api object with proper configuration:

```python
api = Api(app,
    version='_____',  # API version (e.g., '1.0')
    title='User Management API',
    description='API with JWT authentication and automatic documentation',
    doc='_____'  # Swagger UI path (e.g., '/docs')
)
```

### Task 1.3: Create a Namespace
Organize endpoints under a namespace:

```python
users_ns = api.namespace('_____', description='User operations')
```

**Hint:** The namespace name appears in the URL path.

### Task 1.4: Convert First Endpoint
Convert the register endpoint from a function to a Resource class.

**Expected Result:**
- Visit `http://localhost:5000/docs`
- See Swagger UI with your API
- See the "users" namespace
- See the POST /users endpoint

## Part 2: Request/Response Models (30 minutes)

### Task 2.1: Define User Registration Model
Complete the model for user registration:

```python
user_register_model = api.model('UserRegister', {
    'username': fields.String(required=_____, description='Username', example='johndoe'),
    'password': fields.String(required=_____, description='Password', example='pass123')
})
```

**Hint:** Should username and password be required for registration?

### Task 2.2: Define Response Models
Create models for API responses:

```python
user_response_model = api.model('UserResponse', {
    'message': fields.String(description='Response message'),
    'username': fields.String(description='Registered username')
})
```

### Task 2.3: Document Request Body
Use `@ns.expect()` to document what the endpoint expects:

```python
@users_ns.expect(user_register_model)
def post(self):
    '''Register a new user'''
```

### Task 2.4: Document Response
Use `@ns.marshal_with()` or `@ns.response()` to document responses:

```python
@users_ns.response(201, 'User created successfully', user_response_model)
@users_ns.response(400, 'Invalid input or user already exists')
def post(self):
    '''Register a new user'''
```

**Expected Result:**
- Swagger UI shows request body structure
- Shows example values
- Shows possible response codes (201, 400)

## Part 3: JWT Authentication Documentation (30 minutes)

### Task 3.1: Define Security Scheme
Add JWT Bearer token authentication to your API:

```python
authorizations = {
    'Bearer': {
        'type': 'apiKey',
        'in': 'header',
        'name': 'Authorization',
        'description': 'JWT Bearer token. Format: Bearer <token>'
    }
}

api = Api(app,
    # ... other config ...
    authorizations=authorizations,
    security='Bearer'
)
```

### Task 3.2: Document Login Endpoint
Create a login model and endpoint:

```python
login_model = api.model('Login', {
    'username': fields.String(required=True, description='Username'),
    'password': fields.String(required=True, description='Password')
})

token_model = api.model('Token', {
    'access_token': fields.String(description='JWT access token')
})
```

### Task 3.3: Mark Protected Endpoints
Indicate which endpoints require authentication:

```python
@users_ns.doc(security='Bearer')  # Requires JWT token
@jwt_required()
def get(self):
    '''Get list of all users (requires authentication)'''
```

**Expected Result:**
- Swagger UI shows a lock icon on protected endpoints
- Shows "Authorize" button at the top
- Can input JWT token and test protected endpoints

## Part 4: CRUD Operations Documentation (40 minutes)

### Task 4.1: Document GET Endpoint (Read)
```python
@users_ns.route('/')
class UserList(Resource):
    @users_ns.doc(security='Bearer')
    @users_ns.marshal_list_with(user_model)  # Response is a list
    def get(self):
        '''Get list of all users'''
```

### Task 4.2: Document POST Endpoint (Create)
Already done in Part 2, but ensure proper status codes:

```python
@users_ns.response(201, 'Success', user_response_model)
@users_ns.response(400, 'Validation error')
@users_ns.response(409, 'User already exists')
```

### Task 4.3: Document PUT Endpoint (Update)
```python
@users_ns.route('/<string:username>')
class UserDetail(Resource):
    @users_ns.doc(security='Bearer', params={'username': 'Username to update'})
    @users_ns.expect(user_update_model)
    def put(self, username):
        '''Update user information'''
```

### Task 4.4: Document DELETE Endpoint
```python
@users_ns.doc(security='Bearer', params={'username': 'Username to delete'})
@users_ns.response(200, 'User deleted')
@users_ns.response(404, 'User not found')
def delete(self, username):
    '''Delete a user'''
```

**Expected Result:**
- Swagger UI shows all CRUD operations
- Each operation has clear descriptions
- Path parameters are documented
- Response codes are listed

## Part 5: Advanced Features (30 minutes)

### Task 5.1: Document Query Parameters
Add pagination parameters:

```python
pagination_parser = api.parser()
pagination_parser.add_argument('page', type=int, default=1, help='Page number')
pagination_parser.add_argument('per_page', type=int, default=10, help='Items per page')

@users_ns.route('/')
class UserList(Resource):
    @users_ns.expect(pagination_parser)
    def get(self):
        '''Get paginated list of users'''
```

### Task 5.2: Add Multiple Namespaces
Organize your API into logical sections:

```python
auth_ns = api.namespace('auth', description='Authentication operations')
admin_ns = api.namespace('admin', description='Admin operations')
```

### Task 5.3: Document Error Responses
Create a standard error model:

```python
error_model = api.model('Error', {
    'error': fields.String(description='Error message'),
    'code': fields.Integer(description='Error code')
})

@users_ns.response(500, 'Internal server error', error_model)
```

**Expected Result:**
- Multiple organized namespaces in Swagger UI
- Query parameters are testable
- Consistent error response format

## Testing Your API

### Test Flow in Swagger UI:

1. **Register a User**
   - Expand POST /users
   - Click "Try it out"
   - Fill in username/password in the example
   - Click "Execute"
   - Should see 201 response

2. **Login to Get Token**
   - Expand POST /auth/login
   - Click "Try it out"
   - Use the credentials from step 1
   - Click "Execute"
   - Copy the `access_token` from response

3. **Authorize**
   - Click "Authorize" button at top
   - Enter: `Bearer <your_token>`
   - Click "Authorize"

4. **Test Protected Endpoint**
   - Expand GET /users
   - Click "Try it out"
   - Click "Execute"
   - Should see list of users (200 response)

### Manual Testing with curl:

```bash
# Register
curl -X POST http://localhost:5000/users \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "test123"}'

# Login
curl -X POST http://localhost:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "testuser", "password": "test123"}'

# Get users (with token)
curl -X GET http://localhost:5000/users \
  -H "Authorization: Bearer YOUR_TOKEN_HERE"
```

## Common Errors and Solutions

### Error 1: "Api is not defined"
**Problem:** Forgot to import Api from flask_restx
**Solution:** `from flask_restx import Api, Resource, fields`

### Error 2: Swagger UI shows empty
**Problem:** No namespaces or endpoints defined
**Solution:** Make sure you created at least one namespace and one Resource

### Error 3: Models not showing in documentation
**Problem:** Model not registered with api.model()
**Solution:** Ensure `user_model = api.model('Name', {...})`

### Error 4: "Authorization header missing"
**Problem:** Didn't click "Authorize" in Swagger UI
**Solution:** Click "Authorize" button and enter: `Bearer <token>`

### Error 5: Changes not reflecting
**Problem:** Browser cache
**Solution:** Hard refresh (Ctrl+F5) or open in incognito mode

## Best Practices

1. **Clear Descriptions**: Write helpful descriptions for all models and endpoints
2. **Examples**: Provide realistic example values in your models
3. **Status Codes**: Document all possible response codes (200, 201, 400, 401, 404, 500)
4. **Namespaces**: Group related endpoints together
5. **Consistent Naming**: Use consistent model names (e.g., UserCreate, UserUpdate, UserResponse)
6. **Security**: Clearly mark which endpoints require authentication
7. **Versioning**: Include API version in your configuration

## Comparison: Before vs After

### Before (Standard Flask):
```python
@app.route('/users', methods=['POST'])
def register_user():
    data = request.get_json()
    # ... implementation ...
    return jsonify({'message': 'User created'}), 201
```

**Problems:**
- No automatic documentation
- Developers must read the code
- No type validation
- Manual testing only

### After (Flask-RESTX):
```python
@users_ns.route('/')
class UserList(Resource):
    @users_ns.expect(user_model)
    @users_ns.response(201, 'Success', response_model)
    @users_ns.response(400, 'Validation error')
    def post(self):
        '''Register a new user'''
        data = api.payload
        # ... implementation ...
        return {'message': 'User created'}, 201
```

**Benefits:**
- Automatic Swagger UI documentation
- Request validation
- Type checking
- Interactive testing interface
- Professional appearance

## Additional Resources

### Official Documentation
- [Flask-RESTX Documentation](https://flask-restx.readthedocs.io/)
- [Swagger/OpenAPI Specification](https://swagger.io/specification/)
- [Flask-JWT-Extended Docs](https://flask-jwt-extended.readthedocs.io/)

### Tutorials
- [Flask-RESTX Quickstart](https://flask-restx.readthedocs.io/en/latest/quickstart.html)
- [API Documentation Best Practices](https://swagger.io/blog/api-documentation/best-practices-in-api-documentation/)

### Tools
- [Swagger Editor](https://editor.swagger.io/) - Online OpenAPI editor
- [Swagger UI Demo](https://petstore.swagger.io/) - See Swagger UI in action
- [Postman](https://www.postman.com/) - Can import OpenAPI specs

## Deliverables

When you complete this exercise, you should have:

1. A working Flask-RESTX API with Swagger documentation
2. At least 5 documented endpoints (register, login, get users, update, delete)
3. Request/response models defined
4. JWT authentication documented
5. Interactive Swagger UI at `/docs`
6. All blanks in `app.py` completed

## Evaluation Criteria

Your work will be evaluated on:

1. **Completeness** (30%): All blanks filled correctly
2. **Documentation Quality** (25%): Clear descriptions and examples
3. **Functionality** (25%): API works as expected
4. **Swagger UI** (20%): Professional, usable documentation interface

## Next Steps

After completing this exercise:

1. **Apply to Exercise 09**: Add Swagger documentation to your RBAC API
2. **Explore Advanced Features**:
   - Custom error handlers
   - File upload documentation
   - Nested resources
3. **Prepare for Exercise 11**: Use this documented API pattern in the ProManage team project

## Questions to Consider

1. How does automatic documentation improve API development workflow?
2. What's the difference between `@ns.expect()` and `@ns.marshal_with()`?
3. Why is it important to document all response codes?
4. How would you version your API (v1, v2) with Flask-RESTX?
5. What are the benefits of using namespaces?

Good luck building your professionally documented API!
