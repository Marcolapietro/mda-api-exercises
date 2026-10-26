# Ejercicio 14: Autenticación OAuth 2.0 con GitHub

## Objetivo

Aprender a implementar **autenticación OAuth 2.0** en una API REST con Flask integrándose con un proveedor externo (GitHub). Entender el flujo OAuth, manejar redirecciones y callbacks, y combinar OAuth con JWT para autenticación de API.

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

1. **Flujo de Código de Autorización OAuth 2.0** (flujo OAuth más común)
2. **Integración con terceros** usando GitHub OAuth
3. **Manejo de redirecciones** y URLs de callback
4. **Intercambio de tokens** (código de autorización → token de acceso)
5. **Consumo de APIs** usando tokens de acceso OAuth
6. **Combinación de OAuth con JWT** para autenticación de API sin estado
7. **Gestión de sesiones** en flujos OAuth
8. **Mejores prácticas de seguridad** (parámetros de estado, HTTPS, secretos)

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
                                          │ Redirige a GitHub
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
     code: "abc123"
   }
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
     login: "alice",                             │
     email: "alice@example.com",                 │
     name: "Alice Smith"                         │
   }                                             │
                  │                               │
                  │                               │
6. Tu app crea token JWT                         │
                  │                               │
   jwt_token = create_access_token(identity="alice")
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
| 2 | `login_github()` (línea 86) | Endpoint de la URL de callback: `url_for('callback', _external=True)` |
| 3 | `login_github()` (línea 90) | Redirigir a GitHub: `github.authorize_redirect(redirect_uri)` |
| 4 | `callback()` (línea 112) | Intercambiar el código por un token: `github.authorize_access_token()` |
| 5 | `callback()` (línea 116) | Endpoint de la API de GitHub para el perfil: `github.get('user')` |
| 6 | `callback()` (línea 138) | Crear nuestro JWT: `create_access_token(identity=username)` |
| 7 | `@app.route('/profile', ...)` (línea 159) | Método HTTP: `'GET'` |
| 8 | `profile()` (línea 175) | Leer el usuario del JWT: `get_jwt_identity()` |

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
    client_kwargs={'scope': 'user:email'}  # Permisos solicitados
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
    # Detrás de escena: POST a GitHub con código + client_secret
    # Devuelve: { "access_token": "gho_xxxx...", "scope": "user:email", ... }

    # Paso 2: Usar token de acceso para obtener perfil de usuario
    response = github.get('user')  # GET https://api.github.com/user
    user_info = response.json()

    # Paso 3: Extraer datos de usuario
    username = user_info.get('login')
    email = user_info.get('email')
    name = user_info.get('name')

    # Paso 4: Almacenar usuario en base de datos
    users[username] = { ... }

    # Paso 5: Crear token JWT para tu API
    access_token = create_access_token(identity=username)

    return jsonify({'access_token': access_token})
```

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

5. **Solicitar scopes mínimos**
   ```python
   # ❌ Mal: Solicitar permisos innecesarios
   client_kwargs={'scope': 'user repo delete_repo admin:org'}

   # ✅ Bien: Solo lo que necesitas
   client_kwargs={'scope': 'user:email'}
   ```

### ❌ NO HACER

1. **No hacer commit de client secrets**
   ```bash
   # Agregar a .gitignore
   .env
   config.py
   ```

2. **No usar Implicit Flow** (obsoleto desde 2019)
   - Menos seguro que Authorization Code
   - Usar Authorization Code + PKCE para SPAs

3. **No omitir HTTPS** en producción
   - Desarrollo (localhost): HTTP está bien
   - Producción: HTTPS es obligatorio

---

## Criterios de Aceptación

Tu implementación debería:

- ✅ Registrar GitHub como proveedor OAuth con Authlib
- ✅ Redirigir a la página de autorización de GitHub
- ✅ Manejar callback OAuth con código de autorización
- ✅ Intercambiar código por token de acceso (lado del servidor)
- ✅ Obtener perfil de usuario de la API de GitHub
- ✅ Almacenar usuario en base de datos
- ✅ Generar token JWT después de OAuth exitoso
- ✅ Proteger rutas con decorador `@jwt_required()`
- ✅ Usar JWT para peticiones posteriores a la API
- ✅ Manejar errores de OAuth con elegancia
- ✅ Limpiar sesión al cerrar sesión

---

## Recursos Adicionales

- **RFC 6749**: [OAuth 2.0 Authorization Framework](https://tools.ietf.org/html/rfc6749)
- **Documentación de Authlib**: https://docs.authlib.org/en/latest/
- **GitHub OAuth**: https://docs.github.com/en/developers/apps/building-oauth-apps
- **OAuth 2.0 Playground**: https://www.oauth.com/playground/
- **OWASP OAuth Security**: https://cheatsheetseries.owasp.org/cheatsheets/OAuth2_Cheat_Sheet.html

---

## Resumen

**Puntos Clave:**

1. **OAuth 2.0 = Autorización Delegada**
   - Los usuarios inician sesión con proveedores de confianza (GitHub, Google)
   - Tu app nunca ve las contraseñas de los usuarios
   - El proveedor maneja seguridad y gestión de cuentas

2. **Flujo de Código de Autorización**
   - Flujo OAuth más seguro para aplicaciones web
   - Intercambio código de autorización → token de acceso en servidor
   - Client secret nunca expuesto al navegador

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
