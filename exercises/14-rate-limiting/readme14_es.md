# Ejercicio 14: Limitación de Tasa y Seguridad de API

## Inicio Rápido

```bash
cd exercises/14-rate-limiting
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
fastapi dev app.py
```

## Objetivo

Aprende a proteger tu API del abuso usando **limitación de tasa** con slowapi:

- **Prevenir Abuso**: Protege tu API de usuarios maliciosos y bots
- **Gestión de Recursos**: Controla la carga del servidor y previene el agotamiento de recursos
- **Uso Justo**: Asegura que todos los usuarios tengan acceso equitativo a tu API
- **Seguridad**: Previene ataques de fuerza bruta en endpoints de autenticación
- **Control de Costos**: Limita operaciones costosas (consultas de base de datos, llamadas a API externas)

## ¿Qué es la Limitación de Tasa?

La **limitación de tasa** restringe el número de solicitudes que un cliente puede hacer a tu API dentro de una ventana de tiempo específica.

**Ejemplos del mundo real** (en el momento de escribir esto, consulta la documentación de cada proveedor):
- **Twitter API**: 300 solicitudes por 15 minutos (nivel gratuito)
- **GitHub API**: 60 solicitudes por hora (no autenticado), 5000/hora (autenticado)
- **Stripe API**: 100 solicitudes por segundo
- **OpenAI API**: Varía según el plan y endpoint

**Por qué importa la limitación de tasa:**
1. **Previene ataques DoS**: Los usuarios maliciosos no pueden saturar tu servidor
2. **Detiene fuerza bruta**: Limita los intentos de adivinación de contraseñas
3. **Controla costos**: Previene que operaciones costosas agoten recursos
4. **Asegura disponibilidad**: Protege la API para todos los usuarios legítimos
5. **Cumplimiento**: Algunas regulaciones requieren limitación de tasa (ej., APIs de pago)

## Prerrequisitos

Antes de comenzar este ejercicio, completa:
- **Ejercicio 11**: Autenticación JWT (este ejercicio se basa en conceptos JWT)
- **Ejercicio 04**: Fundamentos de API (comprensión de códigos de estado HTTP)

## Lo que Aprenderás

1. **Biblioteca slowapi**: Limitación de tasa para FastAPI (un port del popular Flask-Limiter)
2. **Estrategias de limitación de tasa**:
   - Por dirección IP (predeterminado)
   - Por usuario (solicitudes autenticadas)
   - Por endpoint (límites diferentes para diferentes rutas)
3. **Código de estado HTTP 429**: "Demasiadas Solicitudes"
4. **Cabeceras de límite de tasa**: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `Retry-After`
5. **Patrones de decoradores**: `@limiter.limit()`, `@limiter.exempt`
6. **Manejadores de errores personalizados**: Mensajes amigables de límite de tasa
7. **Mejores prácticas de seguridad**: Proteger endpoints sensibles

## Instalación

El ejercicio requiere estas dependencias (ya en `requirements.txt`):

```txt
fastapi[standard]==0.162.0
bcrypt==5.0.0
PyJWT==2.15.1
slowapi==0.1.10
```

Instálalas:
```bash
pip install -r requirements.txt
```

## Cómo Funciona slowapi

### Concepto Básico

```python
from slowapi import Limiter
from slowapi.middleware import SlowAPIMiddleware
from slowapi.util import get_remote_address

limiter = Limiter(
    key_func=get_remote_address,  # Identificar clientes por dirección IP
    default_limits=["200/day", "50/hour"]  # Aplicado a las rutas sin límite propio
)
app.state.limiter = limiter  # slowapi busca el limiter aquí
app.add_middleware(SlowAPIMiddleware)  # aplica los límites predeterminados a todas las rutas
```

**Componentes clave:**
- `key_func`: Cómo identificar clientes (dirección IP, ID de usuario, clave API, etc.)
- `default_limits`: Límites de respaldo aplicados a todas las rutas a menos que se sobrescriban
- `storage_uri`: Dónde almacenar datos de límite de tasa (memoria, Redis, etc.)

**Dos cosas que slowapi necesita de tus funciones de ruta** (`app.py` ya las tiene):
- Toda ruta con `@limiter.limit(...)` debe recibir un parámetro `request: Request`: slowapi lee de él la dirección del cliente.
- Una ruta que devuelve un dict también debe recibir `response: Response`: es el objeto al que slowapi añade las cabeceras `X-RateLimit-*` en una llamada exitosa (en un `429` las añade el manejador de errores).

### Sintaxis de Límite de Tasa

slowapi usa un formato de cadena corto, `<cantidad>/<periodo>`:

```python
"5/minute"      # 5 solicitudes por minuto
"100/hour"      # 100 solicitudes por hora
"1000/day"      # 1000 solicitudes por día
"1/second"      # 1 solicitud por segundo
"5 per minute"  # Sintaxis alternativa (igual que "5/minute")
```

**Puedes combinar límites:**
```python
@limiter.limit("5/minute;100/hour;1000/day")
```

Esto aplica TODOS los límites simultáneamente - el que se alcance primero activa el límite de tasa.

## Estructura del Ejercicio

El `app.py` proporcionado tiene una API parcialmente completa con TODOs:

- `app.py` - Archivo de inicio con espacios en blanco para completar
- `example/example14.py` - Solución de referencia completa
- `requirements.txt` - Dependencias
- `readme14_es.md` - Este archivo de instrucciones

Completa los espacios en blanco de arriba hacia abajo. La app no arranca hasta que completes `key_func`, `default_limits` y los cuatro `@limiter.limit(_____)` (Python los evalúa al cargar el archivo). El último TODO, el `@limiter.exempt` que falta, no impide que la app arranque, pero mientras no lo agregues `/api/unlimited` queda limitado por los límites predeterminados.

