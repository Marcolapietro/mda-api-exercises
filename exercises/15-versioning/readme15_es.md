# Ejercicio 15: Versionado de APIs

## Inicio Rápido

```bash
cd exercises/15-versioning
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env  # Windows (cp en Linux/Mac)
fastapi dev app.py
```

Opcional: pon un `JWT_SECRET_KEY` fijo en `.env` (plantilla: `.env.example`, genera un valor con `python -c "import secrets; print(secrets.token_hex(32))"`) para que tus tokens sobrevivan a los reinicios; sin él se genera un secreto aleatorio en cada arranque. Tras editar `.env`, para la app (Ctrl+C) y vuelve a arrancarla.

Rellena los huecos (`_____`) de arriba abajo. La app arranca cuando están rellenos tres huecos: el `status_code` del decorador `POST` de v1 y las dos llamadas a `app.include_router(...)` al final de las rutas. Los demás huecos no impiden arrancar el servidor: los prefijos de los routers dan `404` hasta que son correctos, y el resto falla solo cuando una petición llega hasta ellos (un error `500` o una cabecera ausente).

## Objetivo

Aprende a gestionar versiones de API y manejar cambios incompatibles profesionalmente:

- **Gestión de Versiones**: Comprender cuándo y cómo crear nuevas versiones de API
- **Cambios Compatibles vs Incompatibles**: Identificar cambios que requieren nuevas versiones
- **Versionado por Ruta URL**: Implementar endpoints específicos de versión (`/api/v1`, `/api/v2`)
- **Estrategias de Deprecación**: Retirar versiones antiguas con advertencias apropiadas
- **Migración de Clientes**: Ayudar a los clientes a transicionar entre versiones
- **Cabeceras de Versión**: Comunicar información de versión a través de cabeceras HTTP

## ¿Qué es el Versionado de APIs?

El **versionado de APIs** es la práctica de gestionar múltiples versiones de tu API simultáneamente para permitir la evolución sin romper clientes existentes.

**Por qué importa el versionado de APIs:**
- **Compatibilidad hacia atrás**: Los clientes antiguos continúan funcionando mientras mejoras la API
- **Migración gradual**: Los clientes pueden actualizar según su cronograma
- **Comunicación clara**: Las advertencias de deprecación dan tiempo a los clientes para adaptarse
- **Libertad de innovación**: Puedes mejorar la API sin miedo a romper clientes

**Ejemplos del mundo real:**
- **Twitter API**: v1.1 → v2 (rediseño mayor, ~2 años de migración)
- **Stripe API**: Usa versiones con fechas (2023-10-16, 2024-06-20)
- **GitHub API**: versiones con fecha elegidas con una cabecera (`X-GitHub-Api-Version: 2022-11-28`)
- **Google Maps API**: v3 (estable), con advertencias de deprecación

## Prerequisitos

Antes de comenzar este ejercicio, completa:
- **Ejercicio 11**: Autenticación JWT (este ejercicio usa JWT)
- **Ejercicio 05**: Endpoints CRUD (comprensión de operaciones REST)
- **Ejercicio 06**: Paginación de API (v2 incluye paginación)

## Cambios Compatibles vs Incompatibles

### Cambios No Incompatibles (No se necesita nueva versión)

**Agregar campos opcionales:**
```json
// Respuesta antigua
{"id": 1, "name": "Alice"}

// Respuesta nueva (compatible hacia atrás)
{"id": 1, "name": "Alice", "email": "alice@example.com"}
```
✅ Los clientes antiguos ignoran el nuevo campo - ¡sin problema!

**Agregar nuevos endpoints:**
- `POST /api/v1/notes` (existente)
- `DELETE /api/v1/notes/{note_id}` (nuevo)

✅ Los clientes antiguos no usan el nuevo endpoint - ¡sin problema!

**Agregar parámetros opcionales:**
```bash
# Solicitud antigua (aún funciona)
GET /api/v1/notes

# Solicitud nueva con filtro opcional
GET /api/v1/notes?tag=work
```
✅ Los clientes antiguos funcionan sin el parámetro - ¡sin problema!

### Cambios Incompatibles (Nueva versión requerida)

**Eliminar campos:**
```json
// Respuesta v1
{"id": 1, "name": "Alice", "email": "alice@example.com"}

// Respuesta v2 (INCOMPATIBLE - email eliminado)
{"id": 1, "name": "Alice"}
```
❌ ¡Los clientes antiguos esperando `email` se romperán!

**Renombrar campos:**
```json
// v1
{"user_id": 1, "user_name": "Alice"}

// v2 (INCOMPATIBLE - nombres de campo cambiados)
{"id": 1, "name": "Alice"}
```
❌ ¡Los clientes antiguos buscando `user_id` se romperán!

**Cambiar estructura de respuesta:**
```json
// v1 (array)
[{"id": 1}, {"id": 2}]

// v2 (INCOMPATIBLE - ahora es un objeto)
{"data": [{"id": 1}, {"id": 2}], "count": 2}
```
❌ ¡Los clientes antiguos esperando un array se romperán!

