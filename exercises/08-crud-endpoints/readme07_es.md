# Ejercicio 8: Creación de Endpoints CRUD (API de Notas)

## Objetivo
Implementar un CRUD completo (Crear, Leer, Actualizar, Eliminar) para un recurso, `/notes`, en una API REST con Python y Flask, usando los códigos de estado, las cabeceras y el formato de error correctos.

## Descripción
En el ejercicio 03 construiste `GET /notes` y `POST /notes`. Aquí completas la API de notas: leer una nota, sustituirla (`PUT`), modificar parte de ella (`PATCH`) y eliminarla (`DELETE`). En este ejercicio **no hay autenticación** (se ve más adelante en el curso): el foco está en los métodos HTTP, los códigos de estado, las cabeceras y la validación. Completa los espacios en blanco (`_____`) de `app.py`.

## Inicio Rápido

```bash
cd exercises/08-crud-endpoints
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

La API arranca en `http://127.0.0.1:5000` con 3 notas de ejemplo (ids 1, 2 y 3), así que `GET /notes` no sale vacío.

## Requisitos
1. **Dependencias:**
   - Solo `Flask` (ver `requirements.txt`).

2. **Estructura de la API:**

   | Método | URI | Qué hace | Éxito |
   |--------|-----|----------|-------|
   | `GET` | `/notes?limit=10` | Lista las notas, de la más nueva a la más antigua | `200` |
   | `POST` | `/notes` | Crea una nota | `201` + cabecera `Location` |
   | `GET` | `/notes/<id>` | Devuelve una nota | `200` (`404` si no existe) |
   | `PUT` | `/notes/<id>` | Sustituye la nota completa | `200` |
   | `PATCH` | `/notes/<id>` | Modifica solo los campos enviados | `200` |
   | `DELETE` | `/notes/<id>` | Elimina la nota | `204`, sin cuerpo |

   - Sustantivos en plural y sin verbos en las URIs: el **método** dice qué pasa (`DELETE /notes/1`, no `/deleteNote?id=1`).
   - Una nota tiene este aspecto. `id`, `created_at` y `updated_at` los pone el servidor (ISO 8601, UTC):

     ```json
     {"id": 1, "title": "Welcome", "content": "This is your Notes API.", "created_at": "2026-10-26T09:30:00Z", "updated_at": "2026-10-26T09:30:00Z"}
     ```

   - `GET /notes` acepta `?limit=` (por defecto `20`, máximo `100`; los valores mayores se recortan a `100`). La paginación completa (offset y cursor) es el ejercicio 09.

3. **Implementación del CRUD:**
   - `title` es obligatorio y debe ser un texto no vacío. `content` debe ser un texto (opcional en `POST`, donde vale `""` por defecto).
   - `PUT` envía el recurso **completo**: `title` y `content` son obligatorios.
   - `PATCH` envía solo lo que cambia: al menos uno de `title` / `content`.
   - Todos los errores usan el mismo formato, los *problem details* de la RFC 9457 (ver más abajo).

4. **Pruebas:**
   - Usa Postman o `curl` para probar cada operación, incluidos los casos de error.

## Pasos Sugeridos

1. **Lee `app.py`:**
   - La función `problem()` construye todas las respuestas de error (ya la viste en el ejercicio 03).
   - `read_json_object()` comprueba el `Content-Type` y lee el cuerpo; `validate_note()` devuelve la lista de errores por campo.
   - `GET /notes` y `GET /notes/<id>` ya están implementados. Fíjate en que la misma URL `/notes/<id>` hace cosas distintas según el método.

2. **Completa los espacios en blanco (`_____`) en `exercises/08-crud-endpoints/app.py`:**

   ```python
   # Códigos de error: 422 (JSON válido, datos inválidos), 415 (no es JSON), 400 (JSON mal formado)
   return problem(_____, 'Unprocessable Content', ...)

   # POST: "creado" + dónde vive la nota nueva
   return jsonify(note), _____, {'Location': _____}

   # PUT vs PATCH: el método y qué campos son obligatorios
   @app.route('/notes/<int:note_id>', methods=['_____'])  # TODO: Set the HTTP method that REPLACES a resource
   errors = validate_note(data, required=_____)

   # DELETE: éxito, sin nada que devolver
   return '', _____
   ```

   Los comentarios junto a cada hueco te dan una pista. La solución completa está en `example/example08.py` (¡inténtalo antes!).

