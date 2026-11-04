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
copy .env.example .env  # Windows (cp on Linux/Mac); then put your OpenWeatherMap key in .env
fastapi dev app.py
```

Fill the blanks (`_____`) from top to bottom; the app starts once the decorator of `/login` is complete. The other blanks (the environment variable name, `create_access_token`, the `params` dicts, `client.get`, `200`, `.json()`) are only used when a request reaches them, so you will notice them while testing. The API runs at `http://127.0.0.1:8000`.

---

## What You'll Learn

The JWT login (`/register`, `/login`, `/profile`) is given to you here: it is a copy of what Exercise 11 explains in depth, and you only consume it. This exercise adds:

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

**Modern Approach:**
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

The easiest place for it is a `.env` file in the exercise folder. Copy the template and put your key in the copy:
```bash
cp .env.example .env     # Linux / macOS
copy .env.example .env   # Windows (CMD or PowerShell)
```
```
OPENWEATHER_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

At startup, `load_dotenv()` (from the `python-dotenv` package) copies the variables of `.env` into the environment, so `os.environ.get` finds them.

- `.env` is in `.gitignore`, so your key never reaches GitHub. `.env.example` has empty values only and **is** committed: it tells others which variables to set.
- `fastapi dev` reloads when you save a `.py` file, not `.env`: after editing `.env`, stop the app (Ctrl+C) and start it again.
- `.env` can also hold `JWT_SECRET_KEY`, so tokens survive reloads (see Issue 5).

You can also set the variable in the terminal where you run the app; it wins over `.env`:
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

### Authentication Endpoints (given; explained in depth in Exercise 11)

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| POST | `/register` | No | Register a new user |
| POST | `/login` | No | Login with JSON credentials, get JWT |
| GET | `/profile` | JWT | Get user profile |

### Weather Endpoint (New in Exercise 10)

| Method | Endpoint | Auth Required | Description |
|--------|----------|---------------|-------------|
| GET | `/weather?city=CityName&country=CC` | **No** | Get weather for a city |

**Why is `/weather` public?**
- Focus of exercise is **consuming external APIs**, not authentication
- Simpler testing (no need to login first)
- Real-world use case: Public weather widgets

### How JWT works in FastAPI (new concept)

The login code is given to you; you only need to know what it does (Exercise 11 explains it in depth). It uses the `PyJWT` library directly:

- `create_access_token(username)` signs a token with `jwt.encode(...)`. It carries `sub` (the user) and `exp` (expires in 15 minutes).
- `HTTPBearer` reads the `Authorization: Bearer <token>` header and gives it to a **dependency**, `get_current_user`, which checks it with `jwt.decode(...)`. A missing, expired or tampered token answers `401` with a `WWW-Authenticate: Bearer` header. `HTTPBearer(auto_error=False)` lets us return our own `401` message and `WWW-Authenticate` header when the header is missing (FastAPI's default is a generic `401 Not authenticated`).
- A route is protected by asking for that dependency: `user: Annotated[str, Depends(get_current_user)]`. FastAPI runs `get_current_user` before the route and puts the username it returns in `user`; if the token is bad, the route never runs.
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

You need to complete **10 TODOs** (13 `_____` blanks; the two params dicts have several each).
Line numbers can shift as you type, so search for `_____`:

#### Setup and Authentication TODOs (in the given JWT code):
1. `OPENWEATHER_API_KEY` (line 48): The name of the environment variable: `OPENWEATHER_API_KEY`
2. `@app._____("/login")` (line 123): The HTTP method that sends credentials in a body: `post`
3. `login()` (line 136): Create the JWT access token: `create_access_token(data.username)`

#### Geocoding API TODOs (in `weather()`, step 1):
4. `geo_params` (line 192): Fill `"q"` with `query` and `"appid"` with `OPENWEATHER_API_KEY`
5. `geo_response` (line 197): Make the GET request: `client.get(GEOCODING_API_URL, params=geo_params)`
6. `geo_response.status_code` (line 207): The status code that means success: `200`
7. `geo_data` (line 215): Parse the JSON response: `geo_response.json()`

#### Weather API TODOs (in `weather()`, step 2):
8. `weather_params` (lines 248-250): Fill `"lat"`, `"lon"` and `"appid"`
9. `weather_response` (line 258): Make the GET request: `client.get(WEATHER_API_URL, params=weather_params)`
10. `weather_data` (line 272): Parse the JSON response: `weather_response.json()`

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
    elif response.status_code == 401:
        # OUR key is wrong or not active yet (503: the server is misconfigured, not the client)
        raise HTTPException(status_code=503, detail="Weather service is not configured correctly")
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

### 0. Test the Authentication Endpoints

`/weather` is public, but `/profile` needs a token (passwords need 8 to 72 characters):

> The commands below use `curl` with `bash` quoting. In **Windows CMD** use `example/commands_cmd.txt`, and in **PowerShell** use `example/commands_powershell.txt` (with `curl.exe` the quotes inside the JSON must be escaped as `\"`, otherwise the server answers `422`).