**Cambiar tipos de datos:**
```json
// v1
{"id": "1", "price": "19.99"}

// v2 (INCOMPATIBLE - strings → números)
{"id": 1, "price": 19.99}
```
❌ ¡Los clientes antiguos esperando strings se romperán!

**Hacer campos opcionales requeridos:**
```bash
# v1 (email opcional)
POST /api/v1/users {"name": "Alice"}

# v2 (INCOMPATIBLE - email ahora requerido)
POST /api/v2/users {"name": "Alice", "email": "alice@example.com"}
```
❌ ¡Los clientes antiguos que no envían email obtendrán errores!

## Estrategias de Versionado

### 1. Versionado por Ruta URL (Este Ejercicio)

**Formato:** `/api/v1/resource` vs `/api/v2/resource`

**Pros:**
- ✅ Muy explícito y visible
- ✅ Fácil de probar (solo cambia la URL)
- ✅ Funciona con todos los clientes HTTP
- ✅ Puede cachear diferentes versiones separadamente
- ✅ Simple de entender

**Cons:**
- ❌ Puede llevar a duplicación de código
- ❌ Las URLs cambian cuando cambia la versión

**Ejemplo:**
```python
v1 = APIRouter(prefix="/api/v1")
v2 = APIRouter(prefix="/api/v2")

@v1.get("/notes")
def get_notes_v1():
    return [...]  # Array simple

@v2.get("/notes")
def get_notes_v2():
    return {'data': [...], 'count': 10}  # Objeto envuelto
```

**Usado por:** Stripe, Twilio, Twitter, Shopify

### 2. Versionado Basado en Cabeceras

**Formato:** `Accept: application/vnd.api.v2+json`

**Pros:**
- ✅ Las URLs permanecen iguales
- ✅ Sigue principios REST
- ✅ Flexible

**Cons:**
- ❌ Menos visible
- ❌ Más difícil de probar
- ❌ Caché más complejo

**Ejemplo:**
```python
@app.get('/api/notes')
def get_notes(api_version: Annotated[str, Header()] = 'v1'):  # lee la cabecera API-Version
    if api_version == 'v2':
        return {'data': [...]}
    return [...]
```

**Usado por:** API de GitHub, API de Azure

### 3. Versionado por Parámetro de Consulta

**Formato:** `/api/notes?version=2`

**Pros:**
- ✅ Fácil de probar

**Cons:**
- ❌ No es RESTful
- ❌ Puede olvidarse/omitirse

**Ejemplo:**
```bash
GET /api/notes?version=2&page=1&per_page=10
```

**Usado por:** Algunas APIs internas, raramente en APIs públicas

### 4. Negociación de Contenido

**Formato:** `Accept: application/json; version=2`

**Pros:**
- ✅ Mecanismo HTTP estándar
- ✅ Flexible

**Cons:**
- ❌ Complejo de implementar
- ❌ Poco intuitivo

**Usado por:** Algunas APIs empresariales

## Este Ejercicio: Versionado por Ruta URL

Usamos **versionado por ruta URL** porque es:
- El más común en APIs del mundo real
- El más fácil de aprender y entender
- El más explícito y testeable
- Estándar de la industria

## Estructura del Ejercicio

Este ejercicio proporciona:
- `app.py` - Archivo de inicio con TODOs para estudiantes
- `example/example15.py` - Solución de referencia completa
- `requirements.txt` - Dependencias
- `readme15_es.md` - Este archivo de instrucciones

## Parte 1: Comprendiendo el Escenario (10 minutos)

### La Historia de Evolución

**Versión 1 (Original):**
Construiste una API de notas simple que devuelve notas como un array simple:
```json
[
  {"id": 1, "title": "Nota 1", "content": "...", "owner": "alice"},
  {"id": 2, "title": "Nota 2", "content": "...", "owner": "alice"}
]
```

**Problema:** ¡Los clientes han estado usando esto durante meses. No puedes simplemente cambiarlo!

**Versión 2 (Mejorada):**
Quieres agregar:
- Soporte de paginación
- Metadatos (conteo total, información de página)
- Timestamps (created_at, updated_at)
- Campo de tags
- Respuestas envueltas para consistencia

**Nueva estructura de respuesta:**
```json
{
  "data": [
    {
      "id": 1,
      "title": "Nota 1",
      "content": "...",
      "tags": ["trabajo", "importante"],
      "owner": "alice",
      "created_at": "2026-11-02T11:12:05.580221+00:00",
      "updated_at": "2026-11-02T11:12:05.580221+00:00"
    }
  ],
  "count": 1,
  "page": 1,
  "per_page": 10,
  "version": "v2"
}
```

**Solución:** Mantén v1 funcionando mientras lanzas v2, luego depreca v1 con advertencias.

### Cabeceras de Versión

Usaremos cabeceras HTTP para comunicar información de versión:

**Cabecera `API-Version`:**
Indica a los clientes qué versión están usando
```
API-Version: v2
```

**Cabecera `Deprecation` (RFC 9745):**
Indica a los clientes que la versión está deprecada y desde cuándo: `@` seguido de un timestamp Unix (aquí, 1 de enero de 2026)
```
Deprecation: @1767225600
```

