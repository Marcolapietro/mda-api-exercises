# Ejercicio 12: Implementación de Roles y Permisos en una API Flask

## Inicio Rápido

```bash
cd exercises/12-roles-permissions
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

## Objetivo
- **Asignación de Roles y Permisos:** Implementar un sistema de control de acceso basado en roles para la API.
- **Protección de Rutas:** Asegurar que solo los usuarios con los permisos adecuados puedan acceder a rutas específicas.
- **Autenticación y Seguridad:** Utilizar JWT (JSON Web Tokens) y Flask-Principal para gestionar usuarios, roles y permisos.

---

## Requisitos Previos

1. **Instalar Dependencias:**
   Asegúrate de tener instaladas las siguientes bibliotecas:
   - Flask
   - Flask-JWT-Extended
   - Flask-Principal
   - Werkzeug

   Puedes instalarlas con:
   ```bash
   pip install -r requirements.txt
   ```

2. **Clonar el Proyecto:**
   Clona el repositorio o copia el archivo `app.py` proporcionado.

3. **Ejecutar el Script:**
   Inicia la aplicación con:
   ```bash
   python app.py
   ```

---

## Funcionalidades

### **Registro de Usuarios**
Los usuarios nuevos se registran **siempre** como `student`. El rol nunca se lee del cuerpo de la petición: aceptarlo permitiría que cualquiera se registrase como admin (una vulnerabilidad de *mass assignment*). Solo un admin puede cambiar el rol de un usuario, con `PUT /users/<username>`.

### **Cuenta de Administrador**
Al arrancar, la app crea un usuario `admin`. Su contraseña se toma de la variable de entorno `ADMIN_PASSWORD`; si no está definida, se genera una aleatoria y se muestra en la consola:

```
Admin user created -> username: admin  password: Xy3...
```

### **Inicio de Sesión**
Autentica a los usuarios y les proporciona un token JWT que será necesario para acceder a las rutas protegidas. El token incluye el rol del usuario como *claim*. En cada petición la identidad se reconstruye a partir del token (`Principal(app, use_sessions=False)`), así que los permisos nunca dependen de una cookie de sesión.

### **Roles Disponibles**
1. **Admin:**
   - Acceso a todas las rutas, incluidas aquellas que gestionan usuarios.
   - Puede realizar acciones como actualizar o eliminar otros usuarios.

2. **Student:**
   - Acceso restringido a rutas específicas diseñadas para estudiantes.

### **Protección de Rutas**
El acceso a las rutas está restringido según el rol del usuario. Esto se gestiona mediante los decoradores de Flask-Principal que verifican los permisos asignados.

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
   - **Descripción:** Devuelve una lista paginada de usuarios registrados.

5. **Actualizar Usuario**
   - **Método:** `PUT`
   - **Ruta:** `/users/<username>`
   - **Descripción:** Actualiza información del usuario (contraseña o rol).
   - **Requiere:** Rol de administrador.

6. **Eliminar Usuario**
   - **Método:** `DELETE`
   - **Ruta:** `/users/<username>`
   - **Descripción:** Elimina a un usuario.
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
4. Como admin, asciende a ese usuario con `PUT /users/<username>` y `{"role": "admin"}` y comprueba el nuevo acceso con el token que ya tiene: no hace falta volver a iniciar sesión, porque el rol se lee del servidor en cada petición (el *claim* `role` dentro del token es solo informativo).

Comandos listos para usar: `example/commands_cmd.txt` y `example/commands_powershell.txt`.

### **Errores Comunes**
- **Token Inválido:** Asegúrate de incluir el token JWT en el encabezado `Authorization` con el formato `Bearer <token>`.
- **Acceso Denegado:** Verifica que el usuario tiene el rol correcto para acceder a la ruta.

---

## Notas Adicionales
- Usa herramientas como Postman o curl para probar las rutas de la API.
- Asegúrate de que el archivo `app.py` esté configurado correctamente antes de ejecutar las pruebas.
- Puedes ajustar los roles y permisos según las necesidades de tu aplicación.

---

¡Buena suerte implementando roles y permisos en tu API Flask! 🎉
