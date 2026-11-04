# Ejercicio 11: Autenticación con JSON Web Tokens (JWT)

## Objetivo

Aprender a implementar **autenticación sin estado** (stateless) utilizando JSON Web Tokens (JWT) en una API REST con FastAPI. Comprender por qué JWT es el método de autenticación preferido para APIs modernas, cómo difiere de la autenticación básica, y cómo usarlo de forma segura: access tokens de vida corta, refresh tokens, y verificación completa de firma, `exp`, `iss` y `aud`.

## Inicio Rápido

```bash
cd exercises/11-jwt-auth
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
copy .env.example .env  # Windows (cp en Linux/Mac)
fastapi dev app.py
```

Rellena los huecos (`_____`) de arriba abajo; la app arranca cuando el decorador de `/refresh` y el `Depends(...)` de `/profile` están completos: hasta entonces se para con `AttributeError: 'FastAPI' object has no attribute '_____'` (el decorador), o con `NameError: name '_____' is not defined` en Python 3.12/3.13 y `TypeError: ForwardRef('_____'...) is not a callable object` en Python 3.14 (el `Depends`). Los demás huecos (los nombres de los claims, `HS256`, el nombre del header, `DUMMY_HASH`, las funciones que crean los tokens, el tipo de token y el conjunto `revoked`) solo se usan cuando una petición llega hasta ellos, así que los notarás al probar. La API corre en `http://127.0.0.1:8000`.

Opcional, pero recomendado: da al secreto de firma un valor fijo en `.env` **antes** de `fastapi dev app.py`. Si no lo haces, el servidor genera uno aleatorio en cada arranque y tus tokens dejan de funcionar tras reiniciar. Genera un valor y pégalo detrás de `JWT_SECRET_KEY=` en `.env`:

```bash
python -c "import secrets; print(secrets.token_hex(32))"
```

- `app.py` carga `.env` al arrancar con `load_dotenv()` (del paquete `python-dotenv`), así que `os.environ.get("JWT_SECRET_KEY")` lo encuentra.
- `.env` está en `.gitignore`, así que el secreto nunca llega a GitHub. `.env.example` solo tiene valores vacíos y **sí** se sube: indica a los demás qué variables tienen que definir.
- `fastapi dev` se reinicia cuando guardas un fichero `.py`, no `.env`: después de editar `.env`, para la app (Ctrl+C) y vuelve a arrancarla.
- Una variable definida en el terminal (`$env:JWT_SECRET_KEY=...`, `set`, `export`) sigue funcionando y tiene prioridad sobre `.env`.

---

## ¿Qué es la Autenticación JWT?

### El Problema con Basic Auth

En el Ejercicio 08, aprendiste Autenticación Básica donde:
- El cliente envía **usuario y contraseña con CADA petición**
- Las credenciales están codificadas en Base64 (¡no encriptadas!)
- El servidor debe verificar credenciales en cada petición
- Las credenciales viajan constantemente por la red (riesgo de seguridad)

### La Solución JWT

**JWT (JSON Web Token)** proporciona **autenticación sin estado**:
1. El cliente envía usuario/contraseña **UNA SOLA VEZ** a `/login`
2. El servidor valida y devuelve dos **tokens firmados**: un **access token** de vida corta y un **refresh token** de vida más larga
3. El cliente envía el access token en cada petición
4. El servidor valida la firma y los claims del token (¡no necesita consultar la base de datos!)
5. Cuando el access token expira (15 minutos), el cliente llama a `/refresh` con el refresh token para obtener uno nuevo
6. **Ya no se envían contraseñas por la red después del login**

### Estructura de JWT

Un token JWT tiene tres partes separadas por puntos:
```
eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiJ1c2VyMSIsImV4cCI6MTY3ODg4ODg4OH0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
│                                      │                                      │
│                                      │                                      └─ Firma (verifica que el token no ha sido alterado)
│                                      └─ Payload (identidad del usuario, expiración, emisor, audiencia...)
└─ Header (algoritmo y tipo de token)
```

