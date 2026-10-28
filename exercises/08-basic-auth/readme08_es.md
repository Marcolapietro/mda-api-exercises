# Ejercicio 8: Autenticación Básica

## Objetivo
Implementar autenticación básica (Basic Auth) en una API REST utilizando Python y Flask.

## Descripción
En este ejercicio, desarrollarás una API REST sencilla que maneja recursos de "usuarios". Implementarás la autenticación básica para proteger ciertas rutas, asegurando que solo usuarios autenticados puedan acceder a ellas.

## Inicio Rápido

```bash
cd exercises/08-basic-auth
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Requisitos
1. **Configuración del Proyecto:**
   - Inicializa un entorno virtual.
   - Instala las dependencias necesarias (`Flask`, `Flask-HTTPAuth`, `Werkzeug`).

2. **Estructura de la API:**
   - Crea una ruta para registrar nuevos usuarios (`POST /users`).
   - Crea una ruta para obtener la lista de usuarios (`GET /users`), protegida con autenticación básica.

3. **Implementación de Autenticación Básica:**
   - Utiliza `Flask-HTTPAuth` para manejar la autenticación.
   - Almacena las contraseñas de forma segura utilizando `Werkzeug` para hashear las contraseñas.
   - Protege las rutas que requieren autenticación, verificando las credenciales proporcionadas.

4. **Pruebas:**
   - Utiliza herramientas como Postman o `curl` para probar las rutas protegidas con y sin credenciales válidas.

## Instrucciones

En el espacio `_____`, utiliza la función adecuada de Werkzeug para hashear la contraseña proporcionada por el usuario.
También, observa los espacios dentro del código para configurar los métodos HTTP adecuados para cada función.
Una vez corregido, ejecuta el script y realiza las pruebas desde Postman.

## Pasos Sugeridos

1. **Inicializa el Proyecto:**
   ```bash
   cd exercises/08-basic-auth
   python -m venv venv
   source venv/bin/activate  # En Windows usa `venv\Scripts\activate`
   pip install -r requirements.txt
   ```

2. **Crea la API:**
   - Configura la aplicación Flask.
   - Define las rutas para registrar y listar usuarios.

3. **Implementa la Autenticación Básica:**
   - Usa `Flask-HTTPAuth` para crear el manejador de autenticación.
   - Hashea las contraseñas con `generate_password_hash` de Werkzeug.
   - Verifica las credenciales con `check_password_hash`.

4. **Prueba la API:**
   - Registra un usuario con `POST /users`.
   - Intenta acceder a `GET /users` sin credenciales (debe fallar).
   - Accede a `GET /users` con credenciales válidas (debe funcionar).

## Ejemplos de Peticiones con `curl`

1. **Registrar un usuario:**
   ```bash
   curl -X POST -H "Content-Type: application/json" \
   -d '{"username": "user1", "password": "password123"}' \
   http://127.0.0.1:5000/users
   ```

2. **Obtener la lista de usuarios (con autenticación):**
   ```bash
   curl -u user1:password123 http://127.0.0.1:5000/users
   ```

3. **Obtener la lista de usuarios (sin autenticación):**
   ```bash
   curl -i http://127.0.0.1:5000/users
   ```
   Debe devolver `401 Unauthorized` con la cabecera `WWW-Authenticate: Basic realm="Authentication Required"`: así el servidor le indica al cliente qué tipo de autenticación espera.

> **Windows:** en PowerShell usa `curl.exe` en lugar de `curl`. En CMD las comillas simples no funcionan; tienes los comandos listos en `example/commands_cmd.txt` y `example/commands_powershell.txt`.

## Puntos a Considerar

- Las contraseñas nunca deben almacenarse en texto plano.
- Basic Auth envía las credenciales codificadas en Base64 (codificación, no cifrado), así que en producción usa siempre HTTPS.
- Prueba tanto los casos de autenticación correcta como los fallidos.

¡Buena suerte!
