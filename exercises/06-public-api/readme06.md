# Exercise 6: Public API Consumption

## Objective

Consume external APIs and integrate their data into your own API using Python and Flask.

## Description

In this exercise, you will expand the API developed in previous exercises to include a new route that consumes data from the OpenWeatherMap API to obtain weather information. Students will need to implement this functionality by filling in the provided blanks.

## Requirements

### 1. Installation of Additional Dependencies
- Install the `requests` library to make HTTP requests.

### 2. Registration on OpenWeatherMap
- Go to [OpenWeatherMap](https://openweathermap.org/)
- Click on "Sign Up" and create a free account
- Once registered, go to "API Keys" in your profile
- Generate a new API key (it may take up to 2 hours to activate, although it's usually instant. If it takes too long, notify the instructor)
- Save your API key securely

### 3. API Structure
- Create a route (`GET /weather`) that obtains weather data using the OpenWeatherMap API
- Use your API key in requests

### 4. Implementation of API Consumption
- Use the `requests` library to make a request to OpenWeatherMap
- Process the response and return relevant data (temperature, description, city)

### 5. Testing
- Use tools like Postman or `curl` to test the new route
- Test different cities using the `?city=CityName` parameter

## Suggested Steps

### 1. Instructions
In the _____ blank within the `login` function, use the appropriate Flask-JWT-Extended function to create an access token.

In the /profile route, use the appropriate function to obtain the user's identity from the token.

### 2. Install Additional Dependencies
```bash
pip install requests
```

### 3. Example API Usage
```bash
# Get weather for Madrid (default)
curl http://localhost:5000/weather

# Get weather for another city
curl http://localhost:5000/weather?city=Barcelona
```

## Additional Documentation
- [OpenWeatherMap API Documentation](https://openweathermap.org/api)
- [OpenWeatherMap Quick Start Guide](https://openweathermap.org/guide)