## Parte 1: Comprendiendo la Estructura del Código (10 minutos)

### Paso 1.1: Revisar la Configuración

Abre `app.py` y examina la configuración:

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

# TODO: Initialize slowapi
# Hint: limiter = Limiter(key_func=get_remote_address, default_limits=["200/day", "50/hour"])
limiter = Limiter(
    key_func=_____,  # TODO: What function determines who is making the request?
    default_limits=_____,  # TODO: Set default limits (e.g., ["200/day", "50/hour"])
    headers_enabled=True,  # send X-RateLimit-* and Retry-After headers
    storage_uri="memory://",  # in-memory storage (use Redis in production)
)
```

**Tu tarea:**
1. Completa `key_func` con `get_remote_address` (rastrea por dirección IP)
2. Completa `default_limits` con `["200/day", "50/hour"]`

**¿Por qué estos valores predeterminados?**
- `200/day`: Previene que una sola IP haga miles de solicitudes
- `50/hour`: Control más granular dentro del límite diario
- Ambos límites se aplican - alcanzar cualquiera activa la limitación de tasa

### Paso 1.2: Entender la Función Clave

El parámetro `key_func` determina **quién** está haciendo la solicitud.

**Estrategias comunes:**

```python
# Estrategia 1: Por dirección IP (simple, funciona para solicitudes no autenticadas)
from slowapi.util import get_remote_address
key_func=get_remote_address

# Estrategia 2: Por usuario autenticado (requiere JWT/sesión)
def get_user_id(request: Request) -> str:
    try:
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])["sub"]  # Nombre de usuario JWT
    except jwt.InvalidTokenError:
        return get_remote_address(request)  # Recurrir a IP si no está autenticado

key_func=get_user_id
```

Para este ejercicio, usaremos **dirección IP** ya que es más simple y funciona tanto para endpoints autenticados como no autenticados.

## Parte 2: Implementando Límites de Tasa (30 minutos)

### Tarea 2.1: Proteger Endpoint de Registro

Los endpoints de registro son a menudo objetivo de bots que crean cuentas de spam.

**Encuentra este código en `app.py`:**

```python
@app.post("/register", status_code=201)
# TODO: Add rate limit to prevent spam registrations
# Hint: @limiter.limit("5/hour")
@limiter.limit(_____)
def register(request: Request, response: Response, data: UserCreate) -> dict[str, str]:
    # ... lógica de registro
```

**Tu tarea:**
Completa el espacio en blanco con: `"5/hour"`

`@limiter.limit` va justo debajo del decorador de la ruta, y la función debe recibir `request: Request`.

**¿Por qué 5 por hora?**
- Los usuarios legítimos rara vez necesitan crear múltiples cuentas
- Previene el registro automático de bots
- Aún permite a un usuario reintentar si comete un error

**Prueba:**
```bash
# Intenta registrarte 6 veces en rápida sucesión - la sexta debería fallar
for i in {1..6}; do
  curl -X POST http://127.0.0.1:8000/register \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"user$i\",\"password\":\"pass1234\"}"
  echo ""
