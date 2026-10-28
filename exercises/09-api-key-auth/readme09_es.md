# Ejercicio 9: Autenticación con Clave API

## Objetivo

Aprender a implementar **autenticación con clave API** en una API REST Flask como lo hacen los proveedores reales: claves aleatorias enviadas en una cabecera, almacenadas solo como hash, mostradas una vez, y rotadas o revocadas cuando hace falta.

## Inicio Rápido

```bash
cd exercises/09-api-key-auth
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python app.py
```

---

## Lo Que Aprenderás

Este ejercicio se basa en el Ejercicio 08 (Autenticación Básica) e introduce:

1. **Generación Segura de Claves API** con `secrets.token_urlsafe()`
2. **Almacenar solo un hash** de la clave (SHA-256), nunca la clave
3. **Comparación en tiempo constante** con `hmac.compare_digest()`
4. **Decoradores Personalizados** para validación de claves API
5. **Autenticación Basada en Cabeceras** con `X-API-Key`
6. **Rotación y Revocación de Claves** (en lugar de "recuperar" una clave perdida)

---

## ¿Qué Son las Claves API?

Las **claves API** son secretos aleatorios y largos utilizados para autenticar peticiones API sin enviar credenciales usuario/contraseña repetidamente.

### Ejemplos del Mundo Real:

- **Google Maps API**: Requiere clave API en cada petición
- **OpenWeatherMap**: Acepta la clave en el query string (`?appid=TU_CLAVE`). Es cómodo, pero las URLs acaban en logs del servidor, historial del navegador y proxies. En este ejercicio las claves van en una cabecera, **nunca en la URL**
- **GitHub API**: Usa tokens de acceso personal (un tipo de clave API) con el prefijo `ghp_`
- **Stripe**: Usa claves secretas con el prefijo `sk_live_` / `sk_test_`

### Clave API vs Autenticación Básica

| Característica | Auth Básica | Clave API |
|----------------|-------------|-----------|
| **Envía credenciales** | Cada petición (usuario:contraseña) | Contraseña solo en registro y rotación |
| **Formato del token** | Base64 codificado `user:pass` | Cadena aleatoria larga (ej. `sk_...`) |
| **Expira** | Nunca (a menos que cambie contraseña) | Puede rotarse/revocarse en cualquier momento |
| **Almacenamiento (cliente)** | Cliente almacena contraseña | Cliente almacena clave API (variable de entorno, gestor de secretos) |
| **Almacenamiento (servidor)** | Hash de la contraseña | Hash de la clave API |
| **Caso de uso** | Apps simples, paneles admin | APIs públicas, acceso terceros |

---

## Estructura de la API

### Endpoints Públicos (Sin Autenticación)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/register` | Registrar nuevo usuario, recibir clave API (se muestra **una vez**) |

### Protegidos por Autenticación Básica

| Método | Endpoint | Auth Requerida | Descripción |
|--------|----------|----------------|-------------|
| POST | `/api-key/rotate` | Auth Básica | Emitir una clave API nueva; la anterior deja de funcionar |
| DELETE | `/api-key` | Auth Básica | Revocar tu clave API (ej. se ha filtrado) |

### Protegidos por Clave API

| Método | Endpoint | Auth Requerida | Descripción |
|--------|----------|----------------|-------------|
| GET | `/users` | Clave API | Listar todos los usuarios |

---

## Cómo Funciona

### Patrón 1: Registrarse y Obtener Clave API

```
Cliente                         Servidor
  |                               |
  |  POST /register               |
  |  {username, password}         |
  | ----------------------------> |
  |                               | Genera clave API aleatoria
  |                               | Hashea contraseña (werkzeug)
  |                               | Hashea clave API (SHA-256)
  |                               | Almacena ambos HASHES
  |  {api_key: "sk_..."}          |
  | <---------------------------- |
  |                               |
  | Cliente guarda la clave       |
  | (el servidor no puede         |
  |  mostrarla otra vez)          |
```

**Ejemplo:**
```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"username":"alice","password":"secret123"}' \
     http://127.0.0.1:5000/register
```

