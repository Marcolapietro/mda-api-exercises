# Ejercicio 14: Autenticación OAuth con GitHub (Authorization Code + PKCE)

## Objetivo

Aprender a implementar **autenticación OAuth** en una API REST con Flask integrándose con un proveedor externo (GitHub), usando el flujo que las buenas prácticas actuales (RFC 9700, OAuth 2.1) recomiendan para todos los clientes: **Authorization Code + PKCE**. Entender el flujo OAuth, manejar redirecciones y callbacks, identificar a los usuarios por el id estable del proveedor y combinar OAuth con JWT para autenticación de API.

## Inicio Rápido

```bash
cd exercises/14-oauth
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
# Configurar GitHub OAuth App (ver sección de Configuración más abajo)
python app.py
```

---

## ¿Qué es OAuth 2.0?

**OAuth 2.0** es un framework de autorización que permite a las aplicaciones obtener acceso limitado a cuentas de usuario en servicios de terceros (como GitHub, Google, Facebook) **sin exponer contraseñas**.

> **OAuth 2.0 vs OAuth 2.1:** OAuth 2.0 (RFC 6749, 2012) es el estándar publicado. Desde entonces, la experiencia
> en seguridad se ha recogido en **RFC 9700** (OAuth 2.0 Security Best Current Practice, 2025), y el borrador
> **OAuth 2.1** la consolida: Authorization Code **siempre con PKCE**, y los grants Implicit y Password eliminados.
> Este ejercicio sigue ese perfil moderno (ver "Entendiendo los Flujos OAuth" más abajo).

### Ejemplos del Mundo Real

Probablemente has usado OAuth muchas veces:
- **"Iniciar sesión con Google"** en sitios web
- **"Continuar con Facebook"** en aplicaciones móviles
- **Autenticación de GitHub CLI** (`gh auth login`)
- **Spotify** conectándose a Last.fm
- **Aplicaciones móviles** accediendo a tu Google Drive

### ¿Por Qué OAuth en Lugar de Login Tradicional?

| Característica | Login Tradicional | OAuth 2.0 |
|----------------|-------------------|-----------|
| **Almacenamiento de contraseñas** | Tu app almacena contraseñas | No se almacenan contraseñas |
| **Confianza del usuario** | Los usuarios crean nueva cuenta | Los usuarios confían en GitHub/Google |
| **Gestión de cuentas** | Tú manejas restablecimiento de contraseñas | El proveedor lo maneja |
| **Seguridad** | Tú eres responsable de brechas | Equipo de seguridad del proveedor |
| **Conveniencia del usuario** | Otra contraseña para recordar | Single sign-on (SSO) |
| **Datos de perfil** | Usuario los ingresa manualmente | Auto-completados del proveedor |

---

## Prerrequisitos

Antes de comenzar este ejercicio, completa:
- **Ejercicio 06**: Autenticación JWT (este ejercicio combina OAuth + JWT)
- **Ejercicio 04**: Autenticación Básica (entendiendo conceptos de autenticación)

---

## Lo Que Aprenderás

1. **Flujo Authorization Code con PKCE** (el flujo recomendado para todos los clientes)
2. **Integración con terceros** usando GitHub OAuth
3. **Manejo de redirecciones** y URLs de callback
4. **Intercambio de tokens** (código de autorización → token de acceso)
5. **Consumo de APIs** usando tokens de acceso OAuth
6. **Combinación de OAuth con JWT** para autenticación de API sin estado
7. **Gestión de sesiones** en flujos OAuth
8. **Mejores prácticas de seguridad** (PKCE, parámetro state, HTTPS, secretos, ids de usuario estables)

---

## Cómo Funciona OAuth 2.0

### Los Actores de OAuth

```
┌──────────────┐
│   Usuario    │  (La persona usando la app)
│   (Tú)       │
└──────────────┘
       │
       │ Quiere usar
       ▼
┌──────────────┐         ┌──────────────┐         ┌──────────────┐
│   Cliente    │◄───────►│  Servidor de │◄───────►│  Servidor de │
│     App      │         │ Autorización │         │   Recursos   │
│ (Tu Flask)   │         │  (GitHub)    │         │ (API GitHub) │
└──────────────┘         └──────────────┘         └──────────────┘
```

- **Usuario**: La persona intentando iniciar sesión
- **Cliente (Tu App)**: Tu aplicación Flask
- **Servidor de Autorización**: Servicio OAuth de GitHub (emite tokens)
- **Servidor de Recursos**: API de GitHub (proporciona datos de usuario)

### Flujo de Código de Autorización OAuth (Paso a Paso)

