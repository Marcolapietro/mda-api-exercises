# Exercise 7: Consuming External Public APIs

## Objective

Learn how to consume external public APIs and integrate their data into your own Flask API. This exercise teaches you to work with **multiple API endpoints** and handle real-world API integration challenges.

## Quick Start

```bash
cd exercises/07-public-api
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python app.py
```

---

## What You'll Learn

This exercise builds on Exercise 06 (JWT authentication) and adds:

1. **Consuming External APIs** with the `requests` library
2. **Working with Multiple API Endpoints** (Geocoding + Weather)
3. **Handling API Keys** and authentication with third-party services
4. **Error Handling** for external API failures
5. **Query Parameters** for flexible API requests
6. **Modern API Best Practices** (coordinates vs. deprecated city names)

---

## The Challenge: Building a Weather API

You'll create a Flask API that:
- Uses **OpenWeatherMap Geocoding API** to convert city names to coordinates
- Uses **OpenWeatherMap Current Weather API** to get weather data by coordinates
- Combines both APIs to provide weather information for any city worldwide

### Why Two API Calls?

**Modern Approach (2025):**
```
User Request: "Get weather for Paris"
    ↓
Step 1: Geocoding API
    City "Paris" → Coordinates (48.8566, 2.3522)
    ↓
Step 2: Weather API
    Coordinates → Weather Data
    ↓
Response: {temperature: 15°C, description: "cloudy", ...}
```

**Why not just use city names directly?**
- City name queries (`?q=Paris`) are **deprecated** by OpenWeatherMap
- Multiple cities share the same name (Paris, France vs Paris, Texas)
- Coordinates are **unambiguous** and work globally
- Geocoding provides additional location context (country, state)

---

## Prerequisites

### 1. Get a Free OpenWeatherMap API Key

**Step-by-step:**