done
```

Windows PowerShell (5.1 y 7):
```powershell
for ($i = 1; $i -le 6; $i++) {
  $body = @{ username = "user$i"; password = "pass1234" } | ConvertTo-Json
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Method Post -Uri "http://127.0.0.1:8000/register" `
      -ContentType "application/json" -Body $body
    Write-Host "user$i -> $($r.StatusCode)"
  } catch {
    # Windows PowerShell 5.1 lanza una excepción con cualquier estado no 2xx: lee el código del error
    $resp = $_.Exception.Response
    if (-not $resp) { throw }  # no hubo respuesta HTTP (¿está la app en marcha?)
    Write-Host "user$i -> $($resp.StatusCode.value__)"
  }
}
```

**Esperado:** Las primeras 5 tienen éxito, la sexta devuelve HTTP 429 (Límite de tasa excedido)

> Esta prueba agota los 5 registros de la hora para tu IP. Reinicia la app antes de la Tarea 3.2, o sus registros también devolverán 429.

### Tarea 2.2: Proteger Endpoint de Login

Los endpoints de login son objetivos principales para **ataques de fuerza bruta** (probar muchas contraseñas).

**Encuentra este código:**

```python
@app.post("/login")
# TODO: Add rate limit to prevent brute force attacks
# Hint: @limiter.limit("10/minute")
@limiter.limit(_____)
def login(request: Request, response: Response, data: Credentials) -> dict[str, str]:
    # ... lógica de login
```

**Tu tarea:**
Completa con: `"10/minute"`

**¿Por qué 10 por minuto?**
- Permite a usuarios legítimos reintentar contraseñas incorrectas
- Previene adivinación automática de contraseñas
- Estándar de la industria para endpoints de autenticación

**Comparación del mundo real** (en el momento de escribir esto, consulta la documentación de cada proveedor):
- **GitHub**: 5 intentos fallidos activan CAPTCHA
- **AWS**: Ralentiza después de 5 intentos fallidos
- **Google**: Usa limitación de tasa adaptativa (ralentiza después de fallas)

### Tarea 2.3: Endpoint de API General

La mayoría de los endpoints de API necesitan limitación de tasa moderada.

**Encuentra este código:**

```python
@app.get("/api/data")
# TODO: Add rate limit for general API usage
# Hint: @limiter.limit("20/minute")
@limiter.limit(_____)
def get_data(
    request: Request,
    response: Response,
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict:
    # ... lógica de recuperación de datos
```

**Tu tarea:**
Completa con: `"20/minute"`

**¿Por qué 20 por minuto?**
- Permite uso normal de la aplicación
- Previene que un solo usuario sature el servidor
- Equilibra usabilidad con protección

### Tarea 2.4: Operaciones Costosas

Algunos endpoints consumen **muchos recursos** (consultas complejas de base de datos, llamadas a API externas, procesamiento de IA).

**Encuentra este código:**

```python
@app.get("/api/search")
# TODO: Add strict rate limit for expensive operations
# Hint: @limiter.limit("5/minute")
@limiter.limit(_____)
def search(
    request: Request,
    response: Response,
    q: Annotated[str, Query(min_length=1)],
    creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)],
) -> dict:
    # ... operación de búsqueda costosa
```

**Tu tarea:**
Completa con: `"5/minute"`

**¿Por qué límites más estrictos?**
- La búsqueda a menudo involucra escaneos de base de datos o llamadas a API externas
- Previene el agotamiento de recursos
- Fomenta el almacenamiento en caché eficiente del lado del cliente

**Ejemplos reales** (en el momento de escribir esto, consulta la documentación de cada proveedor):
- **Algolia Search**: 10,000 solicitudes/mes (nivel gratuito)
- **Elasticsearch**: A menudo limitado a 5-10 búsquedas concurrentes
- **OpenAI GPT-4**: 3 solicitudes/minuto (nivel gratuito)

### Tarea 2.5: Endpoints Exentos

Algunos endpoints **nunca** deberían tener límite de tasa.

**Encuentra este código:**

```python
@app.get("/api/unlimited")
# TODO: Exempt this endpoint from rate limiting by adding the @limiter.exempt decorator above this line
def unlimited(creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> dict[str, str]:
    # ... operación crítica
```

**Tu tarea:**
Agrega: `@limiter.exempt`

**Cuándo exentar endpoints:**
- Comprobaciones de salud (los sistemas de monitoreo necesitan acceso confiable)
- Operaciones de emergencia/seguridad críticas (ej., "eliminar mi cuenta")
- Comunicación interna entre microservicios (usa autenticación en su lugar)
- Webhooks de fuentes confiables

**Advertencia:** Usa las exenciones con moderación - ¡incluso los endpoints "ilimitados" pueden ser abusados!

## Parte 3: Probando Límites de Tasa (30 minutos)

### Tarea 3.1: Ejecutar la Aplicación

```bash
cd exercises/14-rate-limiting
fastapi dev app.py
```

Deberías ver el servidor arrancar en `http://127.0.0.1:8000`. Los endpoints y sus límites:

```
  POST   /register          - Registrar usuario (5/hour)
  POST   /login             - Login (10/minute)
  GET    /api/data          - Obtener datos (20/minute)
  GET    /api/search?q=...  - Búsqueda (5/minute)
  GET    /api/unlimited     - Sin límite
  GET    /api/stats         - Estadísticas (10/minute)
  GET    /health            - Health check (sin límite)
```

Límites predeterminados para cualquier otra ruta: 200/day y 50/hour. Swagger UI está en `http://127.0.0.1:8000/docs`. `/docs` y
`/openapi.json` también son "otras rutas", así que consumen ese cupo predeterminado de 50/hour (Swagger UI pide
`/openapi.json` en cada recarga): recarga `/docs` unas 50 veces en una hora y responderá 429.

### Tarea 3.2: Probar Límite de Tasa de Registro

> **¿Ya ejecutaste la prueba de la Tarea 2.1?** Esos 6 intentos agotaron los 5 registros de esta hora para tu IP, así que el Paso 1 de abajo devolvería 429 - incluso con otro nombre de usuario, porque el límite es por IP del cliente, no por usuario. Reinicia antes la app (`Ctrl+C` y luego `fastapi dev app.py`): el almacenamiento `memory://` vuelve a empezar vacío (contadores *y* usuarios registrados).

**Paso 1: Registrar un usuario (debería tener éxito):**
```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'
```

Windows PowerShell (5.1 y 7):
```powershell
$body = @{ username = "alice"; password = "password123" } | ConvertTo-Json
Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/register" -ContentType "application/json" -Body $body
```

**Respuesta esperada:**
```json
{
  "message": "User alice registered successfully"
}
```

**Paso 2: Intentar registrar 5 usuarios más rápidamente:**

Windows PowerShell (5.1 y 7):
```powershell
for ($i = 1; $i -le 5; $i++) {
  $body = @{ username = "user$i"; password = "pass1234" } | ConvertTo-Json
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Method Post -Uri "http://127.0.0.1:8000/register" `
      -ContentType "application/json" -Body $body
    Write-Host "user$i -> $($r.StatusCode)  X-RateLimit-Remaining: $($r.Headers['X-RateLimit-Remaining'])"
  } catch {
    # Windows PowerShell 5.1 lanza una excepción con cualquier estado no 2xx: lee la respuesta del error
    $resp = $_.Exception.Response
    if (-not $resp) { throw }  # no hubo respuesta HTTP (¿está la app en marcha?)
    Write-Host "user$i -> $($resp.StatusCode.value__)  Retry-After: $($resp.Headers.GetValues('Retry-After'))"
    Write-Host $_.ErrorDetails.Message  # el cuerpo JSON del error
  }
}
```

Mac/Linux:
```bash
for i in {1..5}; do
  curl -X POST http://127.0.0.1:8000/register \
    -H "Content-Type: application/json" \
    -d "{\"username\":\"user$i\",\"password\":\"pass1234\"}"
  echo ""
