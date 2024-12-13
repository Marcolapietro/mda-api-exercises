# Ejercicio 5: Autenticación con JSON Web Tokens (JWT)

## Objetivo

Implementar autenticación utilizando JSON Web Tokens (JWT) en una API REST desarrollada con Python y Flask.

## Descripción

En este ejercicio, ampliarás la API para incluir autenticación mediante JWT. Implementarás endpoints para que los usuarios puedan iniciar sesión y obtener un token JWT, el cual deberán incluir en las solicitudes a rutas protegidas para acceder a recursos seguros.

## Requisitos

1. **Instalación de Dependencias Adicionales:**

   - Instala las bibliotecas necesarias para manejar JWT:
     ```bash
     pip install Flask-JWT-Extended
     ```

2. **Estructura de la API:**

   - Crea una ruta para registrar usuarios (`POST /estudiantes`).
   - Crea una ruta para que los usuarios inicien sesión (`POST /login`) y obtengan un token JWT.
   - Crea una ruta protegida (`GET /perfil`) que solo pueda ser accedida con un token JWT válido.
   - Incluye una ruta para obtener la lista de estudiantes (`GET /estudiantes`), protegida con autenticación.

3. **Implementación de JWT:**

   - Configura `Flask-JWT-Extended` en tu aplicación.
   - Genera un token JWT al autenticar correctamente al usuario en la ruta de inicio de sesión.
   - Protege rutas sensibles utilizando decoradores que verifiquen la presencia y validez del token JWT.

4. **Pruebas:**

   - Utiliza herramientas como Postman o `curl` para probar el flujo de autenticación y el acceso a rutas protegidas con y sin un token válido.

## Pasos Detallados

1. **Configura la Aplicación:**

   - Define una clave secreta para firmar los tokens JWT:
     ```python
     app.config['JWT_SECRET_KEY'] = 'tu_clave_secreta_jwt'
     ```

2. **Registro de Usuarios:**

   - Implementa la ruta `POST /estudiantes` para registrar usuarios, hasheando las contraseñas antes de almacenarlas.

3. **Inicio de Sesión:**

   - Implementa la ruta `POST /login` para autenticar usuarios registrados.
   - Genera un token JWT utilizando la función `create_access_token`:
     ```python
     access_token = create_access_token(identity=username)
     ```

4. **Protección de Rutas:**

   - Usa el decorador `@jwt_required()` para proteger la ruta `GET /perfil`.
   - Obtén la identidad del usuario desde el token JWT usando `get_jwt_identity`:
     ```python
     current_user = get_jwt_identity()
     ```

5. **Pruebas:**

   - Registra un usuario mediante una solicitud `POST /estudiantes`.
   - Inicia sesión mediante `POST /login` y obtén el token JWT.
   - Revisa en [jwt.io](https://www.postman.com/downloads/) copiando y pegando el token generado.
   - Usa el token JWT como encabezado de autorización en `GET /perfil` y verifica el acceso.

## Ejemplo de Solicitudes con `curl`

1. **Registro de Usuario:**

   ```bash
   curl -X POST -H "Content-Type: application/json" \
   -d '{"username": "usuario1", "password": "1234"}' \
   http://127.0.0.1:5000/estudiantes
   ```

2. **Inicio de Sesión:**

   ```bash
   curl -X POST -u usuario1:1234 \
   http://127.0.0.1:5000/login
   ```

3. **Acceso a Rutas Protegidas:**

   ```bash
   curl -X GET -H "Authorization: Bearer <tu_token_jwt>" \
   http://127.0.0.1:5000/perfil
   ```

## Puntos a Considerar

- Cambia la clave secreta utilizada en `JWT_SECRET_KEY` en producción.
- Maneja correctamente los errores para solicitudes no autenticadas o con tokens inválidos.
- Configura tiempos de expiración para los tokens JWT si es necesario.

¡Buena suerte! Si tienes dudas, consulta la documentación oficial de [Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/en/stable/).

