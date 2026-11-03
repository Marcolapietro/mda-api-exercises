# Ejercicio 5: Creación de Endpoints CRUD (API de Notas)

## Objetivo
Implementar un CRUD completo (Crear, Leer, Actualizar, Eliminar) para un recurso, `/notes`, en una API REST con Python y FastAPI, usando los códigos de estado, las cabeceras y el formato de error correctos.

## Descripción
En el ejercicio 04 construiste `GET /notes` y `POST /notes`. Aquí completas la API de notas: sustituir una nota (`PUT`), modificar parte de ella (`PATCH`) y eliminarla (`DELETE`). En este ejercicio **no hay autenticación** (se ve más adelante en el curso): el foco está en los métodos HTTP, los códigos de estado, las cabeceras y la validación. Completa los espacios en blanco (`_____`) de `app.py`.

## Inicio Rápido

```bash
cd exercises/05-crud-endpoints
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Completa los huecos de arriba abajo; la app arranca cuando están completos los decoradores de PUT, PATCH y DELETE (con el `status_code=` de DELETE) y el `le=` del límite
fastapi dev app.py
```

La API arranca en `http://127.0.0.1:8000` (documentación automática en `/docs`) con 3 notas de ejemplo (ids 1, 2 y 3), así que `GET /notes` no sale vacío.

## Requisitos
1. **Dependencias:**
   - Solo `fastapi[standard]` (ver `requirements.txt`).

2. **Estructura de la API:**

   | Método | URI | Qué hace | Éxito |
   |--------|-----|----------|-------|
   | `GET` | `/notes?limit=10` | Lista las notas, de la más nueva a la más antigua | `200` |
   | `POST` | `/notes` | Crea una nota | `201` + cabecera `Location` |
   | `GET` | `/notes/{id}` | Devuelve una nota | `200` (`404` si no existe) |
   | `PUT` | `/notes/{id}` | Sustituye la nota completa | `200` |
   | `PATCH` | `/notes/{id}` | Modifica solo los campos enviados | `200` |
   | `DELETE` | `/notes/{id}` | Elimina la nota | `204`, sin cuerpo |

   - Sustantivos en plural y sin verbos en las URIs: el **método** dice qué pasa (`DELETE /notes/1`, no `/deleteNote?id=1`).
   - Una nota tiene este aspecto. `id`, `created_at` y `updated_at` los pone el servidor (ISO 8601, UTC):

     ```json
     {"id": 1, "title": "Welcome", "content": "This is your Notes API.", "created_at": "2026-10-26T09:30:00Z", "updated_at": "2026-10-26T09:30:00Z"}
     ```

   - `GET /notes` acepta `?limit=` (por defecto `20`, entre `1` y `100`). Un `limit` mayor que `100` se rechaza con `422`, no se recorta. La paginación completa (offset y cursor) es el ejercicio 06.

3. **Implementación del CRUD:**
   - Tres modelos de Pydantic describen los datos: `NoteCreate` (cuerpo de `POST` y `PUT`), `NoteUpdate` (cuerpo de `PATCH`) y `Note` (lo que devuelve la API).
   - `title` es obligatorio en `NoteCreate` y debe tener al menos un carácter. `content` es un texto (opcional, vale `""` por defecto).
   - `PUT` envía el recurso **completo**, así que usa `NoteCreate`: si falta `title`, es un `422`.
   - `PATCH` envía solo lo que cambia. En `NoteUpdate` todos los campos son opcionales, y `model_dump(exclude_unset=True)` te da únicamente los campos que envió el cliente. Un cuerpo vacío (`{}`) no cambia nada y es un `422`.
   - Todos los errores usan el mismo formato, los *problem details* de la RFC 9457 (ver más abajo).

4. **Pruebas:**
   - Usa Postman o `curl` para probar cada operación, incluidos los casos de error.

## Pasos Sugeridos

1. **Lee `app.py`:**
   - Parte del mismo código del ejercicio 04: los modelos, la función `problem()` y los dos manejadores de excepciones.
   - `get_or_404()` devuelve una nota o lanza el `404`; las rutas de una nota la comparten.
   - `GET /notes/{id}` ya está implementado, y a `POST /notes` solo le falta el nombre de la cabecera que indica dónde vive la nueva nota. Fíjate en que la misma URL `/notes/{id}` hace cosas distintas según el método.