done
```

**Esperado:** El Paso 1 ya usó uno de los 5 registros, así que `user1`-`user4` tienen éxito (201) y `user5` obtiene:
```json
{
  "error": "Rate limit exceeded",
  "message": "5 per 1 hour",
  "retry_after_seconds": 3599
}
```

**Estado HTTP:** `429 Too Many Requests`

`retry_after_seconds` (y la cabecera `Retry-After`) son los segundos que faltan para que se reinicie la ventana de una hora: unos 3600 justo después del Paso 1, y menos cuanto más esperes.

### Tarea 3.3: Inspeccionar Cabeceras de Límite de Tasa

Las respuestas exitosas y las `429` llevan las cabeceras del límite (la `429` incluye además `Retry-After`). Las respuestas `401` de `/login` no: slowapi solo añade las cabeceras cuando la ruta termina con normalidad o cuando se supera el límite, así que un login fallido no muestra `X-RateLimit-*`. Los endpoints exentos como `/health` no tienen límite, así que no envían estas cabeceras.

Necesitas un token de acceso para `/api/data`: haz primero el **Paso 1 de la Tarea 3.4** y vuelve aquí.

**Hacer una solicitud a un endpoint con límite:**
```bash
curl -i http://127.0.0.1:8000/api/data -H "Authorization: Bearer TU_TOKEN"
```

Windows PowerShell (5.1 y 7), con `$TOKEN` guardado en el Paso 1 de la Tarea 3.4:
```powershell
$r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/api/data" -Headers @{ Authorization = "Bearer $TOKEN" }
$r.StatusCode
'X-RateLimit-Limit', 'X-RateLimit-Remaining', 'X-RateLimit-Reset', 'Retry-After' |
  ForEach-Object { "${_}: $($r.Headers[$_])" }
```
> También puedes usar `curl.exe -i ...` (no `curl`: en PowerShell 5.1, `curl` es un alias de `Invoke-WebRequest`).

**Busca estas cabeceras:**
```
X-RateLimit-Limit: 20
X-RateLimit-Remaining: 19
X-RateLimit-Reset: 1704672000.51
Retry-After: 60
```

**Significado de las cabeceras:**
- `X-RateLimit-Limit`: Total de solicitudes permitidas en la ventana
- `X-RateLimit-Remaining`: Solicitudes restantes antes de alcanzar el límite
- `X-RateLimit-Reset`: Timestamp Unix cuando se reinicia el límite (slowapi puede incluir decimales)
- `Retry-After`: Segundos hasta que se reinicia la ventana - en un `429` es lo que el cliente debe esperar. slowapi
  también la envía en las respuestas exitosas, pero según la RFC 9110 solo tiene significado en un `429` (y en
  `503`/`3xx`), así que los clientes estándar la ignoran en un `200`

**Los clientes deberían usar estas cabeceras para:**
1. Mostrar la cuota restante a los usuarios
2. Reintentar automáticamente después del período de enfriamiento
3. Implementar retroceso exponencial

### Tarea 3.4: Probar Límite de Tasa de Login

**Paso 1: Login exitoso:**
```bash
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'
```

Guarda el `access_token` de la respuesta.

Windows PowerShell (5.1 y 7) - esto guarda el token en `$TOKEN` para las siguientes tareas:
```powershell
$body = @{ username = "alice"; password = "password123" } | ConvertTo-Json
$TOKEN = (Invoke-RestMethod -Method Post -Uri "http://127.0.0.1:8000/login" -ContentType "application/json" -Body $body).access_token
$TOKEN
```

**Paso 2: Simular ataque de fuerza bruta (11 intentos rápidos de login):**

Windows PowerShell (5.1 y 7):
```powershell
$body = @{ username = "alice"; password = "wrongpassword" } | ConvertTo-Json
for ($i = 1; $i -le 11; $i++) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Method Post -Uri "http://127.0.0.1:8000/login" `
      -ContentType "application/json" -Body $body
    Write-Host "Intento $i -> $($r.StatusCode)"
  } catch {
    $resp = $_.Exception.Response
    if (-not $resp) { throw }
    $code = $resp.StatusCode.value__
    if ($code -eq 429) {
      Write-Host "Intento $i -> $code  X-RateLimit-Remaining: $($resp.Headers.GetValues('X-RateLimit-Remaining'))  Retry-After: $($resp.Headers.GetValues('Retry-After'))"
    } else {
      Write-Host "Intento $i -> $code"
    }
  }
}
```

Mac/Linux:
```bash
for i in {1..11}; do
  echo "Intento $i"
  curl -X POST http://127.0.0.1:8000/login \
    -H "Content-Type: application/json" \
    -d '{"username":"alice","password":"wrongpassword"}'
  echo ""
done
```

**Esperado:** Toda solicitud a `/login` cuenta para el límite de 10 por minuto, tenga éxito o no, y el login del Paso 1 ya usó una. Así que los intentos 1-9 devuelven 401 (No autorizado) y los intentos 10-11 devuelven 429 (Límite de tasa excedido).

> Si pasó más de un minuto entre el Paso 1 y el Paso 2, la ventana ya se ha reiniciado: los intentos 1-10 devuelven 401 y el intento 11 devuelve 429.

**Beneficio de seguridad:** Un atacante solo puede probar 10 contraseñas por minuto, haciendo impracticable la fuerza bruta.

### Tarea 3.5: Probar Endpoints Autenticados

**Paso 1: Obtener un token válido:**

Reutiliza el token del Paso 1 de la Tarea 3.4 (es válido durante 1 hora). Si necesitas uno nuevo, **espera antes un minuto**: la Tarea 3.4 agotó los logins de este minuto, así que hacer login ahora mismo devuelve 429.
```bash
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'
```

Copia el `access_token`. (En PowerShell, vuelve a ejecutar los comandos del Paso 1 de la Tarea 3.4 para renovar `$TOKEN`.)

**Paso 2: Probar el endpoint `/api/data` (límite: 20 por minuto):**