**Cabecera `Sunset` (RFC 8594):**
Indica a los clientes cuándo dejará de funcionar la versión, como fecha HTTP
```
Sunset: Wed, 30 Jun 2027 00:00:00 GMT
```

**Cabecera `Link` con `rel="successor-version"`:**
Indica a los clientes qué versión sustituye a esta
```
Link: </api/v2>; rel="successor-version"
```

> La antigua cabecera `Warning` (`Warning: 299 - "..."`) está obsoleta desde el RFC 9111 (2022): no la uses en APIs nuevas.

## Parte 2: Implementando Cabeceras de Versión (15 minutos)

### Routers: uno por versión

Hasta ahora todas las rutas colgaban directamente de `app`. Aquí cada versión tiene su propio **`APIRouter`**, una mini-app que agrupa rutas:

- `APIRouter(prefix="/api/v1")` añade el prefijo a cada ruta declarada con `@v1.get(...)`, `@v1.post(...)`, así que no repites `/api/v1` en cada decorador.
- `dependencies=[Depends(...)]` ejecuta esas dependencias en todas las rutas del router. Aquí: la autenticación y las cabeceras de versión, escritas una vez en lugar de una por ruta.
- Un router no sirve nada hasta que la app lo incluye con `app.include_router(v1)`. Hazlo después de declarar las rutas: `include_router` copia las rutas que el router tiene en ese momento.

Una dependencia también puede declarar un parámetro `response: Response` (como el ejercicio 04 para poner `Location`). Las cabeceras que pongas ahí se añaden a la respuesta de la ruta. Así `add_deprecation_headers` marca todas las respuestas de v1 sin tocar las rutas.

> **Las cabeceras solo viajan en las respuestas correctas.** Cuando la dependencia de autenticación o una ruta lanza `HTTPException` (`401`, `403`, `404`), FastAPI construye una respuesta nueva y las cabeceras puestas en el `response` de la dependencia no forman parte de ella. Lo mismo pasa con `422` y con `405` (un `PUT` a `/api/v1/notes/2` nunca llega a las dependencias del router). Por eso `Deprecation`, `Sunset` y `Link` aparecen en los `200` y `201` de v1, no en sus errores. Compruébalo en la Parte 5.

### Tarea 2.1: Completar la Dependencia `add_deprecation_headers`

Abre `app.py` y encuentra la función `add_deprecation_headers`:

```python
def add_deprecation_headers(response: Response) -> None:
    """Dependencia del router: se ejecuta en cada petición a v1"""
    info = API_VERSIONS['v1']

    # TODO: Agregar cabecera API-Version con la versión que sirve este router
    # Hint: response.headers['API-Version'] = 'v1'
    response.headers['API-Version'] = _____

    # TODO: Agregar cabecera Deprecation (RFC 9745): "@" + cuándo se deprecó, como timestamp Unix
    response.headers['Deprecation'] = _____

    # TODO: Agregar cabecera Sunset (RFC 8594): cuándo dejará de funcionar, como fecha HTTP
    response.headers['Sunset'] = _____

    # TODO: Agregar cabecera Link apuntando a la versión que sustituye a esta
    response.headers['Link'] = _____
```

Las funciones `to_epoch()` y `to_http_date()` (definidas justo después de `API_VERSIONS`) convierten las fechas guardadas como `'2026-01-01'` al formato que necesitan las cabeceras.

**Tus tareas:**
1. Completa la cabecera `API-Version` con la versión que sirve este router
2. Agrega la cabecera `Deprecation`: `@` seguido de `to_epoch(...)` de la fecha de deprecación
3. Agrega la cabecera `Sunset`: `to_http_date(...)` de la fecha de sunset de `API_VERSIONS`
4. Agrega la cabecera `Link` apuntando a la versión sucesora

**Solución:**
```python
response.headers['API-Version'] = 'v1'
response.headers['Deprecation'] = f"@{to_epoch(info['deprecation_date'])}"
response.headers['Sunset'] = to_http_date(info['sunset_date'])
response.headers['Link'] = f'<{info["successor"]}>; rel="successor-version"'
```

### Tarea 2.2: Completar los Prefijos de los Routers

Debajo de las dependencias están los dos routers. `add_v2_header` ya está hecha: v2 solo pone `API-Version`, porque no está deprecada.

```python
# TODO: Completar el prefijo de cada router
v1 = APIRouter(
    prefix="/api/_____",
    tags=["v1 (deprecated)"],
    dependencies=[Depends(get_current_user), Depends(add_deprecation_headers)],
)
v2 = APIRouter(
    prefix="/api/_____",
    tags=["v2"],
    dependencies=[Depends(get_current_user), Depends(add_v2_header)],
)
```

**Tu tarea:** escribe `v1` y `v2` para que los prefijos sean `/api/v1` y `/api/v2`.

## Parte 3: Implementando Versión 1 (20 minutos)

La versión 1 es la API original y simple que muchos clientes ya están usando.

### Tarea 3.1: Completar las Rutas de v1

