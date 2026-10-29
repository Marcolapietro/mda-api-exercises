# Exercise 10: Consuming External Public APIs

## Objective

Learn how to consume external public APIs and integrate their data into your own FastAPI API. This exercise teaches you to work with **multiple API endpoints** and handle real-world API integration challenges.

## Quick Start

```bash
cd exercises/10-public-api
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
fastapi dev app.py
```

Fill the blanks (`_____`) from top to bottom; the app starts once the decorator of `/login` and the `Depends(...)` of `/weather` are complete. The other blanks (the environment variable name, `create_access_token`, the `params` dicts, `client.get`, `200`, `.json()`) are only used when a request reaches them, so you will notice them while testing. The API runs at `http://127.0.0.1:8000`.

---

## What You'll Learn

This exercise builds on Exercise 11 (JWT authentication) and adds:

1. **Consuming External APIs** with the `httpx` library
2. **Working with Multiple API Endpoints** (Geocoding + Weather)
3. **Handling API Keys** and authentication with third-party services
4. **Error Handling** for external API failures
5. **Query Parameters** for flexible API requests
6. **Modern API Best Practices** (coordinates vs. deprecated city names)

---

## The Challenge: Building a Weather API

You'll create a FastAPI API that:
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
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
```

If the variable is not set, `/weather` answers `503 Service Unavailable`: the problem is on the server side, not in your request.

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

### Authentication Endpoints (from Exercise 11)

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/register` | No | Register a new user |
| POST | `/login` | No | Login with JSON credentials, get JWT |
| GET | `/profile` | JWT | Get user profile |

### Weather Endpoint (New in Exercise 10)

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/weather?city=CityName&country=CC` | **JWT** | Get weather for a city |

**Why is `/weather` protected?**
- Every call to `/weather` spends your OpenWeatherMap quota (60 calls per minute on the free tier)
- Without a token, anybody could burn it: a request without one answers `401`
- The focus is still **consuming external APIs**: login once, then reuse the token

### How JWT works in FastAPI (new concept)

FastAPI has no `@jwt_required()` decorator; we use the `PyJWT` library directly:

- `create_access_token(username)` signs a token with `jwt.encode(...)`. It carries `sub` (the user) and `exp` (expires in 15 minutes).
- `HTTPBearer` reads the `Authorization: Bearer <token>` header and gives it to a **dependency**, `get_current_user`, which checks it with `jwt.decode(...)`. A missing, expired or tampered token answers `401` with a `WWW-Authenticate: Bearer` header. `HTTPBearer(auto_error=False)` is there because by default FastAPI would answer 403 when the header is missing.
- A route is protected by asking for that dependency: `user: Annotated[str, Depends(get_current_user)]`. It replaces `@jwt_required()`, and `user` replaces `get_jwt_identity()`.
- `/login` takes the credentials as **JSON** (not a form): the form-based password flow in the FastAPI tutorial is the OAuth password grant, which OAuth 2.1 removed. Swagger UI (`/docs`) still shows an "Authorize" button for the token.

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

You need to complete **10 TODOs** (14 `_____` blanks; the two params dicts have several each).
Line numbers can shift as you type, so search for `_____`:

#### Setup and Authentication TODOs (from Exercise 11):
1. `OPENWEATHER_API_KEY` (line 44): The name of the environment variable: `OPENWEATHER_API_KEY`
2. `@app._____("/login")` (line 119): The HTTP method that sends credentials in a body: `post`
3. `login()` (line 132): Create the JWT access token: `create_access_token(data.username)`
4. `weather()` (line 150): Require a valid token: `Depends(get_current_user)`

#### Geocoding API TODOs (in `weather()`, step 1):
5. `geo_params` (line 188): Fill `"q"` with `query` and `"appid"` with `OPENWEATHER_API_KEY`
6. `geo_response` (line 193): Make the GET request: `client.get(GEOCODING_API_URL, params=geo_params)`
7. `geo_response.status_code` (line 198): The status code that means success: `200`
8. `geo_data` (line 206): Parse the JSON response: `geo_response.json()`

#### Weather API TODOs (in `weather()`, step 2):
9. `weather_params` (lines 239-241): Fill `"lat"`, `"lon"` and `"appid"`
10. `weather_response` (line 249) and `weather_data` (line 259): Make the GET request, `client.get(WEATHER_API_URL, params=weather_params)`, and parse it with `weather_response.json()`

### Key Concepts to Implement

**1. Building the request parameters:**
```python
# Geocoding API: GET {GEOCODING_API_URL}?q=...&appid=...&limit=1
geo_params = {"q": query, "appid": OPENWEATHER_API_KEY, "limit": 1}

