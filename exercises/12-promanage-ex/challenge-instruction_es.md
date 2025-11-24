# Proyecto en Equipo: API para la Gestión de Proyectos y Tareas

## **Contexto: Business Case**

Tu equipo ha sido contratado por una empresa ficticia, **ProManage**, que desea una solución para gestionar proyectos y equipos de trabajo. La empresa necesita una API que permita registrar proyectos, asignar miembros a los equipos, gestionar tareas, y controlar permisos según los roles de los usuarios.

### **Objetivo del Proyecto**

Desarrollar una API RESTful que permita a **ProManage**:
1. Registrar usuarios y asignarles roles (`admin`, `manager`, `developer`).
2. Crear proyectos y asignar un equipo a cada proyecto.
3. Crear tareas asociadas a un proyecto, asignarlas a miembros del equipo y controlar su estado.
4. Restringir el acceso a ciertas rutas según los roles de los usuarios:
   - **Admin:** Puede gestionar todo.
   - **Manager:** Puede gestionar proyectos y tareas de su equipo.
   - **Developer:** Puede actualizar tareas asignadas a ellos.

---

## **Requisitos del Ejercicio**

### **Roles y Permisos**
- **Admin:**
  - Crear y eliminar usuarios.
  - Asignar roles a los usuarios.
  - Ver todos los proyectos y tareas.
- **Manager:**
  - Crear proyectos.
  - Asignar usuarios a proyectos.
  - Crear y asignar tareas a miembros del equipo.
- **Developer:**
  - Ver tareas asignadas.
  - Actualizar el estado de sus tareas (`To Do`, `In Progress`, `Done`).

### **Estructura de Datos**
- **Usuarios:**
  - `id`, `username`, `password`, `role`
- **Proyectos:**
  - `id`, `nombre`, `manager_id`, `equipo` (lista de `user_id`)
- **Tareas:**
  - `id`, `proyecto_id`, `asignado_a`, `descripcion`, `estado`

---

## **Instrucciones**

### **1. Formación de Equipos**
Forma equipos de 3 a 5 integrantes. Cada integrante asumirá una responsabilidad, como:
- Diseñar la estructura de datos.
- Implementar endpoints.
- Configurar roles y permisos.
- Probar la API.

### **2. Requerimientos Técnicos**
- Utiliza **Flask**, **JWT**, y **Flask-Principal** para autenticación y control de permisos.
- Implementa paginación para listar proyectos y tareas.
- Asegúrate de manejar errores y retornar respuestas claras en la API.

### **3. Endpoints Requeridos**

#### **Usuarios**
- **POST /register:** Registra un usuario con un rol asignado.
- **POST /login:** Autentica a un usuario y retorna un token JWT.
- **GET /usuarios:** (Admin) Lista todos los usuarios.

#### **Proyectos**
- **POST /proyectos:** (Manager/Admin) Crea un nuevo proyecto.
- **GET /proyectos:** (Todos los roles) Lista los proyectos visibles para el usuario.
- **PUT /proyectos/<id>:** (Manager/Admin) Actualiza información del proyecto.
- **DELETE /proyectos/<id>:** (Admin) Elimina un proyecto.

#### **Tareas**
- **POST /proyectos/<id>/tareas:** (Manager/Admin) Crea una tarea para un proyecto.
- **GET /proyectos/<id>/tareas:** (Todos los roles) Lista las tareas del proyecto.
- **PUT /tareas/<id>:** (Developer) Actualiza el estado de una tarea asignada al usuario.
- **DELETE /tareas/<id>:** (Manager/Admin) Elimina una tarea.

---

## **Criterios de Evaluación**

1. **Funcionalidad:** Los endpoints funcionan según lo esperado.
2. **Seguridad:** Se implementan roles y permisos correctamente.
3. **Organización:** El código está estructurado y fácil de entender.
4. **Colaboración:** Todos los integrantes del equipo participan en el desarrollo.

---

## **Pasos para el Equipo**

1. **Planificación:**
   - Define la estructura de la API y divide las responsabilidades.
2. **Desarrollo:**
   - Implementa los endpoints y prueba la funcionalidad de cada uno.
3. **Pruebas:**
   - Usa Postman para verificar los flujos de trabajo.
   - Asegúrate de manejar correctamente las restricciones de roles.
4. **Documentación:**
   - Escribe un archivo README que explique cómo usar la API.
   - Incluye ejemplos de solicitudes y respuestas.

---

## **Entregables**
1. Código fuente de la API.
2. Un archivo README detallado con instrucciones de uso.
3. Un informe breve explicando cómo dividieron el trabajo y resolvieron problemas.

---

¡Buena suerte desarrollando esta solución para **ProManage**! 🎉
