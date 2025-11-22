# Exercise 5: Authentication with JSON Web Tokens (JWT)

## Objective

Implement authentication using JSON Web Tokens (JWT) in a REST API developed with Python and Flask.

## Description

In this exercise, you will extend the API to include JWT-based authentication. You will implement endpoints that allow users to log in and obtain a JWT token, which they must include in requests to protected routes to access secure resources.

## Requirements

1. **Installing Additional Dependencies:**

   - Install the necessary libraries to handle JWT:
     ```bash
     pip install Flask-JWT-Extended
     ```

2. **API Structure:**

   - Create a route to register users (`POST /students`).
   - Create a route for users to log in (`POST /login`) and obtain a JWT token.
   - Create a protected route (`GET /profile`) that can only be accessed with a valid JWT token.
   - Include a route to get the list of students (`GET /students`), protected with authentication.

3. **JWT Implementation:**

   - Configure `Flask-JWT-Extended` in your application.
   - Generate a JWT token when successfully authenticating the user in the login route.
   - Protect sensitive routes using decorators that verify the presence and validity of the JWT token.

4. **Testing:**

   - Use tools like Postman or `curl` to test the authentication flow and access to protected routes with and without a valid token.

## Detailed Steps

1. **Configure the Application:**

   - Define a secret key to sign JWT tokens:
     ```python
     app.config['JWT_SECRET_KEY'] = 'your_jwt_secret_key'
     ```

2. **User Registration:**

   - Implement the `POST /students` route to register users, hashing passwords before storing them.

3. **Login:**

   - Implement the `POST /login` route to authenticate registered users.
   - Generate a JWT token using the `create_access_token` function:
     ```python
     access_token = create_access_token(identity=username)
     ```

4. **Route Protection:**

   - Use the `@jwt_required()` decorator to protect the `GET /profile` route.
   - Get the user's identity from the JWT token using `get_jwt_identity`:
     ```python
     current_user = get_jwt_identity()
     ```

5. **Testing:**

   - Register a user via a `POST /students` request.
   - Log in via `POST /login` and obtain the JWT token.
   - Review the token at [jwt.io](https://jwt.io/) by copying and pasting the generated token.
   - Use the JWT token as an authorization header in `GET /profile` and verify access.

## Example Requests with `curl`

1. **User Registration:**

   ```bash
   curl -X POST -H "Content-Type: application/json" \
   -d '{"username": "user1", "password": "1234"}' \
   http://127.0.0.1:5000/students
   ```

2. **Login:**

   ```bash
   curl -X POST -u user1:1234 \
   http://127.0.0.1:5000/login
   ```

3. **Accessing Protected Routes:**

   ```bash
   curl -X GET -H "Authorization: Bearer <your_jwt_token>" \
   http://127.0.0.1:5000/profile
   ```

## Points to Consider

- Change the secret key used in `JWT_SECRET_KEY` in production.
- Properly handle errors for unauthenticated requests or invalid tokens.
- Configure expiration times for JWT tokens if necessary.

Good luck! If you have questions, consult the official [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/en/stable/) documentation.