**Respuesta:**
```json
{
  "message": "User registered successfully",
  "username": "alice",
  "api_key": "sk_Vq3o0m3k8X0bS2Yc1d5yGQ0q3ZpWm1x9lJ7cE4tR2uA",
  "warning": "Store this API key now. It will not be shown again."
}
```

**El cliente guarda esta clave API** en una variable de entorno o un gestor de secretos. Nunca la subas a Git.

### Patrón 2: Usar Clave API para Endpoints Protegidos

```
Cliente                         Servidor
  |                               |
  |  GET /users                   |
  |  Header: X-API-Key: sk_...    |
  | ----------------------------> |
  |                               | Hashea la clave recibida
  |                               | Compara con hashes guardados
  |                               | (tiempo constante)
  |  {users: [...]}               |
  | <---------------------------- |
```

**Ejemplo:**
```bash
curl -H "X-API-Key: sk_Vq3o0m3k8X0bS2Yc1d5yGQ0q3ZpWm1x9lJ7cE4tR2uA" \
     http://127.0.0.1:5000/users
```

**Respuesta:**
```json
{
  "users": ["alice", "bob"],
  "count": 2
}
```

> **Los nombres de cabecera son insensibles a mayúsculas** en HTTP. `X-API-Key`, `x-api-key` y `X-API-KEY` son la misma cabecera, así que los ejemplos antiguos que usan `x-api-key` siguen funcionando.

### Patrón 3: Rotar o Revocar una Clave

El servidor **no puede recuperar** una clave perdida: solo guarda el hash. Si pierdes la clave, o se filtra, obtienes una **nueva** con tu usuario/contraseña. La clave anterior deja de funcionar inmediatamente.

```bash
# Rotar: clave nueva, la anterior queda invalidada
curl -X POST -u alice:secret123 http://127.0.0.1:5000/api-key/rotate
```

**Respuesta:**
```json
{
  "message": "API key rotated. The previous key no longer works.",
  "username": "alice",
  "api_key": "sk_9fJk2LmQ0wE7rT1yU5iO3pA8sD6fG4hJ2kL0zX9cV7b",
  "warning": "Store this API key now. It will not be shown again."
}
```

```bash
# Revocar: sin clave hasta que vuelvas a rotar
curl -X DELETE -u alice:secret123 http://127.0.0.1:5000/api-key
```

---

## Guía de Implementación

### TODOs en app.py

Necesitas completar **8 espacios estratégicos** (busca `_____`):

1. **`generate_api_key()`**: Generar la parte aleatoria con `secrets.token_urlsafe(32)`
2. **`hash_api_key()`**: Hashear la clave con `hashlib.sha256(...)`
3. **`find_user_by_api_key()`**: Comparar hashes con `hmac.compare_digest()`
4. **`api_key_required`**: Leer la cabecera `X-API-Key`
5. **`register()`**: Guardar el **hash** de la clave, no la clave
6. **`rotate_api_key()`**: Establecer el método HTTP del endpoint de rotación
7. **`rotate_api_key()`**: Sobrescribir el hash guardado con el hash de la clave nueva
8. **`get_users()`**: Aplicar el decorador `@api_key_required`

### Conceptos Clave a Implementar

#### 1. Generar Claves API con `secrets`

```python
import secrets

API_KEY_PREFIX = 'sk_'

def generate_api_key():
    return API_KEY_PREFIX + secrets.token_urlsafe(32)
# Resultado: "sk_Vq3o0m3k8X0bS2Yc1d5yGQ0q3ZpWm1x9lJ7cE4tR2uA"
```

**¿Por qué `secrets` y no `uuid4` o `random`?**
- `secrets` es el módulo de la librería estándar **diseñado para secretos**: usa el generador aleatorio criptográficamente seguro del sistema operativo
- `token_urlsafe(32)` da 32 bytes aleatorios (256 bits), codificados con caracteres seguros en cabeceras y URLs
- `uuid4` está diseñado para ser **único**, no **secreto**: solo tiene 122 bits aleatorios y un formato fijo reconocible, y el estándar UUID no garantiza un generador criptográficamente seguro (CPython usa uno, otras librerías puede que no). Usa UUIDs para IDs, `secrets` para claves
- `random` es predecible y nunca debe usarse para seguridad

