# Exercise 4: API Key Authentication

## Objective
Implement authentication using API Keys in a REST API developed with Python and Flask.

## Description
In this exercise, you will expand the API developed in Exercise 2 to include authentication through API Keys. Each registered user will receive a unique API Key that must be sent in requests to access protected routes. This will allow an additional way to authenticate requests, in addition to basic authentication.

## Instructions

Update the 'app.py' File:

Import the uuid library.
Modify user registration to generate and store an API Key.
Create a new decorator or middleware to verify the API Key in requests.

## Requirements
1. **API Key Generation:**
   - When registering a new user, generate a unique API Key (you can use the `uuid` library).
   - Store the API Key associated with the user in the "database".

2. **API Key Submission:**
   - Requests to protected routes must include the API Key in the headers (`x-api-key`).

3. **API Key Validation:**
   - Implement middleware that verifies the validity of the API Key in each protected request.
   - If the API Key is valid, allow access; otherwise, respond with an authentication error.

4. **Route Updates:**
   - Adjust protected routes to accept authentication through both Basic Auth and API Keys.

5. **Testing:**
   - Use tools like Postman or `curl` to test access to protected routes using valid and invalid API Keys.


   - Register a user and get their API key:

   ```bash
   curl -X POST -H "Content-Type: application/json" -d '{"username":"example", "password":"secret"}' http://127.0.0.1:5000/users
   ```

   - Access 'users' with API Key:

   ```bash
   curl -H "x-api-key: <your_api_key_here>" http://127.0.0.1:5000/users
   ```





## Suggested Steps

1. **Install Additional Dependencies:**
   ```bash
   pip install uuid
   ```

2. **Generate API Keys:**
   - Import the `uuid` library.
   - In the user registration function, generate a unique API Key using `uuid.uuid4()`.

3. **Store API Keys:**
   - Modify the user data structure to include the API Key.
   - Example:
     ```python
     users = {
         'username': {
             'password': 'hashed_password',
             'api_key': 'generated_api_key'
         }
     }
     ```

4. **Create Middleware for API Keys:**
   - Implement a decorator that verifies the API Key from the request headers.
   - Validate if the API Key exists in the "database".

5. **Update Protected Routes:**
   - Apply the new decorator to routes that should be protected with API Keys.
   - Ensure routes accept both Basic Auth and API Keys.

6. **Test the API:**
   - Register a new user and note the returned API Key.
   - Make requests to protected routes using the API Key.
   - Verify that requests with invalid or missing API Keys are rejected.

## Additional Notes

- **Security:** Ensure API Keys are stored securely and transmitted over HTTPS in production environments.
- **UUID Library:** The `uuid` library is part of the Python standard library, so it doesn't require separate installation.
- **Error Handling:** Implement appropriate error responses for authentication failures.