Windows PowerShell (5.1 y 7):
```powershell
# Solo si $TOKEN aún no está definido en esta ventana:
# $TOKEN = "YOUR_TOKEN_HERE"

for ($i = 1; $i -le 21; $i++) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/api/data" `
      -Headers @{ Authorization = "Bearer $TOKEN" }
    Write-Host "Solicitud $i -> $($r.StatusCode)  X-RateLimit-Remaining: $($r.Headers['X-RateLimit-Remaining'])"
  } catch {
    $resp = $_.Exception.Response
    if (-not $resp) { throw }
    Write-Host "Solicitud $i -> $($resp.StatusCode.value__)  Retry-After: $($resp.Headers.GetValues('Retry-After'))"
  }
}
```

Mac/Linux:
```bash
# Reemplaza YOUR_TOKEN_HERE con tu token real
TOKEN="YOUR_TOKEN_HERE"
for i in {1..21}; do
  echo "Solicitud $i"
  curl http://127.0.0.1:8000/api/data \
    -H "Authorization: Bearer $TOKEN"
  echo ""
done
```

**Esperado:** Las solicitudes 1-20 tienen éxito, la solicitud 21 devuelve 429.

> Si llamaste a `/api/data` en la Tarea 3.3 hace menos de un minuto, esa solicitud también cuenta, así que el 429 llega una solicitud antes.

### Tarea 3.6: Probar Endpoint de Búsqueda Costosa

**Probar el límite estricto en búsqueda (5 por minuto):**

Windows PowerShell (5.1 y 7):
```powershell
for ($i = 1; $i -le 6; $i++) {
  try {
    $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/api/search?q=test" `
      -Headers @{ Authorization = "Bearer $TOKEN" }
    Write-Host "Búsqueda $i -> $($r.StatusCode)  X-RateLimit-Remaining: $($r.Headers['X-RateLimit-Remaining'])"
  } catch {
    $resp = $_.Exception.Response
    if (-not $resp) { throw }
    Write-Host "Búsqueda $i -> $($resp.StatusCode.value__)  Retry-After: $($resp.Headers.GetValues('Retry-After'))"
  }
}
```

Mac/Linux:
```bash
TOKEN="YOUR_TOKEN_HERE"
for i in {1..6}; do
  echo "Búsqueda $i"
  curl "http://127.0.0.1:8000/api/search?q=test" \
    -H "Authorization: Bearer $TOKEN"
  echo ""
