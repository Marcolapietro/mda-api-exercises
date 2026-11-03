# Ejercicio 4: Fundamentos de APIs (API de Notas)

## Introducción

Este ejercicio presenta los fundamentos de las APIs HTTP + JSON con una pequeña API de notas construida con FastAPI. Va justo después del 03 (introducción a FastAPI) y antes del 05 (CRUD), y se centra en un diseño limpio de peticiones y respuestas y en la validación básica, todavía sin autenticación. La misma API de notas se convierte en un CRUD completo en el ejercicio 05 y añade paginación en el ejercicio 06.

## Objetivos de Aprendizaje

1. Modelar recursos con sustantivos en plural (`/notes`, `/notes/{id}`), sin verbos en las URIs
2. Usar correctamente los métodos HTTP (GET/POST) y devolver los códigos de estado adecuados (`201` + `Location` al crear)
3. Dejar que FastAPI valide la petición con modelos de Pydantic y entender el `422` con el que responde
4. Devolver todos los errores en un único formato estándar: los problem details de la RFC 9457
5. Practicar las pruebas con Postman y curl

## Endpoints

- `GET /health`
  - Devuelve `{"status": "ok"}` para comprobar que el servicio está en marcha
  - Respuesta: `200` con `{ "status": "ok" }`

- `GET /notes`
  - Devuelve una lista de notas (en memoria)
  - Respuesta: `200` con la lista `[ { id, title, content } ]`

- `POST /notes`
  - Crea una nota nueva
  - Cuerpo (JSON): `{ "title": str, "content": str }`; `title` debe tener al menos un carácter, `content` es opcional y vale `""` por defecto
  - Respuesta: `201` con la nota creada y una cabecera `Location` que apunta a ella (por ejemplo `Location: http://127.0.0.1:8000/notes/1`)
  - Errores: `422` para cualquier cosa que FastAPI no pueda aceptar como una nota válida (ver más abajo)

- `GET /notes/{id}`
  - Devuelve una nota por su id
  - Respuesta: `200` si todo va bien, `404` si no existe

## Requisitos

- Usa un almacenamiento en memoria (un dict de Python), sin base de datos
- Describe los datos con modelos de Pydantic: `NoteCreate` (lo que envía el cliente) y `Note` (lo que devuelve la API)
- Todos los errores son *problem details* de la RFC 9457, con `Content-Type: application/problem+json`, y los construye una única función, `problem(request, status, title, detail, **extra)`. `instance` es la ruta de la petición que ha fallado:

  ```json
  {"type": "about:blank", "title": "Not Found", "status": 404, "detail": "Note 99 does not exist.", "instance": "/notes/99"}
  ```

  Los errores de validación (`422`) añaden la extensión `errors`, con la lista que produce Pydantic, una entrada por problema (`loc` indica dónde está el problema):

  ```json
  {
    "type": "about:blank",
    "title": "Unprocessable Content",
    "status": 422,
    "detail": "Request body or parameters are invalid.",
    "instance": "/notes",
    "errors": [
      {"type": "missing", "loc": ["body", "title"], "msg": "Field required", "input": {"content": "Hello"}}
    ]
  }
  ```

- Dos manejadores de excepciones producen estas respuestas: uno para `HTTPException` (tus `404`, y también el `404` y el `405` que lanza el propio router) y otro para `RequestValidationError` (los `422`)

## Cómo responde FastAPI a una entrada inválida

En HTTP, `400` significa "no he podido entender la petición" y `415` significa "no acepto este media type". Aquí no escribimos esas comprobaciones a mano. FastAPI valida la *forma* y el *contenido* de la petición a la vez, antes de que se ejecute tu función, y responde `422 Unprocessable Content` con el detalle de lo que está mal. Eso cubre un `Content-Type` que no es JSON, JSON mal formado, un campo que falta, un campo de tipo incorrecto y un `title` vacío. Tu código solo declara el modelo; si la función se ejecuta, los datos son válidos. `400` y `415` siguen existiendo en HTTP, simplemente aquí no los fabricamos.

## Ficheros de Partida

- `app.py` – Fichero de partida con TODOs y huecos (`_____`) para que los completes
- `example/example04.py` – Solución de referencia completa (para después de intentarlo)
- `requirements.txt` – Dependencias mínimas

## Primeros Pasos

```bash
# (Opcional) Crea y activa un entorno virtual
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate

# Instala las dependencias
pip install -r requirements.txt

# Ejecuta la app (completa los huecos de arriba abajo; la app arranca cuando están completos los decoradores y el `status_code=` de `POST /notes`)
fastapi dev app.py
```

