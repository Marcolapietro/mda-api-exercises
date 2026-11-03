# Ejercicio 12: Implementación de Roles y Permisos en una API con FastAPI

## Inicio Rápido

```bash
cd exercises/12-roles-permissions
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
fastapi dev app.py
```

Rellena los huecos (`_____`) de arriba abajo. Los dos roles de `require_role(_____)` al final del fichero se leen al cargar el fichero: en Python 3.12 y 3.13 la app no arranca hasta que los rellenas (`NameError: name '_____' is not defined`), y en Python 3.14 arranca pero `/admin/dashboard` y `/student/data` responden `403` a todo el mundo. Los demás huecos (el código de estado `403`, el rol `"student"` de los usuarios nuevos y el método `pop`) solo importan cuando una petición llega hasta ellos. Los roles son strings, así que escríbelos con comillas: `"admin"`, `"student"`. La API se ejecuta en `http://127.0.0.1:8000`.

## Objetivo
- **Asignación de Roles y Permisos:** Implementar un sistema de control de acceso basado en roles para la API.
- **Protección de Rutas:** Asegurar que solo los usuarios con los permisos adecuados puedan acceder a rutas específicas.
- **Autenticación y Seguridad:** Utilizar JWT (JSON Web Tokens) y una dependencia que comprueba el rol para gestionar usuarios, roles y permisos.

---

## Requisitos Previos

1. **Instalar Dependencias:**
   Asegúrate de tener instaladas las siguientes bibliotecas:
   - FastAPI (`fastapi[standard]`)
   - PyJWT
   - bcrypt

   Puedes instalarlas con:
   ```bash
   pip install -r requirements.txt
   ```

2. **Clonar el Proyecto:**
   Clona el repositorio o copia el archivo `app.py` proporcionado.

3. **Ejecutar el Script:**
   Inicia la aplicación con:
   ```bash
   fastapi dev app.py
   ```

---

## Funcionalidades

### **Registro de Usuarios**
Los usuarios nuevos se registran **siempre** como `student`. El rol nunca se lee del cuerpo de la petición: aceptarlo permitiría que cualquiera se registrase como admin (una vulnerabilidad de *mass assignment*). Solo un admin puede cambiar el rol de un usuario, con `PUT /users/{username}`.

### **Cuenta de Administrador**
Al arrancar, la app crea un usuario `admin`. Su contraseña se toma de la variable de entorno `ADMIN_PASSWORD`; si no está definida, se genera una aleatoria y se muestra en la consola (la terminal donde se ejecuta `fastapi dev`):

```
Admin user created -> username: admin  password: Xy3...
```

La línea se muestra una sola vez, aunque `fastapi dev` carga tu archivo dos veces (una para encontrar la app y otra en el proceso de recarga): la primera carga guarda la contraseña generada en la variable de entorno `ADMIN_PASSWORD` y la segunda la reutiliza. Para elegir tu propia contraseña, define `ADMIN_PASSWORD` antes de arrancar el servidor.

### **Inicio de Sesión**
Autentica a los usuarios y les proporciona un token JWT que será necesario para acceder a las rutas protegidas. El token incluye el rol del usuario como *claim*, pero ese *claim* es solo informativo. En cada petición se vuelve a buscar al usuario a partir del *claim* `sub` del token, así que los permisos nunca dependen de lo que diga el token: el rol se lee del almacén del servidor en cada petición.

### **Roles Disponibles**
1. **Admin:**
   - Acceso a las rutas de admin, incluidas aquellas que gestionan usuarios. No a `/student/data`: `require_role(...)` comprueba un rol exacto, así que un admin también recibe `403` ahí.
   - Puede realizar acciones como actualizar o eliminar otros usuarios.

2. **Student:**
   - Acceso restringido a rutas específicas diseñadas para estudiantes.

### **Protección de Rutas**
El acceso a las rutas está restringido según el rol del usuario. Esto se gestiona con una dependencia, `require_role("admin")`, que añades a cada operación protegida. En cada petición lee el rol **actual** del usuario en el almacén del servidor (no en el token) y responde `403` con `Permission denied.` si no coincide. Una petición sin token o con un token inválido ni siquiera llega ahí: responde `401`.