```python
@v1.get("/notes")
def get_notes_v1(user: Annotated[str, Depends(get_current_user)]) -> list[dict]:
    """Versión 1: Obtener todas las notas - Devuelve una lista simple"""
    user_notes = [note for note in notes.values() if note['owner'] == user]

    # TODO: Devolver la lista tal cual. Los clientes v1 esperan un array, no un objeto
    return _____


# TODO: Se creó una nota. ¿Qué código de estado?
@v1.post("/notes", status_code=_____)
def create_note_v1(data: NoteCreate, user: Annotated[str, Depends(get_current_user)]) -> dict:
    ...
```

**Tus tareas:**
1. Devolver la lista `user_notes` tal cual
2. Poner el código de estado de la ruta de creación

**¿Por qué no hay cabeceras aquí?**
Las rutas no tocan las cabeceras: la dependencia del router `v1` las añade a cada respuesta. Ese es el sentido del router.

## Parte 4: Implementando Versión 2 (30 minutos)

La versión 2 introduce cambios incompatibles con funcionalidad mejorada.

### Tarea 4.1: Completar `get_notes_v2` con Paginación

```python
@v2.get("/notes")
def get_notes_v2(
    user: Annotated[str, Depends(get_current_user)],
    page: Annotated[int, Query(ge=1)] = 1,
    per_page: Annotated[int, Query(ge=1, le=100)] = 10,
) -> dict:
    """Versión 2: Obtener todas las notas con paginación"""
    user_notes = [note for note in notes.values() if note['owner'] == user]

    # TODO: Calcular paginación
    start = _____
    end = start + per_page
    paginated_notes = user_notes[start:end]

    # TODO: Crear estructura de respuesta v2
    return {
        'data': _____,
        'count': _____,
        'page': page,
        'per_page': per_page,
        'version': 'v2'
    }
```

**Tus tareas:**
1. Calcular el índice de inicio para paginación: `(page - 1) * per_page`
2. Completar la estructura de respuesta con datos paginados

`page` y `per_page` se validan con `Query(ge=1)`: un `page=0` responde `422`.

### Tarea 4.2: Completar `create_note_v2` con Timestamps

```python
@v2.post("/notes", status_code=201)
def create_note_v2(data: NoteCreateV2, user: Annotated[str, Depends(get_current_user)]) -> dict:
    """Versión 2: Crear nota con timestamps y tags"""
    global note_id_counter

    now = datetime.now(timezone.utc).isoformat()  # calculado una vez, así los dos timestamps son idénticos
    # TODO: Crear nota con campos v2
    note = {
        'id': note_id_counter,
        'title': data.title,
        'content': data.content,
        'tags': data.tags,
        'owner': user,
        'created_at': _____,  # TODO: Agregar timestamp
        'updated_at': _____   # TODO: Agregar timestamp
    }

    notes[note_id_counter] = note
    note_id_counter += 1

    # TODO: Envolver respuesta en objeto 'data' para v2
    return _____
```

**Tus tareas:**
1. Agregar timestamp `created_at`: `now`, la cadena `datetime.now(timezone.utc).isoformat()` calculada justo arriba
2. Agregar timestamp `updated_at`: el mismo `now` (llamar dos veces a `datetime.now()` daría dos valores distintos)
3. Envolver la respuesta: `{'data': note, 'message': 'Note created successfully'}`

`get_note_v2` (también envuelta en `data`) y el nuevo `PATCH /api/v2/notes/{note_id}` ya están implementados.

### Tarea 4.3: Conectar los Routers a la App

Al final de las rutas:

```python
# TODO: Incluir los dos routers en la app
app.include_router(_____)
app.include_router(_____)
```

**Tu tarea:** incluir `v1` y `v2`.

## Parte 5: Probando las Versiones (40 minutos)

### Paso 5.1: Iniciar la Aplicación

```bash
cd exercises/15-versioning
fastapi dev app.py
```

Abre http://127.0.0.1:8000/docs: las rutas aparecen agrupadas por tag (`auth`, `v1 (deprecated)`, `v2`).

### Paso 5.2: Registrarse e Iniciar Sesión

