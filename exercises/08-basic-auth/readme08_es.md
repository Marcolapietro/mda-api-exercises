# Ejercicio 8: Autenticación Básica

## Objetivo
Implementar autenticación básica (Basic Auth) en una API REST utilizando Python y FastAPI.

## Descripción
En este ejercicio, desarrollarás una API REST sencilla que maneja recursos de "usuarios". Implementarás la autenticación básica para proteger ciertas rutas, asegurando que solo usuarios autenticados puedan acceder a ellas.

## Inicio Rápido

```bash
cd exercises/08-basic-auth
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac
pip install -r requirements.txt
fastapi dev app.py
```

Rellena los huecos (`_____`) de arriba abajo; la app arranca cuando el decorador `POST` y el `Depends(...)` de `get_users` están completos. El hueco del nombre de la cabecera solo se usa cuando una petición falla la autenticación: lanza la petición con contraseña incorrecta con `curl -i` y mira la cabecera `WWW-Authenticate`.

## Requisitos
1. **Configuración del Proyecto:**
   - Inicializa un entorno virtual.
   - Instala las dependencias necesarias (`fastapi[standard]`, `bcrypt`).

2. **Estructura de la API (dada, complétala):**
   - Una ruta para registrar nuevos usuarios (`POST /users`): tú escribes su método HTTP.
   - Una ruta para obtener la lista de usuarios (`GET /users`), protegida con autenticación básica: tú conectas la dependencia que la protege.

3. **Autenticación Básica (dada, entiéndela):**
   - `fastapi.security.HTTPBasic` lee las credenciales de la petición.
   - Las contraseñas se guardan como hashes `bcrypt`, nunca en texto plano.
   - `get_current_user` verifica las credenciales y responde `401` con la cabecera adecuada (tú escribes el nombre de la cabecera).

4. **Pruebas:**
   - Utiliza herramientas como Postman o `curl` para probar las rutas protegidas con y sin credenciales válidas.

## Instrucciones

Rellena los tres espacios `_____` de `app.py`:

- el método HTTP de la ruta que registra un usuario (en minúsculas, porque es el nombre de un método de `app`: `@app.post`);
- la dependencia dentro de `Depends(...)` que protege `GET /users` (la función que comprueba las credenciales);
- el nombre de la cabecera que le dice al cliente qué tipo de autenticación espera el servidor (va en la respuesta 401).

El hasheo de contraseñas (`hash_password`, `verify_password`) ya está escrito. Una vez corregido, ejecuta la app y realiza las pruebas desde Postman.

## Pasos Sugeridos

1. **Inicializa el Proyecto:**
   ```bash
   cd exercises/08-basic-auth
   python -m venv venv
   venv\Scripts\activate  # macOS / Linux: source venv/bin/activate
   pip install -r requirements.txt
   ```

2. **Lee `app.py`:**
   - La aplicación FastAPI, el diccionario `users` en memoria y las funciones auxiliares de `bcrypt` ya están ahí.
   - También las dos rutas: `POST /users` registra un usuario y `GET /users` los lista.

3. **Entiende la Autenticación Básica y rellena los huecos:**
   - Busca dónde se crea `HTTPBasic` de `fastapi.security` y cómo lo usa `get_current_user` para comprobar las credenciales.
   - Mira cómo `hash_password` hashea con `bcrypt.hashpw` y `verify_password` comprueba con `bcrypt.checkpw`.
   - Rellena los tres huecos (ver Instrucciones arriba).

4. **Prueba la API:**
   - Registra un usuario con `POST /users`.
   - Intenta acceder a `GET /users` sin credenciales (debe fallar).
   - Accede a `GET /users` con credenciales válidas (debe funcionar).

## Novedad en FastAPI: `Depends` y `fastapi.security`

Una **dependencia** es una función que FastAPI ejecuta *antes* de tu ruta y cuyo resultado le pasa a tu ruta. Se declara en los parámetros con `Annotated[Tipo, Depends(función)]`; aquí `get_users` recibe el nombre de usuario autenticado desde `get_current_user`. Si la dependencia lanza un error (por ejemplo `HTTPException(401)`), la ruta no se ejecuta, así que proteger una ruta es solo añadirle un parámetro con `Depends(...)`.

`fastapi.security` incluye dependencias ya hechas para los esquemas habituales. `HTTPBasic` lee la cabecera `Authorization: Basic ...` y te da un `HTTPBasicCredentials` con el `username` y el `password` decodificados; si falta la cabecera, responde `401` con `WWW-Authenticate` por sí sola. `get_current_user` depende de ella, compara las credenciales con el hash guardado y lanza `401` si no coinciden. Swagger UI (`/docs`) también muestra un botón "Authorize" para ella.

## Reglas de contraseña

Las contraseñas se guardan como hashes `bcrypt`, nunca en texto plano. `hash_password` y `verify_password` envuelven las dos llamadas a `bcrypt`, y el modelo `UserCreate` exige una contraseña de **8 a 72 caracteres ASCII imprimibles**; el nombre de usuario no puede contener espacios ni `:`, porque HTTP Basic envía `usuario:contraseña` en ASCII. `bcrypt` no puede manejar más de 72 bytes, así que el modelo rechaza con `422` las contraseñas más largas, igual que las que no son ASCII. Un login con un usuario desconocido también ejecuta una comparación `bcrypt` contra un hash falso, para que el tiempo de respuesta no revele qué usuarios existen.

## Ejemplos de Peticiones con `curl`

1. **Registrar un usuario:**
   ```bash
   curl -X POST -H "Content-Type: application/json" \
   -d '{"username": "user1", "password": "password123"}' \
   http://127.0.0.1:8000/users
   ```

2. **Obtener la lista de usuarios (con autenticación):**
   ```bash
   curl -u user1:password123 http://127.0.0.1:8000/users
   ```

3. **Obtener la lista de usuarios (sin autenticación):**
   ```bash
   curl -i http://127.0.0.1:8000/users
   ```
   Debe devolver `401 Unauthorized` con la cabecera `WWW-Authenticate: Basic realm="Authentication Required"`: así el servidor le indica al cliente qué tipo de autenticación espera.

4. **Obtener la lista de usuarios (contraseña incorrecta):**
   ```bash
   curl -i -u user1:wrongpass http://127.0.0.1:8000/users
   ```
   También `401` con `WWW-Authenticate`, pero esta vez el cuerpo es `{"detail":"Invalid credentials"}`: la cabecera la pone tu `get_current_user` (el hueco del nombre de la cabecera), no `HTTPBasic`.

> **Windows:** en PowerShell 5.1 `curl` es un alias de `Invoke-WebRequest`, así que usa `curl.exe`, escribe el comando en una sola línea y escapa las comillas dentro del JSON (si no, el servidor responde `422`): `curl.exe -X POST -H "Content-Type: application/json" -d '{\"username\":\"user1\",\"password\":\"password123\"}' http://127.0.0.1:8000/users`. En CMD las comillas simples no funcionan. Tienes los comandos listos para ambas consolas en `example/commands_cmd.txt` y `example/commands_powershell.txt`.

## Puntos a Considerar

- Las contraseñas nunca deben almacenarse en texto plano.
- Registrar el mismo usuario dos veces responde `409 Conflict`; una contraseña de menos de 8 o más de 72 caracteres responde `422`.
- Basic Auth envía las credenciales codificadas en Base64 (codificación, no cifrado), así que en producción usa siempre HTTPS.
- Prueba tanto los casos de autenticación correcta como los fallidos.

¡Buena suerte!
