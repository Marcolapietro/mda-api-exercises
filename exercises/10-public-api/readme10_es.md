# Ejercicio 10: Consumo de APIs Públicas Externas

## Objetivo

Aprender a consumir APIs públicas externas e integrar sus datos en tu propia API FastAPI. Este ejercicio te enseña a trabajar con **múltiples endpoints de API** y a manejar los desafíos reales de integración con APIs.

## Inicio Rápido

```bash
cd exercises/10-public-api
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
copy .env.example .env  # Windows (cp en Linux/Mac); después pon tu clave de OpenWeatherMap en .env
fastapi dev app.py
```

Rellena los huecos (`_____`) de arriba abajo; la app arranca cuando el decorador de `/login` está completo. Los demás huecos (el nombre de la variable de entorno, `create_access_token`, los diccionarios `params`, `client.get`, `200`, `.json()`) solo se usan cuando una petición llega hasta ellos, así que los notarás al probar. La API corre en `http://127.0.0.1:8000`.

---

## Lo Que Aprenderás

El login con JWT (`/register`, `/login`, `/profile`) te lo damos hecho: es una copia de lo que el Ejercicio 11 explica en profundidad, y aquí solo lo consumes. Este ejercicio añade:

1. **Consumir APIs Externas** con la librería `httpx`
2. **Trabajar con Múltiples Endpoints de API** (Geocodificación + Clima)
3. **Gestionar Claves API** y autenticación con servicios de terceros
4. **Manejo de Errores** para fallos de APIs externas
5. **Parámetros de Consulta** para peticiones API flexibles
6. **Mejores Prácticas Modernas** (coordenadas vs nombres de ciudad obsoletos)

---

## El Reto: Construir una API del Clima

Crearás una API FastAPI que:
- Usa la **API de Geocodificación de OpenWeatherMap** para convertir nombres de ciudad en coordenadas
- Usa la **API de Clima Actual de OpenWeatherMap** para obtener datos del clima por coordenadas
- Combina ambas APIs para proporcionar información del clima para cualquier ciudad del mundo

### ¿Por Qué Dos Llamadas API?

**Enfoque Moderno:**
```
Solicitud Usuario: "Obtener clima de París"
    ↓
Paso 1: API de Geocodificación
    Ciudad "París" → Coordenadas (48.8566, 2.3522)
    ↓
Paso 2: API del Clima
    Coordenadas → Datos del Clima
    ↓
Respuesta: {temperatura: 15°C, descripción: "nublado", ...}
```

**¿Por qué no usar directamente nombres de ciudad?**
- Las consultas por nombre de ciudad (`?q=Paris`) están **obsoletas** en OpenWeatherMap
- Múltiples ciudades comparten el mismo nombre (París, Francia vs París, Texas)
- Las coordenadas son **inequívocas** y funcionan globalmente
- La geocodificación proporciona contexto de ubicación adicional (país, estado)

---

## Requisitos Previos

### 1. Obtener una Clave API Gratuita de OpenWeatherMap

**Paso a paso:**