```bash
curl -X POST -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}' http://127.0.0.1:8000/register
curl -X POST -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}' http://127.0.0.1:8000/login
```

**Login response:**
```json
{
  "message": "Login successful",
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

Send the token as `-H "Authorization: Bearer YOUR_TOKEN"`:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://127.0.0.1:8000/profile
# Without the header: 401 Unauthorized, header WWW-Authenticate: Bearer
```

### 1. Test Without API Key (Should Fail)

```bash
curl -i "http://127.0.0.1:8000/weather?city=Madrid"
```

**Expected Response (503):**
```json
{
  "detail": "OpenWeatherMap API key not configured: set OPENWEATHER_API_KEY in the .env file (free key at https://openweathermap.org/api)"
}
```

### 2. Test With API Key - Madrid

```bash
curl "http://127.0.0.1:8000/weather?city=Madrid"
```

**Expected Response:**
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
curl "http://127.0.0.1:8000/weather?city=Paris&country=FR"

# London, UK
curl "http://127.0.0.1:8000/weather?city=London&country=GB"

# New York, USA (the space is encoded as %20)
curl "http://127.0.0.1:8000/weather?city=New%20York&country=US"

# Tokyo, Japan
curl "http://127.0.0.1:8000/weather?city=Tokyo&country=JP"
```

**Always quote URLs that contain `&`.** Unquoted, bash treats `&` as "run in the background" and
drops `country=...`; PowerShell refuses to parse it; in CMD you must escape it as `^&`.

**Spaces:** a literal space is not valid in a URL, so quotes alone are not enough
(`"...city=New York..."` fails). Either encode it as `%20` (above) or let curl encode it:
```bash
curl -G "http://127.0.0.1:8000/weather" --data-urlencode "city=New York" --data-urlencode "country=US"
```

**Windows PowerShell 5.1:** `curl` is an alias of `Invoke-WebRequest`; use `curl.exe` to run the real curl.

### 4. Test Ambiguous City Names

**Without country code:**
```bash
curl "http://127.0.0.1:8000/weather?city=Paris"
# Returns: Paris, France (most common)
```

**With country code:**
```bash
curl "http://127.0.0.1:8000/weather?city=Paris&country=US"
# Returns: Paris, Texas, USA
```

### 5. Test Invalid City (Should Fail)

```bash
curl "http://127.0.0.1:8000/weather?city=InvalidCityXYZ"
```

**Expected Response (404):**
```json
{
  "detail": "Could not find coordinates for city: InvalidCityXYZ. Try adding a country code, e.g., ?city=Paris&country=FR"
}
```

### 6. Test Missing City (Should Fail)

`city` is required: `Query(min_length=1)` with no default value. Without it, or with it empty (`?city=`), FastAPI answers `422 Unprocessable Content` before your code runs, so OpenWeatherMap is never called (not even when the key is missing).

```bash
curl "http://127.0.0.1:8000/weather"
```

**Expected Response (422):**
```json
{
  "detail": [
    {
      "type": "missing",
      "loc": ["query", "city"],
      "msg": "Field required",
      "input": null
    }
  ]
}
```

With `?city=` the error `type` is `string_too_short` instead of `missing`.

---

## Understanding the `httpx` Library

`httpx` is installed together with `fastapi[standard]`, and its calls look just like the ones of `requests`.

Note: the examples below use the module-level `httpx.get(...)` for brevity; the solution uses `httpx.Client(timeout=10)` for its two calls, which reuses one connection.

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

**Symptom** (OpenWeatherMap answers `401 Invalid API key`; your API answers `503`, because a bad key is a server misconfiguration, not the client's fault; the reason is in the server log):
```json
{
  "detail": "Weather service is not configured correctly"
}
```

**Solution:**
- Wait 10 minutes to 2 hours for activation
- Verify you copied the entire key into `.env` (no spaces or quotes around it), and restart the app after editing `.env`
- Check you're using the correct key from your OpenWeatherMap account

### Issue 2: City Not Found

**Symptom:**
```json
{
  "detail": "Could not find coordinates for city: Madrd. Try adding a country code, e.g., ?city=Paris&country=FR"
}
```

**Solution:**
- Check spelling: "Madrd" → "Madrid"
- Add country code for disambiguation
- Use English city names (e.g., "Munich" not "München")

### Issue 3: Network Timeout

**Symptom** (502 Bad Gateway):
```json
{
  "detail": "Could not connect to Geocoding API"
}
```

**Solution:**
- Check internet connection
- Verify OpenWeatherMap API is not down: [status.openweathermap.org](https://status.openweathermap.org/)
- Try again in a few seconds

### Issue 4: Rate Limiting

**Free tier limits:**
- 60 calls per minute
- 1,000,000 calls per month

**If you hit the limit** (OpenWeatherMap answers 429; your API reports a 502):
```json
{
  "detail": "Geocoding API request failed (upstream status 429)"
}
```

**Solution:**
- Wait 60 seconds
- Implement caching (stretch goal)
- Upgrade to paid tier if needed

### Issue 5: Token Suddenly Invalid (401) After Editing `app.py`

`fastapi dev` restarts the app every time you save a file. The restart empties the in-memory `users` dictionary and, unless `JWT_SECRET_KEY` is set, generates a new random secret, so every token issued before is now rejected with `401`.

**Solution:**
- Register and log in again after each change, then use the new token
- Or set `JWT_SECRET_KEY` in `.env` (generate one with `python -c "import secrets; print(secrets.token_hex(32))"`): tokens then survive a reload (this API only checks the token, not the `users` dictionary), but you still have to register again before you can log in

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
- ✅ Require the `city` parameter (422 if missing or empty)
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
    city: Annotated[str, Query(min_length=1)],  # required parameters go first
    units: Annotated[str, Query()] = "metric",  # metric, imperial, standard
):
    # Use in API call: "units": units
    ...
```

### 5. Protect Weather Endpoint with JWT

Make weather endpoint require authentication, with the same dependency `/profile` uses:

```python
@app.get("/weather")
def weather(
    user: Annotated[str, Depends(get_current_user)],  # Add this parameter
    city: Annotated[str, Query(min_length=1)],
):
    # Track user's weather queries for analytics
    ...
```

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
   - JWT authentication (given here; Exercise 11 explains it in depth)
   - FastAPI routing and error handling
   - JSON responses
   - Now adding: External API consumption!

**Next Steps:**
- **Exercise 11**: JWT Authentication
- **Exercise 12**: Roles and Permissions

Good luck! 🌤️