**Conceptos Clave:**
- **Auto-contenido**: Contiene toda la info del usuario necesaria (sin consultar BD)
- **Sin estado**: El servidor no almacena sesiones
- **Firmado**: El servidor puede verificar que no fue modificado
- **Solo codificado, no encriptado**: Cualquiera que tenga el token puede leer el payload
- **Expiración**: Los access tokens expiran a los **15 minutos**; los refresh tokens al día

### Access Token vs Refresh Token

| | Access token | Refresh token |
|---|---|---|
| **Se usa para** | Cada petición a la API (`/profile`, `/users`...) | Solo `POST /refresh` |
| **Duración** | Corta (15 minutos) | Más larga (1 día en este ejercicio) |
| **Si lo roban** | Útil para el atacante 15 minutos como mucho | Se puede revocar con `/logout` |
| **Se envía** | En cada petición | Raramente |

Los access tokens cortos limitan el daño de un token robado; el refresh token evita que el usuario tenga que escribir su contraseña cada 15 minutos.

---

## Estructura de la API

### Endpoints Públicos (Sin Autenticación)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| POST | `/register` | Registrar una nueva cuenta de usuario |
| POST | `/login` | Iniciar sesión con credenciales, obtener access + refresh tokens |

### Gestión de Tokens

| Método | Endpoint | Token Requerido | Descripción |
|--------|----------|-----------------|-------------|
| POST | `/refresh` | **Refresh** token | Obtener un access token nuevo |
| POST | `/logout` | Access **o** refresh token | Revocar el token que envías |

### Endpoints Protegidos (Requieren Access Token)

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/profile` | Obtener información del perfil del usuario actual |
| GET | `/users` | Obtener lista de todos los usuarios |
| GET | `/protected` | Recurso protegido de ejemplo |

---

## Cómo Funciona la Autenticación JWT

### Flujo Paso a Paso

```
1. Registro de Usuario
   Cliente                   Servidor
     |                         |
     |  POST /register         |
     |  {username, password}   |
     |------------------------>|
     |                         | • Validar entrada
     |                         | • Hashear contraseña
     |                         | • Almacenar usuario
     |  201 Created            |
     |<------------------------|

2. Login de Usuario (Obtener Tokens)
   Cliente                   Servidor
     |                         |
     |  POST /login            |
     |  {username, password}   |
     |------------------------>|
     |                         | • Validar credenciales
     |                         | • Crear access token (15 min)
     |                         | • Crear refresh token (1 día)
     |                         | • Firmar ambos con el secreto
     |  200 OK                 |
     |  {access_token,         |
     |   refresh_token}        |
     |<------------------------|
     | Guardar tokens          |
     | de forma segura         |

3. Acceder a Recurso Protegido
   Cliente                   Servidor
     |                         |
     | GET /profile            |
     | Authorization: Bearer   |
     | <access_token>          |
     |------------------------>|
     |                         | • Verificar firma
     |                         | • Verificar exp, iss, aud
     |                         | • Comprobar que no está revocado
     |                         | • Extraer identidad del usuario
     |  200 OK                 |
     |  {datos del usuario}    |
     |<------------------------|

4. Access Token Expirado -> Refresh
   Cliente                   Servidor
     |                         |
     | POST /refresh           |
     | Authorization: Bearer   |
     | <refresh_token>         |
     |------------------------>|
     |                         | • Verificar que es un REFRESH token
     |                         | • Crear access token nuevo
     |  200 OK                 |
     |  {access_token}         |
     |<------------------------|
```

---

## Detalles de Implementación

### 1. Configuración de JWT

```python
import os
import secrets
import uuid
from datetime import datetime, timedelta, timezone

import jwt  # PyJWT

# El secreto viene del entorno, nunca del código.
# Alternativa: un secreto aleatorio por ejecución (los tokens mueren al reiniciar el servidor).
JWT_SECRET = os.environ.get("JWT_SECRET_KEY") or secrets.token_hex(32)
JWT_ALG = "HS256"

# Emisor (iss) y audiencia (aud)
JWT_ISSUER = "notes-api"
JWT_AUDIENCE = "notes-client"

