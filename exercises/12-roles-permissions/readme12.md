# Exercise 12: Implementation of Roles and Permissions in an API with FastAPI

## Quick Start

```bash
cd exercises/12-roles-permissions
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
fastapi dev app.py
```

Fill the blanks (`_____`) from top to bottom. No blank stops the app from starting: the role you write inside `require_role(...)` is just text until a request arrives, so the app starts right away and the blanks (the `403` status code, the `"student"` role of new users, the `pop` method and the two roles of `require_role("...")`) only matter when a request reaches them. The API runs at `http://127.0.0.1:8000`.

## Objective
- **Role and Permission Assignment:** Implement a role-based access control system for the API.
- **Route Protection:** Ensure that only users with appropriate permissions can access specific routes.
- **Authentication and Security:** Use JWT (JSON Web Tokens) and a dependency that checks the role to manage users, roles, and permissions.

---

## Prerequisites

1. **Install Dependencies:**
   Make sure you have the following libraries installed:
   - FastAPI (`fastapi[standard]`)
   - PyJWT
   - bcrypt

   You can install them with:
   ```bash
   pip install -r requirements.txt
   ```

2. **Clone the Project:**
   Clone the repository or copy the provided `app.py` file.

3. **Run the Script:**
   Start the application with:
   ```bash
   fastapi dev app.py
   ```

---

## Features

### **User Registration**
New users are **always** registered as `student`. The role is never read from the request body: accepting it would let anyone register as admin (a *mass assignment* vulnerability). Only an admin can change a user's role, with `PUT /users/{username}`.

### **Admin Account**
At start-up the app creates one `admin` user. Its password is taken from the `ADMIN_PASSWORD` environment variable; if it is not set, a random password is generated and printed in the console (the terminal where `fastapi dev` runs):

```
Admin user created -> username: admin  password: Xy3...
```

The line is printed once, even though `fastapi dev` loads your file twice (once to find the app, once in the reload worker): the first load keeps the generated password in the `ADMIN_PASSWORD` environment variable and the second load reuses it. To choose your own password, set `ADMIN_PASSWORD` before starting the server.

### **Login**
Authenticates users and provides them with a JWT token that will be required to access protected routes. The token includes the user's role as a claim, but that claim is only informative. On every request the user is looked up again from the token's `sub` claim, so permissions never depend on what the token says: the role is read from the server store on every request.

### **Available Roles**
1. **Admin:**
   - Access to all routes, including those that manage users.
   - Can perform actions such as updating or deleting other users.

2. **Student:**
   - Restricted access to specific routes designed for students.

### **Route Protection**
Access to routes is restricted based on the user's role. This is managed with a dependency, `require_role("admin")`, that you add to each protected path operation. On every request it reads the user's **current** role from the server's user store (not from the token) and answers `403` with `Permission denied.` if it does not match. A request with a missing or invalid token never gets that far: it answers `401`.

---

## API Structure

### **Main Endpoints**

1. **User Registration**
   - **Method:** `POST`
   - **Route:** `/register`
   - **Description:** Registers a new user (always with the `student` role).

2. **Login**
   - **Method:** `POST`
   - **Route:** `/login`
   - **Description:** Authenticates a user and returns a JWT token.

3. **User Profile**
   - **Method:** `GET`
   - **Route:** `/profile`
   - **Description:** Returns information about the authenticated user.

4. **List Users**
   - **Method:** `GET`
   - **Route:** `/users`
   - **Description:** Returns a paginated list of registered users (`page` >= 1, `per_page` 1-100; anything else answers `422`, a page past the end `404`).
   - **Requires:** Administrator role.

5. **Update User**
   - **Method:** `PUT`
   - **Route:** `/users/{username}`
   - **Description:** Updates user information (password or role). The role must be `admin` or `student`; anything else answers `422`. An admin cannot change their own role (`409 Conflict`), so the API never runs out of admins.
   - **Requires:** Administrator role.

6. **Delete User**
   - **Method:** `DELETE`
   - **Route:** `/users/{username}`
   - **Description:** Deletes a user. An admin cannot delete their own account (`409 Conflict`).
   - **Requires:** Administrator role.

7. **Admin Dashboard**
   - **Method:** `GET`
   - **Route:** `/admin/dashboard`
   - **Description:** Returns information exclusive to administrators.

8. **Student Data**
   - **Method:** `GET`
   - **Route:** `/student/data`
   - **Description:** Returns specific information about the authenticated student.

---

## Testing

### **Basic Tests**
- Register a user and verify they can log in.
- Try to access protected routes without a JWT token and verify that access is denied.
- Generate a valid token and try to access specific routes based on the user's role.

### **Role Tests**
1. Log in as `admin` (password printed at start-up) and as a student you registered.
2. Try to access restricted routes with each token and verify that restrictions are applied correctly (`/admin/dashboard` must return `403` for a student).
3. Try to register a user sending `"role": "admin"` in the body: it must still be created as `student`.
4. As admin, promote that user with `PUT /users/{username}` and `{"role": "admin"}` and check the new access with the token they already have: no need to log in again, because the role is read from the server on every request (the `role` claim inside the token is only informative).

Ready-made commands: `example/commands_cmd.txt` and `example/commands_powershell.txt`.

### **Common Errors**
- **Invalid Token:** Make sure to include the JWT token in the `Authorization` header with the format `Bearer <token>`.
- **Access Denied:** Verify that the user has the correct role to access the route.
- **"It already works" before filling the blanks:** with the blanks unfilled every new user gets the role `"_____"` and both `require_role("_____")` endpoints let them in (the role matches the blank), so `/admin/dashboard` and `/student/data` answer `200` for every new user. That is expected; fill the blanks and test again.

---

## Additional Notes
- Use tools like Postman or curl to test the API routes.
- Make sure the `app.py` file is configured correctly before running the tests.
- You can adjust roles and permissions according to your application's needs.

---

Good luck implementing roles and permissions in your API with FastAPI!
