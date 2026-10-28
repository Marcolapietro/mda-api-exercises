# Ejercicio 15: Versionado de APIs

## Inicio Rápido

```bash
cd exercises/15-versioning
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

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
- **GitHub API**: v3 → v4 (REST → GraphQL)
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
- `DELETE /api/v1/notes/<id>` (nuevo)

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
@app.route('/api/v1/notes', methods=['GET'])
def get_notes_v1():
    return jsonify([...])  # Array simple

@app.route('/api/v2/notes', methods=['GET'])
def get_notes_v2():
    return jsonify({'data': [...], 'count': 10})  # Objeto envuelto
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

**Usado por:** API de GitHub, API de Azure

### 3. Versionado por Parámetro de Consulta

**Formato:** `/api/notes?version=2`

**Pros:**
- ✅ Fácil de probar

**Cons:**
- ❌ No es RESTful
- ❌ Puede olvidarse/omitirse

**Usado por:** Algunas APIs internas, raramente en APIs públicas

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
      "created_at": "2024-01-01T10:00:00Z",
      "updated_at": "2024-01-01T10:00:00Z"
    }
  ],
  "count": 1,
  "page": 1,
  "per_page": 10
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

### Tarea 2.1: Completar la Función `add_version_headers`

Abre `app.py` y encuentra la función `add_version_headers`:

```python
def add_version_headers(response, version):
    """Agregar cabeceras relacionadas con versión a la respuesta"""

    # TODO: Agregar cabecera API-Version con la versión actual
    response.headers['API-Version'] = _____

    if API_VERSIONS[version]['status'] == 'deprecated':
        # TODO: Agregar cabecera Deprecation (RFC 9745): "@" + cuándo se deprecó, como timestamp Unix
        response.headers['Deprecation'] = _____

        # TODO: Agregar cabecera Sunset (RFC 8594): cuándo dejará de funcionar, como fecha HTTP
        response.headers['Sunset'] = _____

        # TODO: Agregar cabecera Link apuntando a la versión que sustituye a esta
        response.headers['Link'] = _____

    return response
```

Las funciones `to_epoch()` y `to_http_date()` (definidas justo después de `API_VERSIONS`) convierten las fechas guardadas como `'2026-01-01'` al formato que necesitan las cabeceras.

**Tus tareas:**
1. Completa la cabecera `API-Version` con el parámetro version
2. Agrega la cabecera `Deprecation`: `@` seguido de `to_epoch(...)` de la fecha de deprecación
3. Agrega la cabecera `Sunset`: `to_http_date(...)` de la fecha de sunset de `API_VERSIONS`
4. Agrega la cabecera `Link` apuntando a la versión sucesora

**Solución:**
```python
response.headers['API-Version'] = version
response.headers['Deprecation'] = f"@{to_epoch(API_VERSIONS[version]['deprecation_date'])}"
response.headers['Sunset'] = to_http_date(API_VERSIONS[version]['sunset_date'])
response.headers['Link'] = f'<{API_VERSIONS[version]["successor"]}>; rel="successor-version"'
```

## Parte 3: Implementando Versión 1 (20 minutos)

La versión 1 es la API original y simple que muchos clientes ya están usando.

### Tarea 3.1: Completar `get_notes_v1`

```python
@app.route('/api/v1/notes', methods=['GET'])
@jwt_required()
def get_notes_v1():
    """Versión 1: Obtener todas las notas - Devuelve una lista simple"""
    current_user = get_jwt_identity()
    user_notes = [note for note in notes.values() if note['owner'] == current_user]

    # TODO: Crear respuesta con jsonify y user_notes
    response = make_response(jsonify(_____))

    # TODO: Agregar cabeceras de versión a la respuesta
    response = add_version_headers(response, _____)

    return response
```

**Tus tareas:**
1. Crear respuesta con la lista `user_notes`
2. Agregar cabeceras de versión para 'v1'

## Parte 4: Implementando Versión 2 (30 minutos)

La versión 2 introduce cambios incompatibles con funcionalidad mejorada.

### Tarea 4.1: Completar `get_notes_v2` con Paginación

```python
@app.route('/api/v2/notes', methods=['GET'])
@jwt_required()
def get_notes_v2():
    """Versión 2: Obtener todas las notas con paginación"""
    current_user = get_jwt_identity()
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 10, type=int)

    user_notes = [note for note in notes.values() if note['owner'] == current_user]

    # TODO: Calcular paginación
    start = _____
    end = start + per_page
    paginated_notes = user_notes[start:end]

    # TODO: Crear estructura de respuesta v2
    response_data = {
        'data': _____,
        'count': _____,
        'page': _____,
        'per_page': _____
    }

    response = make_response(jsonify(response_data))
    response = add_version_headers(response, 'v2')

    return response
