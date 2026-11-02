# Guía de Introducción a FastAPI

## Índice
1. [¿Qué es FastAPI?](#qué-es-fastapi)
2. [Preparación del Entorno](#preparación-del-entorno)
3. [Tu Primera Aplicación FastAPI](#tu-primera-aplicación-fastapi)
4. [Conceptos Básicos](#conceptos-básicos)
5. [Trabajar con JSON](#trabajar-con-json)
6. [Recursos Adicionales](#recursos-adicionales)

## ¿Qué es FastAPI?
FastAPI es un framework web moderno escrito en Python para crear APIs de manera rápida y con un mínimo número de líneas de código. Es popular porque usa las anotaciones de tipo estándar de Python para leer, validar y documentar por ti las peticiones y respuestas.

### Características Principales:
- Rápido de escribir: las anotaciones de tipo sustituyen gran parte del análisis y las comprobaciones manuales
- Validación automática de datos con Pydantic
- Documentación interactiva de la API generada automáticamente (Swagger UI en `/docs`)
- Basado en el estándar ASGI (Starlette y uvicorn)
- Servidor de desarrollo con recarga automática (`fastapi dev`)
- Documentación extensiva
- Gran comunidad

## Preparación del Entorno

### Paso 1: Instalación de Python
1. Descarga Python desde [python.org](https://python.org)
2. Asegúrate de marcar la opción "Add Python to PATH" durante la instalación
3. Verifica la instalación abriendo una terminal y escribiendo:
   ```bash
   python --version
   ```

### Paso 2: Crear un Entorno Virtual
```bash
# Windows
python -m venv venv

# Linux/Mac
python3 -m venv venv

# Activar el entorno virtual
# Windows
venv\Scripts\activate

# Linux/Mac
source venv/bin/activate
```

### Paso 3: Instalar FastAPI
```bash
pip install "fastapi[standard]"
```
La opción `standard` instala también el comando `fastapi` y el servidor uvicorn.

## Tu Primera Aplicación FastAPI

### Paso 1: Crear el archivo app.py
```python
from fastapi import FastAPI

app = FastAPI()

@app.get("/")
def hello_world():
    return {"message": "¡Hola, estudiantes!"}
```

### Paso 2: Ejecutar la aplicación
```bash
fastapi dev app.py
```
Visita http://127.0.0.1:8000 en tu navegador.

`fastapi dev` es el servidor de desarrollo: recarga la app cada vez que guardas el archivo. Nunca lo uses en un servidor público; su equivalente para producción es `fastapi run`.

FastAPI también genera automáticamente documentación interactiva de tu app. Abre http://127.0.0.1:8000/docs para ver todos los endpoints y probarlos desde el navegador.

## Conceptos Básicos

### 1. Operaciones de Ruta (Path Operations)
Una operación de ruta es una función que responde a una combinación de método HTTP y ruta. El decorador indica cuál: `@app.get(...)` para GET, `@app.post(...)` para POST, etc.

```python
@app.get("/about")
def about():
    return "¡Bienvenidos a mi primera aplicación FastAPI!"

@app.get("/user/{username}")
def show_user(username: str):
    return f"¡Hola, {username}!"
```

### 2. Métodos HTTP
Hay un decorador por método, con su mismo nombre:

```python
@app.get("/login")
def login_form():
    return "Por favor, inicia sesión"

@app.post("/login")
def login():
    return "Procesando login..."
```

### 3. Parámetros de Ruta
Un nombre entre llaves en la ruta se convierte en un parámetro de la función con el mismo nombre. Su anotación de tipo le dice a FastAPI cómo convertir (y comprobar) el valor:

```python
@app.get("/user/{username}")
def show_user(username: str):
    return f"Perfil de usuario: {username}"

@app.get("/post/{post_id}")
def show_post(post_id: int):
    return f"Mostrando publicación {post_id}"
```

Si alguien pide `/post/abc`, FastAPI responde con un error (422) antes de ejecutar tu función, porque `abc` no es un `int`.

## Trabajar con JSON

Ya que construirás APIs en este curso, es importante aprender cómo FastAPI maneja datos JSON. JSON es el formato estándar para enviar y recibir datos en APIs web.

### 1. Devolver Respuestas JSON

Simplemente devuelve un diccionario o una lista de Python; FastAPI la convierte a JSON por ti:

```python
@app.get("/api/hello")
def hello_api():
    return {"message": "¡Hola, Mundo!"}

@app.get("/api/user/{user_id}")
def get_user(user_id: int):
    return {"id": user_id, "name": "Juan Pérez", "email": "juan@ejemplo.com"}

@app.get("/api/users")
def get_users():
    return [
        {"id": 1, "name": "Alicia"},
        {"id": 2, "name": "Roberto"},
    ]
```

Un texto simple también se envía como JSON (entre comillas). Cuando quieras texto plano, como en `GET /` y `GET /about`, indícalo en el decorador:

```python
from fastapi.responses import PlainTextResponse

@app.get("/", response_class=PlainTextResponse)
def index():
    return "¡Bienvenidos a mi primera aplicación FastAPI!"
```

### 2. Leer JSON de las Peticiones

Para recibir un cuerpo JSON, describe su forma con un modelo de Pydantic: una clase que hereda de `BaseModel` y lista los campos con sus tipos. Un campo con valor, como `name: str = "Invitado"`, es opcional y usa ese valor por defecto.

```python
from pydantic import BaseModel

class GreetRequest(BaseModel):
    name: str = "Invitado"

@app.post("/api/greet")
def greet(body: GreetRequest):
    # FastAPI ya leyó el JSON y lo comprobó contra GreetRequest
    return {"greeting": f"¡Hola, {body.name}!"}
```

Declarar `body: GreetRequest` es todo lo que FastAPI necesita: lee el JSON, lo valida (un `name` que no sea texto recibe automáticamente un error 422) y te entrega un objeto listo para usar. Como el modelo también describe el cuerpo, `/docs` lo muestra y permite probarlo.

**Probar con Postman:**
- Establece el método a POST
- En la pestaña Body, selecciona "raw" y "JSON"
- Ingresa: `{"name": "Alicia"}`
- Envía la petición

### 3. Almacenamiento Simple en Memoria

Para estos ejercicios, usaremos diccionarios de Python para almacenar datos (no se necesita base de datos):

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()

class UserCreate(BaseModel):
    name: str
    email: str

# Almacenar usuarios en memoria
users = {}
next_id = 1

@app.post("/api/users")
def create_user(data: UserCreate):
    global next_id
    user = {"id": next_id, "name": data.name, "email": data.email}
    users[next_id] = user
    next_id += 1
    return user

@app.get("/api/users")
def list_users():
    return list(users.values())

@app.get("/api/users/{user_id}")
def get_user(user_id: int):
    if user_id in users:
        return users[user_id]
    raise HTTPException(status_code=404, detail="Usuario no encontrado")
```

### 4. Parámetros de Consulta

Un parámetro de la función que no está en la ruta se lee de la cadena de consulta:

```python
@app.get("/api/search")
def search(q: str = ""):
    # Acceder a parámetro de consulta: /api/search?q=fastapi
    return {"search_query": q}
```

**Nota:** Aprenderás más sobre códigos de estado HTTP, validación y manejo de errores en los próximos ejercicios.

## Recursos Adicionales

### Documentación Oficial
- [Documentación de FastAPI](https://fastapi.tiangolo.com/es/)
- [Tutorial Oficial de FastAPI](https://fastapi.tiangolo.com/es/tutorial/)

### Herramientas Útiles
- Postman (para probar APIs)
- Git (para control de versiones)

### Mejores Prácticas
1. Siempre usa entornos virtuales
2. Mantén el código organizado en módulos
3. Implementa manejo de errores
4. Escribe pruebas para tu código
5. Documenta tu código adecuadamente

## Consejos para Estudiantes
- Practica escribiendo código regularmente
- No tengas miedo de experimentar
- Únete a comunidades de FastAPI/Python
- Revisa proyectos de código abierto
- Mantén un registro de tu aprendizaje

¡Feliz aprendizaje!

## Tarea del ejercicio (lo que debes entregar)

**Objetivo:** Crear tu primera aplicación FastAPI con rutas simples y probarla usando Postman.

### 1) Construir la Aplicación
Crea un archivo `app.py` con los siguientes endpoints:

**Endpoints requeridos:**
- `GET /` - Retornar un mensaje de bienvenida (texto o JSON)
- `GET /about` - Retornar información sobre la app
- `GET /api/hello` - Retornar un mensaje JSON: `{"message": "¡Hola, Mundo!"}`
- `GET /api/user/{username}` - Retornar JSON con el nombre de usuario
- `POST /api/greet` - Aceptar JSON con un campo "name", retornar un saludo

**Ejemplo para el endpoint POST:**
```python
# Cuerpo de petición: {"name": "Alicia"}
# Respuesta: {"greeting": "¡Hola, Alicia!"}
```

### 2) Ejecutar la Aplicación
```bash
# Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Instalar dependencias
pip install -r requirements.txt

# Ejecutar la app (rellena los huecos de arriba abajo; la app arranca cuando los decoradores están completos)
fastapi dev app.py
```

Visita http://127.0.0.1:8000 en tu navegador para ver tu app en ejecución, y http://127.0.0.1:8000/docs para ver la documentación automática.

### 3) Probar con Postman
- Crear una colección de Postman llamada "FastAPI Intro" (mantenerla local, no subirla al repo)
- Añadir peticiones para los 5 endpoints
- Para cada petición, incluir:
  - Un nombre claro (ej., "Obtener Mensaje de Bienvenida")
  - Una breve descripción de lo que hace el endpoint
  - El método HTTP correcto (GET o POST)
  - Respuesta de ejemplo
- Para la petición POST, recuerda:
  - Establecer Body a "raw" y "JSON"
  - Incluir un cuerpo JSON de ejemplo: `{"name": "Tu Nombre"}`

### 4) Entregables
Enviar lo siguiente:
1. Tu archivo `app.py`
2. Captura de pantalla mostrando la app ejecutándose en tu terminal
3. Captura de pantalla de tu colección de Postman mostrando las 5 peticiones
4. Colección de Postman exportada (archivo JSON) compartida por el canal indicado

### 5) Consejos
- Usa los ejemplos de esta guía como referencia
- Prueba cada endpoint en tu navegador (para peticiones GET) antes de probar en Postman
- Asegúrate de que tu app esté ejecutándose antes de probar en Postman
- No te preocupes por el manejo de errores o validación todavía - lo aprenderás en los próximos ejercicios