**¿Por qué el prefijo `sk_`?**
- Reconoces de un vistazo qué tipo de cadena es
- Los **escáneres de secretos** (GitHub secret scanning, GitLab, gitleaks...) buscan prefijos conocidos. Una clave con prefijo reconocible que se sube a un repositorio puede detectarse y revocarse automáticamente

#### 2. Almacenar Solo un Hash de la Clave

La base de datos nunca contiene la clave. Si la base de datos se filtra, el atacante obtiene hashes, no claves que funcionen.

```python
import hashlib

def hash_api_key(api_key):
    return hashlib.sha256(api_key.encode('utf-8')).hexdigest()

users[username] = {
    'password': generate_password_hash(password),  # hash lento, con sal
    'api_key_hash': hash_api_key(api_key)          # SHA-256 rápido
}
```

**¿Por qué un hash rápido (SHA-256) vale para claves API pero NO para contraseñas?**
- Un atacante que roba un hash intenta **adivinar** la entrada y hashear cada intento
- Una contraseña es corta y la elige una persona (`secret123`). Con un hash rápido, miles de millones de intentos por segundo la encuentran enseguida. Las contraseñas necesitan un hash **lento y con sal**: `generate_password_hash` de werkzeug (scrypt/pbkdf2) hace caro cada intento
- Una clave API tiene 256 bits aleatorios. No hay nada que adivinar: incluso a miles de millones de intentos por segundo tardaría mucho más que la edad del universo. Un hash lento no aporta nada, y uno rápido mantiene rápida cada petición (la clave se comprueba en **cada** petición, la contraseña solo en el login)

Por eso también el servidor **muestra la clave solo una vez**: después del registro ya no la tiene.

#### 3. Comparación en Tiempo Constante

```python
import hmac

def find_user_by_api_key(api_key):
    candidate_hash = hash_api_key(api_key)

    for username, user_data in users.items():
        stored_hash = user_data.get('api_key_hash')
        if stored_hash and hmac.compare_digest(stored_hash, candidate_hash):
            return username

    return None
```

`==` se detiene en el primer carácter distinto, así que una comparación tarda un poco más cuantos más caracteres coinciden. Medir esa diferencia de tiempo (un **ataque de temporización**) puede filtrar un secreto carácter a carácter. `hmac.compare_digest()` siempre tarda lo mismo. Úsalo siempre que compares secretos.

> En una base de datos real pondrías un índice sobre `api_key_hash` y lo buscarías directamente (`WHERE api_key_hash = ?`). Eso también es seguro: el atacante no puede elegir el hash de su intento, así que el tiempo no revela nada útil.

#### 4. Crear Decoradores Personalizados

**¿Qué es un decorador?**
Un decorador es una función que envuelve otra función para añadir comportamiento extra.

**Patrón básico de decorador:**
```python
from functools import wraps

def mi_decorador(f):
    @wraps(f)
    def funcion_decorada(*args, **kwargs):
        # Código antes de la función
        print("Antes de llamar a la función")

        # Llamar a la función original
        resultado = f(*args, **kwargs)

        # Código después de la función
        print("Después de llamar a la función")

        return resultado
    return funcion_decorada

@mi_decorador
def hola():
    print("¡Hola!")
```

**Para validación de clave API:**
```python
def api_key_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Extraer clave API de las cabeceras
        api_key = request.headers.get('X-API-Key')

        # 2. Validar que existe
        if not api_key:
            return jsonify({'error': 'API key missing'}), 401

        # 3. Buscarla por su hash
        if find_user_by_api_key(api_key) is None:
            return jsonify({'error': 'Invalid API key'}), 401

        # 4. Si es válida, llamar a la función original
        return f(*args, **kwargs)

    return decorated
```

#### 5. Leer Cabeceras en Flask