2. **Completa los espacios en blanco (`_____`) en `exercises/05-crud-endpoints/app.py`:**

   ```python
   # Problem details y manejador de validación: el media type y el código de estado
   return JSONResponse(body, status_code=status, media_type="_____")
   return problem(request, _____, "Unprocessable Content", ...)

   # POST: la cabecera que dice dónde vive la nota nueva
   response.headers["_____"] = str(request.url_for("get_note", note_id=note.id))

   # PUT vs PATCH vs DELETE: el decorador se llama como el método HTTP
   @app._____("/notes/{note_id}")  # ¿qué método SUSTITUYE un recurso?

   # PATCH: solo los campos que envió el cliente
   changes = data.model_dump(_____=True, exclude_none=True)

   # DELETE: éxito, sin nada que devolver (en el decorador y en la Response)
   @app._____("/notes/{note_id}", status_code=_____)
   return Response(status_code=_____)

   # GET /notes: el tamaño de página máximo
   limit: Annotated[int, Query(ge=1, le=_____)] = 20
   ```

   Los comentarios junto a cada hueco te dan una pista. La solución completa está en `example/example05.py` (¡inténtalo antes!).

3. **Ejecuta la aplicación:**

   ```bash
   fastapi dev app.py
   ```

4. **Prueba la API:**

   Usa Postman, `curl` o la página `/docs`. `-i` muestra la línea de estado y las cabeceras.

   > **Windows:** en PowerShell usa `curl.exe` (en Windows PowerShell 5.1 `curl` es un alias de `Invoke-WebRequest`). Incluso con `curl.exe`, PowerShell 5.1 elimina las comillas internas de `-d '{...}'` y el JSON llega roto. Usa mejor los ficheros listos para ejecutar: `example/commands_cmd.txt` (CMD) y `example/commands_powershell.txt` (PowerShell, con `Invoke-WebRequest`).

   - **Listar notas (`200`):**
     ```bash
     curl -i "http://127.0.0.1:8000/notes?limit=10"
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

   - **`limit` fuera de rango (`422`):** los valores mayores que `100` (o menores que `1`, o que no son un número) se rechazan, no se recortan.
     ```bash
     curl -i "http://127.0.0.1:8000/notes?limit=500"
     ```

   - **Crear una nota (`201` + `Location`):**
     ```bash
     curl -i -X POST http://127.0.0.1:8000/notes -H "Content-Type: application/json" -d '{"title": "My first note", "content": "Hello"}'
     ```
     ```
     HTTP/1.1 201 Created
     content-type: application/json
     location: http://127.0.0.1:8000/notes/4

     {"id": 4, "title": "My first note", "content": "Hello", "created_at": "2026-10-26T09:30:00Z", "updated_at": "2026-10-26T09:30:00Z"}
     ```

   - **Obtener una nota (`200`, o `404` si no existe):**
     ```bash
     curl -i http://127.0.0.1:8000/notes/4
     curl -i http://127.0.0.1:8000/notes/999
     ```

   - **Sustituir con PUT (`200`):** se envían todos los campos.
     ```bash
     curl -i -X PUT http://127.0.0.1:8000/notes/4 -H "Content-Type: application/json" -d '{"title": "Replaced title", "content": "Replaced content"}'
     ```

   - **PUT con un campo que falta (`422`):** PUT sustituye la nota entera, así que `title` es obligatorio.
     ```bash
     curl -i -X PUT http://127.0.0.1:8000/notes/4 -H "Content-Type: application/json" -d '{"content": "No title"}'
     ```

   - **Actualización parcial con PATCH (`200`):** solo cambia `content`, el título se queda igual.
     ```bash
     curl -i -X PATCH http://127.0.0.1:8000/notes/4 -H "Content-Type: application/json" -d '{"content": "Only the content changed"}'
     ```

   - **Eliminar (`204`, cuerpo vacío) y volver a pedirla (`404`):**
     ```bash
     curl -i -X DELETE http://127.0.0.1:8000/notes/4
     curl -i http://127.0.0.1:8000/notes/4
     ```

   - **Content-Type incorrecto (`422`):**
     ```bash
     curl -i -X POST http://127.0.0.1:8000/notes -d 'title=bad'
     ```

   - **JSON mal formado (`422`):**
     ```bash
     curl -i -X POST http://127.0.0.1:8000/notes -H "Content-Type: application/json" -d '{"title": '
     ```

   - **JSON válido con datos inválidos (`422`):** título vacío y `content` es un número.
     ```bash
     curl -i -X POST http://127.0.0.1:8000/notes -H "Content-Type: application/json" -d '{"title": "", "content": 42}'
     ```
     ```
     HTTP/1.1 422 Unprocessable Content
     content-type: application/problem+json

     {
       "type": "about:blank",
       "title": "Unprocessable Content",
       "status": 422,
       "detail": "Request body or parameters are invalid.",
       "instance": "/notes",
       "errors": [
         {"type": "string_too_short", "loc": ["body", "title"], "msg": "String should have at least 1 character", ...},
         {"type": "string_type", "loc": ["body", "content"], "msg": "Input should be a valid string", ...}
       ]
     }
     ```

   - **Método no permitido (`405`):**
     ```bash
     curl -i -X DELETE http://127.0.0.1:8000/notes
     ```
     Nota: la cabecera `Allow` está incompleta aquí (solo `POST`) porque FastAPI registra `POST /notes` y `GET /notes` como dos rutas separadas.

## Modelos de respuesta, `Response` y `Query`

El ejercicio 04 presentó `-> Note` y `status_code=201`. Aquí aparecen dos piezas más.

**`204 No Content` significa que no hay cuerpo.** Sin `status_code=204`, una función que devuelve `None` responde `200` con el texto JSON `null` como cuerpo. Con `status_code=204` en el decorador FastAPI quita ese cuerpo, pero sigue enviando un `content-type: application/json` engañoso. Por eso `DELETE` devuelve explícitamente una respuesta vacía: `return Response(status_code=204)` (y el decorador dice `status_code=204`, para que `/docs` lo documente).

**`Query` valida la query string.** `limit: Annotated[int, Query(ge=1, le=100)] = 20` se lee así: un entero, mayor o igual que 1, menor o igual que 100, y `20` si el cliente no envía nada. Si el valor no es un entero o está fuera de rango, FastAPI responde `422` antes de que se ejecute tu función. El ejercicio 06 profundiza en `Query`.

## Resultados Esperados

- La API permite crear, leer, sustituir, actualizar parcialmente y eliminar notas.
- `POST` devuelve `201` con cabecera `Location`; `DELETE` devuelve `204` sin cuerpo.
- `PUT` sin `title` devuelve `422`; `PATCH` con un solo campo cambia solo ese campo.
- `?limit=500` devuelve `422`, no se recorta a `100`.
- Todos los errores son `application/problem+json` con `type`, `title`, `status`, `detail` e `instance`.

## Entendiendo los Códigos de Estado HTTP

- **200 OK**: la petición ha ido bien (`GET`, `PUT`, `PATCH`)
- **201 Created**: se ha creado un recurso (`POST`). La cabecera `Location` dice dónde está.
- **204 No Content**: éxito sin cuerpo (`DELETE`)
- **404 Not Found**: el recurso no existe
- **405 Method Not Allowed**: la URL existe, pero no con ese método
- **422 Unprocessable Content**: FastAPI no pudo aceptar la petición: un cuerpo que no es JSON, JSON mal formado, campos que faltan, tipos incorrectos, título vacío, un `limit` que no es un número o está fuera de rango
- **409 Conflict**: no se usa aquí (dos notas pueden tener el mismo título). Lo usarías para un conflicto real, por ejemplo un valor duplicado en un campo que debe ser único.
- **500 Internal Server Error**: error en el servidor

`400` y `415` siguen existiendo en HTTP, pero, como en el ejercicio 04, no escribimos esas comprobaciones a mano: FastAPI valida la forma y el contenido de la petición a la vez y responde `422` con los detalles.

### Métodos HTTP y su Propósito

- **POST**: crear un recurso nuevo
- **GET**: obtener uno o varios recursos
- **PUT**: sustituir el recurso **completo** (se envían todos los campos)
- **PATCH**: cambiar **algunos** campos (se envía solo lo que cambia)
- **DELETE**: eliminar un recurso

### Errores: Problem Details (RFC 9457)

Todos los errores tienen la misma forma y el `Content-Type: application/problem+json`. Los construye una única función, `problem(request, status, title, detail, **extra)`, que usan los dos manejadores de excepciones (el de `HTTPException` cubre tus `404` y también el `404` y el `405` que lanza el propio router). Los errores de validación añaden la extensión `errors`, con la lista que produce Pydantic; `loc` indica dónde está el problema:

```json
{"type": "about:blank", "title": "Not Found", "status": 404, "detail": "Note 999 does not exist.", "instance": "/notes/999"}
```

## Recursos Adicionales

- [Documentación de FastAPI](https://fastapi.tiangolo.com/es/)
- [RFC 9457: Problem Details for HTTP APIs](https://www.rfc-editor.org/rfc/rfc9457)
- [RFC 9110: HTTP Semantics (métodos y códigos de estado)](https://www.rfc-editor.org/rfc/rfc9110)
- [Códigos de estado HTTP](https://developer.mozilla.org/es/docs/Web/HTTP/Status)

## Notas

- Este ejercicio usa almacenamiento en memoria, así que todos los datos (y tus notas nuevas) se pierden al reiniciar la aplicación. `fastapi dev` también recarga la app cuando guardas `app.py`, y eso reinicia los datos.
- El código tiene espacios en blanco (`_____`) para completar: céntrate en entender **por qué** cada código de estado y cada cabecera es el correcto.