Abre el navegador: http://127.0.0.1:8000/health, y http://127.0.0.1:8000/docs para la documentación automática.

## Modelos de respuesta y códigos de estado

Como en el 03, la anotación del tipo de retorno hace el trabajo: `-> Note` le dice a FastAPI la forma de la respuesta. Filtra la salida a los campos de `Note`, la valida y la documenta en `/docs`; `-> list[Note]` hace lo mismo con una lista. (Si una función devuelve algo que no es el tipo que quieres documentar, pasa `response_model=` al decorador.)

Un `GET` correcto responde `200` por defecto. Para otros casos pones el código en el decorador: `@app.post("/notes", status_code=201)`. Escribimos el número, como en las diapositivas; `fastapi.status` tiene constantes con nombre para los mismos códigos (`status.HTTP_201_CREATED`) si las prefieres.

Para añadir una cabecera a la respuesta, declara un parámetro de tipo `Response`; FastAPI te da la respuesta que está a punto de enviar, y tú pones `response.headers["Name"] = value`. Para construir la URL de otra ruta a partir del nombre de su función, usa `request.url_for("get_note", note_id=1)`.

## Tareas (completa los huecos de app.py)

1. Problem details
   - Pon el media type de la función `problem()`: `application/problem+json`
   - Responde `422` en el manejador de validación
2. Rutas y métodos
   - Elige el decorador (`get` o `post`) de cada ruta
3. Creación de recursos
   - Responde `201` con la nota creada y la cabecera `Location`
4. No encontrado
   - Responde `404` cuando la nota no existe

## Pruebas (curl)

```bash
# Health
curl -i http://127.0.0.1:8000/health

# Crear nota (éxito) -> 201 + Location: http://127.0.0.1:8000/notes/1
curl -i -X POST http://127.0.0.1:8000/notes \
  -H "Content-Type: application/json" \
  -d '{"title": "First note", "content": "Hello world"}'

# Crear nota (JSON mal formado) -> 422 problem+json
curl -i -X POST http://127.0.0.1:8000/notes -H "Content-Type: application/json" -d '{"title": '

# Crear nota (sin title) -> 422 problem+json con una lista "errors"
curl -i -X POST http://127.0.0.1:8000/notes -H "Content-Type: application/json" -d '{"content": "No title"}'

# Listar notas -> 200
curl -i http://127.0.0.1:8000/notes

# Obtener una nota por id -> 200, o 404 si no existe
curl -i http://127.0.0.1:8000/notes/1
curl -i http://127.0.0.1:8000/notes/99

# Método no permitido -> 405
curl -i -X DELETE http://127.0.0.1:8000/notes
```

Nota: la cabecera `Allow` está incompleta aquí (solo `GET`) porque FastAPI registra `GET /notes` y `POST /notes` como dos rutas separadas.

> **Windows:** en PowerShell usa `curl.exe` (en PowerShell 5.1 `curl` es un alias de `Invoke-WebRequest`). Windows PowerShell 5.1 además elimina las comillas internas de `-d '{...}'` y el JSON llega roto: ejecuta los ejemplos con JSON desde CMD, o usa `Invoke-RestMethod -Method Post -Uri http://127.0.0.1:8000/notes -ContentType "application/json" -Body (@{title="First note"; content="Hello world"} | ConvertTo-Json)`. En CMD las comillas simples no funcionan: usa comillas dobles y escapa las internas, por ejemplo `-d "{\"title\": \"First note\", \"content\": \"Hello world\"}"`.

## Criterios de Aceptación

- Códigos de estado correctos (`200`, `201`, `404`, `405`, `422`)
- `POST /notes` devuelve `201` con la nota creada y una cabecera `Location`
- Todos los errores son `application/problem+json` con `type`, `title`, `status`, `detail` e `instance`
- Una entrada inválida (JSON mal formado, `title` que falta o está vacío, un cuerpo que no es JSON) devuelve `422`, nunca `500`
- Sin autenticación

## Retos Adicionales

- Añade `PUT`, `PATCH` y `DELETE` (eso es justo el ejercicio 05)
- Añade marcas de tiempo `created_at`/`updated_at`
- Añade paginación (`?offset`/`limit` o un cursor) como en el ejercicio 06
- Añade un CORS sencillo para probar desde el navegador

¡Suerte construyendo una API limpia y bien estructurada!
