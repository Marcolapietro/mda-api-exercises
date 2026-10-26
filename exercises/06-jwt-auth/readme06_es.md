# Ejercicio 6: Autenticación con JSON Web Tokens (JWT)

## Objetivo

Aprender a implementar **autenticación sin estado** (stateless) utilizando JSON Web Tokens (JWT) en una API REST con Flask. Comprender por qué JWT es el método de autenticación preferido para APIs modernas, cómo difiere de la autenticación básica, y cómo usarlo de forma segura: access tokens de vida corta, refresh tokens, y verificación completa de firma, `exp`, `iss` y `aud`.

## Inicio Rápido

```bash
cd exercises/06-jwt-auth
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
python app.py
```

Opcional, pero recomendado: define el secreto de firma en una variable de entorno **antes** de `python app.py`. Si no lo haces, el servidor genera uno aleatorio en cada arranque y tus tokens dejan de funcionar tras reiniciar.

```bash
# Windows PowerShell
$env:JWT_SECRET_KEY = python -c "import secrets; print(secrets.token_hex(32))"
# Windows CMD: genéralo una vez y pégalo
python -c "import secrets; print(secrets.token_hex(32))"
set JWT_SECRET_KEY=<pega el valor>
# Linux/Mac
export JWT_SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
```

---

## ¿Qué es la Autenticación JWT?

### El Problema con Basic Auth

En el Ejercicio 04, aprendiste Autenticación Básica donde:
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
from datetime import timedelta
from flask_jwt_extended import JWTManager

# El secreto viene del entorno, nunca del código.
# Alternativa: un secreto aleatorio por ejecución (los tokens mueren al reiniciar el servidor).
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY') or secrets.token_hex(32)

# Access tokens de vida corta + refresh tokens de vida más larga
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(minutes=15)
app.config['JWT_REFRESH_TOKEN_EXPIRES'] = timedelta(days=1)

# Emisor (iss) y audiencia (aud)
JWT_ISSUER = 'mda-api-exercises'
JWT_AUDIENCE = 'mda-api-clients'
app.config['JWT_ENCODE_ISSUER'] = JWT_ISSUER      # se escribe en nuestros tokens
app.config['JWT_DECODE_ISSUER'] = JWT_ISSUER      # se exige en los tokens recibidos
app.config['JWT_ENCODE_AUDIENCE'] = JWT_AUDIENCE
app.config['JWT_DECODE_AUDIENCE'] = JWT_AUDIENCE

jwt = JWTManager(app)
```

**Nunca** escribas el secreto en el código (`JWT_SECRET_KEY = 'tu_clave_secreta'`): cualquiera que lea el repositorio podría falsificar tokens válidos para cualquier usuario.

**¿Qué son `iss` y `aud`?**
- `iss` (**issuer**, emisor): quién creó el token. Rechazamos tokens creados por otro, aunque usen el mismo secreto
- `aud` (**audience**, audiencia): para quién es el token. Un token emitido para otra API (ej. la API de facturación) no debe aceptarse en esta
- Los ajustes `ENCODE_*` añaden el claim a los tokens que creamos; los ajustes `DECODE_*` hacen que `@jwt_required()` **rechace** cualquier token cuyo claim falte o sea distinto

### 2. Registro de Usuario (Público)

```python
@app.route('/register', methods=['POST'])
def register():
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Almacenar usuario con contraseña hasheada
    users[username] = {
        'password': generate_password_hash(password)
    }
    return jsonify({'message': 'Usuario registrado'}), 201
```

### 3. Endpoint de Login (Público)

**¡Aquí es donde JWT difiere de Basic Auth!**

```python
# Hash de una contraseña aleatoria, creado una vez al arrancar
DUMMY_PASSWORD_HASH = generate_password_hash(secrets.token_urlsafe(16))

@app.route('/login', methods=['POST'])
def login():
    # Obtener credenciales del CUERPO DE LA PETICIÓN, no del header Authorization
    data = request.get_json()
    username = data.get('username')
    password = data.get('password')

    # Comprobar siempre una contraseña, aunque el usuario no exista
    user = users.get(username)
    password_hash = user['password'] if user else DUMMY_PASSWORD_HASH
    password_ok = check_password_hash(password_hash, password)

    if not user or not password_ok:
        return jsonify({'error': 'Invalid credentials'}), 401

    # Generar ambos tokens con la identidad del usuario
    access_token = create_access_token(identity=username)
    refresh_token = create_refresh_token(identity=username)
    return jsonify({'access_token': access_token,
                    'refresh_token': refresh_token}), 200