# Tokens revocados, por su id único (el claim jti)
revoked: set[str] = set()
```

PyJWT es una librería pequeña y dos funciones hacen el trabajo de verdad. Estas son las tres líneas que debes recordar:

```python
token = jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALG)                                               # crear y firmar
claims = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG], issuer=JWT_ISSUER, audience=JWT_AUDIENCE)  # verificar y leer
jwt.decode(token, options={"verify_signature": False})                                                  # solo para MIRAR dentro de un token
```

`jwt.decode` comprueba la firma y `exp` por ti, y `iss` y `aud` cuando le pasas `issuer=` y `audience=`. Fija siempre `algorithms=[...]`: nunca dejes que el token decida cómo se verifica.

**Nunca** escribas el secreto en el código (`JWT_SECRET = "tu_clave_secreta"`): cualquiera que lea el repositorio podría falsificar tokens válidos para cualquier usuario.

**Los claims que ponemos en cada token:**
- `sub` (**subject**, sujeto): el usuario. `iat` / `exp`: emitido / expira. Los access tokens duran 15 minutos, los refresh tokens 1 día
- `iss` (**issuer**, emisor): quién creó el token. Rechazamos tokens creados por otro, aunque usen el mismo secreto
- `aud` (**audience**, audiencia): para quién es el token. Un token emitido para otra API (ej. la API de facturación) no debe aceptarse en esta
- `jti` (**JWT ID**): un id único (`uuid4`) por token. La lista de bloqueo del logout guarda estos ids
- `type`: `"access"` o `"refresh"`, para que un refresh token no sirva como access token, ni al revés

Crear los dos tipos de token es una función pequeña:

```python
def create_token(username: str, token_type: str, lifetime: timedelta) -> str:
    now = datetime.now(timezone.utc)
    claims = {
        "sub": username,
        "iat": now,
        "exp": now + lifetime,
        "iss": JWT_ISSUER,
        "aud": JWT_AUDIENCE,
        "jti": str(uuid.uuid4()),
        "type": token_type,
    }
    return jwt.encode(claims, JWT_SECRET, algorithm=JWT_ALG)

def create_access_token(username: str) -> str:
    return create_token(username, "access", timedelta(minutes=15))

def create_refresh_token(username: str) -> str:
    return create_token(username, "refresh", timedelta(days=1))
```

Y **una** función comprueba todo a la entrada: firma, `exp`, `iss`, `aud`, `type` y revocación. `require` hace inválido un token al que le falten esos claims:

```python
def decode_token(token: str, expected_type: str | None) -> dict:
    try:
        claims = jwt.decode(
            token, JWT_SECRET, algorithms=[JWT_ALG],
            issuer=JWT_ISSUER, audience=JWT_AUDIENCE,
            options={"require": ["sub", "exp", "iss", "aud", "jti", "type"]},
        )
    except jwt.ExpiredSignatureError:
        raise unauthorized("Token has expired")
    except jwt.InvalidTokenError:  # firma incorrecta, iss o aud distintos, malformado...
        raise unauthorized("Invalid token")
    if expected_type is not None and claims["type"] != expected_type:
        raise unauthorized(f"Wrong token type: expected {expected_type}")
    if claims["jti"] in revoked:
        raise unauthorized("Token has been revoked")
    return claims
```

`unauthorized(...)` construye `HTTPException(401, detail=..., headers={"WWW-Authenticate": "Bearer"})`. Con `expected_type=None` se acepta cualquiera de los dos tipos (solo lo usa `/logout`).

### 2. Registro de Usuario (Público)

```python
@app.post("/register", status_code=201)
def register(data: UserCreate) -> dict[str, str]:
    if data.username in users:
        raise HTTPException(status_code=409, detail="User already exists")
    # Almacenar el hash bcrypt, nunca la contraseña
    users[data.username] = hash_password(data.password)
    return {"message": "User registered successfully", "username": data.username}