# Weather API: GET {WEATHER_API_URL}?lat=...&lon=...&appid=...&units=metric&lang=en
weather_params = {"lat": latitude, "lon": longitude, "appid": OPENWEATHER_API_KEY,
                  "units": "metric", "lang": "en"}
```

**Why a `params` dict and not an f-string URL?** `httpx` URL-encodes every value. With
`f"...?q={query}&appid=..."`, a user who asks for `?city=Paris%26limit%3D50` would inject an extra
`limit=50` parameter into the call to OpenWeatherMap, and a space in `New York` would break the URL.
With `params=`, `Paris&limit=50` is sent as **one** value of `q` (`q=Paris%26limit%3D50`).

**2. Making HTTP Requests:**
```python
import httpx

# Always set a timeout on outbound calls: without it a slow upstream API blocks your worker forever
with httpx.Client(timeout=10) as client:
    response = client.get(GEOCODING_API_URL, params=geo_params)
    if response.status_code == 200:
        data = response.json()
        # Process data
    else:
        # Handle error (502 Bad Gateway: the upstream API failed, not your client)
        raise HTTPException(status_code=502, detail="Geocoding API request failed")
```

**3. Error Handling:**
```python
try:
    response = client.get(GEOCODING_API_URL, params=geo_params)
    data = response.json()
except httpx.HTTPError:
    # Network error. Do NOT return str(e) to the client: the exception message
    # can include the full URL, and that URL contains your appid (API key).
    logger.exception("Geocoding API request failed")   # details stay in the server log
    raise HTTPException(status_code=502, detail="Could not connect to Geocoding API")
except (KeyError, IndexError, ValueError):
    # Invalid response format
    logger.exception("Invalid response from Geocoding API")
    raise HTTPException(status_code=502, detail="Unexpected response format from Geocoding API")
```

Errors use FastAPI's default `{"detail": "..."}` body.

---

## Testing the API

### 0. Register, Log In and Keep the Token

`/weather` is protected, so get a token first (passwords need 8 to 72 characters):

```bash
curl -X POST -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}' http://127.0.0.1:8000/register
curl -X POST -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}' http://127.0.0.1:8000/login
```

The login response is `{"access_token": "...", "token_type": "bearer"}`. Send the token on every call as `-H "Authorization: Bearer YOUR_TOKEN"` (the examples below use that). Without it:

```bash
curl -i "http://127.0.0.1:8000/weather?city=Madrid"
# 401 Unauthorized, header: WWW-Authenticate: Bearer
```

### 1. Test Without API Key (Should Fail)

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather?city=Madrid"
```

**Expected Response (503):**
```json
{
  "detail": "OpenWeatherMap API key not configured: set the OPENWEATHER_API_KEY environment variable (free key at https://openweathermap.org/api)"
}
```

### 2. Test With API Key - Default City

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather"
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
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather?city=Paris&country=FR"

# London, UK
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather?city=London&country=GB"

# New York, USA (the space is encoded as %20)
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather?city=New%20York&country=US"