1. Go to [https://openweathermap.org/](https://openweathermap.org/)
2. Click "Sign Up" in the top-right corner
3. Create a free account with your email
4. Verify your email address
5. Log in and go to "API Keys" in your profile
6. Copy your default API key OR generate a new one
7. **Wait 10 minutes to 2 hours** for activation (usually instant)

**API Key Example:**
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

### 2. Configure Your API Key

**Never paste the key into `app.py`**: code ends up on GitHub and keys pushed to public repos are found by bots within minutes. `app.py` reads it from an environment variable instead:
```python
OPENWEATHER_API_KEY = os.environ.get('OPENWEATHER_API_KEY', 'YOUR_API_KEY_HERE')
```

Set the variable in the terminal where you run the app:
```bash
# Linux / macOS
export OPENWEATHER_API_KEY="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

# Windows PowerShell
$env:OPENWEATHER_API_KEY="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

# Windows CMD
set OPENWEATHER_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

---

## API Structure

### Authentication Endpoints (from Exercise 06)

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/register` | No | Register a new user |
| POST | `/login` | No | Login with JSON credentials, get JWT |
| GET | `/profile` | JWT | Get user profile |

### Weather Endpoint (New in Exercise 07)

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/weather?city=CityName&country=CC` | **No** | Get weather for a city |

**Why is `/weather` public?**
- Focus of exercise is **consuming external APIs**, not authentication
- Simpler testing (no need to login first)
- Real-world use case: Public weather widgets

---

## How It Works: Two-Step API Flow

### Step 1: Geocoding API (City → Coordinates)

**Request:**
```
GET https://api.openweathermap.org/geo/1.0/direct?q=Madrid,ES&appid=YOUR_KEY&limit=1
```

**Response:**
```json
[
  {
    "name": "Madrid",
    "lat": 40.4165,
    "lon": -3.7026,
    "country": "ES",
    "state": "Madrid"
  }
]
```

**What you extract:**
- `lat`: Latitude (40.4165)
- `lon`: Longitude (-3.7026)
- `name`: Official city name
- `country`: ISO country code
- `state`: State/region (if available)

### Step 2: Weather API (Coordinates → Weather)

**Request:**
```
GET https://api.openweathermap.org/data/2.5/weather?lat=40.4165&lon=-3.7026&appid=YOUR_KEY&units=metric&lang=en
```

**Response:**
```json
{
  "main": {
    "temp": 18.5,
    "feels_like": 17.2,
    "humidity": 65,
    "pressure": 1013
  },
  "weather": [
    {
      "main": "Clouds",
      "description": "scattered clouds",
      "icon": "03d"
    }
  ],
  "wind": {
    "speed": 3.5,
    "deg": 180
  },
  "dt": 1678888888
}
```

**What you extract:**
- `temp`: Temperature in Celsius
- `feels_like`: "Feels like" temperature
- `humidity`: Humidity percentage
- `description`: Weather description
- `wind.speed`: Wind speed (m/s)

---

## Implementation Guide

### TODOs in app.py

You need to complete **10 TODOs** (13 `_____` blanks; the two params dicts have several each).
Line numbers can shift as you type, so search for `_____`:

#### Authentication TODOs (from Exercise 06):
1. `login()` (line 81): Create the JWT access token: `create_access_token(identity=username)`
2. `profile()` (line 96): Get the user identity from the JWT: `get_jwt_identity()`

#### Geocoding API TODOs (in `weather()`, step 1):
3. `geo_params` (line 151): Fill `'q'` with `query` and `'appid'` with `OPENWEATHER_API_KEY`
4. `geo_response` (line 157): Make the GET request: `requests.get(GEOCODING_API_URL, params=geo_params, timeout=10)`
5. `geo_data` (line 169): Parse the JSON response: `geo_response.json()`
6. `latitude` (line 182): `geo_data[0]['lat']`
7. `longitude` (line 186): `geo_data[0]['lon']`

#### Weather API TODOs (in `weather()`, step 2):
8. `weather_params` (lines 215-217): Fill `'lat'`, `'lon'` and `'appid'`
9. `weather_response` (line 225): Make the GET request: `requests.get(WEATHER_API_URL, params=weather_params, timeout=10)`
10. `weather_data` (line 236): Parse the JSON response: `weather_response.json()`

### Key Concepts to Implement

**1. Building the request parameters:**
```python
# Geocoding API: GET {GEOCODING_API_URL}?q=...&appid=...&limit=1
geo_params = {'q': query, 'appid': OPENWEATHER_API_KEY, 'limit': 1}

# Weather API: GET {WEATHER_API_URL}?lat=...&lon=...&appid=...&units=metric&lang=en
weather_params = {'lat': latitude, 'lon': longitude, 'appid': OPENWEATHER_API_KEY,
                  'units': 'metric', 'lang': 'en'}
```

**Why a `params` dict and not an f-string URL?** `requests` URL-encodes every value. With
`f'...?q={query}&appid=...'`, a user who asks for `?city=Paris%26limit%3D50` would inject an extra
`limit=50` parameter into the call to OpenWeatherMap, and a space in `New York` would break the URL.
With `params=`, `Paris&limit=50` is sent as **one** value of `q` (`q=Paris%26limit%3D50`).

**2. Making HTTP Requests:**
```python
import requests

# Always set a timeout on outbound calls: without it a slow upstream API blocks your worker forever
response = requests.get(GEOCODING_API_URL, params=geo_params, timeout=10)
if response.status_code == 200:
    data = response.json()
    # Process data
else:
    # Handle error (502 Bad Gateway: the upstream API failed, not your client)
```

**3. Error Handling:**
```python
try:
    response = requests.get(GEOCODING_API_URL, params=geo_params, timeout=10)
    data = response.json()
except requests.exceptions.RequestException:
    # Network error. Do NOT return str(e) to the client: the exception message
    # can include the full URL, and that URL contains your appid (API key).
    app.logger.exception('Geocoding API request failed')   # details stay in the server log
    return jsonify({'error': 'Network error',
                    'message': 'Could not connect to Geocoding API'}), 502
except (KeyError, IndexError, ValueError):
    # Invalid response format
    app.logger.exception('Invalid response from Geocoding API')
    return jsonify({'error': 'Invalid response from Geocoding API'}), 502
```

---

## Testing the API

### 1. Test Without API Key (Should Fail)

```bash
curl "http://127.0.0.1:5000/weather?city=Madrid"
```

**Expected Response:**
```json
{
  "error": "OpenWeatherMap API key not configured",
  "message": "Please set the OPENWEATHER_API_KEY environment variable",
  "help": "Get a free API key at https://openweathermap.org/api"
}
```

### 2. Test With API Key - Default City

```bash
curl "http://127.0.0.1:5000/weather"
```

**Expected Response (Madrid, default):**
```json
{
  "location": {
    "city": "Madrid",
    "country": "ES",
    "state": "Madrid",
    "coordinates": {
      "latitude": 40.4165,
      "longitude": -3.7026
    }
  },
  "weather": {
    "temperature": 18.5,
    "feels_like": 17.2,
    "humidity": 65,
    "pressure": 1013,
    "description": "scattered clouds",
    "main": "Clouds",
    "icon": "03d"
  },
  "wind": {
    "speed": 3.5,
    "direction": 180
  },
  "timestamp": 1678888888
}
```

### 3. Test Different Cities

```bash
# Paris, France
curl "http://127.0.0.1:5000/weather?city=Paris&country=FR"

# London, UK
curl "http://127.0.0.1:5000/weather?city=London&country=GB"

# New York, USA (the space is encoded as %20)
curl "http://127.0.0.1:5000/weather?city=New%20York&country=US"

# Tokyo, Japan
curl "http://127.0.0.1:5000/weather?city=Tokyo&country=JP"
```

**Always quote URLs that contain `&`.** Unquoted, bash treats `&` as "run in the background" and
drops `country=...`; PowerShell refuses to parse it; in CMD you must escape it as `^&`.

**Spaces:** a literal space is not valid in a URL, so quotes alone are not enough
(`"...city=New York..."` fails). Either encode it as `%20` (above) or let curl encode it:
```bash
curl -G "http://127.0.0.1:5000/weather" --data-urlencode "city=New York" --data-urlencode "country=US"
```

**Windows PowerShell 5.1:** `curl` is an alias of `Invoke-WebRequest`; use `curl.exe` to run the real curl.

### 4. Test Ambiguous City Names

**Without country code:**
```bash
curl "http://127.0.0.1:5000/weather?city=Paris"
# Returns: Paris, France (most common)
```

**With country code:**
```bash
curl "http://127.0.0.1:5000/weather?city=Paris&country=US"
# Returns: Paris, Texas, USA
```

### 5. Test Invalid City (Should Fail)

```bash
curl "http://127.0.0.1:5000/weather?city=InvalidCityXYZ"
```

**Expected Response:**
```json
{
  "error": "City not found",
  "message": "Could not find coordinates for city: InvalidCityXYZ",
  "suggestion": "Try adding a country code, e.g., ?city=Paris&country=FR"
}
```

---

## Understanding the `requests` Library

### Installation

```bash
pip install requests
```

### Basic Usage

```python
import requests

# GET request
response = requests.get('https://api.example.com/data')

# Check status
if response.status_code == 200:
    print("Success!")

# Parse JSON
data = response.json()

# Access data
print(data['key'])
```

### With Query Parameters

**Method 1: params dictionary (use this one)**
```python
params = {'param1': value1, 'param2': value2}
response = requests.get('https://api.example.com/data', params=params, timeout=10)
```
`requests` URL-encodes each value, so spaces, `&`, `=` or `#` in user input can't break the URL
or add extra parameters.

**Method 2: URL string (avoid with user input)**
```python
# ❌ value1 is not encoded: "a&admin=1" becomes an extra parameter
url = f'https://api.example.com/data?param1={value1}&param2={value2}'
response = requests.get(url, timeout=10)
```

### Error Handling

```python
try:
    response = requests.get(url, timeout=5)
    response.raise_for_status()  # Raises exception for 4xx/5xx
    data = response.json()
except requests.exceptions.Timeout:
    print("Request timed out")
except requests.exceptions.ConnectionError:
    print("Network error")
except requests.exceptions.HTTPError as e:
    print(f"HTTP error: {e}")
except ValueError:
    print("Invalid JSON response")
```

---

## Common Issues and Solutions

### Issue 1: API Key Not Activated

**Symptom:**
```json
{
  "cod": 401,
  "message": "Invalid API key"
}
```

**Solution:**
- Wait 10 minutes to 2 hours for activation
- Verify you copied the entire key (no spaces)
- Check you're using the correct key from your OpenWeatherMap account

### Issue 2: City Not Found

**Symptom:**
```json
{
  "error": "City not found",
  "message": "Could not find coordinates for city: Madrd"
}
```

**Solution:**
- Check spelling: "Madrd" → "Madrid"
- Add country code for disambiguation
- Use English city names (e.g., "Munich" not "München")

### Issue 3: Network Timeout

**Symptom:**
```
Error: Could not connect to Geocoding API
```

**Solution:**
- Check internet connection
- Verify OpenWeatherMap API is not down: [status.openweathermap.org](https://status.openweathermap.org/)
- Try again in a few seconds

### Issue 4: Rate Limiting

**Free tier limits:**
- 60 calls per minute
- 1,000,000 calls per month

**If you hit the limit:**
```json
{
  "cod": 429,
  "message": "Too many requests"
}
```

**Solution:**
- Wait 60 seconds
- Implement caching (stretch goal)
- Upgrade to paid tier if needed

---

## Acceptance Criteria

Your implementation should:

- ✅ Successfully call OpenWeatherMap Geocoding API
- ✅ Successfully call OpenWeatherMap Current Weather API
- ✅ Handle API key validation
- ✅ Handle city not found errors
- ✅ Handle network errors gracefully
- ✅ Parse JSON responses correctly
- ✅ Return structured weather data
- ✅ Support optional country code parameter
- ✅ Use HTTPS (not HTTP) for API calls
- ✅ Use coordinates (not deprecated city name queries)

---

## Stretch Goals

Once you complete the basic implementation:

### 1. Add Response Caching

Avoid repeated API calls for the same city:

```python
from datetime import datetime, timedelta

weather_cache = {}  # {city: {data: {...}, expires: timestamp}}

def get_cached_weather(city):
    if city in weather_cache:
        if weather_cache[city]['expires'] > datetime.now():
            return weather_cache[city]['data']
    return None

def cache_weather(city, data, ttl_minutes=10):
    weather_cache[city] = {
        'data': data,
        'expires': datetime.now() + timedelta(minutes=ttl_minutes)
    }
```

### 2. Add More Weather Endpoints

```python
# 5-day forecast
@app.route('/weather/forecast', methods=['GET'])
def forecast():
    # Use: https://api.openweathermap.org/data/2.5/forecast
    pass

# Air quality
@app.route('/weather/air-quality', methods=['GET'])
def air_quality():
    # Use: https://api.openweathermap.org/data/2.5/air_pollution
    pass
```

### 3. Add Weather Icons

Return icon URLs for frontend display:

```python
weather_info['weather']['icon_url'] = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
```

### 4. Add Temperature Unit Conversion

```python
@app.route('/weather', methods=['GET'])
def weather():
    units = request.args.get('units', 'metric')  # metric, imperial, standard
    # Use in API call: &units={units}
```

### 5. Protect Weather Endpoint with JWT

Make weather endpoint require authentication:

```python
@app.route('/weather', methods=['GET'])
@jwt_required()  # Add this decorator
def weather():
    current_user = get_jwt_identity()
    # Track user's weather queries for analytics
```

---

## Understanding API Deprecation

**⚠️ Important Note About OpenWeatherMap Changes**

OpenWeatherMap has deprecated city name queries:

**Old Way (Deprecated, but still works):**
```python
# Direct city name query - NOT RECOMMENDED
requests.get('https://api.openweathermap.org/data/2.5/weather',
             params={'q': city, 'appid': api_key}, timeout=10)
```

**Problems:**
- No longer actively maintained
- Bug fixes not guaranteed
- May be removed in future versions
- Ambiguous for cities with same names

**New Way (Recommended):**
```python
# Step 1: Geocode
requests.get('https://api.openweathermap.org/geo/1.0/direct',
             params={'q': city, 'appid': api_key, 'limit': 1}, timeout=10)
# Get coordinates

# Step 2: Weather by coordinates
requests.get('https://api.openweathermap.org/data/2.5/weather',
             params={'lat': lat, 'lon': lon, 'appid': api_key}, timeout=10)
```

**Benefits:**
- Actively maintained
- Unambiguous results
- Better error messages
- Future-proof
- Additional location context

**This exercise teaches the NEW way!**

---

## Additional Resources

### OpenWeatherMap Documentation

- [Current Weather API](https://openweathermap.org/current)
- [Geocoding API](https://openweathermap.org/api/geocoding-api)
- [API Key Guide](https://openweathermap.org/appid)
- [FAQ](https://openweathermap.org/faq)

### Python requests Library

- [Official Documentation](https://requests.readthedocs.io/)
- [Quickstart Guide](https://requests.readthedocs.io/en/latest/user/quickstart/)

### ISO Country Codes

- [ISO 3166-1 alpha-2 codes](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)
- Examples: ES (Spain), FR (France), US (United States), GB (United Kingdom)

---

## Summary

**Key Takeaways:**

1. **External API Consumption**
   - Use `requests` library for HTTP calls
   - Parse JSON responses with `.json()`
   - Handle errors gracefully

2. **Multi-Step API Workflows**
   - Some tasks require multiple API calls
   - Geocoding → Coordinates → Weather
   - Chain responses together

3. **API Best Practices**
   - Use HTTPS, not HTTP
   - Follow current recommendations (coordinates vs city names)
   - Validate API keys before making requests
   - Handle rate limits and errors

4. **Real-World Integration**
   - Third-party API keys and authentication
   - Query parameters for flexible requests
   - Structured error responses
   - Comprehensive data extraction

5. **Building on Previous Knowledge**
   - JWT authentication (Exercise 06)
   - Flask routing and error handling
   - JSON responses
   - Now adding: External API consumption!

**Next Steps:**
- **Exercise 08**: CRUD Operations (Create, Read, Update, Delete)
- **Exercise 09**: API Pagination
- **Exercise 10**: Role-Based Access Control (RBAC)

Good luck! 🌤️