```python
from flask import request

# Obtener una cabecera específica (la búsqueda es insensible a mayúsculas)
api_key = request.headers.get('X-API-Key')

# Comprobar si la cabecera existe
if 'X-API-Key' in request.headers:
    print("Clave API presente")

# Obtener todas las cabeceras
todas_cabeceras = request.headers
```

**Nombres comunes de cabecera para claves API:**
- `X-API-Key` (más común; también se escribe `x-api-key`, es la misma cabecera)
- `Authorization: Bearer TU_CLAVE`
- `api-key`

**Nunca** envíes la clave en la URL (`/users?api_key=...`): las URLs se guardan en logs, historial del navegador y cachés de proxies.

#### 6. Rotar y Revocar Claves

```python
@app.route('/api-key/rotate', methods=['POST'])
@auth.login_required          # usuario + contraseña (Auth Básica)
def rotate_api_key():
    current_user = auth.current_user()
    new_api_key = generate_api_key()

    # Sobrescribir el hash invalida la clave anterior inmediatamente
    users[current_user]['api_key_hash'] = hash_api_key(new_api_key)

    return jsonify({'api_key': new_api_key}), 200   # se muestra una vez


@app.route('/api-key', methods=['DELETE'])
@auth.login_required
def revoke_api_key():
    users[auth.current_user()]['api_key_hash'] = None
    return jsonify({'message': 'API key revoked'}), 200
```

- **Rota** con regularidad, y siempre que una clave pueda haberse filtrado o alguien que la conocía deje el equipo
- **Revoca** cuando una clave se ha filtrado y todavía no necesitas una sustituta
- La rotación usa `POST` porque **crea** una clave nueva en cada llamada

---

## Probar la API

> Los comandos siguientes usan `curl` con comillas de `bash`. En **CMD de Windows** usa `example/commands_cmd.txt`, y en **PowerShell** usa `example/commands_powershell.txt`.

### 1. Registrar un Nuevo Usuario

```bash
curl -X POST -H "Content-Type: application/json" \
     -d '{"username":"alice","password":"secret123"}' \
     http://127.0.0.1:5000/register
```

**Respuesta Esperada:**
```json
{
  "message": "User registered successfully",
  "username": "alice",
  "api_key": "sk_Vq3o0m3k8X0bS2Yc1d5yGQ0q3ZpWm1x9lJ7cE4tR2uA",
  "warning": "Store this API key now. It will not be shown again."
}
```

**¡Guarda la clave API!** La necesitarás para peticiones posteriores, y el servidor no puede mostrarla otra vez.

### 2. Acceder a Endpoint Protegido con Clave API

```bash
curl -H "X-API-Key: sk_Vq3o0m3k8X0bS2Yc1d5yGQ0q3ZpWm1x9lJ7cE4tR2uA" \
     http://127.0.0.1:5000/users
```

**Respuesta Esperada:**
```json
{
  "users": ["alice"],
  "count": 1
}
```

### 3. Probar con Clave API Inválida

```bash
curl -H "X-API-Key: sk_invalid-key-12345" \
     http://127.0.0.1:5000/users
```

**Respuesta Esperada (401):**
```json
{
  "error": "Invalid API key",
  "message": "API key not recognized"
}
```

### 4. Probar sin Clave API

```bash
curl http://127.0.0.1:5000/users
```

**Respuesta Esperada (401):**
```json
{
  "error": "API key missing",
  "message": "Include X-API-Key header"
}
```

### 5. Rotar tu Clave API

```bash
curl -X POST -u alice:secret123 http://127.0.0.1:5000/api-key/rotate
```

**Respuesta Esperada:**
```json
{
  "message": "API key rotated. The previous key no longer works.",
  "username": "alice",
  "api_key": "sk_9fJk2LmQ0wE7rT1yU5iO3pA8sD6fG4hJ2kL0zX9cV7b",
  "warning": "Store this API key now. It will not be shown again."
}
```

Ahora repite el paso 2 con la clave **anterior** (401) y con la clave **nueva** (200).

### 6. Revocar tu Clave API