# Tokyo, Japan
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather?city=Tokyo&country=JP"
```

**Always quote URLs that contain `&`.** Unquoted, bash treats `&` as "run in the background" and
drops `country=...`; PowerShell refuses to parse it; in CMD you must escape it as `^&`.

**Spaces:** a literal space is not valid in a URL, so quotes alone are not enough
(`"...city=New York..."` fails). Either encode it as `%20` (above) or let curl encode it:
```bash
curl -G -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather" --data-urlencode "city=New York" --data-urlencode "country=US"
```

**Windows PowerShell 5.1:** `curl` is an alias of `Invoke-WebRequest`; use `curl.exe` to run the real curl.

### 4. Test Ambiguous City Names

**Without country code:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather?city=Paris"
# Returns: Paris, France (most common)
```

**With country code:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather?city=Paris&country=US"
# Returns: Paris, Texas, USA
```

### 5. Test Invalid City (Should Fail)

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather?city=InvalidCityXYZ"
```

**Expected Response (404):**
```json
{
  "detail": "Could not find coordinates for city: InvalidCityXYZ. Try adding a country code, e.g., ?city=Paris&country=FR"
}
```

---

## Understanding the `httpx` Library

`httpx` is installed together with `fastapi[standard]`, and its calls look just like the ones of `requests`.

### Basic Usage

```python
import httpx

# GET request
response = httpx.get('https://api.example.com/data')

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
response = httpx.get('https://api.example.com/data', params=params, timeout=10)
```
`httpx` URL-encodes each value, so spaces, `&`, `=` or `#` in user input can't break the URL
or add extra parameters.

**Method 2: URL string (avoid with user input)**
```python
# ❌ value1 is not encoded: "a&admin=1" becomes an extra parameter
url = f'https://api.example.com/data?param1={value1}&param2={value2}'
response = httpx.get(url, timeout=10)
```

### Error Handling

```python
try:
    response = httpx.get(url, timeout=5)
    response.raise_for_status()  # Raises exception for 4xx/5xx
    data = response.json()
except httpx.TimeoutException:
    print("Request timed out")
except httpx.ConnectError:
    print("Network error")
except httpx.HTTPStatusError as e:
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
@app.get("/weather/forecast")
def forecast():
    # Use: https://api.openweathermap.org/data/2.5/forecast
    pass

# Air quality
@app.get("/weather/air-quality")
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
@app.get("/weather")
def weather(
    user: Annotated[str, Depends(get_current_user)],
    units: Annotated[str, Query()] = "metric",  # metric, imperial, standard
    city: Annotated[str, Query()] = "Madrid",
):
    # Use in API call: "units": units
    ...
```

### 5. Track Each User's Queries

`/weather` already knows who is calling (`user`). Count the queries per user:

```python
query_counts: dict[str, int] = {}

# inside weather(), after the token check
query_counts[user] = query_counts.get(user, 0) + 1
```

Expose it in a new protected `GET /weather/stats` endpoint.

---

## Understanding API Deprecation

**⚠️ Important Note About OpenWeatherMap Changes**

OpenWeatherMap has deprecated city name queries:

**Old Way (Deprecated, but still works):**
```python
# Direct city name query - NOT RECOMMENDED
httpx.get('https://api.openweathermap.org/data/2.5/weather',
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
httpx.get('https://api.openweathermap.org/geo/1.0/direct',
          params={'q': city, 'appid': api_key, 'limit': 1}, timeout=10)
# Get coordinates

# Step 2: Weather by coordinates
httpx.get('https://api.openweathermap.org/data/2.5/weather',
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

### Python httpx Library

- [Official Documentation](https://www.python-httpx.org/)
- [Quickstart Guide](https://www.python-httpx.org/quickstart/)

### ISO Country Codes

- [ISO 3166-1 alpha-2 codes](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)
- Examples: ES (Spain), FR (France), US (United States), GB (United Kingdom)

---

## Summary

**Key Takeaways:**

1. **External API Consumption**
   - Use the `httpx` library for HTTP calls
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
   - JWT authentication (Exercise 11)
   - FastAPI routing and error handling
   - JSON responses
   - Now adding: External API consumption!

**Next Steps:**
- **Exercise 05**: CRUD Operations (Create, Read, Update, Delete)
- **Exercise 06**: API Pagination
- **Exercise 12**: Role-Based Access Control (RBAC)

Good luck! 🌤️
