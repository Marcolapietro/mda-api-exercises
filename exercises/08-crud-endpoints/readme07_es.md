# Ejercicio 8: Creación de Endpoints CRUD

## Objetivo
Implementar endpoints CRUD (Crear, Leer, Actualizar, Eliminar) en una API REST utilizando Python y Flask.

## Descripción
En este ejercicio, ampliarás la API desarrollada en los ejercicios anteriores para incluir operaciones CRUD completas sobre el recurso "usuarios" (`/users`). Deberás crear rutas que permitan crear, leer, actualizar y eliminar usuarios. Completa los espacios en blanco del código proporcionado para implementar estas funcionalidades.

## Inicio Rápido

```bash
cd exercises/08-crud-endpoints
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

**Nota:** este ejercicio usa "users" como nombre del recurso y se apoya en los patrones de autenticación de los ejercicios anteriores.

## Requisitos
1. **Instalación de Dependencias Adicionales:**
   - Asegúrate de tener instalada la biblioteca `Flask` y las extensiones utilizadas en ejercicios anteriores (`pip install -r requirements.txt`).

2. **Estructura de la API:**
   - **Registrar usuario (`POST /users`):** endpoint público para registrar un usuario nuevo
   - **Login (`POST /login`):** autentica y devuelve un token JWT
   - **Obtener usuarios (`GET /users`):** protegido - devuelve la lista de todos los usuarios
   - **Crear usuario (admin) (`POST /users/admin`):** protegido - endpoint de administración para crear usuarios
   - **Actualizar usuario (`PUT /users/<username>`):** protegido - actualiza la contraseña de un usuario
   - **Eliminar usuario (`DELETE /users/<username>`):** protegido - elimina un usuario

3. **Implementación de CRUD:**
   - Utiliza los métodos HTTP adecuados para cada operación.
   - Asegura que las rutas estén protegidas utilizando la autenticación JWT implementada en ejercicios anteriores.
   - Valida las entradas y maneja errores apropiadamente.

4. **Pruebas:**
   - Utiliza herramientas como Postman o `curl` para probar cada una de las operaciones CRUD.
   - Asegúrate de que las operaciones funcionen correctamente y que se manejen los errores de manera adecuada.

## Pasos Sugeridos

1. **Lee `app.py`:**
   - El registro (`POST /users`), el login (`POST /login`), `GET /users` y `POST /users/admin` ya están implementados.
   - Fíjate en que cada ruta combina una URL con un método HTTP: la misma URL `/users/<username>` hace cosas distintas según el método.

2. **Completa los espacios en blanco (`_____`) en `exercises/08-crud-endpoints/app.py`:**

   ```python
   @app.route('/users/<username>', methods=['_____'])  # TODO: Set the correct HTTP method
   # Hint: Use 'PUT' for updates
   @jwt_required()
   def update_user(username):
       ...

   @app.route('/users/<username>', methods=['_____'])  # TODO: Set the correct HTTP method
   # Hint: Use 'DELETE' to remove a resource
   @jwt_required()
   def delete_user(username):
       ...
   ```

3. **Ejecuta la aplicación:**

   ```bash
   python app.py
   ```

4. **Prueba la API:**

   Usa Postman o `curl` para probar los endpoints CRUD:

   - **Registrar un usuario:**
     ```bash
     curl -X POST http://127.0.0.1:5000/users -H "Content-Type: application/json" -d '{"username": "user1", "password": "password123"}'
     ```

   - **Login (Basic Auth, devuelve un JWT):**
     ```bash
     curl -X POST http://127.0.0.1:5000/login -u user1:password123
     ```

   - **Obtener usuarios (usa el token del login):**
     ```bash
     curl -X GET http://127.0.0.1:5000/users -H "Authorization: Bearer TU_TOKEN"
     ```

   - **Actualizar un usuario:**
     ```bash
     curl -X PUT http://127.0.0.1:5000/users/user1 -H "Content-Type: application/json" -H "Authorization: Bearer TU_TOKEN" -d '{"password": "newpassword456"}'
     ```

   - **Eliminar un usuario:**
     ```bash
     curl -X DELETE http://127.0.0.1:5000/users/user1 -H "Authorization: Bearer TU_TOKEN"
     ```

   - **Registrar el mismo usuario dos veces (esperado: 409 Conflict):**
     ```bash
     curl -i -X POST http://127.0.0.1:5000/users -H "Content-Type: application/json" -d '{"username": "user1", "password": "password123"}'
     ```

   > **Windows:** tienes estos comandos listos para ejecutar en `example/commands_cmd.txt` y `example/commands_powershell.txt` (en PowerShell usa `curl.exe`, no `curl`).

## Resultados Esperados

- La API debe permitir crear, leer, actualizar y eliminar usuarios.
- Todas las rutas protegidas deben requerir un token JWT válido.
- Deben devolverse respuestas de error ante entradas inválidas o recursos inexistentes.

## Entendiendo los Códigos de Estado HTTP

Este ejercicio usa varios códigos de estado HTTP. Es importante saber cuándo usar cada uno:

- **200 OK**: la petición ha ido bien (GET, PUT)
- **201 Created**: se ha creado un recurso nuevo (POST)
- **400 Bad Request**: datos de entrada inválidos (campos que faltan, formato incorrecto)
- **401 Unauthorized**: falta la autenticación o el token no es válido
- **404 Not Found**: el recurso no existe
- **409 Conflict**: el recurso ya existe (usuario duplicado)
- **500 Internal Server Error**: error en el servidor

### Métodos HTTP y su Propósito

- **POST**: crear un recurso nuevo
- **GET**: obtener uno o varios recursos
- **PUT**: actualizar un recurso completo (sustituye todos los campos)
- **DELETE**: eliminar un recurso

## Recursos Adicionales

- [Documentación de Flask](https://flask.palletsprojects.com/)
- [Documentación de Flask-JWT-Extended](https://flask-jwt-extended.readthedocs.io/)
- [Buenas prácticas de APIs REST](https://restfulapi.net/)
- [Códigos de estado HTTP](https://developer.mozilla.org/es/docs/Web/HTTP/Status)

## Notas

- Este ejercicio usa almacenamiento en memoria, así que todos los datos se pierden al reiniciar la aplicación.
- En producción usarías una base de datos real y medidas de seguridad adicionales.
- El código tiene espacios en blanco (`_____`) para completar: céntrate en entender qué método HTTP corresponde a cada ruta.
