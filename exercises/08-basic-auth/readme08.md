# Exercise 8: Basic Authentication

## Objective
Implement basic authentication (Basic Auth) in a REST API using Python and FastAPI.

## Description
In this exercise, you will develop a simple REST API that manages "user" resources. You will implement basic authentication to protect certain routes, ensuring that only authenticated users can access them.

## Quick Start

```bash
cd exercises/08-basic-auth
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
fastapi dev app.py
```

Fill the blanks (`_____`) from top to bottom; the app starts once the `POST` decorator and the `Depends(...)` of `get_users` are complete. The header name blank is only used when a request fails authentication: run the wrong-password request with `curl -i` and look at the `WWW-Authenticate` header.

## Requirements
1. **Project Setup:**
   - Initialize a virtual environment.
   - Install the necessary dependencies (`fastapi[standard]`, `bcrypt`).

2. **API Structure (given, complete it):**
   - A route to register new users (`POST /users`): you write its HTTP method.
   - A route to get the list of users (`GET /users`), protected with basic authentication: you plug in the dependency that protects it.

3. **Basic Authentication (given, understand it):**
   - `fastapi.security.HTTPBasic` reads the credentials from the request.
   - Passwords are stored as `bcrypt` hashes, never in plain text.
   - `get_current_user` verifies the credentials and answers `401` with the right header (you write the header name).

4. **Testing:**
   - Use tools like Postman or `curl` to test the protected routes with and without valid credentials.

## Instructions:

Fill in the three `_____` spaces in `app.py`:

- the HTTP method of the route that registers a user (in lowercase, because it is the name of a method of `app`: `@app.post`);
- the dependency inside `Depends(...)` that protects `GET /users` (the function that checks the credentials);
- the name of the header that tells the client which kind of authentication the server expects (it goes in the 401 response).

The password hashing (`hash_password`, `verify_password`) is already written for you. Once corrected, run the app and perform tests from Postman.

## Suggested Steps

1. **Initialize the Project:**
   ```bash
   cd exercises/08-basic-auth
   python -m venv venv
   venv\Scripts\activate  # macOS / Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Read `app.py`:**
   - The FastAPI application, the in-memory `users` dictionary and the `bcrypt` helpers are already there.
   - So are the two routes: `POST /users` registers a user and `GET /users` lists them.

3. **Understand Basic Authentication, then fill the blanks:**
   - Find where `HTTPBasic` from `fastapi.security` is created and how `get_current_user` uses it to check the credentials.
   - See how `hash_password` hashes with `bcrypt.hashpw` and `verify_password` checks with `bcrypt.checkpw`.
   - Fill the three blanks (see Instructions above).

4. **Test the API:**
   - Register a user via `POST /users`.
   - Try accessing `GET /users` without credentials (should fail).
   - Access `GET /users` with valid credentials (should succeed).

## New in FastAPI: `Depends` and `fastapi.security`

A **dependency** is a function that FastAPI runs *before* your route and whose result it hands to your route. You declare it in the parameters with `Annotated[Type, Depends(function)]`; here `get_users` receives the authenticated username from `get_current_user`. If the dependency raises an error (for example `HTTPException(401)`), the route never runs, so protecting a route is just adding a `Depends(...)` parameter to it.

`fastapi.security` contains ready-made dependencies for common schemes. `HTTPBasic` reads the `Authorization: Basic ...` header and gives you `HTTPBasicCredentials` with the decoded `username` and `password`; if the header is missing it answers `401` with `WWW-Authenticate` by itself. `get_current_user` depends on it, compares the credentials with the stored hash and raises `401` when they do not match. Swagger UI (`/docs`) also shows an "Authorize" button for it.

## Password rules

Passwords are stored as `bcrypt` hashes, never in plain text. `hash_password` and `verify_password` wrap the two `bcrypt` calls, and the `UserCreate` model requires a password of **8 to 72 printable ASCII characters**; the username cannot contain spaces or `:`, because HTTP Basic sends `username:password` as ASCII. `bcrypt` cannot handle more than 72 bytes, so longer passwords are rejected with `422` by the model, like non-ASCII ones. A login with an unknown username still runs a `bcrypt` comparison against a dummy hash, so response time does not reveal which usernames exist.

## Example Requests with `curl`

1. **Register a User:**
   ```bash
   curl -X POST -H "Content-Type: application/json" \
   -d '{"username": "user1", "password": "password123"}' \
   http://127.0.0.1:8000/users
   ```

2. **Get List of Users (With Authentication):**
   ```bash
   curl -u user1:password123 http://127.0.0.1:8000/users
   ```

3. **Get List of Users (Without Authentication):**
   ```bash
   curl -i http://127.0.0.1:8000/users
   ```
   This should return `401 Unauthorized` with the header `WWW-Authenticate: Basic realm="Authentication Required"`: that is how the server tells the client which kind of authentication it expects.

4. **Get List of Users (Wrong Password):**
   ```bash
   curl -i -u user1:wrongpass http://127.0.0.1:8000/users
   ```
   Also `401` with `WWW-Authenticate`, but this time the body is `{"detail":"Invalid credentials"}`: the header comes from your `get_current_user` (the header name blank), not from `HTTPBasic`.

> **Windows:** in PowerShell 5.1 `curl` is an alias of `Invoke-WebRequest`, so use `curl.exe`, write the command on one line and escape the quotes inside the JSON (otherwise the server answers `422`): `curl.exe -X POST -H "Content-Type: application/json" -d '{\"username\":\"user1\",\"password\":\"password123\"}' http://127.0.0.1:8000/users`. In CMD single quotes don't work. Ready-made commands for both shells are in `example/commands_cmd.txt` and `example/commands_powershell.txt`.

## Points to Consider

- Passwords should never be stored in plain text.
- Registering the same username twice answers `409 Conflict`; a password shorter than 8 or longer than 72 characters answers `422`.
- Basic Auth sends credentials in Base64 encoding (not encryption), so use HTTPS in production.
- Test both successful and failed authentication scenarios.

Good luck!
