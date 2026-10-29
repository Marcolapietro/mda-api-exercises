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
fastapi dev app.py
```

Rellena los huecos (`_____`) de arriba abajo; la app arranca cuando el decorador de `/login` y el `Depends(...)` de `/weather` están completos. Los demás huecos (el nombre de la variable de entorno, `create_access_token`, los diccionarios `params`, `client.get`, `200`, `.json()`) solo se usan cuando una petición llega hasta ellos, así que los notarás al probar. La API corre en `http://127.0.0.1:8000`.

---

## Lo Que Aprenderás

Este ejercicio se basa en el Ejercicio 11 (autenticación JWT) y añade:

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

**Enfoque Moderno (2025):**
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

Define la variable en el terminal donde ejecutas la app:
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

### Endpoints de Autenticación (del Ejercicio 11)

| Método | Endpoint | Auth Requerida | Descripción |
|--------|----------|----------------|-------------|
| POST | `/register` | No | Registrar un nuevo usuario |
| POST | `/login` | No | Login con credenciales JSON, obtener JWT |
| GET | `/profile` | JWT | Obtener perfil de usuario |

### Endpoint del Clima (Nuevo en el Ejercicio 10)

| Método | Endpoint | Auth Requerida | Descripción |
|--------|----------|----------------|-------------|
| GET | `/weather?city=NombreCiudad&country=CC` | **JWT** | Obtener clima de una ciudad |

**¿Por qué `/weather` está protegido?**
- Cada llamada a `/weather` gasta tu cuota de OpenWeatherMap (60 llamadas por minuto en el nivel gratuito)
- Sin token, cualquiera podría agotarla: una petición sin él responde `401`
- El foco sigue siendo **consumir APIs externas**: haces login una vez y reutilizas el token

### Cómo funciona JWT en FastAPI (concepto nuevo)

FastAPI no tiene un decorador `@jwt_required()`; usamos la librería `PyJWT` directamente:

- `create_access_token(username)` firma un token con `jwt.encode(...)`. Lleva `sub` (el usuario) y `exp` (caduca en 15 minutos).
- `HTTPBearer` lee la cabecera `Authorization: Bearer <token>` y se la pasa a una **dependencia**, `get_current_user`, que la comprueba con `jwt.decode(...)`. Un token ausente, caducado o manipulado responde `401` con la cabecera `WWW-Authenticate: Bearer`. `HTTPBearer(auto_error=False)` existe porque por defecto FastAPI respondería 403 cuando falta la cabecera.
- Una ruta se protege pidiendo esa dependencia: `user: Annotated[str, Depends(get_current_user)]`. Sustituye a `@jwt_required()`, y `user` sustituye a `get_jwt_identity()`.
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

Necesitas completar **10 TODOs** (14 huecos `_____`; los dos diccionarios de parámetros tienen varios cada uno).
Los números de línea pueden desplazarse mientras escribes, así que busca `_____`:

#### TODOs de Configuración y Autenticación (del Ejercicio 11):
1. `OPENWEATHER_API_KEY` (línea 44): El nombre de la variable de entorno: `OPENWEATHER_API_KEY`
2. `@app._____("/login")` (línea 119): El método HTTP que envía credenciales en un cuerpo: `post`
3. `login()` (línea 132): Crear el token de acceso JWT: `create_access_token(data.username)`
4. `weather()` (línea 150): Exigir un token válido: `Depends(get_current_user)`

#### TODOs de API de Geocodificación (en `weather()`, paso 1):
5. `geo_params` (línea 188): Rellenar `"q"` con `query` y `"appid"` con `OPENWEATHER_API_KEY`
6. `geo_response` (línea 193): Hacer la petición GET: `client.get(GEOCODING_API_URL, params=geo_params)`
7. `geo_response.status_code` (línea 198): El código de estado que significa éxito: `200`
8. `geo_data` (línea 206): Parsear la respuesta JSON: `geo_response.json()`

#### TODOs de API del Clima (en `weather()`, paso 2):
9. `weather_params` (líneas 239-241): Rellenar `"lat"`, `"lon"` y `"appid"`
10. `weather_response` (línea 249) y `weather_data` (línea 259): Hacer la petición GET, `client.get(WEATHER_API_URL, params=weather_params)`, y parsearla con `weather_response.json()`

### Conceptos Clave a Implementar

**1. Construir los parámetros de la petición:**
```python
# API de Geocodificación: GET {GEOCODING_API_URL}?q=...&appid=...&limit=1
geo_params = {"q": query, "appid": OPENWEATHER_API_KEY, "limit": 1}

# API del Clima: GET {WEATHER_API_URL}?lat=...&lon=...&appid=...&units=metric&lang=en
weather_params = {"lat": latitude, "lon": longitude, "appid": OPENWEATHER_API_KEY,
                  "units": "metric", "lang": "en"}   # "es" para descripciones en español
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

### 0. Registrarse, Hacer Login y Guardar el Token

`/weather` está protegido, así que primero consigue un token (las contraseñas necesitan de 8 a 72 caracteres):

```bash
curl -X POST -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}' http://127.0.0.1:8000/register
curl -X POST -H "Content-Type: application/json" -d '{"username":"alice","password":"secret123"}' http://127.0.0.1:8000/login
```

La respuesta del login es `{"access_token": "...", "token_type": "bearer"}`. Envía el token en cada llamada como `-H "Authorization: Bearer YOUR_TOKEN"` (los ejemplos de abajo lo usan). Sin él:

```bash
curl -i "http://127.0.0.1:8000/weather?city=Madrid"
# 401 Unauthorized, cabecera: WWW-Authenticate: Bearer
```

### 1. Probar Sin Clave API (Debería Fallar)

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather?city=Madrid"
```