3. **Ejecuta la aplicación:**

   ```bash
   python app.py
   ```

4. **Prueba la API:**

   Usa Postman o `curl`. `-i` muestra la línea de estado y las cabeceras.

   > **Windows:** en PowerShell usa `curl.exe` (en Windows PowerShell 5.1 `curl` es un alias de `Invoke-WebRequest`). Incluso con `curl.exe`, PowerShell 5.1 elimina las comillas internas de `-d '{...}'` y el JSON llega roto. Usa mejor los ficheros listos para ejecutar: `example/commands_cmd.txt` (CMD) y `example/commands_powershell.txt` (PowerShell, con `Invoke-WebRequest`).

   - **Listar notas (`200`):**
     ```bash
     curl -i "http://127.0.0.1:5000/notes?limit=10"
     ```
     ```json
     {
       "data": [
         {"id": 3, "title": "API Management", "content": "Status codes, Location header and RFC 9457 errors", "created_at": "...", "updated_at": "..."},
         {"id": 2, "title": "Shopping list", "content": "Milk, eggs, coffee", "created_at": "...", "updated_at": "..."},
         {"id": 1, "title": "Welcome", "content": "This is your Notes API.", "created_at": "...", "updated_at": "..."}
       ],
       "page": {"limit": 10, "total": 3}
     }
     ```

   - **Crear una nota (`201` + `Location`):**
     ```bash
     curl -i -X POST http://127.0.0.1:5000/notes -H "Content-Type: application/json" -d '{"title": "My first note", "content": "Hello"}'
     ```
     ```
     HTTP/1.1 201 CREATED
     Content-Type: application/json
     Location: http://127.0.0.1:5000/notes/4

     {"id": 4, "title": "My first note", "content": "Hello", "created_at": "2026-10-26T09:30:00Z", "updated_at": "2026-10-26T09:30:00Z"}
     ```

   - **Obtener una nota (`200`, o `404` si no existe):**
     ```bash
     curl -i http://127.0.0.1:5000/notes/4
     curl -i http://127.0.0.1:5000/notes/999
     ```

   - **Sustituir con PUT (`200`):** se envían todos los campos.
     ```bash
     curl -i -X PUT http://127.0.0.1:5000/notes/4 -H "Content-Type: application/json" -d '{"title": "Replaced title", "content": "Replaced content"}'
     ```

   - **PUT con un campo que falta (`422`):** PUT sustituye la nota entera, así que `content` es obligatorio.
     ```bash
     curl -i -X PUT http://127.0.0.1:5000/notes/4 -H "Content-Type: application/json" -d '{"title": "Only the title"}'
     ```

   - **Actualización parcial con PATCH (`200`):** solo cambia `content`, el título se queda igual.
     ```bash
     curl -i -X PATCH http://127.0.0.1:5000/notes/4 -H "Content-Type: application/json" -d '{"content": "Only the content changed"}'
     ```

   - **Eliminar (`204`, cuerpo vacío) y volver a pedirla (`404`):**
     ```bash
     curl -i -X DELETE http://127.0.0.1:5000/notes/4
     curl -i http://127.0.0.1:5000/notes/4
     ```

   - **Content-Type incorrecto (`415`):**
     ```bash
     curl -i -X POST http://127.0.0.1:5000/notes -d 'title=bad'
     ```

   - **JSON mal formado (`400`):**
     ```bash
     curl -i -X POST http://127.0.0.1:5000/notes -H "Content-Type: application/json" -d '{"title": '
     ```

   - **JSON válido con datos inválidos (`422`):** título vacío y `content` es un número.
     ```bash
     curl -i -X POST http://127.0.0.1:5000/notes -H "Content-Type: application/json" -d '{"title": "", "content": 42}'
     ```
     ```
     HTTP/1.1 422 UNPROCESSABLE ENTITY
     Content-Type: application/problem+json

     {
       "type": "about:blank",
       "title": "Unprocessable Content",
       "status": 422,
       "detail": "The note has invalid or missing fields.",
       "errors": [
         {"pointer": "#/title", "detail": "title must be a non-empty string"},
         {"pointer": "#/content", "detail": "content must be a string"}
       ]
     }
     ```

   - **Método no permitido (`405`, con cabecera `Allow`):**
     ```bash
     curl -i -X DELETE http://127.0.0.1:5000/notes
     ```

   - **`limit` inválido (`400`):**
     ```bash
     curl -i "http://127.0.0.1:5000/notes?limit=0"
     ```