---

## Estructura de la API

### **Endpoints Principales**

1. **Registro de Usuarios**
   - **Método:** `POST`
   - **Ruta:** `/register`
   - **Descripción:** Registra un nuevo usuario (siempre con el rol `student`).

2. **Inicio de Sesión**
   - **Método:** `POST`
   - **Ruta:** `/login`
   - **Descripción:** Autentica a un usuario y retorna un token JWT.

3. **Perfil del Usuario**
   - **Método:** `GET`
   - **Ruta:** `/profile`
   - **Descripción:** Devuelve información del usuario autenticado.

4. **Listar Usuarios**
   - **Método:** `GET`
   - **Ruta:** `/users`
   - **Descripción:** Devuelve una lista paginada de usuarios registrados (`page` >= 1, `per_page` 1-100; cualquier otro valor responde `422`, y una página más allá del final `404`).
   - **Requiere:** Rol de administrador.

5. **Actualizar Usuario**
   - **Método:** `PUT`
   - **Ruta:** `/users/{username}`
   - **Descripción:** Actualiza información del usuario (contraseña o rol). El rol debe ser `admin` o `student`; cualquier otro responde `422`. Un admin no puede cambiar su propio rol (`409 Conflict`), así que la API nunca se queda sin admins.
   - **Requiere:** Rol de administrador.

6. **Eliminar Usuario**
   - **Método:** `DELETE`
   - **Ruta:** `/users/{username}`
   - **Descripción:** Elimina a un usuario. Un admin no puede eliminar su propia cuenta (`409 Conflict`).
   - **Requiere:** Rol de administrador.

7. **Dashboard de Administrador**
   - **Método:** `GET`
   - **Ruta:** `/admin/dashboard`
   - **Descripción:** Devuelve información exclusiva para administradores.

8. **Datos del Estudiante**
   - **Método:** `GET`
   - **Ruta:** `/student/data`
   - **Descripción:** Devuelve información específica del estudiante autenticado.

---

## Pruebas

### **Pruebas Básicas**
- Registra un usuario y verifica que puede iniciar sesión.
- Intenta acceder a rutas protegidas sin un token JWT y verifica que el acceso sea denegado.
- Genera un token válido e intenta acceder a rutas específicas según el rol del usuario.

### **Pruebas de Roles**
1. Inicia sesión como `admin` (contraseña mostrada al arrancar) y como un estudiante que hayas registrado.
2. Intenta acceder a rutas restringidas con cada token y verifica que las restricciones se aplican correctamente (`/admin/dashboard` debe devolver `403` a un estudiante).
3. Intenta registrar un usuario enviando `"role": "admin"` en el cuerpo: debe crearse igualmente como `student`.
4. Como admin, asciende a ese usuario con `PUT /users/{username}` y `{"role": "admin"}` y comprueba el nuevo acceso con el token que ya tiene: no hace falta volver a iniciar sesión, porque el rol se lee del servidor en cada petición (el *claim* `role` dentro del token es solo informativo).

Comandos listos para usar: `example/commands_cmd.txt` y `example/commands_powershell.txt`.

### **Errores Comunes**
- **Token Inválido:** Asegúrate de incluir el token JWT en el encabezado `Authorization` con el formato `Bearer <token>`.
- **Acceso Denegado:** Verifica que el usuario tiene el rol correcto para acceder a la ruta.
- **`NameError: name '_____' is not defined` al arrancar la app** (Python 3.12/3.13), **o incluso el admin recibe `403`** (Python 3.14): rellena los dos huecos de `require_role(_____)` al final del fichero, con comillas. Sin ellas (`require_role(admin)`) obtienes `NameError: name 'admin' is not defined` en 3.12/3.13 y `403` para todos en 3.14. **`500` en `/register`:** el rol de los usuarios nuevos sigue siendo un hueco.

---

## Notas Adicionales
- Usa herramientas como Postman o curl para probar las rutas de la API.
- Asegúrate de que el archivo `app.py` esté configurado correctamente antes de ejecutar las pruebas.
- Puedes ajustar los roles y permisos según las necesidades de tu aplicación.

---

¡Buena suerte implementando roles y permisos en tu API con FastAPI! 🎉