```

**Tus tareas:**
1. Calcular el índice de inicio para paginación: `(page - 1) * per_page`
2. Completar la estructura de respuesta con datos paginados

### Tarea 4.2: Completar `create_note_v2` con Timestamps

```python
@app.route('/api/v2/notes', methods=['POST'])
@jwt_required()
def create_note_v2():
    """Versión 2: Crear nota con timestamps y tags"""
    global note_id_counter
    current_user = get_jwt_identity()
    data = request.get_json()

    if not data or 'title' not in data:
        return jsonify({'error': 'Missing title'}), 400

    # TODO: Crear nota con campos v2
    note = {
        'id': note_id_counter,
        'title': data['title'],
        'content': data.get('content', ''),
        'tags': data.get('tags', []),
        'owner': current_user,
        'created_at': _____,  # TODO: Agregar timestamp
        'updated_at': _____   # TODO: Agregar timestamp
    }

    notes[note_id_counter] = note
    note_id_counter += 1

    # TODO: Envolver respuesta en objeto 'data' para v2
    response_data = _____

    response = make_response(jsonify(response_data), 201)
    response = add_version_headers(response, 'v2')

    return response
```

**Tus tareas:**
1. Agregar timestamp `created_at` usando `datetime.utcnow().isoformat()`
2. Agregar timestamp `updated_at`
3. Envolver la respuesta: `{'data': note, 'message': 'Note created successfully'}`

## Parte 5: Probando las Versiones (40 minutos)

### Paso 5.1: Iniciar la Aplicación

```bash
cd exercises/15-versioning
python app.py
```

Deberías ver listados los endpoints de v1 y v2.

### Paso 5.2: Registrarse e Iniciar Sesión

```bash
# Registrar un usuario
curl -X POST http://127.0.0.1:5000/auth/register \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'

# Iniciar sesión para obtener token JWT
curl -X POST http://127.0.0.1:5000/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"alice","password":"password123"}'
```

Guarda el `access_token` de la respuesta.

### Paso 5.3: Probar Versión 1 (Deprecada)

**Crear notas usando v1:**
```bash
TOKEN="tu_token_de_acceso_aqui"

curl -X POST http://127.0.0.1:5000/api/v1/notes \
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
curl -i http://127.0.0.1:5000/api/v1/notes \
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

curl -X POST http://127.0.0.1:5000/api/v2/notes \
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
    "created_at": "2024-01-01T10:30:00.123456",
    "updated_at": "2024-01-01T10:30:00.123456"
  },
  "message": "Note created successfully"
}
```

**Obtener notas usando v2 (con paginación):**
```bash
curl -i "http://127.0.0.1:5000/api/v2/notes?page=1&per_page=5" \
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
      "owner": "alice"
    },
    {
      "id": 2,
      "title": "Mi Segunda Nota",
      "content": "Esto es v2",
      "tags": ["trabajo", "importante"],
      "owner": "alice",
      "created_at": "2024-01-01T10:30:00.123456",
      "updated_at": "2024-01-01T10:30:00.123456"
    }
  ],
  "count": 2,
  "page": 1,
  "per_page": 5
}
```

### Paso 5.5: Probar Características Exclusivas de v2

**Actualizar una nota (solo en v2):**
```bash
curl -X PUT http://127.0.0.1:5000/api/v2/notes/2 \
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
    "created_at": "2024-01-01T10:30:00.123456",
    "updated_at": "2024-01-01T10:35:00.789012"
  },
  "message": "Note updated successfully"
}
```

¡Observa que `updated_at` cambió!

### Paso 5.6: Verificar Información de Versión

```bash
curl http://127.0.0.1:5000/api/versions
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
      "deprecation_notice": "API v1 está deprecada. Por favor migra a v2."
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
  "per_page": 10
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

## Mejores Prácticas

### 1. Versionar desde el Inicio

¡No esperes! Comienza con `/api/v1` desde el día uno, incluso si no planeas cambios.

```python
# ✅ Bueno - versionado desde el inicio
@app.route('/api/v1/users')

# ❌ Malo - difícil de versionar después
@app.route('/api/users')
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
```

### 6. Monitorear Uso de Versiones

Rastrea qué clientes usan qué versiones:

```python
from collections import Counter

version_usage = Counter()

@app.after_request
def track_version(response):
    version = response.headers.get('API-Version')
    if version:
        version_usage[version] += 1
    return response
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

## Lista de Verificación de Pruebas

**Configuración:**
- [ ] Aplicación Flask instalada y ejecutándose
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
- [ ] Puede actualizar nota usando endpoint PUT v2
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

**Enfoque:** Cambios de versión mayor (v3 REST → v4 GraphQL)

```bash
# v3 (REST)
GET https://api.github.com/users/octocat

# v4 (GraphQL)
POST https://api.github.com/graphql
```

**¿Por qué?** GraphQL es fundamentalmente diferente de REST, requiriendo un cambio de versión mayor.

### API de Twitter

**Enfoque:** Cambios de versión mayor con deprecación larga

```bash
# v1.1 (deprecada 2023)
GET https://api.twitter.com/1.1/statuses/home_timeline.json

# v2 (actual)
GET https://api.twitter.com/2/tweets
```

**¿Por qué?** Rediseño completo de API. Dio a desarrolladores ~2 años para migrar.

## Recursos Adicionales

### Documentación Oficial
- **[RFC 8594 - Sunset HTTP Header](https://www.rfc-editor.org/rfc/rfc8594.html)** - Estándar para deprecación
- **[Versionado Semántico](https://semver.org/)** - Estrategia de numeración de versiones

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