```bash
curl -X DELETE -u alice:secret123 http://127.0.0.1:5000/api-key
```

**Respuesta Esperada:**
```json
{
  "message": "API key revoked. Use POST /api-key/rotate to get a new one.",
  "username": "alice"
}
```

---

## Entendiendo el Flujo del Código

### Flujo de Registro

```python
@app.route('/register', methods=['POST'])
def register():
    # 1. Obtener usuario y contraseña del cuerpo JSON
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # 2. Validar entrada
    if not username or not password:
        return jsonify({'error': 'Usuario y contraseña requeridos'}), 400

    # 3. Comprobar si el usuario existe
    if username in users:
        return jsonify({'error': 'El usuario ya existe'}), 409

    # 4. Generar una clave API aleatoria
    api_key = generate_api_key()

    # 5. Guardar el hash de la contraseña y el HASH de la clave API
    users[username] = {
        'password': generate_password_hash(password),
        'api_key_hash': hash_api_key(api_key)
    }

    # 6. Devolver la clave API al cliente (la única vez)
    return jsonify({'api_key': api_key}), 201
```

### Flujo de Validación de Clave API

```python
def api_key_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        # 1. Extraer clave API de las cabeceras
        api_key = request.headers.get('X-API-Key')

        # 2. Comprobar si está presente
        if not api_key:
            return respuesta_error('Falta la clave API'), 401

        # 3. Hashearla y compararla con los hashes guardados (tiempo constante)
        if find_user_by_api_key(api_key) is None:
            return respuesta_error('Clave API inválida'), 401

        # 4. ¡Válida! Llamar función protegida
        return f(*args, **kwargs)

    return decorated
```

---

## Problemas Comunes y Soluciones

### Problema 1: "pip install secrets" falla

**Síntoma:**
```
ERROR: Could not find a version that satisfies the requirement secrets
```

**Solución:**
`secrets`, `hashlib` y `hmac` son parte de la librería estándar de Python. **No necesitas instalarlos.**
Solo impórtalos directamente:
```python
import hashlib
import hmac
import secrets
```

### Problema 2: Clave API No Funciona

**Síntoma:**
```json
{
  "error": "Invalid API key"
}
```

**Solución:**
- Verifica que estás usando la clave API exacta de la respuesta de registro o rotación **más reciente** (rotar invalida la clave anterior)
- Reiniciar el servidor borra todos los usuarios y claves (almacenamiento en memoria): vuelve a registrarte
- Comprueba espacios extra o comillas en la cabecera
- El nombre de cabecera es `X-API-Key` (insensible a mayúsculas en HTTP, así que `x-api-key` también funciona)

**Consejo de depuración:**
```bash
# Almacenar clave API en variable para evitar errores tipográficos
API_KEY="sk_Vq3o0m3k8X0bS2Yc1d5yGQ0q3ZpWm1x9lJ7cE4tR2uA"
curl -H "X-API-Key: $API_KEY" http://127.0.0.1:5000/users
```

### Problema 3: Error de Clave API Ausente

**Síntoma:**
```json
{
  "error": "API key missing"
}
```

**Solución:**
Asegúrate de incluir el flag `-H` con curl:
```bash
# Incorrecto (sin cabecera)
curl http://127.0.0.1:5000/users

# Incorrecto (clave en la URL: el servidor la ignora, y acaba en los logs)
curl "http://127.0.0.1:5000/users?api_key=TU_CLAVE"

# Correcto
curl -H "X-API-Key: TU_CLAVE" http://127.0.0.1:5000/users
```

### Problema 4: Decorador No Funciona

**Síntoma:**
Endpoint protegido accesible sin clave API.

**Solución:**
Asegúrate de que el decorador está aplicado:
```python
# Incorrecto
@app.route('/users', methods=['GET'])
def get_users():  # Falta @api_key_required
    ...

# Correcto
@app.route('/users', methods=['GET'])
@api_key_required  # Decorador aplicado
def get_users():
    ...
```

### Problema 5: "He perdido mi clave API, ¿cómo la recupero?"

