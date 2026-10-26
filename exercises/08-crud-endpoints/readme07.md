# Exercise 8: Creating CRUD Endpoints

## Objective
Implement CRUD (Create, Read, Update, Delete) endpoints in a REST API using Python and Flask.

## Description
In this exercise, you will expand the API developed in previous exercises to include full CRUD operations on "users" resources. You will need to create routes that allow creating, reading, updating, and deleting users. Complete the blank spaces in the provided code to implement these functionalities.

## Quick Start

```bash
cd exercises/08-crud-endpoints
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

**Note:** This exercise uses "users" as the resource name, building on the authentication patterns from previous exercises.

## Requirements
1. **Installation of Additional Dependencies:**
   - Make sure you have the `Flask` library and the extensions used in previous exercises installed.

2. **API Structure:**
   - **Register User (`POST /users`):** Public endpoint to register a new user
   - **Login (`POST /login`):** Authenticate and receive JWT token
   - **Get Users (`GET /users`):** Protected - Returns list of all users
   - **Create User (Admin) (`POST /users/admin`):** Protected - Admin endpoint to create users
   - **Update User (`PUT /users/<username>`):** Protected - Updates a specific user's password
   - **Delete User (`DELETE /users/<username>`):** Protected - Deletes a specific user

3. **CRUD Implementation:**
   - Use the appropriate HTTP methods for each operation.
   - Ensure that routes are protected using JWT authentication implemented in previous exercises.
   - Validate inputs and handle errors appropriately.

4. **Testing:**
   - Use tools like Postman or `curl` to test each of the CRUD operations.
   - Ensure that operations work correctly and that errors are handled appropriately.

## Suggested Steps

1. **Read `app.py`:**
   - Registration (`POST /users`), login (`POST /login`), `GET /users` and `POST /users/admin` are already implemented.
   - Notice how each route combines a URL with an HTTP method: the same URL `/users/<username>` can do different things depending on the method.

2. **Fill in the blanks (`_____`) in `exercises/08-crud-endpoints/app.py`:**

   ```python
   @app.route('/users/<username>', methods=['_____'])  # TODO: Set the correct HTTP method
   # Hint: Use 'PUT' for updates
   @jwt_required()
   def update_user(username):
       ...

   @app.route('/users/<username>', methods=['_____'])  # TODO: Set the correct HTTP method
   # Hint: Use 'DELETE' to remove a resource
   @jwt_required()
   def delete_user(username):
       ...
   ```

3. **Run the Application:**

   ```bash
   python app.py
   ```

4. **Test the API:**

   Use Postman or `curl` to test the CRUD endpoints:

   - **Register a user:**
     ```bash
     curl -X POST http://127.0.0.1:5000/users -H "Content-Type: application/json" -d '{"username": "user1", "password": "password123"}'
     ```

   - **Login (Basic Auth, returns a JWT):**
     ```bash
     curl -X POST http://127.0.0.1:5000/login -u user1:password123
     ```

   - **Get users (use the token from login):**
     ```bash
     curl -X GET http://127.0.0.1:5000/users -H "Authorization: Bearer YOUR_TOKEN"
     ```

   - **Update a user:**
     ```bash
     curl -X PUT http://127.0.0.1:5000/users/user1 -H "Content-Type: application/json" -H "Authorization: Bearer YOUR_TOKEN" -d '{"password": "newpassword456"}'
     ```

   - **Delete a user:**
     ```bash
     curl -X DELETE http://127.0.0.1:5000/users/user1 -H "Authorization: Bearer YOUR_TOKEN"
     ```

   - **Register the same user twice (expected: 409 Conflict):**
     ```bash
     curl -i -X POST http://127.0.0.1:5000/users -H "Content-Type: application/json" -d '{"username": "user1", "password": "password123"}'
     ```

   > **Windows:** ready-to-run versions of these commands are in `example/commands_cmd.txt` and `example/commands_powershell.txt` (in PowerShell use `curl.exe`, not `curl`).

## Expected Results

- The API should allow you to create, read, update, and delete users.
- All protected routes should require a valid JWT token.
- Error responses should be returned for invalid inputs or when resources are not found.

## Understanding HTTP Status Codes

This exercise uses several HTTP status codes. Understanding when to use each is important:

- **200 OK**: Request succeeded (GET, PUT requests)
- **201 Created**: New resource created successfully (POST requests)
- **400 Bad Request**: Invalid input data (missing fields, bad format)
- **401 Unauthorized**: Authentication required or invalid token
- **404 Not Found**: Resource doesn't exist
- **409 Conflict**: Resource already exists (duplicate user)
- **500 Internal Server Error**: Server-side error

### HTTP Methods and Their Purpose

- **POST**: Create a new resource
- **GET**: Retrieve resource(s)
- **PUT**: Update an entire resource (replace all fields)
- **DELETE**: Remove a resource

## Additional Resources

- [Flask Documentation](https://flask.palletsprojects.com/)
- [Flask-JWT-Extended Documentation](https://flask-jwt-extended.readthedocs.io/)
- [REST API Best Practices](https://restfulapi.net/)
- [HTTP Status Codes](https://developer.mozilla.org/en-US/docs/Web/HTTP/Status)

## Notes

- This exercise uses in-memory storage, so all data will be lost when the application restarts.
- In a production environment, you would use a proper database and implement additional security measures.
- The code includes blanks (`_____`) for you to complete - focus on understanding the HTTP methods for each route.