done
```

**Esperado:** Las búsquedas 1-5 tienen éxito, la búsqueda 6 devuelve 429.

**Nota:** El límite más estricto (5 vs 20) simula la protección de una operación costosa.

### Tarea 3.7: Probar Endpoint Exento

**Probar el endpoint ilimitado:**

Hacer 100 solicitudes rápidamente - todas deberían tener éxito.

Windows PowerShell (5.1 y 7):
```powershell
$ok = 0
for ($i = 1; $i -le 100; $i++) {
  $r = Invoke-WebRequest -UseBasicParsing -Uri "http://127.0.0.1:8000/api/unlimited" `
    -Headers @{ Authorization = "Bearer $TOKEN" }
  if ($r.StatusCode -eq 200) { $ok++ }
}
Write-Host "$ok de 100 solicitudes devolvieron 200"
```

Mac/Linux:
```bash
TOKEN="YOUR_TOKEN_HERE"
for i in {1..100}; do
  curl http://127.0.0.1:8000/api/unlimited \
    -H "Authorization: Bearer $TOKEN" -s | head -n 1
done
```

**Esperado:** ¡Todas las 100 solicitudes tienen éxito - sin limitación de tasa!

## Parte 4: Comprendiendo Estrategias de Límite de Tasa (20 minutos)

### Estrategia 1: Limitación de Tasa por IP (Implementación Actual)

**Cómo funciona:**
- Rastrea solicitudes por la dirección IP del cliente
- Usa `get_remote_address()` como función clave

**Pros:**
- Simple de implementar
- Funciona para solicitudes no autenticadas
- Protege contra ataques de una sola fuente

**Contras:**
- Los usuarios detrás del mismo NAT/proxy comparten el mismo límite
- No distingue entre usuarios autenticados de la misma IP
- Puede bloquear usuarios legítimos en redes compartidas (oficinas, universidades)

> **Detrás de un proxy:** si la app corre detrás de nginx, Railway, Render, ngrok... `get_remote_address` ve la IP del
> proxy, así que *todos* los usuarios comparten un mismo cupo. Ejecuta uvicorn (o `fastapi run`) con
> `--proxy-headers --forwarded-allow-ips=<ip del proxy>` para que `request.client.host` sea el cliente real, o escribe
> una función clave que lea `X-Forwarded-For` solo cuando la petición venga de tu proxy de confianza. `get_ipaddr` de
> slowapi se fía de esa cabecera a ciegas, y cualquier cliente puede falsificarla.

**Casos de uso:**
- Endpoints públicos (registro, login)
- APIs anónimas
- Aplicaciones simples

### Estrategia 2: Limitación de Tasa por Usuario

**Cómo funciona:**
- Rastrea solicitudes por ID de usuario autenticado (de JWT)
- Recurre a IP para solicitudes no autenticadas

**Ejemplo de implementación:**
```python
def get_user_key(request: Request) -> str:
    """Usar el usuario del JWT si el token es válido, de lo contrario la dirección IP"""
    token = request.headers.get("Authorization", "").removeprefix("Bearer ")
    try:
        return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])["sub"]
    except jwt.InvalidTokenError:
        return get_remote_address(request)

limiter = Limiter(
    key_func=get_user_key,  # Rastreo por usuario
    default_limits=["1000/day", "100/hour"]
)
```

**Pros:**
- Límites justos por usuario (no por IP)
- Los usuarios en redes compartidas no se afectan entre sí
- Puede ofrecer límites diferentes para diferentes niveles de usuario (gratis vs premium)

**Contras:**
- Requiere autenticación
- No protege endpoints no autenticados
- Los usuarios pueden crear múltiples cuentas para eludir los límites
- La clave recurre a la IP cuando el token no es válido, así que un cliente que envía tokens basura sale del cupo
  por usuario y cae en el de la IP; en producción rechaza los tokens inválidos antes de limitar, o usa IP + token como clave

**Casos de uso:**
- APIs SaaS con cuentas de usuario
- Servicios premium/escalonados
- Sistemas de cuota por usuario

### Estrategia 3: Limitación de Tasa Escalonada (Avanzado)

**Cómo funciona:**
- Límites diferentes basados en el rol del usuario, nivel de suscripción o clave de API

**Ejemplo de implementación:**
```python
def get_rate_limit(key: str) -> str:
    """Devolver límites diferentes según el rol del usuario.
    slowapi la llama con la clave del cliente que devolvió key_func (aquí: el usuario, o la IP)."""
    if key not in users:
        return "10/hour"  # Usuarios no autenticados (la clave es una dirección IP)

    role = users[key]["role"]
    if role == "admin":
        return "1000/hour"
    elif role == "premium":
        return "500/hour"
    else:  # nivel gratuito
        return "50/hour"

# Límite dinámico basado en usuario (key_func debe ser por usuario, como get_user_key de arriba)
@app.get("/api/data")
@limiter.limit(get_rate_limit)
def get_data(request: Request, response: Response):
    # ...
```

**Casos de uso:**
- Plataformas SaaS multinivel
- Modelos freemium
- APIs empresariales

## Parte 5: Mejores Prácticas (15 minutos)

### Mejor Práctica 1: Usar Límites Diferentes para Endpoints Diferentes

```python
# Límite generoso para leer datos
@app.get("/api/data")
@limiter.limit("100/minute")

# Límite estricto para crear datos
@app.post("/api/data")
@limiter.limit("10/minute")

# Muy estricto para operaciones costosas
@app.get("/api/export")
@limiter.limit("1/hour")
```

**¿Por qué?** Las operaciones de lectura suelen ser más baratas que las escrituras, y algunas operaciones (exportaciones, informes) son muy costosas.

### Mejor Práctica 2: Incluir Siempre Cabeceras de Límite de Tasa

¡Los clientes necesitan conocer su cuota! slowapi envía estas cabeceras **solo con `headers_enabled=True`** (ya activado en `app.py`):
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`
- `Retry-After`

> El IETF está estandarizando las cabeceras `RateLimit` / `RateLimit-Policy` para sustituir a las `X-RateLimit-*` de facto.

**Mejor práctica para clientes:**
```python
# Pseudocódigo para cliente de API
response = make_request()

if response.status == 429:
    retry_after = int(response.headers['Retry-After'])
    # Limita la espera y añade jitter: si todos los clientes reintentaran en el mismo segundo exacto,
    # volverían a chocar con el límite a la vez (thundering herd)
    sleep(min(retry_after, 60) + random.uniform(0, 1))
    retry_request()

remaining = response.headers['X-RateLimit-Remaining']
if remaining < 10:
    warn_user("Acercándose al límite de tasa")
```

### Mejor Práctica 3: Mensajes de Error Amigables

No solo devuelvas "429 Too Many Requests" - ¡explica qué sucedió!

**Buen manejador de errores (ya en `app.py`):**
```python
def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    # el manejador propio de slowapi ya construye el 429 y añade las cabeceras
    # (este manejador depende de headers_enabled=True en Limiter(...): sin él no hay Retry-After)
    default = _rate_limit_exceeded_handler(request, exc)
    return JSONResponse(
        {
            "error": "Rate limit exceeded",
            "message": str(exc.detail),  # ej., "5 per 1 hour"
            "retry_after_seconds": int(default.headers.get("Retry-After", "0")),  # mismo valor que la cabecera Retry-After
        },
        status_code=429,
        headers={k: v for k, v in default.headers.items() if k.lower().startswith(("retry-after", "x-ratelimit"))},
    )

app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
```

**Ejemplo de respuesta:**
```json
{
  "error": "Rate limit exceeded",
  "message": "5 per 1 hour",
  "retry_after_seconds": 3540
}
```

### Mejor Práctica 4: Exentar Endpoints Críticos

```python
@app.get("/health")
@limiter.exempt  # Los sistemas de monitoreo necesitan acceso confiable
def health():
    return {"status": "ok"}

@app.post("/api/emergency-stop")
@limiter.exempt  # Operación de seguridad crítica
def emergency_stop(creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]):
    # Detener operación peligrosa
    pass
```

**Cuándo exentar endpoints:**
- Comprobaciones de salud (monitoreo)
- Operaciones de emergencia/seguridad
- Comunicación interna entre microservicios (usa autenticación en su lugar)
- Webhooks de fuentes confiables

### Mejor Práctica 5: Usar Redis en Producción

Para este ejercicio, usamos almacenamiento en memoria:
```python
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="memory://"  # Simple, pero no escala
)
```

**En producción, usa Redis:**
```python
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri="redis://localhost:6379"  # Compartido entre múltiples servidores
)
```

**¿Por qué Redis?**
- Contadores de límite de tasa compartidos entre múltiples servidores de API
- Persistente a través de reinicios de la aplicación
- Rápido y confiable
- Estándar de la industria

### Mejor Práctica 6: Registrar Violaciones de Límite de Tasa

Agrega registro para detectar abuso:

```python
import logging