```

**¿Por qué el hash ficticio?** `check_password_hash` es lento a propósito (unos 100 ms). Si un usuario desconocido respondiera al instante, un atacante podría medir el tiempo de respuesta y averiguar **qué usuarios existen** (enumeración de usuarios). Comprobar contra un hash ficticio hace que ambos fallos tarden lo mismo, y ambos devuelven el mismo mensaje.

**Diferencias Clave con el Ejercicio 04:**
- ❌ NO hay decorador `@auth.login_required`
- ❌ NO hay header HTTP Basic Auth
- ✅ Credenciales enviadas en el cuerpo JSON
- ✅ Devuelve tokens JWT en lugar de sesión

### 4. Endpoints Protegidos (Requieren JWT)

```python
@app.route('/profile', methods=['GET'])
@jwt_required()  # ← Valida el access token
def profile():
    # Extraer identidad del usuario del token
    current_user = get_jwt_identity()
    return jsonify({'username': current_user}), 200
```

**Cómo funciona `@jwt_required()`:**
1. Extrae el token del header `Authorization: Bearer <token>`
2. Verifica la firma del token usando `JWT_SECRET_KEY`
3. Comprueba que el token no ha expirado (`exp`)
4. Comprueba el emisor (`iss`) y la audiencia (`aud`)
5. Comprueba que es un token de **acceso** (los refresh tokens se rechazan aquí)
6. Comprueba que no está en la lista de bloqueo (logout)
7. Hace disponible la identidad del usuario vía `get_jwt_identity()`

### 5. Endpoint de Refresh

```python
@app.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)  # ← SOLO se aceptan refresh tokens
def refresh():
    current_user = get_jwt_identity()
    access_token = create_access_token(identity=current_user)
    return jsonify({'access_token': access_token}), 200
```

### 6. Logout (Revocación de Tokens)

Los JWT no tienen estado, así que el servidor no puede "borrar" uno. Para revocar un token antes de que expire, guardamos una **lista de bloqueo** con los ids de los tokens revocados (el claim `jti`) y la comprobamos en cada petición:

```python
revoked_tokens = set()  # en memoria: se pierde al reiniciar (usa Redis o una BD en producción)

@jwt.token_in_blocklist_loader
def is_token_revoked(jwt_header, jwt_payload):
    return jwt_payload['jti'] in revoked_tokens

@app.route('/logout', methods=['POST'])
@jwt_required(verify_type=False)  # acepta access O refresh tokens
def logout():
    revoked_tokens.add(get_jwt()['jti'])
    return jsonify({'message': 'Token revocado'}), 200
```

Llama a `/logout` una vez con el access token y otra con el refresh token para cerrar la sesión por completo.

---

## Probar la API

> Los comandos siguientes usan `curl` con comillas de `bash`. En **CMD de Windows** usa `example/commands_cmd.txt`, y en **PowerShell** usa `example/commands_powershell.txt`.

### 1. Registrar un Usuario

```bash
curl -X POST http://127.0.0.1:5000/register \
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
curl -X POST http://127.0.0.1:5000/login \
  -H "Content-Type: application/json" \
  -d '{"username": "alice", "password": "secret123"}'
```

**Respuesta Esperada:**
```json
{
  "message": "Login successful",
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

**Guarda ambos tokens** - ¡los necesitarás para las siguientes peticiones!

### 3. Acceder a Endpoint Protegido con Token

Reemplaza `<TU_TOKEN>` con el `access_token` del paso 2:

```bash
curl -X GET http://127.0.0.1:5000/profile \
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
curl -X GET http://127.0.0.1:5000/profile
```

**Respuesta Esperada (401):**
```json
{
  "msg": "Missing Authorization Header"
}
```

### 5. Obtener Todos los Usuarios (Protegido)

```bash
curl -X GET http://127.0.0.1:5000/users \
  -H "Authorization: Bearer <TU_TOKEN>"
```

### 6. Obtener un Access Token Nuevo con el Refresh Token

```bash
curl -X POST http://127.0.0.1:5000/refresh \
  -H "Authorization: Bearer <TU_REFRESH_TOKEN>"
```

**Respuesta Esperada:**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer",
  "expires_in": 900
}
```

Prueba con el **access** token en su lugar: obtienes `422 {"msg": "Only refresh tokens are allowed"}`.

### 7. Logout

```bash
curl -X POST http://127.0.0.1:5000/logout \
  -H "Authorization: Bearer <TU_TOKEN>"
