# FastAPI Introduction Guide

## Table of Contents
1. [What is FastAPI?](#what-is-fastapi)
2. [Environment Setup](#environment-setup)
3. [Your First FastAPI Application](#your-first-fastapi-application)
4. [Basic Concepts](#basic-concepts)
5. [Working with JSON](#working-with-json)
6. [Additional Resources](#additional-resources)

## What is FastAPI?
FastAPI is a modern web framework written in Python for building APIs quickly with a minimum number of lines of code. It is popular because it uses standard Python type hints to read, validate and document your requests and responses for you.

### Main Features:
- Fast to write: type hints replace most of the manual parsing and checking
- Automatic data validation with Pydantic
- Interactive API documentation generated automatically (Swagger UI at `/docs`)
- Built on the ASGI standard (Starlette and uvicorn)
- Development server with auto-reload (`fastapi dev`)
- Extensive documentation
- Large community

## Environment Setup

### Step 1: Python Installation
1. Download Python from [python.org](https://python.org)
2. Make sure to check the "Add Python to PATH" option during installation
3. Verify the installation by opening a terminal and typing:
   ```bash
   python --version
   ```

### Step 2: Create a Virtual Environment
```bash
# Windows
python -m venv venv

# Linux/Mac
python3 -m venv venv

# Activate the virtual environment
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Step 3: Install FastAPI
```bash
pip install "fastapi[standard]"
```
The `standard` extra also installs the `fastapi` command and the uvicorn server.

## Your First FastAPI Application

### Step 1: Create the app.py file
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def hello_world():
    return {"message": "Hello, students!"}
```

### Step 2: Run the application
```bash
fastapi dev app.py
```
Visit http://127.0.0.1:8000 in your browser.

`fastapi dev` is the development server: it reloads the app every time you save the file. Never use it on a public server; its production equivalent is `fastapi run`.

FastAPI also generates interactive documentation for your app automatically. Open http://127.0.0.1:8000/docs to see every endpoint and try it from the browser.

## Basic Concepts

### 1. Path Operations
A path operation is a function that answers one combination of HTTP method and path. The decorator says which: `@app.get(...)` for GET, `@app.post(...)` for POST, and so on.

```python
@app.get("/about")
def about():
    return "Welcome to my first FastAPI application!"

@app.get("/user/{username}")
def show_user(username: str):
    return f"Hello, {username}!"
```

### 2. HTTP Methods
There is one decorator per method, named after it:

```python
@app.get("/login")
def login_form():
    return "Please log in"

@app.post("/login")
def login():
    return "Processing login..."
```

### 3. Path Parameters
A name in braces in the path becomes a function parameter with the same name. Its type hint tells FastAPI how to convert (and check) the value:

```python
@app.get("/user/{username}")
def show_user(username: str):
    return f"User profile for: {username}"

@app.get("/post/{post_id}")
def show_post(post_id: int):
    return f"Displaying post {post_id}"
```

If someone requests `/post/abc`, FastAPI answers with an error (422) before your function runs, because `abc` is not an `int`.

## Working with JSON

Since you'll be building APIs in this course, it's important to learn how FastAPI handles JSON data. JSON is the standard format for sending and receiving data in web APIs.

### 1. Returning JSON Responses

Just return a Python dictionary or list; FastAPI converts it to JSON for you:

```python
@app.get("/api/hello")
def hello_api():
    return {"message": "Hello, World!"}

@app.get("/api/user/{user_id}")
def get_user(user_id: int):
    return {"id": user_id, "name": "John Doe", "email": "john@example.com"}

@app.get("/api/users")
def get_users():
    return [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]
```

A plain string is also sent as JSON (with quotes). When you want plain text, as in `GET /` and `GET /about`, say so in the decorator:

```python
from fastapi.responses import PlainTextResponse

@app.get("/", response_class=PlainTextResponse)
def index():
    return "Welcome to my first FastAPI application!"
```

### 2. Reading JSON from Requests

To receive a JSON body, describe its shape with a Pydantic model: a class that inherits from `BaseModel` and lists the fields with their types. A field with a value, like `name: str = "Guest"`, is optional and uses that value as default.

```python
from pydantic import BaseModel

class GreetRequest(BaseModel):
    name: str = "Guest"

@app.post("/api/greet")
def greet(body: GreetRequest):
    # FastAPI already read the JSON and checked it against GreetRequest
    return {"greeting": f"Hello, {body.name}!"}
```

Declaring `body: GreetRequest` is all FastAPI needs: it reads the JSON, validates it (a `name` that is not text is answered with a 422 error automatically) and hands you a ready-made object. Because the model also describes the body, `/docs` shows it and lets you try it.

**Testing with Postman:**
- Set method to POST
- In Body tab, select "raw" and "JSON"
- Enter: `{"name": "Alice"}`
- Send the request

### 3. Simple In-Memory Data Storage

For these exercises, we'll use Python dictionaries to store data (no database needed):

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    name: str
    email: str

# Store users in memory
users = {}
next_id = 1

@app.post("/api/users")
def create_user(data: UserCreate):
    global next_id
    user = {"id": next_id, "name": data.name, "email": data.email}
    users[next_id] = user
    next_id += 1
    return user

@app.get("/api/users")
def list_users():
    return list(users.values())

@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    if user_id in users:
        return users[user_id]
    raise HTTPException(status_code=404, detail="User not found")
```

### 4. Query Parameters

A function parameter that is not in the path is read from the query string:

```python
@app.get("/api/search")
def search(q: str = ""):
    # Access query parameter: /api/search?q=fastapi
    return {"search_query": q}
```

**Note:** You'll learn more about HTTP status codes, validation, and error handling in the next exercises.

## Additional Resources

### Official Documentation
- [FastAPI Documentation](https://fastapi.tiangolo.com/)
- [Official FastAPI Tutorial](https://fastapi.tiangolo.com/tutorial/)

### Useful Tools
- Postman (for testing APIs)
- SQLite Browser (for databases)
- Git (for version control)

### Best Practices
1. Always use virtual environments
2. Keep code organized in modules
3. Implement error handling
4. Write tests for your code
5. Document your code properly

## Tips for Students
- Practice writing code regularly
- Don't be afraid to experiment
- Join FastAPI/Python communities
- Review open source projects
- Keep a learning journal

Happy learning!

## Exercise Task (what to deliver)

**Goal:** Create your first FastAPI application with simple routes and test it using Postman.

### 1) Build the Application
Create an `app.py` file with the following endpoints:

**Required endpoints:**
- `GET /` - Return a welcome message (text or JSON)
- `GET /about` - Return information about the app
- `GET /api/hello` - Return a JSON message: `{"message": "Hello, World!"}`
- `GET /api/user/{username}` - Return JSON with the username
- `POST /api/greet` - Accept JSON with a "name" field, return a greeting

**Example for the POST endpoint:**
```python
# Request body: {"name": "Alice"}
# Response: {"greeting": "Hello, Alice!"}
```

### 2) Run the Application
```bash
# Create and activate virtual environment
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Install dependencies
pip install -r requirements.txt

# Run the app (fill the blanks from top to bottom; the app starts once the decorators are complete)
fastapi dev app.py
```

Visit http://127.0.0.1:8000 in your browser to see your app running, and http://127.0.0.1:8000/docs for the automatic documentation.

### 3) Test with Postman
- Create a Postman collection named "FastAPI Intro" (keep it local, do not commit)
- Add requests for all 5 endpoints
- For each request, include:
  - A clear name (e.g., "Get Welcome Message")
  - A brief description of what the endpoint does
  - The correct HTTP method (GET or POST)
  - Example response
- For the POST request, remember to:
  - Set Body to "raw" and "JSON"
  - Include a sample JSON body: `{"name": "Your Name"}`

### 4) Deliverables
Submit the following:
1. Your `app.py` file
2. Screenshot showing the app running in your terminal
3. Screenshot of your Postman collection showing all 5 requests
4. Exported Postman collection (JSON file) shared via instructed channel

### 5) Tips
- Use the examples from this guide as reference
- Test each endpoint in your browser (for GET requests) before testing in Postman
- Make sure your app is running before testing in Postman
- Don't worry about error handling or validation yet - you'll learn that in the next exercises