```

`UserCreate` es el modelo Pydantic del Ejercicio 08 (contraseña de 8 a 72 caracteres).

### 3. Endpoint de Login (Público)

**¡Aquí es donde JWT difiere de Basic Auth!**

```python
class Credentials(BaseModel):
    username: str
    password: str

@app.post("/login")
def login(data: Credentials) -> LoginResponse:
    # Comprobar siempre una contraseña, aunque el usuario no exista
    password_ok = verify_password(data.password, users.get(data.username, DUMMY_HASH))
    if data.username not in users or not password_ok:
        raise unauthorized("Invalid credentials")

    # Generar ambos tokens con la identidad del usuario
    return LoginResponse(
        message="Login successful",
        access_token=create_access_token(data.username),
        refresh_token=create_refresh_token(data.username),
        expires_in=15 * 60,
    )
```

`LoginResponse` amplía `TokenPair(access_token, refresh_token, token_type="bearer")` con `message` y `expires_in`.

> **Login con JSON, no con el formulario de contraseña.** El tutorial de FastAPI hace el login con `OAuth2PasswordRequestForm`, un formulario que implementa el **password grant** de OAuth. OAuth 2.1 eliminó ese grant (verás por qué en el Ejercicio 13), así que aquí `/login` recibe un cuerpo JSON normal y los tokens viajan con `HTTPBearer`. Swagger UI (`/docs`) sigue mostrando un botón "Authorize" para el token.

**¿Por qué el hash ficticio?** `bcrypt.checkpw` es lento a propósito (unos cientos de milisegundos). Si un usuario desconocido respondiera al instante, un atacante podría medir el tiempo de respuesta y averiguar **qué usuarios existen** (enumeración de usuarios). Comprobar contra un hash ficticio hace que ambos fallos tarden lo mismo, y ambos devuelven el mismo mensaje. `Credentials` usa campos `str` simples (sin límites de longitud), así que unas credenciales incorrectas siempre responden `401`, nunca `422`.

**Diferencias Clave con el Ejercicio 08:**
- ❌ NO hay dependencia `HTTPBasic`
- ❌ NO hay header HTTP Basic Auth
- ✅ Credenciales enviadas en el cuerpo JSON
- ✅ Devuelve tokens JWT en lugar de sesión

### 4. Endpoints Protegidos (Requieren JWT)

`HTTPBearer` lee `Authorization: Bearer <token>`. Con `auto_error=False`, si falta el header recibimos `None` y devolvemos nuestro propio mensaje `401` y la cabecera `WWW-Authenticate` (por defecto FastAPI responde un `401 Not authenticated` genérico). Dos dependencias pequeñas, una sobre otra, sustituyen a un decorador de "login requerido":

```python
bearer = HTTPBearer(auto_error=False)

def get_token(creds: Annotated[HTTPAuthorizationCredentials | None, Depends(bearer)]) -> str:
    if creds is None:
        raise unauthorized("Missing or invalid token")
    return creds.credentials

def get_current_user(token: Annotated[str, Depends(get_token)]) -> str:
    return decode_token(token, "access")["sub"]

@app.get("/profile")
def profile(user: Annotated[str, Depends(get_current_user)]) -> dict[str, str]:  # ← valida el access token
    return {"username": user, "profile": f"Profile information for {user}", "account_created": "2025-01-01"}
```

**Cómo funciona `get_current_user`** (toda ruta que la lista en sus parámetros queda protegida):
1. Extrae el token del header `Authorization: Bearer <token>` (sin header: `401`)
2. Verifica la firma usando `JWT_SECRET`
3. Comprueba que el token no ha expirado (`exp`)
4. Comprueba el emisor (`iss`) y la audiencia (`aud`)
5. Comprueba que es un token de **acceso** (los refresh tokens se rechazan aquí)
6. Comprueba que no está en la lista de bloqueo (logout)
7. Devuelve el usuario (`sub`) a la ruta

### 5. Endpoint de Refresh

```python
@app.post("/refresh")
def refresh(token: Annotated[str, Depends(get_token)]) -> dict[str, str | int]:
    claims = decode_token(token, "refresh")  # ← SOLO se aceptan refresh tokens
    return {"access_token": create_access_token(claims["sub"]), "token_type": "bearer", "expires_in": 900}