No puedes, y es a propósito: el servidor solo guarda el hash. Llama a `POST /api-key/rotate` con tu usuario y contraseña para obtener una nueva.

---

## Criterios de Aceptación

Tu implementación debería:

- ✅ Generar claves API con `secrets.token_urlsafe(32)` (con el prefijo `sk_`)
- ✅ Guardar solo el **hash** SHA-256 de cada clave API, nunca la clave
- ✅ Devolver la clave API **una vez**, en el registro (y en la rotación)
- ✅ Validar claves API desde cabecera `X-API-Key`
- ✅ Comparar hashes con `hmac.compare_digest()`
- ✅ Rechazar peticiones sin clave API (401)
- ✅ Rechazar peticiones con clave API inválida (401)
- ✅ Rotar claves con `POST /api-key/rotate` (Auth Básica); la clave anterior deja de funcionar
- ✅ Revocar claves con `DELETE /api-key` (Auth Básica)
- ✅ Usar decorador personalizado para protección con clave API
- ✅ Permitir múltiples usuarios con claves API únicas

---

## Objetivos Adicionales

Una vez completes la implementación básica:

### 1. Añadir un Periodo de Gracia en la Rotación

Rotar una clave rompe todos los clientes que todavía usan la anterior. Mantén válido el hash anterior durante un tiempo corto para que los clientes puedan cambiar:

```python
from datetime import datetime, timedelta

users[current_user]['previous_api_key_hash'] = users[current_user]['api_key_hash']
users[current_user]['previous_valid_until'] = datetime.now() + timedelta(hours=24)
users[current_user]['api_key_hash'] = hash_api_key(new_api_key)
```

Después acepta cualquiera de los dos hashes en `find_user_by_api_key()` mientras no haya pasado `previous_valid_until`.

### 2. Añadir Expiración de Clave API

Registrar cuándo se crearon las claves API y expirar las antiguas:

```python
from datetime import datetime, timedelta

# En el registro y la rotación
users[username] = {
    'password': hashed_password,
    'api_key_hash': hash_api_key(api_key),
    'key_created_at': datetime.now()
}

# En el decorador, después de encontrar al usuario
created = users[username]['key_created_at']
if datetime.now() - created > timedelta(days=90):
    return jsonify({'error': 'API key expired', 'message': 'Rotate your key'}), 401
```

### 3. Añadir Limitación de Tasa

Rastrear llamadas API por clave y limitar peticiones (el Ejercicio 14 lo hace bien con Flask-Limiter):

```python
from collections import defaultdict
from datetime import datetime, timedelta

# Rastrear peticiones por usuario (nunca uses la clave en claro como clave del diccionario)
api_calls = defaultdict(list)  # {username: [timestamp1, timestamp2, ...]}

def api_key_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        api_key = request.headers.get('X-API-Key')
        username = find_user_by_api_key(api_key) if api_key else None
        if username is None:
            return jsonify({'error': 'Invalid API key'}), 401

        # Limitación de tasa: Máx 10 peticiones por minuto
        now = datetime.now()
        minute_ago = now - timedelta(minutes=1)

        # Eliminar llamadas antiguas
        api_calls[username] = [t for t in api_calls[username] if t > minute_ago]

        # Comprobar límite
        if len(api_calls[username]) >= 10:
            return jsonify({'error': 'Rate limit exceeded'}), 429

        # Registrar esta llamada
        api_calls[username].append(now)

        return f(*args, **kwargs)

    return decorated
```

### 4. Añadir Múltiples Claves API por Usuario

Permitir a los usuarios una clave por aplicación, para poder revocar una sin romper las demás. Guarda hashes, más un **id de clave** corto y no secreto para que los usuarios distingan sus claves:

```python
users = {
    'alice': {
        'password': 'hashed',
        'api_keys': {
            # id de clave -> metadatos (la clave en sí nunca se guarda)
            'k_1a2b': {'hash': 'sha256...', 'name': 'App Móvil', 'last4': 'tR2u'},
            'k_3c4d': {'hash': 'sha256...', 'name': 'Panel Web', 'last4': 'cV7b'}
        }
    }
}
```