```

**Respuesta Esperada:**
```json
{
  "message": "Access token revoked"
}
```

Usar ese token otra vez devuelve `401 {"msg": "Token has been revoked"}`.

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

**Opción 2: PyJWT (ya instalado con Flask-JWT-Extended)**
```python
import jwt
print(jwt.decode("eyJ...", options={"verify_signature": False}))
```

`verify_signature: False` es **solo** para mirar dentro de un token. Nunca lo uses para autenticar una petición.

Verás algo como:

```json
{
  "fresh": false,
  "iat": 1793034905,
  "jti": "54acfacf-b34e-4c02-8440-6868bc0de9f6",
  "type": "access",
  "sub": "alice",
  "nbf": 1793034905,
  "csrf": "4ba7fa40-ec45-41a1-aa21-f921784e12d3",
  "aud": "mda-api-clients",
  "iss": "mda-api-exercises",
  "exp": 1793035805
}
```

| Claim | Significado |
|-------|-------------|
| `sub` | Sujeto: la identidad del usuario |
| `iat` / `nbf` / `exp` | Emitido / no válido antes de / expira (timestamps Unix). `exp - iat` = 900 s = 15 min |
| `iss` | Emisor: quién creó el token |
| `aud` | Audiencia: para quién es el token |
| `jti` | Id único del token (lo usa la lista de bloqueo del logout) |
| `type` | `access` o `refresh` |
| `fresh`, `csrf` | Internos de Flask-JWT-Extended (`csrf` solo importa cuando los tokens van en cookies) |

Los decodificadores online como jwt.io valen para **tokens desechables** que creas para una demo, nunca para tokens reales.

**Importante:** El token está **firmado**, no **encriptado**:
- ✅ El servidor puede verificar que no ha sido alterado
- ❌ Cualquiera puede leer el contenido: **nunca pongas datos sensibles en el payload** (contraseñas, datos personales, IDs internos que no enseñarías al usuario...)
- ✅ Si alguien modifica el payload, la verificación de firma falla

---

## Comparación JWT vs Basic Auth

| Característica | Basic Auth (Ejercicio 04) | JWT (Ejercicio 06) |
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
4. **Verificarlo todo** - Firma, `exp`, `iss` y `aud` (Flask-JWT-Extended lo hace con la configuración de arriba)
5. **Almacenar tokens de forma segura**:
   - Web: Cookies `httpOnly` (previene XSS)
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

### 1. Falta el Header de Autorización (401)

```json
{"msg": "Missing Authorization Header"}
```

**Solución:** Añadir header a la petición:
```bash
-H "Authorization: Bearer <token>"
```

### 2. Token Inválido (422)

```json
{"msg": "Signature verification failed"}
```

**Causas:**
- El token fue modificado
- `JWT_SECRET_KEY` incorrecta
- El token fue generado por otro servidor, **o por el mismo servidor antes de un reinicio** (si `JWT_SECRET_KEY` no está definida, el secreto es aleatorio en cada ejecución)

### 3. Emisor o Audiencia Incorrectos (422)

```json
{"msg": "Invalid issuer"}
{"msg": "Audience doesn't match"}
```

**Causa:** El token no lo creó esta API, o se creó para otra distinta.

### 4. Token Expirado (401)

```json
{"msg": "Token has expired"}
```

**Solución:** Llama a `POST /refresh` con tu refresh token. Si el refresh token también ha expirado, inicia sesión de nuevo.

### 5. Tipo de Token Incorrecto (422)

```json
{"msg": "Only refresh tokens are allowed"}
{"msg": "Only non-refresh tokens are allowed"}
```

**Causa:** Enviaste el access token a `/refresh`, o el refresh token a un endpoint protegido.

### 6. Token Revocado (401)

```json
{"msg": "Token has been revoked"}
```

**Causa:** Llamaste a `/logout` con ese token. Inicia sesión de nuevo.

### 7. Token Malformado (422)

```json
{"msg": "Not enough segments"}
```

**Causa:** El token está incompleto o tiene caracteres de más (normalmente un problema al copiar/pegar)
**Solución:** Copia de nuevo el token completo, sin comillas ni saltos de línea

### 8. Falta "Bearer" (401)

```json
{"msg": "Missing 'Bearer' type in 'Authorization' header. Expected 'Authorization: Bearer <JWT>'"}
```

**Solución:** Asegúrate de que el formato es `Bearer <token>`, no solo `<token>`

---

## Criterios de Aceptación

Tu implementación debería:

- ✅ Permitir registro de usuarios vía POST `/register`
- ✅ Aceptar credenciales de login en cuerpo JSON (no en header Authorization)
- ✅ Devolver un `access_token` (15 minutos) **y** un `refresh_token` en login exitoso
- ✅ Leer `JWT_SECRET_KEY` del entorno (con alternativa aleatoria)
- ✅ Establecer y verificar `iss` y `aud` en cada token
- ✅ Emitir access tokens nuevos vía POST `/refresh` con `@jwt_required(refresh=True)`
- ✅ Revocar tokens vía POST `/logout` (lista de bloqueo)
- ✅ Proteger rutas con el decorador `@jwt_required()`
- ✅ Extraer identidad del usuario con `get_jwt_identity()`
- ✅ Devolver 401 para credenciales inválidas, con el mismo tiempo para usuarios desconocidos y contraseñas incorrectas
- ✅ Devolver 401 para tokens JWT faltantes/expirados/revocados
- ✅ Hashear contraseñas antes de almacenar
- ✅ Usar formato de respuesta de error consistente

---

## Objetivos Adicionales

Una vez completes la implementación básica:

1. **Rotación de Refresh Tokens**
   Devuelve un refresh token **nuevo** desde `/refresh` y revoca el anterior, para que un refresh token robado solo pueda usarse una vez:
   ```python
   @app.route('/refresh', methods=['POST'])
   @jwt_required(refresh=True)
   def refresh():
       revoked_tokens.add(get_jwt()['jti'])
       current_user = get_jwt_identity()
       return jsonify({
           'access_token': create_access_token(identity=current_user),
           'refresh_token': create_refresh_token(identity=current_user)
       }), 200
   ```

2. **Lista de Bloqueo Persistente**
   Guarda los `jti` revocados en Redis con una expiración igual a la vida restante del token, para que la lista sobreviva a reinicios y no crezca sin límite.

3. **Tokens Fresh para Acciones Sensibles**
   Marca los tokens del login como fresh (`create_access_token(identity=..., fresh=True)`) y protege los endpoints sensibles con `@jwt_required(fresh=True)`, para que los tokens obtenidos vía `/refresh` no sirvan para ellos.

4. **Añadir Actualización de Perfil de Usuario**
   ```python
   @app.route('/profile', methods=['PUT'])
   @jwt_required()
   def update_profile():
       # Actualizar datos del usuario
   ```

5. **Añadir Endpoint de Cambio de Contraseña**
   - Requerir contraseña actual para verificación
   - Hashear nueva contraseña antes de almacenar
   - Revocar los tokens existentes del usuario

---

## Próximos Pasos

**Ejercicio 07:** Aprende a consumir APIs externas (clima, GitHub, etc.)

**Ejercicio 10:** Añade **Autorización** (roles y permisos) a tus tokens JWT
- Ejercicio actual: **Autenticación** (quién eres)
- Ejercicio 10: **Autorización** (qué puedes hacer)
- JWT incluirá claims de roles (admin, usuario, etc.)

---

## Recursos Adicionales

- [Documentación Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/)
- [Flask-JWT-Extended: Refresh Tokens](https://flask-jwt-extended.readthedocs.io/en/stable/refreshing_tokens.html)
- [Flask-JWT-Extended: Lista de Bloqueo y Revocación](https://flask-jwt-extended.readthedocs.io/en/stable/blocklist_and_token_revoking.html)
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
   - Todas las rutas protegidas usan `@jwt_required()`

4. **Seguridad**
   - Usar HTTPS en producción
   - Access tokens de vida corta + refresh tokens
   - Verificar firma, `exp`, `iss` y `aud`
   - Secreto desde el entorno, nunca en el código
   - Nunca poner datos sensibles en el payload JWT, y decodificar tokens en local
   - Misma respuesta y mismo tiempo para usuarios desconocidos y contraseñas incorrectas

5. **Autenticación ≠ Autorización**
   - Este ejercicio: ¿Quién eres? (Autenticación)
   - Ejercicio 10: ¿Qué puedes hacer? (Autorización con roles)

¡Buena suerte! 🚀