```
1. Usuario hace clic en "Iniciar sesión con GitHub"
   ┌──────────┐
   │ Usuario  │──── Hace clic en botón ────┐
   └──────────┘                             ▼
                                   ┌─────────────┐
                                   │   Tu App    │
                                   │/login/github│
                                   └─────────────┘
                                          │
                                          │ Crea code_verifier (secreto)
                                          │ Redirige a GitHub con
                                          │ code_challenge = SHA-256(verifier)
                                          ▼
2. Usuario autoriza en GitHub
   ┌──────────────────────────────────┐
   │  Página de Autorización GitHub   │
   │                                  │
   │  [Nombre App] quiere acceder a:  │
   │  ☑ Leer tu perfil                │
   │  ☑ Leer tu email                 │
   │                                  │
   │  [Autorizar] [Cancelar]          │
   └──────────────────────────────────┘
                  │
                  │ Usuario hace clic en Autorizar
                  ▼
3. GitHub redirige de vuelta con código de autorización
   ┌──────────────┐
   │   GitHub     │──── Redirige a callback ────┐
   └──────────────┘                              │
        URL: http://tuapp.com/callback?code=abc123
                                                  ▼
                                         ┌─────────────┐
                                         │   Tu App    │
                                         │  /callback  │
                                         └─────────────┘
                                                  │
4. Tu app intercambia código por token de acceso │
                                                  │
   POST https://github.com/login/oauth/access_token
   {
     client_id: "tu_client_id",
     client_secret: "tu_client_secret",
     code: "abc123",
     code_verifier: "dBjftJeZ4CVP..."   ← PKCE
   }
   GitHub comprueba SHA-256(code_verifier) == code_challenge
                  │
                  ▼
   Respuesta: { access_token: "gho_xxxx..." }
                  │
                  │
5. Tu app obtiene el perfil de usuario            │
                                                  │
   GET https://api.github.com/user               │
   Authorization: Bearer gho_xxxx...             │
                  │                               │
                  ▼                               │
   Respuesta: {                                  │
     id: 12345678,     ← estable, no cambia      │
     login: "alice",   ← se puede renombrar      │
     email: "alice@example.com",                 │
     name: "Alice Smith"                         │
   }                                             │
                  │                               │
                  │                               │
6. Tu app crea token JWT                         │
                  │                               │
   jwt_token = create_access_token(identity="12345678")
                  │                               │
                  ▼                               │
   ┌─────────────────────────────────┐            │
   │  Devolver JWT al usuario        │◄───────────┘
   │  { access_token: "eyJ..." }     │
   └─────────────────────────────────┘
                  │
                  │
7. Usuario usa JWT para peticiones futuras
                  │
   GET /profile
   Authorization: Bearer eyJ...
```

**Puntos Clave:**
- El código de autorización es **temporal** y de **un solo uso**
- El código de autorización debe intercambiarse en el **lado del servidor** (nunca en JavaScript del cliente)
- El client secret **nunca sale de tu servidor**
- La contraseña de GitHub del usuario **nunca toca tu app**
- Con **PKCE**, un código robado no se puede canjear sin el `code_verifier`
- Los usuarios se identifican por el **`id`** numérico de GitHub, no por el `login` (ver más abajo)

### PKCE: Proof Key for Code Exchange (siempre activo en este ejercicio)

El flujo anterior tiene un punto débil: el **código de autorización** pasa por el navegador (paso 3). Si un atacante
lo roba (una app maliciosa registrada para la misma redirección, un log filtrado, el historial del navegador...),
podría intentar canjearlo por un token. **PKCE** (RFC 7636, se pronuncia "pixy") cierra ese hueco: solo la app que
*empezó* el login puede terminarlo.