**Respuesta Esperada (503):**
```json
{
  "detail": "OpenWeatherMap API key not configured: set the OPENWEATHER_API_KEY environment variable (free key at https://openweathermap.org/api)"
}
```

### 2. Probar Con Clave API - Ciudad Predeterminada

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather"
```

**Respuesta Esperada (Madrid, predeterminada):**
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
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather?city=Paris&country=FR"

# Londres, Reino Unido
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather?city=London&country=GB"

# Nueva York, EE.UU. (el espacio se codifica como %20)
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather?city=New%20York&country=US"

# Tokio, Japón
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather?city=Tokyo&country=JP"
```

**Pon siempre entre comillas las URLs que contienen `&`.** Sin comillas, bash interpreta `&` como
"ejecutar en segundo plano" y pierde `country=...`; PowerShell no puede parsearlo; en CMD hay que
escaparlo como `^&`.

**Espacios:** un espacio literal no es válido en una URL, así que las comillas solas no bastan
(`"...city=New York..."` falla). Codifícalo como `%20` (arriba) o deja que curl lo codifique:
```bash
curl -G -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather" --data-urlencode "city=New York" --data-urlencode "country=US"
```

**Windows PowerShell 5.1:** `curl` es un alias de `Invoke-WebRequest`; usa `curl.exe` para ejecutar el curl real.

### 4. Probar Nombres de Ciudad Ambiguos

**Sin código de país:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather?city=Paris"
# Retorna: París, Francia (más común)
```

**Con código de país:**
```bash
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather?city=Paris&country=US"
# Retorna: París, Texas, EE.UU.
```

### 5. Probar Ciudad Inválida (Debería Fallar)

```bash
curl -H "Authorization: Bearer YOUR_TOKEN" "http://127.0.0.1:8000/weather?city=InvalidCityXYZ"
```

**Respuesta Esperada (404):**
```json
{
  "detail": "Could not find coordinates for city: InvalidCityXYZ. Try adding a country code, e.g., ?city=Paris&country=FR"
}
```

---

## Entendiendo la Librería `httpx`

`httpx` se instala junto con `fastapi[standard]`, y sus llamadas son iguales a las de `requests`.

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

**Síntoma:**
```json
{
  "cod": 401,
  "message": "Invalid API key"
}
```

**Solución:**
- Espera de 10 minutos a 2 horas para la activación
- Verifica que copiaste la clave completa (sin espacios)
- Comprueba que estás usando la clave correcta de tu cuenta de OpenWeatherMap

### Problema 2: Ciudad No Encontrada

**Síntoma:**
```json
{
  "error": "City not found",
  "message": "Could not find coordinates for city: Madrd"
}
```

**Solución:**
- Verifica la ortografía: "Madrd" → "Madrid"
- Añade código de país para desambiguación
- Usa nombres de ciudad en inglés (ej: "Munich" no "München")

### Problema 3: Timeout de Red

**Síntoma:**
```
Error: Could not connect to Geocoding API
```

**Solución:**
- Verifica la conexión a internet
- Comprueba que la API de OpenWeatherMap no esté caída: [status.openweathermap.org](https://status.openweathermap.org/)
- Intenta de nuevo en unos segundos

### Problema 4: Límite de Tasa

**Límites del nivel gratuito:**
- 60 llamadas por minuto
- 1,000,000 llamadas por mes

**Si alcanzas el límite:**
```json
{
  "cod": 429,
  "message": "Too many requests"
}
```

**Solución:**
- Espera 60 segundos
- Implementa caché (objetivo adicional)
- Actualiza a nivel de pago si es necesario

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
    user: Annotated[str, Depends(get_current_user)],
    units: Annotated[str, Query()] = "metric",  # metric, imperial, standard
    city: Annotated[str, Query()] = "Madrid",
):
    # Usar en llamada API: "units": units
    ...
```

### 5. Rastrear las Consultas de Cada Usuario

`/weather` ya sabe quién llama (`user`). Cuenta las consultas por usuario:

```python
query_counts: dict[str, int] = {}

# dentro de weather(), después de comprobar el token
query_counts[user] = query_counts.get(user, 0) + 1
```

Exponlo en un nuevo endpoint protegido `GET /weather/stats`.

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
   - Autenticación JWT (Ejercicio 11)
   - Enrutamiento FastAPI y manejo de errores
   - Respuestas JSON
   - ¡Ahora añadiendo: Consumo de APIs externas!

**Próximos Pasos:**
- **Ejercicio 05**: Operaciones CRUD (Crear, Leer, Actualizar, Eliminar)
- **Ejercicio 06**: Paginación de API
- **Ejercicio 12**: Control de Acceso Basado en Roles (RBAC)

¡Buena suerte! 🌤️