1. Ve a [https://openweathermap.org/](https://openweathermap.org/)
2. Haz clic en "Sign Up" en la esquina superior derecha
3. Crea una cuenta gratuita con tu correo electrónico
4. Verifica tu dirección de correo electrónico
5. Inicia sesión y ve a "API Keys" en tu perfil
6. Copia tu clave API predeterminada O genera una nueva
7. **Espera de 10 minutos a 2 horas** para la activación (normalmente instantánea)

**Ejemplo de Clave API:**
```
a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

### 2. Configurar Tu Clave API

**No pegues nunca la clave en `app.py`**: el código acaba en GitHub y los bots encuentran las claves subidas a repos públicos en minutos. `app.py` la lee de una variable de entorno:
```python
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")
```

Si la variable no está definida, `/weather` responde `503 Service Unavailable`: el problema está en el servidor, no en tu petición.

El sitio más cómodo para ella es un fichero `.env` en la carpeta del ejercicio. Copia la plantilla y pon tu clave en la copia:
```bash
cp .env.example .env     # Linux / macOS
copy .env.example .env   # Windows (CMD o PowerShell)
```
```
OPENWEATHER_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

Al arrancar, `load_dotenv()` (del paquete `python-dotenv`) copia las variables de `.env` al entorno, así que `os.environ.get` las encuentra.

- `.env` está en `.gitignore`, así que tu clave nunca llega a GitHub. `.env.example` solo tiene valores vacíos y **sí** se sube: indica a los demás qué variables tienen que definir.
- `fastapi dev` se reinicia cuando guardas un fichero `.py`, no `.env`: después de editar `.env`, para la app (Ctrl+C) y vuelve a arrancarla.
- `.env` también puede llevar `JWT_SECRET_KEY`, para que los tokens sobrevivan a los reinicios (ver Problema 5).

También puedes definir la variable en el terminal donde ejecutas la app; tiene prioridad sobre `.env`:
```bash
# Linux / macOS
export OPENWEATHER_API_KEY="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

# Windows PowerShell
$env:OPENWEATHER_API_KEY="a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6"

# Windows CMD
set OPENWEATHER_API_KEY=a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6
```

---

## Estructura de la API

### Endpoints de Autenticación (dados; se explican en profundidad en el Ejercicio 11)

| Método | Endpoint | Auth Requerida | Descripción |
|--------|----------|----------------|-------------|
| POST | `/register` | No | Registrar un nuevo usuario |
| POST | `/login` | No | Login con credenciales JSON, obtener JWT |
| GET | `/profile` | JWT | Obtener perfil de usuario |

### Endpoint del Clima (Nuevo en el Ejercicio 10)

| Método | Endpoint | Auth Requerida | Descripción |
|--------|----------|----------------|-------------|
| GET | `/weather?city=NombreCiudad&country=CC` | **No** | Obtener clima de una ciudad |

**¿Por qué `/weather` es público?**
- El foco del ejercicio es **consumir APIs externas**, no autenticación
- Pruebas más simples (no necesitas hacer login primero)
- Caso de uso del mundo real: Widgets de clima públicos

### Cómo funciona JWT en FastAPI (concepto nuevo)

El código del login te lo damos hecho; solo necesitas saber qué hace (el Ejercicio 11 lo explica en profundidad). Usa la librería `PyJWT` directamente:

- `create_access_token(username)` firma un token con `jwt.encode(...)`. Lleva `sub` (el usuario) y `exp` (caduca en 15 minutos).
- `HTTPBearer` lee la cabecera `Authorization: Bearer <token>` y se la pasa a una **dependencia**, `get_current_user`, que la comprueba con `jwt.decode(...)`. Un token ausente, caducado o manipulado responde `401` con la cabecera `WWW-Authenticate: Bearer`. `HTTPBearer(auto_error=False)` nos permite devolver nuestro propio mensaje `401` y la cabecera `WWW-Authenticate` cuando falta la cabecera (por defecto FastAPI responde un `401 Not authenticated` genérico).
- Una ruta se protege pidiendo esa dependencia: `user: Annotated[str, Depends(get_current_user)]`. FastAPI ejecuta `get_current_user` antes que la ruta y pone en `user` el nombre de usuario que devuelve; si el token no es válido, la ruta nunca se ejecuta.
- `/login` recibe las credenciales como **JSON** (no como formulario): el flujo con formulario del tutorial de FastAPI es el password grant de OAuth, que OAuth 2.1 eliminó. Swagger UI (`/docs`) sigue mostrando un botón "Authorize" para el token.

---

## Cómo Funciona: Flujo de API de Dos Pasos

### Paso 1: API de Geocodificación (Ciudad → Coordenadas)

**Petición:**
```
GET https://api.openweathermap.org/geo/1.0/direct?q=Madrid,ES&appid=YOUR_KEY&limit=1
```

**Respuesta:**
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

**Lo que extraes:**
- `lat`: Latitud (40.4165)
- `lon`: Longitud (-3.7026)
- `name`: Nombre oficial de la ciudad
- `country`: Código de país ISO
- `state`: Estado/región (si está disponible)

### Paso 2: API del Clima (Coordenadas → Clima)

**Petición:**
```
GET https://api.openweathermap.org/data/2.5/weather?lat=40.4165&lon=-3.7026&appid=YOUR_KEY&units=metric&lang=en
```

**Respuesta:**
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

**Lo que extraes:**
- `temp`: Temperatura en Celsius
- `feels_like`: Temperatura "sensación térmica"
- `humidity`: Porcentaje de humedad
- `description`: Descripción del clima
- `wind.speed`: Velocidad del viento (m/s)

---

## Guía de Implementación

### TODOs en app.py

Necesitas completar **10 TODOs** (13 huecos `_____`; los dos diccionarios de parámetros tienen varios cada uno).
Los números de línea pueden desplazarse mientras escribes, así que busca `_____`:

#### TODOs de Configuración y Autenticación (en el código JWT dado):
1. `OPENWEATHER_API_KEY` (línea 48): El nombre de la variable de entorno: `OPENWEATHER_API_KEY`
2. `@app._____("/login")` (línea 123): El método HTTP que envía credenciales en un cuerpo: `post`
3. `login()` (línea 136): Crear el token de acceso JWT: `create_access_token(data.username)`

#### TODOs de API de Geocodificación (en `weather()`, paso 1):
4. `geo_params` (línea 192): Rellenar `"q"` con `query` y `"appid"` con `OPENWEATHER_API_KEY`
5. `geo_response` (línea 197): Hacer la petición GET: `client.get(GEOCODING_API_URL, params=geo_params)`
6. `geo_response.status_code` (línea 207): El código de estado que significa éxito: `200`
7. `geo_data` (línea 215): Parsear la respuesta JSON: `geo_response.json()`

#### TODOs de API del Clima (en `weather()`, paso 2):
8. `weather_params` (líneas 248-250): Rellenar `"lat"`, `"lon"` y `"appid"`
9. `weather_response` (línea 258): Hacer la petición GET: `client.get(WEATHER_API_URL, params=weather_params)`
10. `weather_data` (línea 272): Parsear la respuesta JSON: `weather_response.json()`

### Conceptos Clave a Implementar

**1. Construir los parámetros de la petición:**
```python
# API de Geocodificación: GET {GEOCODING_API_URL}?q=...&appid=...&limit=1
geo_params = {"q": query, "appid": OPENWEATHER_API_KEY, "limit": 1}

# API del Clima: GET {WEATHER_API_URL}?lat=...&lon=...&appid=...&units=metric&lang=en
weather_params = {"lat": latitude, "lon": longitude, "appid": OPENWEATHER_API_KEY,
                  "units": "metric", "lang": "en"}
```

**¿Por qué un diccionario `params` y no una URL con f-string?** `httpx` codifica (URL-encode) cada
valor. Con `f"...?q={query}&appid=..."`, un usuario que pida `?city=Paris%26limit%3D50` inyectaría un
parámetro `limit=50` extra en la llamada a OpenWeatherMap, y el espacio de `New York` rompería la URL.
Con `params=`, `Paris&limit=50` se envía como **un solo** valor de `q` (`q=Paris%26limit%3D50`).

**2. Hacer Peticiones HTTP:**
```python
import httpx

# Pon siempre un timeout en las llamadas salientes: sin él, una API lenta bloquea tu worker para siempre
with httpx.Client(timeout=10) as client:
    response = client.get(GEOCODING_API_URL, params=geo_params)
    if response.status_code == 200:
        data = response.json()
        # Procesar datos
    elif response.status_code == 401:
        # NUESTRA clave es incorrecta o aún no está activa (503: el servidor está mal configurado, no el cliente)
        raise HTTPException(status_code=503, detail="Weather service is not configured correctly")
    else:
        # Manejar error (502 Bad Gateway: ha fallado la API externa, no tu cliente)
        raise HTTPException(status_code=502, detail="Geocoding API request failed")
```

**3. Manejo de Errores:**
```python
try:
    response = client.get(GEOCODING_API_URL, params=geo_params)
    data = response.json()
except httpx.HTTPError:
    # Error de red. NO devuelvas str(e) al cliente: el mensaje de la excepción
    # puede incluir la URL completa, y esa URL contiene tu appid (clave API).
    logger.exception("Geocoding API request failed")   # el detalle queda en el log del servidor
    raise HTTPException(status_code=502, detail="Could not connect to Geocoding API")
except (KeyError, IndexError, ValueError):
    # Formato de respuesta inválido
    logger.exception("Invalid response from Geocoding API")
    raise HTTPException(status_code=502, detail="Unexpected response format from Geocoding API")
```

Los errores usan el cuerpo por defecto de FastAPI, `{"detail": "..."}`.

---

## Probando la API

### 0. Probar los Endpoints de Autenticación

`/weather` es público, pero `/profile` necesita un token (las contraseñas necesitan de 8 a 72 caracteres):

> Los comandos siguientes usan `curl` con comillas de `bash`. En **CMD de Windows** usa `example/commands_cmd.txt`, y en **PowerShell** usa `example/commands_powershell.txt` (con `curl.exe` hay que escapar las comillas dentro del JSON como `\"`; si no, el servidor responde `422`).

```bash
curl -X POST -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}' http://127.0.0.1:8000/register
curl -X POST -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}' http://127.0.0.1:8000/login
```

**Respuesta del login:**
```json
{
  "message": "Login successful",
  "access_token": "eyJhbGciOi...",
  "token_type": "bearer"
}
```

Envía el token como `-H "Authorization: Bearer YOUR_TOKEN"`:

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" http://127.0.0.1:8000/profile
# Sin la cabecera: 401 Unauthorized, cabecera WWW-Authenticate: Bearer
```

### 1. Probar Sin Clave API (Debería Fallar)

```bash
curl -i "http://127.0.0.1:8000/weather?city=Madrid"
```

**Respuesta Esperada (503):**
```json
{
  "detail": "OpenWeatherMap API key not configured: set OPENWEATHER_API_KEY in the .env file (free key at https://openweathermap.org/api)"
}
```

### 2. Probar Con Clave API - Madrid

```bash
curl "http://127.0.0.1:8000/weather?city=Madrid"
```

**Respuesta Esperada:**
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

### 3. Probar Diferentes Ciudades

```bash
# París, Francia
curl "http://127.0.0.1:8000/weather?city=Paris&country=FR"

# Londres, Reino Unido
curl "http://127.0.0.1:8000/weather?city=London&country=GB"

# Nueva York, EE.UU. (el espacio se codifica como %20)
curl "http://127.0.0.1:8000/weather?city=New%20York&country=US"

# Tokio, Japón
curl "http://127.0.0.1:8000/weather?city=Tokyo&country=JP"
```

**Pon siempre entre comillas las URLs que contienen `&`.** Sin comillas, bash interpreta `&` como
"ejecutar en segundo plano" y pierde `country=...`; PowerShell no puede parsearlo; en CMD hay que
escaparlo como `^&`.

**Espacios:** un espacio literal no es válido en una URL, así que las comillas solas no bastan
(`"...city=New York..."` falla). Codifícalo como `%20` (arriba) o deja que curl lo codifique:
```bash
curl -G "http://127.0.0.1:8000/weather" --data-urlencode "city=New York" --data-urlencode "country=US"
```

**Windows PowerShell 5.1:** `curl` es un alias de `Invoke-WebRequest`; usa `curl.exe` para ejecutar el curl real.

### 4. Probar Nombres de Ciudad Ambiguos

**Sin código de país:**
```bash
curl "http://127.0.0.1:8000/weather?city=Paris"
# Retorna: París, Francia (más común)
```

**Con código de país:**
```bash
curl "http://127.0.0.1:8000/weather?city=Paris&country=US"
# Retorna: París, Texas, EE.UU.
```

### 5. Probar Ciudad Inválida (Debería Fallar)

```bash
curl "http://127.0.0.1:8000/weather?city=InvalidCityXYZ"
```

**Respuesta Esperada (404):**
```json
{
  "detail": "Could not find coordinates for city: InvalidCityXYZ. Try adding a country code, e.g., ?city=Paris&country=FR"
}
```

### 6. Probar Sin Ciudad (Debería Fallar)

`city` es obligatorio: `Query(min_length=1)` sin valor por defecto. Si falta, o va vacío (`?city=`), FastAPI responde `422 Unprocessable Content` antes de ejecutar tu código, así que nunca se llama a OpenWeatherMap (ni siquiera cuando falta la clave).

```bash
curl "http://127.0.0.1:8000/weather"
```

**Respuesta Esperada (422):**
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

Con `?city=` el `type` del error es `string_too_short` en vez de `missing`.

---

## Entendiendo la Librería `httpx`

`httpx` se instala junto con `fastapi[standard]`, y sus llamadas son iguales a las de `requests`.

Nota: los ejemplos de abajo usan `httpx.get(...)` a nivel de módulo por brevedad; la solución usa `httpx.Client(timeout=10)` para sus dos llamadas, que reutiliza una sola conexión.

### Uso Básico

```python
import httpx

# Petición GET
response = httpx.get('https://api.example.com/data')

# Verificar estado
if response.status_code == 200:
    print("¡Éxito!")

# Parsear JSON
data = response.json()

# Acceder a datos
print(data['key'])
```

### Con Parámetros de Consulta

**Método 1: Diccionario de parámetros (usa este)**
```python
params = {'param1': value1, 'param2': value2}
response = httpx.get('https://api.example.com/data', params=params, timeout=10)
```
`httpx` codifica cada valor, así que espacios, `&`, `=` o `#` en la entrada del usuario no pueden
romper la URL ni añadir parámetros extra.

**Método 2: String de URL (evítalo con entrada del usuario)**
```python
# ❌ value1 no se codifica: "a&admin=1" se convierte en un parámetro extra
url = f'https://api.example.com/data?param1={value1}&param2={value2}'
response = httpx.get(url, timeout=10)
```

### Manejo de Errores

```python
try:
    response = httpx.get(url, timeout=5)
    response.raise_for_status()  # Lanza excepción para 4xx/5xx
    data = response.json()
except httpx.TimeoutException:
    print("Tiempo de espera agotado")
except httpx.ConnectError:
    print("Error de red")
except httpx.HTTPStatusError as e:
    print(f"Error HTTP: {e}")
except ValueError:
    print("Respuesta JSON inválida")
```

---

## Problemas Comunes y Soluciones

### Problema 1: Clave API No Activada

**Síntoma** (OpenWeatherMap responde `401 Invalid API key`; tu API responde `503`, porque una clave incorrecta es un error de configuración del servidor, no del cliente; el motivo está en el log del servidor):
```json
{
  "detail": "Weather service is not configured correctly"
}
```

**Solución:**
- Espera de 10 minutos a 2 horas para la activación
- Verifica que copiaste la clave completa en `.env` (sin espacios ni comillas alrededor), y reinicia la app tras editar `.env`
- Comprueba que estás usando la clave correcta de tu cuenta de OpenWeatherMap

### Problema 2: Ciudad No Encontrada

**Síntoma:**
```json
{
  "detail": "Could not find coordinates for city: Madrd. Try adding a country code, e.g., ?city=Paris&country=FR"
}
```

**Solución:**
- Verifica la ortografía: "Madrd" → "Madrid"
- Añade código de país para desambiguación
- Usa nombres de ciudad en inglés (ej: "Munich" no "München")

### Problema 3: Timeout de Red

**Síntoma** (502 Bad Gateway):
```json
{
  "detail": "Could not connect to Geocoding API"
}
```

**Solución:**
- Verifica la conexión a internet
- Comprueba que la API de OpenWeatherMap no esté caída: [status.openweathermap.org](https://status.openweathermap.org/)
- Intenta de nuevo en unos segundos

### Problema 4: Límite de Tasa

**Límites del nivel gratuito:**
- 60 llamadas por minuto
- 1,000,000 llamadas por mes

**Si alcanzas el límite** (OpenWeatherMap responde 429; tu API lo informa como un 502):
```json
{
  "detail": "Geocoding API request failed (upstream status 429)"
}
```

**Solución:**
- Espera 60 segundos
- Implementa caché (objetivo adicional)
- Actualiza a nivel de pago si es necesario

### Problema 5: El Token Deja de Valer (401) Tras Editar `app.py`

`fastapi dev` reinicia la app cada vez que guardas un fichero. El reinicio vacía el diccionario `users` en memoria y, si no has definido `JWT_SECRET_KEY`, genera un secreto aleatorio nuevo, así que todos los tokens emitidos antes se rechazan con `401`.

**Solución:**
- Regístrate y haz login de nuevo tras cada cambio, y usa el token nuevo
- O define `JWT_SECRET_KEY` en `.env` (genera uno con `python -c "import secrets; print(secrets.token_hex(32))"`): los tokens sobreviven al reinicio (esta API solo comprueba el token, no el diccionario `users`), pero tendrás que registrarte otra vez antes de poder hacer login

---

## Criterios de Aceptación

Tu implementación debería:

- ✅ Llamar exitosamente a la API de Geocodificación de OpenWeatherMap
- ✅ Llamar exitosamente a la API de Clima Actual de OpenWeatherMap
- ✅ Manejar validación de clave API
- ✅ Manejar errores de ciudad no encontrada
- ✅ Manejar errores de red con gracia
- ✅ Parsear respuestas JSON correctamente
- ✅ Retornar datos de clima estructurados
- ✅ Exigir el parámetro `city` (422 si falta o va vacío)
- ✅ Soportar parámetro opcional de código de país
- ✅ Usar HTTPS (no HTTP) para llamadas API
- ✅ Usar coordenadas (no consultas por nombre de ciudad obsoletas)

---

## Objetivos Adicionales

Una vez completes la implementación básica:

### 1. Añadir Caché de Respuestas

Evitar llamadas API repetidas para la misma ciudad:

```python
from datetime import datetime, timedelta

weather_cache = {}  # {ciudad: {datos: {...}, expira: timestamp}}

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

### 2. Añadir Más Endpoints del Clima

```python
# Pronóstico de 5 días
@app.get("/weather/forecast")
def forecast():
    # Usar: https://api.openweathermap.org/data/2.5/forecast
    pass

# Calidad del aire
@app.get("/weather/air-quality")
def air_quality():
    # Usar: https://api.openweathermap.org/data/2.5/air_pollution
    pass
```

### 3. Añadir Iconos del Clima

Retornar URLs de iconos para visualización en frontend:

```python
weather_info['weather']['icon_url'] = f"https://openweathermap.org/img/wn/{icon_code}@2x.png"
```

### 4. Añadir Conversión de Unidades de Temperatura

```python
@app.get("/weather")
def weather(
    city: Annotated[str, Query(min_length=1)],  # los parámetros obligatorios van primero
    units: Annotated[str, Query()] = "metric",  # metric, imperial, standard
):
    # Usar en llamada API: "units": units
    ...
```

### 5. Proteger Endpoint del Clima con JWT

Hacer que el endpoint del clima requiera autenticación, con la misma dependencia que usa `/profile`:

```python
@app.get("/weather")
def weather(
    user: Annotated[str, Depends(get_current_user)],  # Añadir este parámetro
    city: Annotated[str, Query(min_length=1)],
):
    # Rastrear consultas de clima del usuario para analíticas
    ...
```

---

## Entendiendo la Obsolescencia de APIs

**⚠️ Nota Importante Sobre Cambios en OpenWeatherMap**

OpenWeatherMap ha marcado como obsoletas las consultas por nombre de ciudad:

**Forma Antigua (Obsoleta, pero aún funciona):**
```python
# Consulta directa por nombre de ciudad - NO RECOMENDADA
httpx.get('https://api.openweathermap.org/data/2.5/weather',
          params={'q': city, 'appid': api_key}, timeout=10)
```

**Problemas:**
- Ya no se mantiene activamente
- Correcciones de bugs no garantizadas
- Puede eliminarse en versiones futuras
- Ambigua para ciudades con el mismo nombre

**Forma Nueva (Recomendada):**
```python
# Paso 1: Geocodificar
httpx.get('https://api.openweathermap.org/geo/1.0/direct',
          params={'q': city, 'appid': api_key, 'limit': 1}, timeout=10)
# Obtener coordenadas

# Paso 2: Clima por coordenadas
httpx.get('https://api.openweathermap.org/data/2.5/weather',
          params={'lat': lat, 'lon': lon, 'appid': api_key}, timeout=10)
```

**Beneficios:**
- Mantenida activamente
- Resultados inequívocos
- Mejores mensajes de error
- A prueba de futuro
- Contexto de ubicación adicional

**¡Este ejercicio enseña la forma NUEVA!**

---

## Recursos Adicionales

### Documentación de OpenWeatherMap

- [API de Clima Actual](https://openweathermap.org/current)
- [API de Geocodificación](https://openweathermap.org/api/geocoding-api)
- [Guía de Clave API](https://openweathermap.org/appid)
- [FAQ](https://openweathermap.org/faq)

### Librería httpx de Python

- [Documentación Oficial](https://www.python-httpx.org/)
- [Guía de Inicio Rápido](https://www.python-httpx.org/quickstart/)

### Códigos de País ISO

- [Códigos ISO 3166-1 alpha-2](https://en.wikipedia.org/wiki/ISO_3166-1_alpha-2)
- Ejemplos: ES (España), FR (Francia), US (Estados Unidos), GB (Reino Unido)

---

## Resumen

**Conclusiones Clave:**

1. **Consumo de APIs Externas**
   - Usa la librería `httpx` para llamadas HTTP
   - Parsea respuestas JSON con `.json()`
   - Maneja errores con gracia

2. **Flujos de Trabajo de API Multipaso**
   - Algunas tareas requieren múltiples llamadas API
   - Geocodificación → Coordenadas → Clima
   - Encadena respuestas juntas

3. **Mejores Prácticas de API**
   - Usa HTTPS, no HTTP
   - Sigue recomendaciones actuales (coordenadas vs nombres de ciudad)
   - Valida claves API antes de hacer peticiones
   - Maneja límites de tasa y errores

4. **Integración del Mundo Real**
   - Claves API y autenticación de terceros
   - Parámetros de consulta para peticiones flexibles
   - Respuestas de error estructuradas
   - Extracción comprehensiva de datos

5. **Construyendo sobre Conocimiento Previo**
   - Autenticación JWT (dada aquí; el Ejercicio 11 la explica en profundidad)
   - Enrutamiento FastAPI y manejo de errores
   - Respuestas JSON
   - ¡Ahora añadiendo: Consumo de APIs externas!

**Próximos Pasos:**
- **Ejercicio 11**: Autenticación JWT
- **Ejercicio 12**: Roles y Permisos

¡Buena suerte! 🌤️
