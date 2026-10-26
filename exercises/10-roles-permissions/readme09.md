# Exercise 10: Implementation of Roles and Permissions in a Flask API

## Quick Start

```bash
cd exercises/10-roles-permissions
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Objective
- **Role and Permission Assignment:** Implement a role-based access control system for the API.
- **Route Protection:** Ensure that only users with appropriate permissions can access specific routes.
- **Authentication and Security:** Use JWT (JSON Web Tokens) and Flask-Principal to manage users, roles, and permissions.

---

## Prerequisites

1. **Install Dependencies:**
   Make sure you have the following libraries installed:
   - Flask
   - Flask-JWT-Extended
   - Flask-Principal
   - Werkzeug

   You can install them with:
   ```bash
   pip install -r requirements.txt
   ```

2. **Clone the Project:**
   Clone the repository or copy the provided `app.py` file.

3. **Run the Script:**
   Start the application with:
   ```bash
   python app.py
   ```

---

## Features

### **User Registration**
New users are **always** registered as `student`. The role is never read from the request body: accepting it would let anyone register as admin (a *mass assignment* vulnerability). Only an admin can change a user's role, with `PUT /users/<username>`.

### **Admin Account**
At start-up the app creates one `admin` user. Its password is taken from the `ADMIN_PASSWORD` environment variable; if it is not set, a random password is generated and printed in the console:

```
Admin user created -> username: admin  password: Xy3...
```

### **Login**
Authenticates users and provides them with a JWT token that will be required to access protected routes. The token includes the user's role as a claim. On every request the identity is rebuilt from the token (`Principal(app, use_sessions=False)`), so permissions never depend on a session cookie.

### **Available Roles**
1. **Admin:**
   - Access to all routes, including those that manage users.
   - Can perform actions such as updating or deleting other users.

2. **Student:**
   - Restricted access to specific routes designed for students.

### **Route Protection**
Access to routes is restricted based on the user's role. This is managed through Flask-Principal decorators that verify assigned permissions.

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
   - **Description:** Returns a paginated list of registered users.

5. **Update User**
   - **Method:** `PUT`
   - **Route:** `/users/<username>`
   - **Description:** Updates user information (password or role).
   - **Requires:** Administrator role.

6. **Delete User**
   - **Method:** `DELETE`
   - **Route:** `/users/<username>`
   - **Description:** Deletes a user.
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
4. As admin, promote that user with `PUT /users/<username>` and `{"role": "admin"}` and check the new access with the token they already have: no need to log in again, because the role is read from the server on every request (the `role` claim inside the token is only informative).

Ready-made commands: `example/commands_cmd.txt` and `example/commands_powershell.txt`.

### **Common Errors**
- **Invalid Token:** Make sure to include the JWT token in the `Authorization` header with the format `Bearer <token>`.
- **Access Denied:** Verify that the user has the correct role to access the route.

---

## Additional Notes
- Use tools like Postman or curl to test the API routes.
- Make sure the `app.py` file is configured correctly before running the tests.
- You can adjust roles and permissions according to your application's needs.

---

Good luck implementing roles and permissions in your Flask API!