### 5. Añadir Ámbitos (Scopes) a Claves API

Implementar permisos para claves API:

```python
users = {
    'alice': {
        'password': 'hashed',
        'api_keys': {
            'k_1a2b': {'hash': 'sha256...', 'scopes': ['read', 'write']},
            'k_3c4d': {'hash': 'sha256...', 'scopes': ['read']}  # Clave de solo lectura
        }
    }
}

def api_key_required(scopes=None):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            api_key = request.headers.get('X-API-Key', '')
            candidate_hash = hash_api_key(api_key)

            # Validar clave API y comprobar ámbitos
            for username, user_data in users.items():
                for key_id, key_info in user_data['api_keys'].items():
                    if hmac.compare_digest(key_info['hash'], candidate_hash):
                        if scopes and not set(scopes).issubset(key_info['scopes']):
                            return jsonify({'error': 'Insufficient permissions'}), 403
                        return f(*args, **kwargs)

            return jsonify({'error': 'Invalid API key'}), 401

        return decorated
    return decorator

# Uso
@app.route('/users', methods=['GET'])
@api_key_required(scopes=['read'])
def get_users():
    ...

@app.route('/users', methods=['POST'])
@api_key_required(scopes=['write'])
def create_user():
    ...
```

---

## Cuándo Usar Claves API vs Otros Métodos de Autenticación

### Usar Claves API Cuando:

✅ Construyes APIs públicas para desarrolladores terceros
✅ Permites acceso programático (scripts, bots)
✅ Necesitas revocar acceso sin cambiar contraseñas
✅ Quieres rastrear uso por aplicación
✅ Construyes comunicación servidor-a-servidor

### Usar Autenticación Básica Cuando:

✅ Paneles de administración simples
✅ Herramientas internas
✅ Autenticación temporal
✅ Prototipos rápidos
✅ Endpoints de gestión de claves (rotar/revocar), como en este ejercicio

### Usar JWT (Siguiente Ejercicio) Cuando:

✅ Se necesita autenticación sin estado
✅ Arquitectura de microservicios
✅ Aplicaciones móviles/web
✅ Necesitas tokens que expiren
✅ Quieres incrustar la identidad del usuario en el token

---

## Resumen

**Conclusiones Clave:**

1. **Claves API vs Autenticación Básica**
   - Las claves API son secretos aleatorios de larga duración
   - Auth Básica envía credenciales en cada petición
   - Claves API mejor para APIs públicas

2. **Generar Claves con `secrets`**
   - Librería estándar, no necesita instalación
   - `secrets.token_urlsafe(32)`: 256 bits aleatorios de un generador criptográficamente seguro
   - `uuid4` es para IDs únicos, no para secretos
   - Un prefijo reconocible (`sk_`) ayuda a los escáneres de secretos a detectar claves filtradas

3. **Guardar un Hash, Mostrar la Clave Una Vez**
   - El servidor guarda SHA-256(clave), nunca la clave
   - Un hash rápido vale para claves aleatorias de alta entropía; las contraseñas necesitan un hash lento y con sal
   - Compara con `hmac.compare_digest()`, nunca con `==`
   - ¿Clave perdida? Rota, no recuperes

4. **Autenticación Basada en Cabeceras**
   - Envía las claves en una cabecera (`X-API-Key`), nunca en URLs
   - Usa `request.headers.get('X-API-Key')`
   - Las cabeceras son insensibles a mayúsculas (`x-api-key` es la misma cabecera)

5. **Mejores Prácticas de Seguridad**
   - Hashea contraseñas y claves API, nunca almacenes texto plano
   - Guarda las claves en variables de entorno o un gestor de secretos, nunca en el código ni en Git
   - Rota las claves con regularidad y revoca inmediatamente las filtradas
   - Siempre usa HTTPS en producción

**Próximos Pasos:**
- **Ejercicio 11**: Autenticación JWT (tokens sin estado)
- **Ejercicio 10**: Consumir APIs Públicas Externas
- **Ejercicio 05**: Operaciones CRUD

¡Buena suerte! 🔑