La buena práctica actual ([RFC 9700](https://datatracker.ietf.org/doc/rfc9700/), OAuth 2.0 Security Best Current
Practice, y el borrador OAuth 2.1) es **Authorization Code + PKCE para todos los clientes**: apps de servidor como
esta, SPAs y apps móviles. En un cliente confidencial como nuestra app Flask, PKCE se usa **además del** client
secret, no en su lugar. GitHub soporta PKCE con `S256`.

**Los 6 pasos (como en las diapositivas):**

```
 Tu app Flask                            Navegador / Usuario            GitHub (servidor de autorización)
 ────────────                            ───────────────────            ─────────────────────────────────
 1. Crea un code_verifier aleatorio
    code_challenge = BASE64URL(SHA-256(code_verifier))
    (guarda el verifier en la sesión, nunca en una URL)
 2. Redirige ─────────────────────────►  /login/oauth/authorize
                                         ?code_challenge=...&code_challenge_method=S256
                                         &state=...&redirect_uri=...   ──────────────►  guarda el challenge
 3.                                      El usuario inicia sesión y autoriza  ◄──────►
 4. /callback?code=...&state=...  ◄────  GitHub redirige de vuelta con el code  ◄─────
 5. POST /login/oauth/access_token
    code + code_verifier (+ client_id, client_secret, redirect_uri)  ─────────────────►
 6.                                                                   comprueba SHA-256(code_verifier)
                                                                      == code_challenge guardado
    ◄─────────────────────────────────────────────── access_token  (solo si coinciden)
```

1. **Se crean el verifier y el challenge:** la app genera un `code_verifier` aleatorio (43-128 caracteres) y calcula `code_challenge = BASE64URL(SHA-256(code_verifier))`.
2. **Redirección con el challenge:** la URL de autorización lleva `code_challenge` y `code_challenge_method=S256` (y `state`). Solo sale de la app el hash.
3. **Login:** el usuario inicia sesión en GitHub y autoriza la app.
4. **Vuelve el código:** GitHub redirige a `/callback` con un `code` de corta duración y un solo uso (y el mismo `state`).
5. **Código + verifier:** la app envía el `code` **y el `code_verifier` original** al endpoint de tokens.
6. **El servidor comprueba:** GitHub calcula `SHA-256(code_verifier)` y lo compara con el challenge que guardó en el paso 2. Si no coinciden, no hay token. Un código robado no sirve sin el verifier, y el verifier nunca viaja en una URL: quien intercepta la redirección se lleva el código, no el verifier.

**Con Authlib es un solo ajuste** en `client_kwargs`, ya presente en `app.py`:

```python
github = oauth.register(
    name='github',
    # ... client_id, client_secret, URLs ...
    client_kwargs={'scope': 'user:email', 'code_challenge_method': 'S256'},
)
```

Con ese ajuste, Authlib hace por ti los pasos 1, 2 y 5: `authorize_redirect()` genera el `code_verifier`, lo
guarda en la sesión y añade `code_challenge` + `code_challenge_method=S256` a la redirección;
`authorize_access_token()` lo recupera y envía `code_verifier` en la petición del token. Tu código de
`/login/github` y `/callback` no cambia.

**Lo que Authlib calcula por ti** (para entenderlo, no hace falta en la app):

```python
import base64, hashlib, secrets

code_verifier = secrets.token_urlsafe(48)
code_challenge = base64.urlsafe_b64encode(
    hashlib.sha256(code_verifier.encode()).digest()
).rstrip(b'=').decode()
```

> Error común: enviar el propio `code_verifier` como `code_challenge` (eso es el método `plain`). Con `S256`
> el challenge tiene que ser el hash; si no, el servidor rechaza el intercambio. Usa siempre `S256`.

> **¿Dónde guarda Authlib el verifier?** En la `session` de Flask. La sesión por defecto de Flask es una cookie
> firmada en el navegador del propio usuario (ver "Sesión vs JWT" más abajo), así que el verifier nunca aparece
> en URLs, logs ni en la cabecera `Referer`, que es por donde se filtran los códigos. En producción puedes pasar
> una `cache` del lado del servidor a `OAuth(app, cache=...)` para que los datos del flujo OAuth se queden en el servidor.

**`state` y PKCE son complementarios:** `state` (un valor aleatorio que Authlib guarda en la sesión y comprueba en
`/callback`) protege a **tu usuario** contra CSRF, es decir, contra acabar logueado con el código de otra persona.
PKCE protege el **código** para que nadie más pueda canjearlo. Mantén los dos.

---

## Instrucciones de Configuración

### Parte 1: Crear una GitHub OAuth App

1. **Ve a Configuración de Desarrollador de GitHub:**
   - Visita: https://github.com/settings/developers
   - Haz clic en **"OAuth Apps"** → **"New OAuth App"**

2. **Completa el formulario:**
   ```
   Application name: Flask OAuth Exercise
   Homepage URL: http://127.0.0.1:5000
   Authorization callback URL: http://127.0.0.1:5000/callback
   ```

   > **Usa `127.0.0.1` en todas partes, no `localhost`.** La app construye su `redirect_uri` a partir
   > del host que escribiste en el navegador (`url_for('callback', _external=True)`). Si abres
   > `http://localhost:5000/login/github`, la app envía `redirect_uri=http://localhost:5000/callback`,
   > y GitHub la compara **carácter a carácter** con la callback URL registrada, así que la rechaza
   > ("redirect_uri MUST match"). Además, el navegador trata `localhost` y `127.0.0.1` como sitios
   > distintos, así que la cookie de sesión que guarda el `state` de OAuth no se enviaría al otro.
   > Empieza siempre el flujo en **http://127.0.0.1:5000/login/github**.

3. **Registra la app:**
   - Haz clic en **"Register application"**
   - Verás:
     - **Client ID**: `Iv1.abc123def456...` (público, seguro para commit)
     - **Client Secret**: `1a2b3c4d5e6f...` (secreto, ¡nunca hacer commit!)

4. **Guarda tus credenciales:**
   - Copia el **Client ID**
   - Haz clic en **"Generate a new client secret"**
   - Copia el **Client Secret** (¡solo puedes verlo una vez!)

### Parte 2: Configurar Tu App

La app lee las credenciales **solo de variables de entorno** (`GITHUB_CLIENT_ID` y
`GITHUB_CLIENT_SECRET`). **No** las pegues en `app.py`: todo lo que está en el código acaba en Git.
Si falta alguna de las dos, la app se detiene al arrancar con un mensaje `Missing GITHUB_CLIENT_ID ...`.

Defínelas **en la misma terminal** donde vas a ejecutar `python app.py` (solo duran esa sesión de terminal):

```bash
# Linux / macOS (bash, zsh)
export GITHUB_CLIENT_ID="Iv1.abc123..."
export GITHUB_CLIENT_SECRET="1a2b3c4d..."
```

```powershell
# Windows PowerShell
$env:GITHUB_CLIENT_ID="Iv1.abc123..."
$env:GITHUB_CLIENT_SECRET="1a2b3c4d..."
```

```bat
:: Windows CMD (sin comillas, sin espacios alrededor del =)
set GITHUB_CLIENT_ID=Iv1.abc123...
set GITHUB_CLIENT_SECRET=1a2b3c4d...
```

Después arranca la app y abre **http://127.0.0.1:5000/login/github** en el navegador.

El fichero `.env.example` de la raíz del repo lista todas las variables que usan los ejercicios
(`GITHUB_CLIENT_ID`, `GITHUB_CLIENT_SECRET` y, opcionalmente, `FLASK_SECRET_KEY` y `JWT_SECRET_KEY`).
Es solo una referencia: la app **no** lo carga automáticamente, así que igualmente tienes que definir
las variables con los comandos de arriba. Si `FLASK_SECRET_KEY` / `JWT_SECRET_KEY` no están definidas,
la app genera unas aleatorias al arrancar (los tokens dejan de funcionar al reiniciarla).

Así es como la app las usa:

```python
client_id=os.environ['GITHUB_CLIENT_ID'],
client_secret=os.environ['GITHUB_CLIENT_SECRET'],
```

---

## Estructura de la API

### Endpoints Públicos

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| GET | `/` | Información de la API e instrucciones |
| GET | `/login/github` | Iniciar flujo OAuth de GitHub |
| GET | `/callback` | Callback OAuth (redirección automática) |
| POST | `/logout` | Limpiar sesión (logout) |

### Endpoints Protegidos (JWT Requerido)

| Método | Endpoint | Auth | Descripción |
|--------|----------|------|-------------|
| GET | `/profile` | JWT | Obtener perfil del usuario actual |
| GET | `/users` | JWT | Listar todos los usuarios registrados |

---

## Guía de Implementación

### TODOs en app.py

Necesitas completar **8 huecos** (`_____`). Los secretos (`app.secret_key`, `client_id`,
`client_secret`) **no** son huecos: se leen de variables de entorno (ver Parte 2).

| # | Dónde (función / sección) | Qué escribir |
|---|---------------------------|--------------|
| 1 | `oauth.register(...)` (línea 32) | Nombre del proveedor: `'github'` |
| 2 | `login_github()` (línea 94) | Endpoint de la URL de callback: `url_for('callback', _external=True)` |
| 3 | `login_github()` (línea 98) | Redirigir a GitHub: `github.authorize_redirect(redirect_uri)` |
| 4 | `callback()` (línea 120) | Intercambiar el código (+ verifier PKCE) por un token: `github.authorize_access_token()` |
| 5 | `callback()` (línea 124) | Endpoint de la API de GitHub para el perfil: `github.get('user')` |
| 6 | `callback()` (línea 152) | Crear nuestro JWT: `create_access_token(identity=user_id)` |
| 7 | `@app.route('/profile', ...)` (línea 175) | Método HTTP: `'GET'` |
| 8 | `profile()` (línea 191) | Leer el usuario del JWT: `get_jwt_identity()` |

PKCE (`'code_challenge_method': 'S256'`) y el id de usuario (`user_id = str(github_id)`) ya están escritos en
`app.py`: no son huecos, pero léelos, son lo que hace seguro el flujo (ver "PKCE" arriba y "Manejando el
Callback" abajo).

(Los números de línea se refieren al `app.py` original; busca `_____` si se han desplazado.)

### Conceptos Clave a Implementar

#### 1. Registro del Proveedor OAuth

**¿Qué es Authlib?**
- **Authlib** es la librería OAuth más popular para Flask
- Maneja OAuth 1.0, OAuth 2.0 y OpenID Connect
- Simplifica el intercambio de tokens, llamadas a API y gestión de sesiones

**Registrando un proveedor:**
```python
from authlib.integrations.flask_client import OAuth

oauth = OAuth(app)

github = oauth.register(
    name='github',  # Nombre interno para este proveedor
    client_id='...',  # De GitHub OAuth App
    client_secret='...',  # De GitHub OAuth App
    access_token_url='https://github.com/login/oauth/access_token',
    authorize_url='https://github.com/login/oauth/authorize',
    api_base_url='https://api.github.com/',
    client_kwargs={
        'scope': 'user:email',            # Permisos solicitados
        'code_challenge_method': 'S256',  # PKCE activado (OAuth 2.1 / RFC 9700)
    }
)
```

**Scopes OAuth:**
- Los scopes definen qué puede acceder tu app
- Scopes de GitHub: `user`, `user:email`, `repo`, `read:org`, etc.
- Los usuarios ven los scopes solicitados en la página de autorización
- Solicita **scopes mínimos** necesarios (mejor práctica de seguridad)

#### 2. Iniciando el Flujo OAuth

```python
@app.route('/login/github')
def login_github():
    # Generar la URL de callback (donde GitHub redirige de vuelta)
    redirect_uri = url_for('callback', _external=True)
    # Resultado: "http://127.0.0.1:5000/callback"

    # Redirigir usuario a la página de autorización de GitHub
    return github.authorize_redirect(redirect_uri)
```

**¿Qué sucede detrás de escena?**
1. `authorize_redirect()` construye una URL como:
   ```
   https://github.com/login/oauth/authorize
     ?client_id=Iv1.abc123
     &redirect_uri=http://127.0.0.1:5000/callback
     &scope=user:email
     &state=token_csrf_aleatorio
     &code_challenge=E9Melhoa2OwvFrEMTJguCHaoeK1t8URWbuGJSstw-cM
     &code_challenge_method=S256
   ```
2. El usuario es redirigido a GitHub
3. GitHub muestra el prompt de autorización
4. El usuario hace clic en "Authorize"
5. GitHub redirige de vuelta a tu `redirect_uri` con un código

**¿Por qué `_external=True`?**
- Genera URL absoluta (`http://127.0.0.1:5000/callback`)
- Sin esto: URL relativa (`/callback`) a la que GitHub no puede redirigir
- OAuth requiere **URLs absolutas** para callbacks

#### 3. Manejando el Callback

```python
@app.route('/callback')
def callback():
    # Paso 1: Intercambiar código de autorización por token de acceso
    token = github.authorize_access_token()
    # Detrás de escena: comprueba state y hace POST a GitHub con
    # code + code_verifier (PKCE) + client_secret
    # Devuelve: { "access_token": "gho_xxxx...", "scope": "user:email", ... }

    # Paso 2: Usar token de acceso para obtener perfil de usuario
    response = github.get('user')  # GET https://api.github.com/user
    user_info = response.json()

    # Paso 3: Extraer datos de usuario
    github_id = user_info.get('id')        # 12345678 - estable, no cambia
    username = user_info.get('login')      # "alice"  - se puede renombrar
    email = user_info.get('email')
    name = user_info.get('name')

    # Paso 4: Almacenar (o actualizar) el usuario, con el id estable como clave
    user_id = str(github_id)
    users[user_id] = {'github_id': github_id, 'username': username, ...}

    # Paso 5: Crear token JWT para tu API (sub = el id, como string)
    access_token = create_access_token(identity=user_id)

    return jsonify({'access_token': access_token})
```

**¿Por qué el `id` y no el `login`?**
- En GitHub puedes **renombrar tu cuenta**: el `login` cambia, el `id` nunca. Si guardáramos los usuarios por
  `login`, un cambio de nombre crearía un usuario "nuevo" y dejaría huérfanos los datos anteriores.
- Peor aún: tras un cambio de nombre, el `login` antiguo queda **libre** y otra persona puede registrarlo. Si
  nuestra base de datos usara el `login` como clave, esa persona heredaría la cuenta del dueño anterior en nuestra app.
- Por eso la **identidad** es el id estable del proveedor (`sub` en OpenID Connect, `id` en la API de GitHub);
  `login`, nombre y avatar son solo **atributos de visualización** que actualizamos en cada login.
- El claim `sub` del JWT tiene que ser un **string** (PyJWT rechaza subjects que no lo sean), así que usamos `str(github_id)`.

**¿Por qué dos tokens?**
- **Token de acceso OAuth** (`gho_xxxx`): Usado para llamar a la **API de GitHub**
- **Token JWT** (`eyJ...`): Usado para llamar a **tu API**
- No almacenamos el token de GitHub (solo lo necesitábamos para obtener el perfil de usuario)

#### 4. Combinando OAuth con JWT

**¿Por qué usar JWT después de OAuth?**
1. **Autenticación sin estado**: No es necesario almacenar tokens de GitHub
2. **Rendimiento**: No llamar a la API de GitHub en cada petición
3. **Estandarización**: Mismo patrón de autenticación que Ejercicio 06
4. **Flexibilidad**: Funciona con múltiples proveedores OAuth

**Patrón:**
```
OAuth (una vez)             JWT (cada petición)
───────────────             ───────────────────
Login de GitHub             Llamadas a tu API
    ↓                           ↓
Perfil de usuario           Auth sin estado
    ↓                           ↓
Crear JWT        ─────────► Usar token JWT
```

#### 5. Gestión de Sesiones

```python
# Las sesiones de Flask son necesarias para gestionar el estado de OAuth
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)

# Authlib guarda datos temporales de OAuth en la sesión:
# - state (protección CSRF)
# - code_verifier (PKCE - se guarda aquí, nunca viaja en una URL)
# - redirect_uri (validación)

# Tras un OAuth correcto, la sesión se puede limpiar
@app.route('/logout', methods=['POST'])
def logout():
    session.clear()
    return jsonify({'message': 'Logged out'})
```

**Sesión vs JWT:**
- **Sesión**: Temporal, solo para el flujo OAuth. La sesión por defecto de Flask es una **cookie firmada
  guardada en el navegador** (lado del cliente): `secret_key` impide que se manipule, pero su contenido solo
  está codificado en base64, no cifrado, así que nunca guardes secretos en ella.
- **JWT**: De corta duración (la solución usa `JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=1)`), lo envía el
  cliente en la cabecera `Authorization`, autenticación de la API

---

## Probando la API

### Método 1: Prueba en Navegador (Más Fácil)

1. **Iniciar el servidor:**
   ```bash
   python app.py
   ```

2. **Abrir navegador:**
   - Ir a: http://127.0.0.1:5000/login/github

3. **Autorizar con GitHub:**
   - Hacer clic en "Authorize [Nombre de Tu App]"
   - Serás redirigido a `/callback`
   - Copiar el `access_token` de la respuesta JSON

4. **Usar el token en Postman/curl:**
   ```bash
   curl http://127.0.0.1:5000/profile \
     -H "Authorization: Bearer <TU_TOKEN_JWT>"
   ```

### Método 2: Prueba con Postman

**Paso 1: Iniciar OAuth (en navegador)**
- Como OAuth requiere redirecciones, inicia el flujo en un navegador
- Visita: http://127.0.0.1:5000/login/github
- Autoriza y copia el token JWT

**Paso 2: Probar endpoints protegidos (en Postman)**

**Obtener tu perfil:**
```
GET http://127.0.0.1:5000/profile
Headers:
  Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Respuesta esperada:**
```json
{
  "user_id": "12345678",
  "username": "tu-usuario-github",
  "profile": {
    "github_id": 12345678,
    "username": "tu-usuario-github",
    "email": "tu@ejemplo.com",
    "name": "Tu Nombre",
    "avatar_url": "https://avatars.githubusercontent.com/u/12345678"
  }
}
```

**Obtener todos los usuarios:**
```
GET http://127.0.0.1:5000/users
Headers:
  Authorization: Bearer eyJ...
```

**Respuesta esperada:**
```json
{
  "users": [
    {"id": "12345678", "username": "alice"},
    {"id": "23456789", "username": "bob"}
  ],
  "count": 2
}
```

### Método 3: Prueba con curl

**Nota:** Las redirecciones de OAuth no funcionan bien con curl. Usa el navegador para obtener el JWT y después:

```bash
# Guarda tu token JWT
TOKEN="eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."

# Obtener tu perfil
curl http://127.0.0.1:5000/profile \
  -H "Authorization: Bearer $TOKEN"

# Obtener todos los usuarios
curl http://127.0.0.1:5000/users \
  -H "Authorization: Bearer $TOKEN"

# Logout
curl -X POST http://127.0.0.1:5000/logout
```

---

## Entendiendo los Flujos OAuth

### Los Grant Types Hoy (OAuth 2.1 / RFC 9700)

OAuth 2.0 (RFC 6749, 2012) definió varios grant types. Años de ataques han mostrado cuáles son seguros, y la
guía actual los consolida:

| Grant Type | Caso de uso | Estado |
|------------|-------------|--------|
| **Authorization Code + PKCE** | **Todos los clientes** en los que inicia sesión un usuario: apps web de servidor, SPAs, apps móviles y de escritorio | ✅ Opción recomendada |
| **Client Credentials** | Máquina a máquina: un servicio que llama a otro, sin usuario | ✅ Para M2M |
| **Device Authorization (Device Code)** | Dispositivos sin navegador ni teclado: smart TVs, CLIs (p. ej. `gh auth login`) | ✅ Para TVs / CLIs |
| **Refresh Token** | Obtener un nuevo access token sin volver a preguntar al usuario | ✅ Junto con los anteriores |
| ~~Implicit~~ | (antes: SPAs) | ❌ **Eliminado en OAuth 2.1**: el access token se devuelve en el fragmento de la URL, donde el historial, las extensiones y los logs pueden filtrarlo, y no se puede vincular al cliente |
| ~~Resource Owner Password~~ | (antes: apps propias "de confianza") | ❌ **Eliminado en OAuth 2.1**: la app recibe la contraseña del usuario, justo lo que OAuth existe para evitar, y no admite MFA ni SSO |

**Este ejercicio usa Authorization Code + PKCE**, la opción recomendada.

> **Estado de los documentos:** OAuth 2.1 sigue siendo un **borrador del IETF** (draft-ietf-oauth-v2-1), no un RFC
> publicado. El documento de buenas prácticas vigente y publicado es **RFC 9700** ("OAuth 2.0 Security Best Current
> Practice", enero de 2025). OAuth 2.1 básicamente reúne RFC 6749 + RFC 7636 (PKCE) + RFC 9700 en una sola
> especificación, así que si sigues RFC 9700 hoy ya estás preparado para OAuth 2.1.

### Por Qué Authorization Code (+ PKCE) es la Opción Segura

```
❌ Implicit Flow (eliminado):
GitHub → Navegador → App
         ↑
      Access token en la URL (visible para navegador, extensiones, historial)

✅ Authorization Code + PKCE (este ejercicio):
GitHub → Navegador → App
         ↑            ↓
      Solo el código  El servidor canjea code + code_verifier por el token
                      (El token nunca toca el navegador; un código robado no sirve)
```

**Beneficios:**
- El client secret nunca se expone al navegador
- El access token nunca va en la URL (ni en logs ni en el historial)
- El código es de un solo uso y de corta duración
- Intercambio del token de servidor a servidor
- PKCE vincula el código a la app que empezó el flujo

---

## Mejores Prácticas de Seguridad

### ✅ HACER

1. **Usar HTTPS en producción**
   - Los tokens OAuth pueden ser interceptados en HTTP
   - GitHub rechaza callbacks no-HTTPS en producción

2. **Almacenar secretos de forma segura**
   ```python
   # ❌ Mal: Secretos hardcodeados
   client_secret = "abc123"

   # ✅ Bien: Variables de entorno
   client_secret = os.getenv('GITHUB_CLIENT_SECRET')
   ```

3. **Validar URIs de redirección**
   - Registra URLs de callback **exactas** con GitHub
   - GitHub rechaza URLs no coincidentes (característica de seguridad)

4. **Usar parámetro state** (Authlib lo hace automáticamente)
   - Protege contra ataques CSRF
   - Valor aleatorio verificado en callback

5. **Usar PKCE con S256** (`'code_challenge_method': 'S256'`)
   - Recomendado para todos los clientes (RFC 9700, OAuth 2.1)
   - Un código de autorización robado no sirve sin el `code_verifier`

6. **Identificar a los usuarios por el id estable del proveedor**
   - El `id` de GitHub (o el `sub` de OIDC), nunca el `login`/email, que pueden cambiar o reasignarse

7. **Solicitar scopes mínimos**
   ```python
   # ❌ Mal: Solicitar permisos innecesarios
   client_kwargs={'scope': 'user repo delete_repo admin:org'}

   # ✅ Bien: Solo lo que necesitas
   client_kwargs={'scope': 'user:email'}
   ```

8. **Validar tokens**
   - Comprobar la expiración del token
   - Verificar la firma del token (JWT lo hace)

9. **Manejar errores con elegancia**
   ```python
   try:
       token = github.authorize_access_token()
   except Exception as e:
       return jsonify({'error': 'OAuth failed'}), 400
   ```

### ❌ NO HACER

1. **No hacer commit de client secrets**
   ```bash
   # Agregar a .gitignore
   .env
   config.py
   ```

2. **No usar los grants Implicit ni Password** (eliminados en OAuth 2.1)
   - Implicit pone el access token en la URL; Password entrega la contraseña del usuario a tu app
   - Usa Authorization Code + PKCE en su lugar, también para SPAs y apps móviles

3. **No omitir HTTPS** en producción
   - Desarrollo (localhost): HTTP está bien
   - Producción: HTTPS es obligatorio

4. **No almacenar tokens de acceso OAuth** (salvo que haga falta)
   - Si solo necesitas el perfil una vez, no lo guardes
   - Si necesitas acceso continuado a la API de GitHub, guárdalo de forma segura

5. **No confiar en la entrada del usuario**
   - Validar el parámetro `state`
   - Sanear los datos del perfil del usuario

---

## Problemas Comunes y Soluciones

### Problema 1: "Redirect URI Mismatch"

**Síntoma:**
```
GitHub error: The redirect_uri MUST match the registered callback URL for this application.
```

**Solución:**
- Revisa los ajustes de tu GitHub OAuth App
- La callback URL debe coincidir **exactamente**: `http://127.0.0.1:5000/callback`
- Empieza el flujo en `http://127.0.0.1:5000/login/github` (la app construye `redirect_uri` a partir del host que usaste)
- Errores comunes:
  - `http://localhost:5000/callback` ≠ `http://127.0.0.1:5000/callback` (GitHub compara la cadena exacta,
    y el navegador los trata como sitios distintos)
  - `https://` vs `http://`
  - Barra final: `/callback/` vs `/callback`

### Problema 2: "Client ID or Secret Invalid"

**Síntoma:**
```json
{
  "error": "invalid_client",
  "error_description": "The client credentials are invalid"
}
```

**Solución:**
- Verifica que el Client ID está copiado correctamente
- Regenera el Client Secret si lo perdiste (solo se puede ver una vez)
- Revisa que no haya espacios de más al pegar
- Asegúrate de usar la GitHub OAuth App correcta

### Problema 3: "Session Error"

**Síntoma:**
```
RuntimeError: The session is unavailable because no secret key was set.
```

**Solución:**
```python
# Añade esto a tu app
app.secret_key = os.environ.get('FLASK_SECRET_KEY') or secrets.token_hex(32)
```

### Problema 4: "El Callback de OAuth Nunca Llega"

**Síntoma:**
- Atascado en la página de autorización de GitHub
- El endpoint de callback nunca recibe la petición

**Solución:**
- Comprueba que Flask está en marcha: http://127.0.0.1:5000
- Comprueba que ningún firewall bloquea el puerto 5000
- Verifica la callback URL en los ajustes de GitHub
- Revisa la consola del navegador por si hay errores

### Problema 5: "Email es None"

**Síntoma:**
```json
{
  "email": null
}
```

**Solución:**
- GitHub solo devuelve el email si pediste el scope `user:email`
- El usuario puede tener el email configurado como privado
- Obtén el email por separado: `github.get('user/emails')`

```python
# Obtener el email principal si no es público
if not email:
    emails_response = github.get('user/emails')
    emails = emails_response.json()
    primary_email = next((e['email'] for e in emails if e['primary']), None)
```

---

## Criterios de Aceptación

Tu implementación debería:

- ✅ Registrar GitHub como proveedor OAuth con Authlib, con PKCE (`code_challenge_method='S256'`)
- ✅ Redirigir a la página de autorización de GitHub (con `state`, `code_challenge` y `code_challenge_method=S256`)
- ✅ Manejar callback OAuth con código de autorización
- ✅ Intercambiar código + `code_verifier` por token de acceso (lado del servidor)
- ✅ Obtener perfil de usuario de la API de GitHub
- ✅ Almacenar el usuario con el `id` numérico de GitHub como clave (`login` solo como atributo de visualización)
- ✅ Generar token JWT después de OAuth exitoso, con `sub` = el id de GitHub como string
- ✅ Proteger rutas con decorador `@jwt_required()`
- ✅ Usar JWT para peticiones posteriores a la API
- ✅ Manejar errores de OAuth con elegancia
- ✅ Limpiar sesión al cerrar sesión

---

## Objetivos Extendidos

Cuando completes la implementación básica:

### 1. Añadir Varios Proveedores OAuth

Soporta Google, Facebook o Twitter:

```python
# Google OAuth
google = oauth.register(
    name='google',
    client_id=os.getenv('GOOGLE_CLIENT_ID'),
    client_secret=os.getenv('GOOGLE_CLIENT_SECRET'),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={'scope': 'openid email profile'}
)

@app.route('/login/google')
def login_google():
    redirect_uri = url_for('google_callback', _external=True)
    return google.authorize_redirect(redirect_uri)

@app.route('/callback/google')
def google_callback():
    token = google.authorize_access_token()
    user_info = token['userinfo']  # OpenID Connect
    # ... crear JWT
```

### 2. Implementar Refresco de Tokens

Guarda los refresh tokens de OAuth para acceso a la API a largo plazo:

```python
# Al guardar el usuario
users[user_id] = {
    'github_id': github_id,
    'access_token': token['access_token'],
    'refresh_token': token.get('refresh_token'),
    'expires_at': token.get('expires_at')
}

# Refrescar cuando expire
if datetime.now().timestamp() > user['expires_at']:
    new_token = github.fetch_access_token(
        refresh_token=user['refresh_token']
    )
    users[user_id]['access_token'] = new_token['access_token']
```

### 3. Gestionar los Scopes OAuth

Deja que los usuarios elijan qué permisos conceden:

```python
@app.route('/login/github/full')
def login_github_full():
    # Pedir scopes adicionales
    redirect_uri = url_for('callback', _external=True)
    return github.authorize_redirect(
        redirect_uri,
        scope='user:email read:org repo'  # Más permisos
    )
```

### 4. Implementar Vinculación de Cuentas

Permite que los usuarios vinculen varios proveedores OAuth:

```python
users = {
    '12345678': {  # nuestro id de usuario
        'primary_email': 'alice@example.com',
        'oauth_providers': {
            'github': {'id': 12345, 'username': 'alice'},
            'google': {'id': 67890, 'email': 'alice@gmail.com'}
        }
    }
}

@app.route('/link/github')
@jwt_required()
def link_github():
    current_user = get_jwt_identity()
    redirect_uri = url_for('link_callback', _external=True)
    return github.authorize_redirect(redirect_uri)

@app.route('/link/callback')
@jwt_required()
def link_callback():
    current_user = get_jwt_identity()
    token = github.authorize_access_token()
    user_info = github.get('user').json()

    # Añadir GitHub al usuario existente
    if 'oauth_providers' not in users[current_user]:
        users[current_user]['oauth_providers'] = {}

    users[current_user]['oauth_providers']['github'] = {
        'id': user_info['id'],
        'username': user_info['login']
    }

    return jsonify({'message': 'GitHub account linked'})
```

### 5. Obtener Datos Adicionales del Usuario

Obtén repositorios, organizaciones, etc.:

```python
@app.route('/profile/repos')
@jwt_required()
def get_repos():
    current_user = get_jwt_identity()
    user_data = users[current_user]

    # Si guardamos el access token de GitHub
    github_token = user_data.get('github_access_token')

    # Obtener los repositorios del usuario
    response = github.get(
        'user/repos',
        token={'access_token': github_token}
    )
    repos = response.json()

    return jsonify({
        'username': user_data['username'],
        'repositories': [
            {
                'name': repo['name'],
                'stars': repo['stargazers_count'],
                'url': repo['html_url']
            }
            for repo in repos
        ]
    })
```

---

## Comparación: Basic Auth vs API Key vs JWT vs OAuth

| Característica | Basic Auth | API Key | JWT | OAuth 2.0 |
|----------------|------------|---------|-----|-----------|
| **Credenciales enviadas** | En cada petición | Una vez al registrarse | Una vez al hacer login | Una vez (al proveedor) |
| **Contraseña almacenada** | Sí (hash) | Sí (hash) | Sí (hash) | No (la guarda el proveedor) |
| **Sin estado** | Sí | Sí | Sí | Híbrido |
| **Expiración** | No | Manual | Automática | Automática |
| **Login con terceros** | No | No | No | Sí |
| **Confianza del usuario** | Baja (cuenta nueva) | Baja | Baja | Alta (proveedor de confianza) |
| **Complejidad de configuración** | Baja | Media | Media | Alta |
| **Ideal para** | APIs sencillas | APIs públicas | Apps modernas | Apps de consumo |

---

## Cuándo Usar OAuth

### ✅ Usa OAuth Cuando:

1. **Construyes apps para el público**
   - Los usuarios prefieren "Iniciar sesión con Google" a crear cuentas
   - Reduce la fricción al darse de alta

2. **No quieres guardar contraseñas**
   - La responsabilidad de seguridad pasa al proveedor
   - No hay que construir flujos de restablecimiento de contraseña

3. **Necesitas datos de perfil**
   - Autocompletar perfiles de usuario
   - Avatares, emails verificados

4. **Construyes integraciones**
   - Acceder a los repos de GitHub del usuario
   - Publicar en el Twitter del usuario
   - Leer el Google Calendar del usuario

5. **SSO empresarial**
   - Integrar con proveedores de identidad corporativos
   - Soportar SAML, OpenID Connect

### ❌ No Uses OAuth Cuando:

1. **Construyes herramientas internas**
   - Basic Auth o API keys son más sencillas
   - Controlas a todos los usuarios

2. **APIs de servidor a servidor**
   - Usa API keys o client credentials
   - No hace falta interacción del usuario

3. **Necesitas simplicidad**
   - OAuth añade complejidad
   - No compensa en proyectos pequeños

4. **Se requiere acceso offline**
   - OAuth necesita red para validar
   - Considera JWT o API keys

---

## Recursos Adicionales

- **RFC 6749**: [OAuth 2.0 Authorization Framework](https://tools.ietf.org/html/rfc6749)
- **RFC 7636**: [Proof Key for Code Exchange (PKCE)](https://datatracker.ietf.org/doc/html/rfc7636)
- **RFC 9700**: [OAuth 2.0 Security Best Current Practice](https://datatracker.ietf.org/doc/rfc9700/) (el documento de buenas prácticas vigente)
- **OAuth 2.1** (borrador del IETF): [draft-ietf-oauth-v2-1](https://datatracker.ietf.org/doc/draft-ietf-oauth-v2-1/) y [oauth.net/2.1](https://oauth.net/2.1/)
- **Documentación de Authlib**: https://docs.authlib.org/en/latest/
- **GitHub OAuth**: https://docs.github.com/en/developers/apps/building-oauth-apps
- **OAuth 2.0 Playground**: https://www.oauth.com/playground/
- **OWASP OAuth Security**: https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html

---

## Resumen

**Puntos Clave:**

1. **OAuth = Autorización Delegada**
   - Los usuarios inician sesión con proveedores de confianza (GitHub, Google)
   - Tu app nunca ve las contraseñas de los usuarios
   - El proveedor maneja seguridad y gestión de cuentas

2. **Authorization Code + PKCE**
   - El flujo recomendado para todos los clientes (RFC 9700, OAuth 2.1); Implicit y Password están eliminados
   - Intercambio código de autorización + code_verifier → token de acceso en servidor
   - Client secret nunca expuesto al navegador; un código robado no sirve sin el verifier
   - Usuarios identificados por el `id` estable del proveedor, no por el `login`

3. **Patrón OAuth + JWT**
   - OAuth para autenticación inicial
   - JWT para peticiones posteriores a la API
   - Lo mejor de ambos mundos: login confiable + auth sin estado

4. **Proceso de Tres Pasos**
   - Redirigir a proveedor → Usuario autoriza → Callback con código
   - Intercambiar código por token → Obtener perfil → Crear JWT
   - Usar JWT para tu API → Logout limpia sesión

5. **Seguridad Primero**
   - Nunca hacer commit de client secrets
   - Usar HTTPS en producción
   - Validar URIs de redirección
   - Solicitar scopes mínimos
   - Manejar errores con elegancia

**Siguientes Pasos:**
- **Objetivos Extendidos**: Agregar Google OAuth, implementar actualización de tokens
- **Ejercicio 10**: Combinar OAuth con Roles y Permisos
- **Proyecto Real**: Construir una integración OAuth completa con múltiples proveedores

¡Buena suerte! 🚀