> Los comandos de esta sección usan `curl` con sintaxis de `bash` (continuación con `\`, JSON entre comillas simples, `$TOKEN`). En **Windows PowerShell 5.1** `curl` es un alias de `Invoke-WebRequest`: usa `curl.exe`, escribe cada comando en una sola línea, escapa las comillas dentro del JSON (`-d '{\"username\":\"alice\",\"password\":\"password123\"}'`) y guarda el token con `$TOKEN = "..."`. Ese escapado se rompe en cuanto un valor del JSON tiene un espacio (`"My First Note"`): para esos bodies usa `Invoke-RestMethod`, p. ej. `Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/api/v2/notes -ContentType "application/json" -Headers @{ Authorization = "Bearer $TOKEN" } -Body (@{ title = "My Second Note"; content = "This is v2"; tags = @("work", "important") } | ConvertTo-Json)`. En **CMD** usa comillas dobles con `\"` dentro (`-d "{\"username\":\"alice\",\"password\":\"password123\"}"`), que también funciona con espacios, y `set TOKEN=...` / `%TOKEN%`.

```bash
# Registrar un usuario
curl -X POST http://127.0.0.1:8000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'

# Iniciar sesión para obtener token JWT
curl -X POST http://127.0.0.1:8000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'
```

Guarda el `access_token` de la respuesta (la contraseña debe tener entre 8 y 72 caracteres).

### Paso 5.3: Probar Versión 1 (Deprecada)

**Crear notas usando v1:**
```bash
TOKEN="tu_token_de_acceso_aqui"

curl -X POST http://127.0.0.1:8000/api/v1/notes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"Mi Primera Nota","content":"Esto es v1"}'
```

**Respuesta esperada (formato v1):**
```json
{
  "id": 1,
  "title": "Mi Primera Nota",
  "content": "Esto es v1",
  "owner": "alice"
}
```

**Obtener notas usando v1:**
```bash
curl -i http://127.0.0.1:8000/api/v1/notes \
  -H "Authorization: Bearer $TOKEN"
```

**Revisa las cabeceras - deberías ver advertencias de deprecación:**
```
API-Version: v1
Deprecation: @1767225600
Sunset: Wed, 30 Jun 2027 00:00:00 GMT
Link: </api/v2>; rel="successor-version"
```

**Cuerpo de respuesta (formato v1 - array simple):**
```json
[
  {
    "id": 1,
    "title": "Mi Primera Nota",
    "content": "Esto es v1",
    "owner": "alice"
  }
]
```

### Paso 5.4: Probar Versión 2 (Actual)

**Crear notas usando v2 (con tags):**
```bash
TOKEN="tu_token_de_acceso_aqui"

curl -X POST http://127.0.0.1:8000/api/v2/notes \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"Mi Segunda Nota","content":"Esto es v2","tags":["trabajo","importante"]}'
```

**Respuesta esperada (formato v2 - envuelto con timestamps):**
```json
{
  "data": {
    "id": 2,
    "title": "Mi Segunda Nota",
    "content": "Esto es v2",
    "tags": ["trabajo", "importante"],
    "owner": "alice",
    "created_at": "2026-11-02T11:12:05.580221+00:00",
    "updated_at": "2026-11-02T11:12:05.580221+00:00"
  },
  "message": "Note created successfully"
}
```

**Obtener notas usando v2 (con paginación):**
```bash
curl -i "http://127.0.0.1:8000/api/v2/notes?page=1&per_page=5" \
  -H "Authorization: Bearer $TOKEN"
```

**Revisa las cabeceras - SIN advertencias de deprecación:**
```
API-Version: v2
```

**Cuerpo de respuesta (formato v2 - envuelto con metadatos):**
```json
{
  "data": [
    {
      "id": 1,
      "title": "Mi Primera Nota",
      "content": "Esto es v1",
      "tags": [],
      "owner": "alice",
      "created_at": null,
      "updated_at": null
    },
    {
      "id": 2,
      "title": "Mi Segunda Nota",
      "content": "Esto es v2",
      "tags": ["trabajo", "importante"],
      "owner": "alice",
      "created_at": "2026-11-02T11:12:05.580221+00:00",
      "updated_at": "2026-11-02T11:12:05.580221+00:00"
    }
  ],
  "count": 2,
  "page": 1,
  "per_page": 5,
  "version": "v2"
}
```

**Nota:** la nota 1 se creó con v1, que no guarda tags ni timestamps. v2 la devuelve igualmente con la forma de v2: `to_v2()` rellena `tags: []` y timestamps `null` (nunca supimos cuándo se creó), así que un cliente de v2 recibe siempre los mismos campos. Es el coste habitual de una versión nueva: los datos antiguos se adaptan al contrato nuevo, no al revés.

### Paso 5.5: Probar Características Exclusivas de v2

**Actualizar una nota (solo en v2):** `PATCH` cambia solo los campos que envías (como en el ejercicio 05: `PUT` reemplazaría la nota entera).
```bash
curl -X PATCH http://127.0.0.1:8000/api/v2/notes/2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"Nota Actualizada","tags":["trabajo","urgente"]}'
```

**Respuesta:**
```json
{
  "data": {
    "id": 2,
    "title": "Nota Actualizada",
    "content": "Esto es v2",
    "tags": ["trabajo", "urgente"],
    "owner": "alice",
    "created_at": "2026-11-02T11:12:05.580221+00:00",
    "updated_at": "2026-11-02T11:12:07.609752+00:00"
  },
  "message": "Note updated successfully"
}
```

¡Observa que `updated_at` cambió!

**Intentar actualizar con v1 (falla: la ruta no existe):**
```bash
curl -i -X PATCH http://127.0.0.1:8000/api/v1/notes/2 \
  -H "Content-Type: application/json" \
  -H "Authorization: Bearer $TOKEN" \
  -d '{"title":"Esto fallará"}'
```

**Respuesta** (`405`, y sin cabeceras de deprecación: nunca llegó al router):
```json
{"detail": "Method Not Allowed"}
```

**Los errores no llevan las cabeceras de deprecación.** Compara un acierto y un error de v1:
```bash
curl -i http://127.0.0.1:8000/api/v1/notes/1 -H "Authorization: Bearer $TOKEN"   # 200: Deprecation, Sunset, Link
curl -i http://127.0.0.1:8000/api/v1/notes/99 -H "Authorization: Bearer $TOKEN"  # 404: ninguna de ellas
```

### Paso 5.6: Verificar Información de Versión

```bash
curl http://127.0.0.1:8000/api/versions
```

**Respuesta:**
```json
{
  "versions": {
    "v1": {
      "status": "deprecated",
      "deprecation_date": "2026-01-01",
      "sunset_date": "2027-06-30",
      "successor": "/api/v2",
      "deprecation_notice": "API v1 is deprecated. Please migrate to v2."
    },
    "v2": {
      "status": "current",
      "deprecation_date": null,
      "sunset_date": null,
      "successor": null,
      "deprecation_notice": null
    }
  },
  "current": "v2",
  "deprecated": ["v1"]
}
```

## Parte 6: Comprendiendo Cambios Incompatibles (15 minutos)

### Comparar las Respuestas

**v1 GET /api/v1/notes:**
```json
[
  {"id": 1, "title": "Nota", "content": "...", "owner": "alice"}
]
```

**v2 GET /api/v2/notes:**
```json
{
  "data": [
    {
      "id": 1,
      "title": "Nota",
      "content": "...",
      "tags": [],
      "owner": "alice",
      "created_at": "...",
      "updated_at": "..."
    }
  ],
  "count": 1,
  "page": 1,
  "per_page": 10,
  "version": "v2"
}
```

**Por qué esto es INCOMPATIBLE:**

Si cambiaras v1 para devolver el formato v2, **todos los clientes** se romperían:

```javascript
// Código de cliente esperando v1
fetch('/api/v1/notes')
  .then(response => response.json())
  .then(notes => {
    notes.forEach(note => {  // Espera un array
      console.log(note.title);
    });
  });
```

Después de cambiar al formato v2, este código fallaría:
```
TypeError: notes.forEach is not a function
```

Porque `notes` ahora es un objeto `{data: [...]}`, ¡no un array!

**Solución:** Mantén v1 como está, crea v2 con el nuevo formato.

## Parte 7: Estrategia de Deprecación (10 minutos)

### La Línea de Tiempo de Deprecación

**Paso 1: Lanzar v2 (Hoy)**
- Anunciar disponibilidad de v2
- Fomentar la migración
- v1 aún completamente soportada

**Paso 2: Deprecar v1 (1-3 meses después)**
- Agregar cabeceras de deprecación a v1
- Establecer fecha de sunset (ej., 6 meses)
- Actualizar documentación
- Enviar email a clientes sobre deprecación

**Paso 3: Advertencia de Sunset (3 meses antes del sunset)**
- Aumentar urgencia en advertencias
- Ofrecer soporte de migración
- Identificar clientes que aún usan v1

**Paso 4: Eliminar v1 (Fecha de sunset)**
- Endpoints v1 devuelven 410 Gone
- Todos los clientes deben usar v2

### Comunicar la Deprecación

**En las cabeceras de respuesta (automático):**
```
Deprecation: @1767225600
Sunset: Wed, 30 Jun 2027 00:00:00 GMT
Link: </api/v2>; rel="successor-version"
```

**En la documentación:**
```markdown
## ⚠️ Aviso de Deprecación

La API v1 está deprecada y se retirará (sunset) el **30 de junio de 2027**.

Por favor, migra a v2. Consulta la guía de migración: [enlace]
```

**Por email:**
```
Asunto: Acción requerida: migra a la API v2

Estimado cliente,

La API v1 se retirará el 30 de junio de 2027. Por favor, migra a v2
antes de esa fecha para evitar interrupciones del servicio.

Guía de migración: [enlace]
¿Necesitas ayuda? Contacta con support@example.com
```

## Mejores Prácticas

### 1. Versionar desde el Inicio

¡No esperes! Comienza con `/api/v1` desde el día uno, incluso si no planeas cambios.

```python
# ✅ Bueno - versionado desde el inicio
v1 = APIRouter(prefix='/api/v1')

# ❌ Malo - difícil de versionar después
app = FastAPI()  # rutas en /api/users
```

### 2. Versionar el Namespace, No Endpoints Individuales

```python
# ✅ Bueno - namespace completo versionado
/api/v1/users
/api/v1/notes
/api/v1/tags

# ❌ Malo - versionado inconsistente
/api/users/v1
/api/v2/notes
```

### 3. No Versionar Autenticación

Los endpoints de autenticación usualmente son estables y no necesitan versionado:

```python
# ✅ Bueno - auth fuera del namespace de versión
/auth/register
/auth/login

# ❌ Malo - versionado innecesario
/api/v1/auth/login
/api/v2/auth/login
```

### 4. Soportar Múltiples Versiones, Pero No Para Siempre

**Recomendado:**
- Soportar 2-3 versiones máximo
- Período de deprecación de 6-12 meses
- Fechas de sunset claras

### 5. Documentar Cambios Incompatibles Claramente

```markdown
## Guía de Migración v2

### Cambios Incompatibles

1. **Formato de respuesta**: Todos los endpoints de lista ahora devuelven `{data: [...], count: N}`
   - **Antes (v1)**: `GET /api/v1/notes` → `[...]`
   - **Después (v2)**: `GET /api/v2/notes` → `{data: [...], count: 2}`
   - **Solución**: Actualizar código de cliente para leer `response.data` en lugar de `response`

### Cambios Compatibles

- **Endpoint de actualización**: nuevo `PATCH /api/v2/notes/{note_id}` (v1 no tenía endpoint de actualización; añadir un endpoint no rompe a nadie)
- **Timestamps**: todos los recursos incluyen ahora `created_at` y `updated_at`
  - **Impacto**: Ninguno (los campos adicionales son compatibles hacia atrás al leer)
- Nuevo campo opcional `tags` en las notas (se puede omitir)
- Parámetros de consulta de paginación `page` y `per_page` (opcionales). El valor por defecto `per_page=10` es la razón por la que la paginación salió junto con el envoltorio incompatible de v2 en lugar de añadirse a v1: un cliente v1 que nunca envía `page` recibiría en silencio solo las 10 primeras notas.
```

### 6. Usar Versionado Semántico (Opcional)

Para APIs complejas, considera el versionado semántico:

```
v1.0.0 → v1.1.0 (campo opcional añadido - compatible hacia atrás)
v1.1.0 → v1.2.0 (nuevo endpoint añadido - compatible hacia atrás)
v1.2.0 → v2.0.0 (formato de respuesta cambiado - INCOMPATIBLE)
```

### 7. Monitorear Uso de Versiones

Rastrea qué clientes usan qué versiones:

```python
from collections import Counter

version_usage = Counter()

@app.middleware('http')
async def track_version(request, call_next):
    response = await call_next(request)
    version = response.headers.get('API-Version')
    if version:
        version_usage[version] += 1
    return response

@app.get('/api/admin/version-stats')
def version_stats():
    return dict(version_usage)
```

## Errores Comunes

### Error 1: Versionar Demasiado Frecuentemente

❌ **Malo:**
```
v1 (Ene) → v2 (Feb) → v3 (Mar) → v4 (Abr)
```

¡Los clientes no pueden mantener el ritmo con cambios incompatibles constantes!

✅ **Bueno:**
```
v1 (Ene 2023) → v2 (Ene 2024)
```

Solo versiona cuando sea absolutamente necesario.

### Error 2: No Comunicar Cambios

❌ **Malo:**
- Cambiar formato de respuesta sin advertencia
- Sin cabeceras de deprecación
- Sin guía de migración

✅ **Bueno:**
- Anunciar lanzamiento de v2
- Agregar cabeceras de deprecación a v1
- Proporcionar guía de migración detallada
- Enviar email a clientes sobre cambios

### Error 3: Eliminar Versiones Antiguas Demasiado Rápido

❌ **Malo:**
```
1 Jun: Lanzar v2
15 Jun: Eliminar v1 (2 semanas después)
```

¡Los clientes necesitan tiempo para migrar!

✅ **Bueno:**
```
1 Jun: Lanzar v2
1 Sep: Deprecar v1 (3 meses para adaptarse)
1 Dic: Sunset v1 (6 meses total)
```

### Error 4: Tratar Cambios Compatibles como Incompatibles

❌ **Malo:**
```python
# v1
{"id": 1, "name": "Alice"}

# v2 creada innecesariamente solo para añadir un campo opcional
# v2
{"id": 1, "name": "Alice", "email": "alice@example.com"}
```

¡Esto es compatible hacia atrás! Simplemente añade el campo a v1.

✅ **Bueno:**
```python
# v1 (actualizada con el campo opcional)
{"id": 1, "name": "Alice", "email": "alice@example.com"}
```

### Error 5: Versionado Inconsistente

❌ **Malo:**
```
/api/v1/users (usa convenciones de v1)
/api/v2/notes (usa convenciones de v2)
/api/comments   (sin versión - ¿usa ??)
```

✅ **Bueno:**
```
/api/v1/users
/api/v1/notes
/api/v1/comments

/api/v2/users
/api/v2/notes
/api/v2/comments
```

Todos los recursos siguen la misma estrategia de versionado.

## Lista de Verificación de Pruebas

**Configuración:**
- [ ] Aplicación FastAPI instalada y ejecutándose (`fastapi dev app.py`)
- [ ] Puede registrarse e iniciar sesión exitosamente
- [ ] Token JWT obtenido

**Versión 1 (Deprecada):**
- [ ] Puede crear nota usando endpoint v1
- [ ] Puede obtener todas las notas usando v1 (devuelve array)
- [ ] Puede obtener nota única usando v1
- [ ] Respuesta incluye cabeceras de deprecación
- [ ] Respuesta incluye cabecera de fecha de sunset

**Versión 2 (Actual):**
- [ ] Puede crear nota usando endpoint v2 (con tags)
- [ ] Nota creada incluye timestamps (created_at, updated_at)
- [ ] Puede obtener todas las notas usando v2 (devuelve objeto envuelto)
- [ ] Respuesta v2 incluye metadatos de count y page
- [ ] Paginación funciona con parámetros page y per_page
- [ ] Puede obtener nota única usando v2 (envuelta en objeto data)
- [ ] Puede actualizar nota usando endpoint PATCH v2
- [ ] Respuesta incluye cabecera API-Version
- [ ] Respuesta NO incluye cabeceras de deprecación

**Información de Versión:**
- [ ] `/api/versions` devuelve información sobre todas las versiones
- [ ] Puede identificar versiones actuales y deprecadas

**Cambios Incompatibles:**
- [ ] v1 y v2 devuelven formatos de respuesta diferentes
- [ ] v1 devuelve array simple, v2 devuelve objeto envuelto
- [ ] v2 incluye campos no en v1 (timestamps, tags)
- [ ] Ambas versiones funcionan simultáneamente

## Ejemplos del Mundo Real

### API de Stripe

**Enfoque:** Versiones con fechas (no v1, v2, sino fechas)

```bash
# Especificar versión vía cabecera
curl https://api.stripe.com/v1/customers \
  -H "Stripe-Version: 2023-10-16"
```

**¿Por qué?** Permite a Stripe lanzar actualizaciones frecuentemente sin forzar migraciones.

### API de GitHub

**Enfoque:** Versiones con fecha elegidas con una cabecera (API REST)

```bash
# Fijar la petición a una versión con fecha de la API REST
curl https://api.github.com/users/octocat \
  -H "X-GitHub-Api-Version: 2022-11-28"
```

**¿Por qué?** Los cambios incompatibles se publican como una fecha nueva; una petición sin la cabecera recibe la versión soportada más antigua, así que los clientes existentes siguen funcionando hasta que deciden cambiar. Cada versión con fecha se mantiene al menos 24 meses después de publicarse la siguiente.

### API de Twitter

**Enfoque:** Cambios de versión mayor con deprecación larga

```bash
# v1.1 (deprecada 2023)
GET https://api.twitter.com/1.1/statuses/home_timeline.json

# v2 (actual)
GET https://api.twitter.com/2/tweets
```

**¿Por qué?** Rediseño completo de API. Dio a desarrolladores ~2 años para migrar.

### API de Twilio

**Enfoque:** Versionado por ruta URL

```bash
# v1 (retirada)
POST https://api.twilio.com/2008-08-01/Accounts/{AccountSid}/SMS/Messages

# v2 (actual)
POST https://api.twilio.com/2010-04-01/Accounts/{AccountSid}/Messages
```

**¿Por qué?** Versiones basadas en fechas, pero en la ruta URL. Las versiones antiguas acaban retirándose.

## Recursos Adicionales

### Documentación Oficial
- **[RFC 9745 - Deprecation HTTP Header](https://www.rfc-editor.org/rfc/rfc9745.html)** - La cabecera `Deprecation` (desde cuándo está deprecada una versión)
- **[RFC 8594 - Sunset HTTP Header](https://www.rfc-editor.org/rfc/rfc8594.html)** - La cabecera `Sunset` (cuándo deja de funcionar una versión)
- **[Versionado Semántico](https://semver.org/)** - Estrategia de numeración de versiones
- **[API Versioning Best Practices](https://www.troyhunt.com/your-api-versioning-is-wrong-which-is/)** - Artículo de Troy Hunt

### Tutoriales
- [Versionado de la API de Stripe](https://stripe.com/docs/api/versioning) - Ejemplo del mundo real
- [Versionado de la API de GitHub](https://docs.github.com/en/rest/overview/api-versions) - Versiones con fecha en una cabecera

## Entregables

Cuando completes este ejercicio, deberías tener:

1. **`app.py` Completado**:
   - Todos los TODOs completados correctamente
   - Cabeceras de versión implementadas
   - Endpoints v1 y v2 funcionando
   - Advertencias de deprecación en v1

2. **Evidencia de Pruebas**:
   - Capturas o logs mostrando v1 con cabeceras de deprecación
   - Capturas mostrando v2 sin deprecación
   - Ejemplos de diferentes formatos de respuesta

3. **Comprensión**:
   - Explicar cuándo crear una nueva versión
   - Identificar cambios compatibles vs incompatibles
   - Describir estrategia de deprecación
   - Comparar estructuras de respuesta v1 y v2

## Preguntas para Considerar

1. ¿Cuándo agregarías un nuevo campo que requiere una nueva versión?
2. ¿Por qué agregamos cabeceras de deprecación a v1 pero no a v2?
3. ¿Cómo manejarías un cliente que se niega a migrar desde v1?
4. ¿Cuál es la diferencia entre versionar `/api/v1/notes` vs `/api/notes?version=1`?
5. ¿Cuándo elegirías versionado basado en cabeceras sobre versionado por ruta URL?

¡Buena suerte gestionando tus versiones de API! 🚀