```

### 6. Logout (Revocación de Tokens)

Los JWT no tienen estado, así que el servidor no puede "borrar" uno. Para revocar un token antes de que expire, guardamos una **lista de bloqueo** con los ids de los tokens revocados (el claim `jti`) y `decode_token` la comprueba en cada petición (el conjunto `revoked` del paso 1):

```python
@app.post("/logout")
def logout(token: Annotated[str, Depends(get_token)]) -> dict[str, str]:
    claims = decode_token(token, None)  # acepta access O refresh tokens
    revoked.add(claims["jti"])
    return {"message": f"{claims['type'].capitalize()} token revoked"}
```

Llama a `/logout` una vez con el access token y otra con el refresh token para cerrar la sesión por completo.

---

## Probar la API

> Los comandos siguientes usan `curl` con comillas de `bash`. En **CMD de Windows** usa `example/commands_cmd.txt`, y en **PowerShell** usa `example/commands_powershell.txt`.

### 1. Registrar un Usuario

```bash
curl -X POST http://127.0.0.1:8000/register \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret123"}'
```

**Respuesta Esperada:**
```json
{
  "message": "User registered successfully",
  "username": "alice"
}
```

### 2. Iniciar Sesión y Obtener Tokens JWT

```bash
curl -X POST http://127.0.0.1:8000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret123"}'
```

**Respuesta Esperada:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "message": "Login successful",
  "expires_in": 900
}
```

**Guarda ambos tokens** - ¡los necesitarás para las siguientes peticiones!

### 3. Acceder a Endpoint Protegido con Token

Reemplaza `<TU_TOKEN>` con el `access_token` del paso 2:

```bash
curl -X GET http://127.0.0.1:8000/profile \
  -H "Authorization: Bearer <TU_TOKEN>"
```

**Respuesta Esperada:**
```json
{
  "username": "alice",
  "profile": "Profile information for alice",
  "account_created": "2025-01-01"
}
```

### 4. Intentar SIN Token (Debe Fallar)

```bash
curl -X GET http://127.0.0.1:8000/profile
```

**Respuesta Esperada (401, con el header `WWW-Authenticate: Bearer`):**
```json
{
  "detail": "Missing or invalid token"
}
```

### 5. Obtener Todos los Usuarios (Protegido)

```bash
curl -X GET http://127.0.0.1:8000/users \
  -H "Authorization: Bearer <TU_TOKEN>"
```

### 6. Obtener un Access Token Nuevo con el Refresh Token

```bash
curl -X POST http://127.0.0.1:8000/refresh \
  -H "Authorization: Bearer <TU_REFRESH_TOKEN>"
```

**Respuesta Esperada:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "expires_in": 900
}
```

Prueba con el **access** token en su lugar: obtienes `401 {"detail": "Wrong token type: expected refresh"}`.

### 7. Logout

```bash
curl -X POST http://127.0.0.1:8000/logout \
  -H "Authorization: Bearer <TU_TOKEN>"
```

**Respuesta Esperada:**
```json
{
  "message": "Access token revoked"
}
```

Usar ese token otra vez devuelve `401 {"detail": "Token has been revoked"}`.

---

## Entendiendo los Tokens JWT

### Inspeccionar tu Token (en Local)

El payload solo está **codificado en Base64URL**, así que puedes leerlo sin el secreto. Hazlo **en local**: nunca pegues un token real en una web. Quien tenga el token puede usarlo hasta que expire.

**Opción 1: Python puro (sin librerías)**
```python
import base64, json

