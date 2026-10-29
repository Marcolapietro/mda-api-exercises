"""
FastAPI Introduction Exercise - Complete Solution
This is the reference solution for the FastAPI introduction exercise.

Run it with:  fastapi dev example03.py
"""

from fastapi import FastAPI
from fastapi.responses import PlainTextResponse
from pydantic import BaseModel

app = FastAPI(title="FastAPI Intro")


class GreetRequest(BaseModel):
    """Body of POST /api/greet. 'name' is optional and defaults to 'Guest'."""
    name: str = "Guest"


@app.get("/", response_class=PlainTextResponse)
def index():
    """
    Root endpoint that returns a welcome message.
    """
    return "Welcome to my first FastAPI application!"


@app.get("/about", response_class=PlainTextResponse)
def about():
    """
    About endpoint that returns information about the app.
    """
    return "This is a FastAPI introduction exercise to learn basic routing and JSON handling."


@app.get("/api/hello")
def hello_api():
    """
    API endpoint that returns a simple JSON message.
    """
    return {"message": "Hello, World!"}


@app.get("/api/user/{username}")
def get_user(username: str):
    """
    API endpoint that accepts a username parameter and returns user information.

    Args:
        username (str): The username from the URL path

    Returns:
        JSON response with username and welcome message
    """
    return {"username": username, "message": f"Welcome, {username}!"}


@app.post("/api/greet")
def greet(body: GreetRequest):
    """
    API endpoint that accepts a POST request with JSON body containing a name,
    and returns a personalized greeting.

    Expected JSON body:
        {
            "name": "Alice"
        }

    Returns:
        JSON response with greeting message
    """
    # FastAPI has already parsed the JSON and validated it against GreetRequest
    return {"greeting": f"Hello, {body.name}!"}