## Resultados Esperados

- La API permite crear, leer, sustituir, actualizar parcialmente y eliminar notas.
- `POST` devuelve `201` con cabecera `Location`; `DELETE` devuelve `204` sin cuerpo.
- `PUT` sin todos los campos devuelve `422`; `PATCH` con un solo campo cambia solo ese campo.
- Todos los errores son `application/problem+json` con `type`, `title`, `status` y `detail`.

## Entendiendo los Códigos de Estado HTTP

- **200 OK**: la petición ha ido bien (`GET`, `PUT`, `PATCH`)
- **201 Created**: se ha creado un recurso (`POST`). La cabecera `Location` dice dónde está.
- **204 No Content**: éxito sin cuerpo (`DELETE`)
- **400 Bad Request**: la petición en sí está rota: JSON mal formado, `?limit=abc`
- **404 Not Found**: el recurso no existe
- **405 Method Not Allowed**: la URL existe, pero no con ese método (la cabecera `Allow` lista los válidos)
- **415 Unsupported Media Type**: el cuerpo no es `application/json`
- **422 Unprocessable Content**: JSON válido, pero con datos inválidos: campos que faltan, tipos incorrectos, título vacío
- **409 Conflict**: no se usa aquí (dos notas pueden tener el mismo título). Lo usarías para un conflicto real, por ejemplo un valor duplicado en un campo que debe ser único.
- **500 Internal Server Error**: error en el servidor

### 400 vs 422

`{"title": ` ni siquiera se puede leer: **400**. `{"title": ""}` es JSON perfectamente válido, pero los datos no cumplen las reglas: **422**. Un cuerpo JSON que no es un objeto (`[1, 2]`) también es **422**.

### Métodos HTTP y su Propósito

- **POST**: crear un recurso nuevo
- **GET**: obtener uno o varios recursos
- **PUT**: sustituir el recurso **completo** (se envían todos los campos)
- **PATCH**: cambiar **algunos** campos (se envía solo lo que cambia)
- **DELETE**: eliminar un recurso

### Errores: Problem Details (RFC 9457)

Todos los errores tienen la misma forma y el `Content-Type: application/problem+json`. Los construye una única función, `problem(status, title, detail, **extra)`, que se usa en todas partes, también en los manejadores de `404`/`405`. Los errores de validación añaden la extensión `errors`, con una entrada por campo (`pointer` es un JSON Pointer al campo):

```json
{"type": "about:blank", "title": "Not Found", "status": 404, "detail": "Note 999 does not exist."}
```

## Recursos Adicionales

- [Documentación de Flask](https://flask.palletsprojects.com/)
- [RFC 9457: Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457)
- [RFC 9110: HTTP Semantics (métodos y códigos de estado)](https://www.rfc-editor.org/rfc/rfc9110)
- [Códigos de estado HTTP](https://developer.mozilla.org/es/docs/Web/HTTP/Status)

## Notas

- Este ejercicio usa almacenamiento en memoria, así que todos los datos (y tus notas nuevas) se pierden al reiniciar la aplicación.
- El modo debug está desactivado por defecto. Para activarlo: `FLASK_DEBUG=1 python app.py` (PowerShell: `$env:FLASK_DEBUG="1"; python app.py`).
- El código tiene espacios en blanco (`_____`) para completar: céntrate en entender **por qué** cada código de estado y cada cabecera es el correcto.