token = "eyJ..."                      # tu access_token
payload = token.split('.')[1]         # header.PAYLOAD.firma
payload += '=' * (-len(payload) % 4)  # restaurar el relleno Base64
print(json.dumps(json.loads(base64.urlsafe_b64decode(payload)), indent=2))
```

**Opción 2: PyJWT (ya instalado con `requirements.txt`)**
```python
import jwt
print(jwt.decode("eyJ...", options={"verify_signature": False}))
```

`verify_signature: False` es **solo** para mirar dentro de un token. Nunca lo uses para autenticar una petición.

Verás algo como:

```json
{
  "sub": "alice",
  "iat": 1793281345,
  "exp": 1793282245,
  "iss": "notes-api",
  "aud": "notes-client",
  "jti": "72526770-fdda-4e67-ada3-0f9d265c83be",
  "type": "access"
}
```

| Claim | Significado |
|-------|-------------|
| `sub` | Sujeto: la identidad del usuario |
| `iat` / `exp` | Emitido / expira (timestamps Unix). `exp - iat` = 900 s = 15 min |
| `iss` | Emisor: quién creó el token |
| `aud` | Audiencia: para quién es el token |
| `jti` | Id único del token (lo usa la lista de bloqueo del logout) |
| `type` | `access` o `refresh` |

Los decodificadores online como jwt.io valen para **tokens desechables** que creas para una demo, nunca para tokens reales.

**Importante:** El token está **firmado**, no **encriptado**:
- ✅ El servidor puede verificar que no ha sido alterado
- ❌ Cualquiera puede leer el contenido: **nunca pongas datos sensibles en el payload** (contraseñas, datos personales, IDs internos que no enseñarías al usuario...)
- ✅ Si alguien modifica el payload, la verificación de firma falla

---

## Comparación JWT vs Basic Auth

| Característica | Basic Auth (Ejercicio 08) | JWT (Ejercicio 11) |
|----------------|---------------------------|-------------------|
| **Credenciales enviadas** | Cada petición | Solo en el login |
| **Con/Sin estado** | Sin estado (pero menos seguro) | Sin estado |
| **Almacenamiento en servidor** | Sin sesiones | Sin sesiones (solo una lista de bloqueo para el logout) |
| **Consulta a base de datos** | Cada petición | Solo en el login |
| **Escalabilidad** | Buena | Excelente |
| **Seguridad** | Base64 (no seguro) | Tokens firmados |
| **Expiración de token** | No | Sí (15 min el access, refresh para renovar) |
| **Compatible Móvil/SPA** | No ideal | Perfecto |
| **Caso de uso** | APIs simples, pruebas | APIs de producción |

### Cuándo Usar Cada Uno

**Basic Auth:**
- Herramientas internas
- Prototipos rápidos
- Desarrollo/pruebas
- APIs simples servidor-a-servidor

**JWT:**
- Aplicaciones web de producción
- Apps móviles
- Single Page Applications (React, Vue, Angular)
- Arquitectura de microservicios
- APIs accedidas por múltiples clientes

---

## Mejores Prácticas de Seguridad

### ✅ HACER

1. **Usar HTTPS en producción** - Los tokens pueden ser interceptados en HTTP
2. **Access tokens de vida corta** - 15 minutos, como en este ejercicio
3. **Usar refresh tokens** - Para sesiones largas sin re-login, y revocarlos en el logout
4. **Verificarlo todo** - Firma, `exp`, `iss` y `aud` (`jwt.decode` con `issuer=` y `audience=`, como arriba)
5. **Almacenar tokens de forma segura**:
   - Web: Cookies `httpOnly` (JavaScript no puede leer el token, así que un XSS no puede robarlo)
   - Móvil: Almacenamiento seguro (Keychain, KeyStore)
   - NO en localStorage (vulnerable a XSS)
6. **Usar claves secretas fuertes** - Aleatorias, largas, desde una variable de entorno o un gestor de secretos
7. **Validar todas las entradas** - Verificar formato de usuario/contraseña

### ❌ NO HACER

1. **No poner datos sensibles en JWT** - Solo está codificado; cualquiera puede decodificarlo
2. **No escribir el secreto en el código ni usar secretos débiles** - Hace los tokens fáciles de falsificar
3. **No omitir HTTPS** - Los tokens pueden ser robados
4. **No hacer tokens válidos para siempre** - Riesgo de seguridad
5. **No pegar tokens reales en decodificadores online** - Decodifícalos en local
6. **No revelar qué usuarios existen** - Mismo mensaje y mismo tiempo para "usuario desconocido" y "contraseña incorrecta"
7. **No almacenar contraseñas en texto plano** - Siempre hashear

---

## Errores Comunes y Soluciones

Todo fallo de autenticación responde `401` con un header `WWW-Authenticate: Bearer` y un mensaje en `detail`. Al cliente solo le hace falta saber "consigue un token válido", así que una firma incorrecta, un emisor equivocado y un token malformado comparten el mismo mensaje.

### 1. Falta el Header de Autorización (401)

```json
{"detail": "Missing or invalid token"}
```

**Solución:** Añadir header a la petición:
```bash
-H "Authorization: Bearer <token>"
```

### 2. Token Inválido (401)

```json
{"detail": "Invalid token"}
```

**Causas:**
- El token fue modificado
- `JWT_SECRET_KEY` incorrecta
- El token fue generado por otro servidor, **o por el mismo servidor antes de un reinicio** (si `JWT_SECRET_KEY` no está definida, el secreto es aleatorio en cada ejecución)

### 3. Emisor o Audiencia Incorrectos (401)

```json
{"detail": "Invalid token"}
```

**Causa:** El token no lo creó esta API (`iss`), o se creó para otra distinta (`aud`). PyJWT lanza `InvalidIssuerError` o `InvalidAudienceError`; nuestro `except jwt.InvalidTokenError` captura ambas.

### 4. Token Expirado (401)

```json
{"detail": "Token has expired"}
```

**Solución:** Llama a `POST /refresh` con tu refresh token. Si el refresh token también ha expirado, inicia sesión de nuevo.

### 5. Tipo de Token Incorrecto (401)

```json
{"detail": "Wrong token type: expected refresh"}
```

**Causa:** Enviaste el access token a `/refresh`, o el refresh token a un endpoint protegido.

### 6. Token Revocado (401)

```json
{"detail": "Token has been revoked"}
```

**Causa:** Llamaste a `/logout` con ese token. Inicia sesión de nuevo.

### 7. Token Malformado (401)

```json
{"detail": "Invalid token"}
```

**Causa:** El token está incompleto o tiene caracteres de más (normalmente un problema al copiar/pegar)
**Solución:** Copia de nuevo el token completo, sin comillas ni saltos de línea

### 8. Falta "Bearer" (401)

```json
{"detail": "Missing or invalid token"}
```

**Solución:** Asegúrate de que el formato es `Bearer <token>`, no solo `<token>`

---

## Criterios de Aceptación

Tu implementación debería:

- ✅ Permitir registro de usuarios vía POST `/register`
- ✅ Aceptar credenciales de login en cuerpo JSON (no en header Authorization)
- ✅ Devolver un `access_token` (15 minutos) **y** un `refresh_token` en login exitoso
- ✅ Leer `JWT_SECRET_KEY` del entorno (con alternativa aleatoria)
- ✅ Poner `iss`, `aud`, `jti` y `type` en cada token, y verificar `iss`, `aud` y `type` en cada petición
- ✅ Emitir access tokens nuevos vía POST `/refresh`, aceptando solo refresh tokens
- ✅ Revocar tokens vía POST `/logout` (lista de bloqueo de `jti`)
- ✅ Proteger rutas con `Depends(get_current_user)`
- ✅ Obtener la identidad del usuario del claim `sub`
- ✅ Devolver 401 (con `WWW-Authenticate: Bearer`) para credenciales inválidas, con el mismo tiempo para usuarios desconocidos y contraseñas incorrectas
- ✅ Devolver 401 para tokens JWT faltantes/expirados/revocados/de tipo incorrecto
- ✅ Hashear contraseñas antes de almacenar
- ✅ Usar formato de respuesta de error consistente

---

## Objetivos Adicionales

Una vez completes la implementación básica:

1. **Rotación de Refresh Tokens**
   Devuelve un refresh token **nuevo** desde `/refresh` y revoca el anterior, para que un refresh token robado solo pueda usarse una vez:
   ```python
   @app.post("/refresh")
   def refresh(token: Annotated[str, Depends(get_token)]) -> dict[str, str]:
       claims = decode_token(token, "refresh")
       revoked.add(claims["jti"])
       return {
           "access_token": create_access_token(claims["sub"]),
           "refresh_token": create_refresh_token(claims["sub"]),
       }
   ```

2. **Lista de Bloqueo Persistente**
   Guarda los `jti` revocados en Redis con una expiración igual a la vida restante del token, para que la lista sobreviva a reinicios y no crezca sin límite.

3. **Tokens Fresh para Acciones Sensibles**
   Añade un claim `"fresh": True` al access token creado en el login (y `False` a los creados por `/refresh`), y escribe una segunda dependencia que rechace los tokens que no sean fresh. Úsala en los endpoints sensibles, para que los tokens obtenidos vía `/refresh` no sirvan para ellos.

4. **Añadir Actualización de Perfil de Usuario**
   PATCH, no PUT: el cliente envía solo los campos que cambia (Ejercicio 05).
   ```python
   @app.patch("/profile")
   def update_profile(user: Annotated[str, Depends(get_current_user)]):
       # Actualizar solo los campos enviados
       ...
   ```

5. **Añadir Endpoint de Cambio de Contraseña**
   - Requerir contraseña actual para verificación
   - Hashear nueva contraseña antes de almacenar
   - Revocar los tokens existentes del usuario

---

## Próximos Pasos

**Ejercicio 12:** Roles y Permisos: añade **Autorización** a tus tokens JWT
- Ejercicio actual: **Autenticación** (quién eres)
- Ejercicio 12: **Autorización** (qué puedes hacer)
- JWT incluirá claims de roles (admin, usuario, etc.)

**Ejercicio 13:** OAuth con GitHub (Authorization Code + PKCE): deja que los usuarios inicien sesión con un proveedor de identidad externo

---

## Recursos Adicionales

- [Documentación PyJWT](https://pyjwt.readthedocs.io/)
- [FastAPI: Seguridad](https://fastapi.tiangolo.com/tutorial/security/)
- [FastAPI: Dependencias](https://fastapi.tiangolo.com/tutorial/dependencies/)
- [RFC 7519 - Especificación JWT](https://tools.ietf.org/html/rfc7519)
- [OWASP JWT Cheat Sheet](https://cheatsheetseries.owasp.org/cheatsheets/JSON_Web_Token_for_Java_Cheat_Sheet.html)

---

## Resumen

**Puntos Clave:**

1. **JWT = Autenticación Sin Estado**
   - Enviar credenciales una vez, obtener tokens
   - Usar el access token para todas las peticiones subsiguientes
   - No se necesitan sesiones del lado del servidor

2. **Estructura JWT**
   - Header + Payload + Firma
   - Firmado (verificable) pero solo codificado, no encriptado (legible)
   - Contiene identidad del usuario, expiración, emisor y audiencia

3. **Flujo de Buenas Prácticas**
   - POST /login con cuerpo JSON → obtener access token (15 min) + refresh token
   - Almacenar tokens de forma segura
   - Enviar el access token en header Authorization: `Bearer <token>`
   - Cuando expire, POST /refresh con el refresh token
   - POST /logout para revocar tokens
   - Todas las rutas protegidas usan `Depends(get_current_user)`

4. **Seguridad**
   - Usar HTTPS en producción
   - Access tokens de vida corta + refresh tokens
   - Verificar firma, `exp`, `iss` y `aud`
   - Secreto desde el entorno, nunca en el código
   - Nunca poner datos sensibles en el payload JWT, y decodificar tokens en local
   - Misma respuesta y mismo tiempo para usuarios desconocidos y contraseñas incorrectas

5. **Autenticación ≠ Autorización**
   - Este ejercicio: ¿Quién eres? (Autenticación)
   - Ejercicio 12: ¿Qué puedes hacer? (Autorización con roles)

¡Buena suerte! 🚀