def rate_limit_handler(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    # Registrar la violación
    logging.warning(
        f"Rate limit exceeded: IP={get_remote_address(request)}, "
        f"Path={request.url.path}, Limit={exc.detail}"
    )

    # Misma respuesta que el manejador de app.py (conserva las cabeceras Retry-After y X-RateLimit-*)
    default = _rate_limit_exceeded_handler(request, exc)
    return JSONResponse(
        {
            "error": "Rate limit exceeded",
            "message": str(exc.detail),
            "retry_after_seconds": int(default.headers.get("Retry-After", "0")),
        },
        status_code=429,
        headers={k: v for k, v in default.headers.items() if k.lower().startswith(("retry-after", "x-ratelimit"))},
    )
```

**Usa registros para:**
- Identificar IPs abusivas
- Detectar tráfico de bots
- Optimizar límites de tasa según patrones de uso reales

## Lista de Verificación de Pruebas

**Configuración Básica:**
- [ ] slowapi instalado (`pip install -r requirements.txt`)
- [ ] La aplicación se ejecuta sin errores (`fastapi dev app.py`)
- [ ] Endpoint de comprobación de salud accesible (`/health`)

**Implementación de Límite de Tasa:**
- [ ] Limiter inicializado con `get_remote_address` y límites predeterminados
- [ ] Endpoint de registro limitado a "5/hour"
- [ ] Endpoint de login limitado a "10/minute"
- [ ] Endpoint de datos limitado a "20/minute"
- [ ] Endpoint de búsqueda limitado a "5/minute"
- [ ] Endpoint ilimitado marcado con `@limiter.exempt`

**Pruebas:**
- [ ] Límite de registro aplicado (el sexto intento en una hora falla)
- [ ] Límite de login aplicado (el undécimo intento en un minuto falla)
- [ ] Límite de endpoint de datos aplicado (la solicitud 21 falla)
- [ ] Límite de búsqueda aplicado (la sexta búsqueda falla)
- [ ] Endpoint ilimitado sin límite (100+ solicitudes tienen éxito)
- [ ] Cabeceras de límite de tasa presentes en las respuestas
- [ ] Código de estado 429 devuelto cuando se excede el límite
- [ ] Manejador de error personalizado devuelve respuesta JSON

**Comprensión:**
- [ ] Puede explicar cuándo usar limitación de tasa
- [ ] Entiende diferentes estrategias de límite de tasa (por IP vs por usuario)
- [ ] Sabe cuándo exentar endpoints
- [ ] Puede elegir límites apropiados para diferentes operaciones

## Problemas Comunes y Soluciones

### Problema 1: El Límite de Tasa No Funciona

**Síntoma:** Puedes hacer solicitudes ilimitadas sin obtener errores 429.

**Causas posibles:**
1. **Decorador mal colocado o falta `request`:**
   `@limiter.limit` va justo debajo del decorador de la ruta, y la función debe recibir `request: Request`:
   ```python
   # INCORRECTO - el limiter decora una función que FastAPI nunca registró
   # (está encima del decorador de la ruta), así que no se limita nada
   @limiter.limit("5/minute")
   @app.get("/endpoint")
   def endpoint(request: Request, response: Response):
       pass

   # CORRECTO
   @app.get("/endpoint")
   @limiter.limit("5/minute")
   def endpoint(request: Request, response: Response):
       pass
   ```
   Ten en cuenta también que FastAPI resuelve los parámetros `Depends(...)` ANTES de ejecutar tu función, y el limiter cuenta la petición cuando tu función empieza. Si la comprobación del token fuera una dependencia que lanza `401`, las peticiones sin token o con token inválido se rechazarían antes de que el limiter las cuente, así que adivinar tokens nunca se limitaría. Por eso `app.py` solo recibe el token como parámetro y lo comprueba dentro del cuerpo de la función. Por la misma razón, las peticiones que no pasan la validación del body o de la query (`422`) las rechaza FastAPI antes de que el limiter las cuente, así que una avalancha de JSON malformado a `/login` no queda limitada por estos decoradores.

2. **Endpoint marcado como exento:**
   Verifica si `@limiter.exempt` está aplicado (intencionalmente o por error).

3. **Límites demasiado generosos:**
   "1000/minute" no se activará durante las pruebas manuales - usa límites pequeños para probar.

### Problema 2: El Límite de Tasa se Reinicia Demasiado Rápido

**Síntoma:** Después de alcanzar el límite, se reinicia inmediatamente en lugar de esperar la ventana completa.

**Causa:** Reiniciar la aplicación (o guardar `app.py`, lo que hace que `fastapi dev` la recargue) borra los contadores de límite de tasa en memoria.

**Solución:** Este es el comportamiento esperado con almacenamiento `memory://`. En producción, usa Redis para contadores persistentes.

### Problema 3: Múltiples Usuarios de la Misma IP Comparten el Límite

**Síntoma:** Dos usuarios en la misma red (oficina, universidad) comparten el mismo límite de tasa.

**Causa:** Usar `get_remote_address()` (basado en IP) en lugar de rastreo por usuario. Lo mismo le pasa a *todo el mundo* cuando la app corre detrás de un proxy inverso (nginx, Railway, Render, ngrok): la app solo ve la IP del proxy.

**Solución:** Implementar limitación de tasa por usuario (ver Parte 4, Estrategia 2). Detrás de un proxy, ejecuta uvicorn con `--proxy-headers --forwarded-allow-ips=<ip del proxy>`, o lee `X-Forwarded-For` solo desde tu proxy de confianza (ver la nota de la Estrategia 1).

### Problema 4: Las Cabeceras de Límite de Tasa No Se Muestran

**Síntoma:** No hay cabeceras `X-RateLimit-*` en las respuestas.

**Causas:**
1. slowapi solo las envía si se pasa `headers_enabled=True` a `Limiter(...)` (por defecto está desactivado).
2. El endpoint está exento (p. ej. `/health`): no tiene límite, así que no hay cabeceras. Una ruta limitada que devuelve un dict también necesita el parámetro `response: Response`, o sus respuestas exitosas no llevan cabeceras.
3. Tu cliente oculta las cabeceras: usa `curl -i` (`curl.exe -i` en PowerShell) o la pestaña Network de DevTools del navegador.

### Problema 5: "429 Too Many Requests" para Comprobaciones de Salud

**Síntoma:** El sistema de monitoreo obtiene errores 429 al verificar `/health`.

**Solución:** Exentar el endpoint de comprobación de salud:
```python
@app.get("/health")
@limiter.exempt
def health():
    return {"status": "ok"}
```

## Ejemplos de Limitación de Tasa del Mundo Real

### Ejemplo 1: API de GitHub

**Nivel gratuito (no autenticado):**
- 60 solicitudes por hora

**Autenticado:**
- 5,000 solicitudes por hora

**API de búsqueda (límite especial):**
- 10 solicitudes por minuto (más estricto porque la búsqueda es costosa)

**Cómo comunican los límites:**
```
X-RateLimit-Limit: 5000
X-RateLimit-Remaining: 4999
X-RateLimit-Reset: 1704672000
X-RateLimit-Resource: core
```

### Ejemplo 2: API de Twitter v2

Cifras en el momento de escribir esto (consulta la documentación del proveedor, estos niveles cambian a menudo).

**Nivel gratuito:**
- 500,000 Tweets leídos por mes
- 1,667 Tweets por hora

**Nivel básico ($100/mes):**
- 10,000,000 Tweets por mes

**Cómo lo aplican:**
- Devuelve 429 con cabecera `x-rate-limit-reset`
- Los clientes deben esperar hasta el tiempo de reinicio antes de reintentar

### Ejemplo 3: API de Stripe

**Límites:**
- 100 solicitudes de lectura por segundo
- 100 solicitudes de escritura por segundo (más estricto en la práctica)

**Manejo especial:**
- Los endpoints de pago tienen límites más estrictos
- El modo de prueba tiene límites separados del modo en vivo

**Cómo manejan los excesos:**
- Código de estado 429
- Retroceso exponencial recomendado
- Los SDKs reintentan automáticamente con retroceso

## Más Allá de Este Ejercicio

### Próximos Pasos

1. **Ejercicio 15+**: Aplica limitación de tasa a tu API de proyecto final
2. **Despliegue en producción**: Configura Redis para almacenamiento de límite de tasa
3. **Monitoreo**: Configura alertas para violaciones de límite de tasa
4. **Análisis**: Rastrea patrones de uso de API para optimizar límites

### Temas Avanzados (Más Allá de Este Curso)

1. **Limitación de Tasa Distribuida**:
   - Redis Cluster para alta disponibilidad
   - Hashing consistente para fragmentación

2. **Limitación de Tasa Adaptativa**:
   - Aumentar límites para usuarios confiables
   - Disminuir límites para IPs sospechosas
   - Detección de anomalías basada en aprendizaje automático

3. **Algoritmo de Token Bucket**:
   - Más sofisticado que ventanas fijas
   - Permite tráfico en ráfagas
   - Se rellena a una tasa constante

4. **Limitación de Tasa Geográfica**:
   - Límites diferentes por región
   - Límites más estrictos para países de alto riesgo
   - Bloqueo basado en GeoIP

5. **Limitación de Tasa Basada en Costos**:
   - Asignar "costo" a cada endpoint
   - Rastrear costo total en lugar de conteo de solicitudes
   - Ejemplo: 1 búsqueda = 5 puntos, 1 lectura = 1 punto

## Recursos Adicionales

### Documentación Oficial
- **[Documentación de slowapi](https://slowapi.readthedocs.io/)** - Referencia de la biblioteca (slowapi es un port de [Flask-Limiter](https://flask-limiter.readthedocs.io/))
- **[RFC 6585](https://tools.ietf.org/html/rfc6585)** - Especificación del código de estado HTTP 429
- **[Redis](https://redis.io/)** - Almacén de datos en memoria para producción

### Tutoriales
- [Mejores Prácticas de Limitación de Tasa](https://nordicapis.com/everything-you-need-to-know-about-api-rate-limiting/)
- [Limitación de Tasa de API de GitHub](https://docs.github.com/en/rest/overview/resources-in-the-rest-api#rate-limiting)

### Bibliotecas Alternativas
- **[django-ratelimit](https://django-ratelimit.readthedocs.io/)** - Para aplicaciones Django
- **[express-rate-limit](https://github.com/nfriedly/express-rate-limit)** - Para Node.js/Express

## Entregables

Cuando completes este ejercicio, deberías tener:

1. **`app.py` Completado**:
   - Todos los TODOs completados correctamente
   - Limiter inicializado con función clave y valores predeterminados apropiados
   - Todos los endpoints tienen límites de tasa apropiados
   - Endpoint exento configurado

2. **Evidencia de Pruebas**:
   - Capturas de pantalla o registros mostrando la aplicación del límite de tasa
   - Respuestas 429 cuando se exceden los límites
   - Cabeceras de límite de tasa en respuestas exitosas

3. **Comprensión**:
   - Explicar por qué endpoints diferentes tienen límites diferentes
   - Describir cuándo usar limitación de tasa por IP vs por usuario
   - Identificar límites apropiados para tus propios proyectos de API

## Preguntas para Considerar

1. ¿Por qué el endpoint de login está limitado más estrictamente que el endpoint de datos?
2. ¿Qué pasaría si usaras limitación de tasa por usuario para el endpoint `/register`?
3. ¿Cómo implementarías límites de tasa diferentes para usuarios gratuitos vs premium?
4. ¿Cuándo exentarías un endpoint de la limitación de tasa? ¿Cuáles son los riesgos?
5. ¿Cómo ayudan las cabeceras de límite de tasa a los clientes de API a implementar mejor lógica de reintento?
6. ¿Cuál es la diferencia entre limitación de tasa y estrangulamiento?

¡Buena suerte protegiendo tus APIs! 🛡️
