# Ejercicio 6: Implementación de Paginación en Endpoints (API de Notas)

## Inicio Rápido

```bash
cd exercises/06-pagination
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Rellena los espacios de arriba abajo; la app arranca cuando el decorador GET y los `ge=` y `le=` del limit están completos
fastapi dev app.py
```

La API arranca en `http://127.0.0.1:8000` (documentación automática en `/docs`) con **95 notas de ejemplo** (ids del 1 al 95), para que haya algo que paginar.

Mientras el decorador `GET` esté en blanco verás un `AttributeError` que apunta a `@app._____`. Cuando lo arregles, un `ge=`/`le=` sin completar aparece como `SchemaError ... 'le' must be coercible to an integer`: también apunta a ese decorador, porque FastAPI lee las reglas de `Query(...)` al registrar la ruta. Los demás espacios están dentro de funciones, así que solo fallan cuando una petición llega hasta ellos (un `500` o una respuesta incorrecta).

## Objetivo

- **Implementar Paginación en Endpoints:** dividir una colección grande en páginas en lugar de devolverlo todo de golpe.
- **Comparar dos estrategias:** offset/limit y cursor, y ver con tus propios ojos por qué los cursores son más estables.
- **Manejo de Parámetros de Consulta:** tamaño de página por defecto y máximo, validación y enlaces `next`/`prev` (en el cuerpo y en la cabecera `Link`).

## Descripción

Este ejercicio parte de la API de notas del ejercicio 05 (mismo recurso `/notes`, mismo CRUD, mismos errores RFC 9457, **sin autenticación**). Ahora `GET /notes` devuelve las notas **de la más nueva a la más antigua** (por `id`, descendente) y admite dos modos de paginación:

| Modo | Petición | Ventajas / inconvenientes |
|------|----------|---------------------------|
| Offset/limit | `GET /notes?offset=40&limit=20` | Sencillo, puedes saltar a cualquier página y conoces el `total`. Inconsistente si los datos cambian mientras paginas. |
| Cursor | `GET /notes?cursor=<opaco>&limit=20` | Estable: continúa "después de la última nota que viste". El cursor es un token opaco (aquí: base64 del último id). |

Completa los espacios en blanco (`_____`) de `app.py`.

## Requisitos

1. **Dependencias:**
   - Solo `fastapi[standard]` (ver `requirements.txt`). `base64` viene con Python.

2. **Estructura de la API:**
   - `GET /notes`: lista paginada (ver las reglas más abajo).
   - `POST /notes`, `GET /notes/{id}`, `PUT /notes/{id}`, `PATCH /notes/{id}`, `DELETE /notes/{id}`: igual que en el ejercicio 05 (`POST` devuelve `201` + `Location`, `DELETE` devuelve `204`).

3. **Reglas de paginación de `GET /notes`:**
   - `limit`: por defecto `20`, entre `1` y `100`. **Un valor mayor se rechaza con `422`** (no se recorta a `100`), y lo mismo ocurre con un `limit` que no es entero o es `< 1`. `page.limit` te dice el valor que se ha usado.
   - **Modo offset** cuando envías `offset` (entero `>= 0`; cualquier otra cosa es un `422`). El objeto `page` incluye `total`.
   - **Modo cursor** en otro caso: sin `cursor` obtienes la primera página; después envías el `next_cursor` que has recibido. El objeto `page` incluye `next_cursor`.
   - Los dos únicos `400` tienen que ver con cómo se usan los modos: enviar `offset` **y** `cursor` a la vez, y enviar un cursor que no es nuestro.
   - Cuerpo de la respuesta: `{"data": [...], "page": {...}}`, donde `page.next` / `page.prev` son URLs completas (o `null`).
   - Cabecera `Link` (RFC 8288) con `rel="next"` y, cuando hay página anterior, `rel="prev"`.
   - En modo cursor la paginación solo avanza (como un feed infinito): `page.prev` siempre es `null`. Para volver atrás, el cliente reutiliza un cursor que ya tiene.

4. **Pruebas:**
   - Usa Postman o `curl` para pedir distintas páginas y tamaños de página, seguir los enlaces `next` y comprobar los errores.
   - Haz el experimento de inserción que hay más abajo.

## Pasos Detallados

1. **Lee `app.py`:** el CRUD, la función `problem()` y los dos manejadores de excepciones son los del ejercicio 05. El código nuevo está en la sección *Pagination helpers* y en `GET /notes`. Cada tipo de página tiene su propio modelo, `OffsetPage` y `CursorPage`, porque sus campos son distintos (`total` en uno, `next_cursor` en el otro).

2. **Parámetros de consulta (`list_notes`):** el decorador `GET` y las reglas de `limit`: como mínimo `1` (`ge=`) y como máximo `100` (`le=`). En la sección siguiente se explica cómo funciona `Query`.

3. **Modo offset (`offset_page`):** corta la lista ordenada con `ordered[offset:offset + limit]`.

4. **Modo cursor (`cursor_page`, `encode_cursor`):**
   - `encode_cursor` necesita la función de `base64` adecuada (apta para URLs).
   - `decode_cursor` ya responde con un `400` si el cursor no se puede decodificar.
   - Las notas van de la más nueva a la más antigua, así que las que vienen *después* del cursor son las de id **menor**.
   - Si quedan más notas, `next_cursor` apunta a la **última** nota de la página actual. Pon nombre a ese campo en `CursorPage`.

5. **Mezclar modos (`list_notes`):** `offset` + `cursor` a la vez es un `400`.

6. **Enlaces de navegación (`link_header`):** completa los tipos de relación de la cabecera `Link`: `next` y `prev`.

## `Query`: declarar y validar la cadena de consulta

En el ejercicio 05 viste `limit: Annotated[int, Query(ge=1, le=100)] = 20`. Aquí tienes el cuadro completo. Cada parámetro de la función que **no** forma parte de la ruta (`/notes/{note_id}`) y no es un modelo de Pydantic (el cuerpo) se lee de la cadena de consulta, y su nombre es el nombre en la URL: `limit` es `?limit=`. Lo que escribes alrededor decide las reglas:

- **El tipo** convierte y valida: `limit: int` acepta `"20"` y lo convierte en `20`; `?limit=abc` se rechaza.
- **El valor por defecto** hace opcional el parámetro: `= 20` significa "20 si el cliente no envía nada". `offset: Annotated[int | None, Query(ge=0)] = None` es opcional y sin valor; dentro de la función, `offset is not None` te dice si el cliente lo envió. Así distingue el mismo endpoint el modo offset del modo cursor.
- **`Query(...)` añade reglas:** `ge` (mayor o igual), `gt`, `le` (menor o igual), `lt`, `min_length`, `max_length`... Van dentro de `Annotated[tipo, Query(...)]` y además quedan escritas en `/docs`. `cursor: Annotated[str | None, Query()] = None` no tiene reglas extra; `Query()` está ahí para dejar explícito que viene de la cadena de consulta.
- **La comprobación se hace antes de tu función.** Si el valor no es un entero o incumple una regla, FastAPI responde `422` (aquí como `application/problem+json`, con la lista en `errors`) y tu código ni se ejecuta. Por eso `?limit=500`, `?limit=abc` y `?offset=-1` son todos `422`.

Lo que FastAPI no puede saber es una regla que involucra **dos** parámetros o el **contenido** de uno: "`offset` y `cursor` a la vez" y "este cursor no es válido" los comprueba tu código, y responden `400` con `raise HTTPException(status_code=400, detail=...)`.

## Ejemplo de Código

El cursor opaco es simplemente base64 (apto para URLs, sin el relleno `=`) del último id que ha visto el cliente. El cliente no debe construirlo ni preocuparse de qué lleva dentro: solo devuelve lo que ha recibido.

```python
def encode_cursor(note_id: int) -> str:
    return base64.urlsafe_b64encode(str(note_id).encode()).decode().rstrip("=")  # 91 -> "OTE"


def decode_cursor(cursor: str) -> int:
    try:
        padded = cursor + "=" * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(padded).decode("ascii")
    except ValueError:  # base64 incorrecto o contenido no ASCII
        raw = ""
    if not raw.isdigit():
        raise HTTPException(status_code=400, detail="The cursor is not valid. Use the next_cursor value from a previous response.")
    return int(raw)
```

La cabecera `Link` pone las mismas URLs `next`/`prev` del cuerpo en un sitio estándar (RFC 8288):

```
Link: <http://127.0.0.1:8000/notes?offset=60&limit=20>; rel="next", <http://127.0.0.1:8000/notes?offset=20&limit=20>; rel="prev"
```

## Pruebas con Postman o `curl`

> **Windows:** en PowerShell usa `curl.exe` (en Windows PowerShell 5.1 `curl` es un alias de `Invoke-WebRequest`) y deja la URL entre comillas dobles por el `&`. Además, PowerShell 5.1 elimina las comillas internas de `-d '{...}'`, así que para el `POST` usa los ficheros listos para ejecutar: `example/commands_cmd.txt` (CMD) y `example/commands_powershell.txt` (PowerShell, que además hace el experimento completo por ti).

1. **Offset: una página del medio (`200`):**

   ```bash
   curl -i "http://127.0.0.1:8000/notes?offset=40&limit=20"
   ```

   ```
   HTTP/1.1 200 OK
   content-type: application/json
   link: <http://127.0.0.1:8000/notes?offset=60&limit=20>; rel="next", <http://127.0.0.1:8000/notes?offset=20&limit=20>; rel="prev"
   ```

   ```json
   {
     "data": [
       {"id": 55, "title": "Note 55", "content": "Seed note number 55", "created_at": "2026-01-01T00:55:00Z", "updated_at": "2026-01-01T00:55:00Z"},
       "... 18 notas más ...",
       {"id": 36, "title": "Note 36", "content": "Seed note number 36", "created_at": "2026-01-01T00:36:00Z", "updated_at": "2026-01-01T00:36:00Z"}
     ],
     "page": {
       "mode": "offset",
       "offset": 40,
       "limit": 20,
       "total": 95,
       "next": "http://127.0.0.1:8000/notes?offset=60&limit=20",
       "prev": "http://127.0.0.1:8000/notes?offset=20&limit=20"
     }
   }
   ```

2. **Offset: primera y última página:** la primera tiene `"prev": null` y solo `rel="next"`; la última tiene `"next": null` y solo `rel="prev"`.

   ```bash
   curl -i "http://127.0.0.1:8000/notes?offset=0&limit=5"
   curl -i "http://127.0.0.1:8000/notes?offset=90&limit=5"
   ```

3. **Cursor: primera página (`200`):** sin `offset` y sin `cursor`.

   ```bash
   curl -i "http://127.0.0.1:8000/notes?limit=5"
   ```

   ```json
   {
     "data": ["... notas 95, 94, 93, 92, 91 ..."],
     "page": {
       "mode": "cursor",
       "limit": 5,
       "next_cursor": "OTE",
       "next": "http://127.0.0.1:8000/notes?cursor=OTE&limit=5",
       "prev": null
     }
   }
   ```

4. **Cursor: página siguiente:** devuelve el `next_cursor` (o simplemente sigue `page.next`). Obtienes las notas 90 a 86. En la última página `next_cursor` y `next` son `null`.

   ```bash
   curl -i "http://127.0.0.1:8000/notes?cursor=OTE&limit=5"
   ```

5. **Tamaño de página por defecto y máximo:** `GET /notes` devuelve 20 notas (`page.limit` vale `20`); `?limit=500` se rechaza, no se recorta.

   ```bash
   curl -i "http://127.0.0.1:8000/notes"
   curl -i "http://127.0.0.1:8000/notes?limit=500"
   ```

6. **`limit` u `offset` inválidos (`422`, `application/problem+json`):** FastAPI los rechaza antes de que se ejecute tu código.

   ```bash
   curl -i "http://127.0.0.1:8000/notes?limit=0"      # menor que 1
   curl -i "http://127.0.0.1:8000/notes?limit=abc"    # no es un entero
   curl -i "http://127.0.0.1:8000/notes?offset=-1"    # menor que 0
   ```

   ```json
   {
     "type": "about:blank",
     "title": "Unprocessable Content",
     "status": 422,
     "detail": "Request body or parameters are invalid.",
     "instance": "/notes",
     "errors": [
       {"type": "greater_than_equal", "loc": ["query", "limit"], "msg": "Input should be greater than or equal to 1", "input": "0", "ctx": {"ge": 1}}
     ]
   }
   ```

7. **Errores de cursor (`400`, `application/problem+json`):** los comprueba tu código.

   ```bash
   curl -i "http://127.0.0.1:8000/notes?offset=0&cursor=OTE"         # offset y cursor a la vez
   curl -i "http://127.0.0.1:8000/notes?cursor=not-a-real-cursor"   # cursor inválido
   ```

   ```json
   {"type": "about:blank", "title": "Bad Request", "status": 400, "detail": "Use either offset or cursor, not both.", "instance": "/notes"}
   ```

8. **Crear una nota (`201` + `Location`)**, necesaria para el experimento:

   ```bash
   curl -i -X POST http://127.0.0.1:8000/notes -H "Content-Type: application/json" -d '{"title": "Inserted while paginating"}'
   ```

## Experimento: ¿Qué Pasa con Offset si Alguien Inserta un Registro Mientras Paginas?

Reinicia la aplicación (párala con `Ctrl+C` y vuelve a ejecutar `fastapi dev app.py`) para empezar desde las 95 notas de ejemplo.

**A. Offset**

1. Lee la página 1: `curl "http://127.0.0.1:8000/notes?offset=0&limit=5"` → notas **95, 94, 93, 92, 91**.
2. Alguien inserta una nota: ejecuta el `POST` del paso 8 → recibe el id **96** y se coloca la primera (las más nuevas van primero).
3. Lee la página 2: `curl "http://127.0.0.1:8000/notes?offset=5&limit=5"` → notas **91, 90, 89, 88, 87**.

La nota **91 sale dos veces**. El offset cuenta posiciones, y la nota nueva ha empujado todo una posición hacia abajo. Es el diagrama de la diapositiva con otros números: allí un elemento nuevo 21 hace que el elemento 16 aparezca dos veces. (Si se *elimina* una nota entre las dos peticiones pasa lo contrario: una nota se *salta* y no la ves nunca. Pruébalo con `DELETE /notes/95`.)

**B. Cursor**

1. Lee la página 1: `curl "http://127.0.0.1:8000/notes?limit=5"` y copia `page.next_cursor` (recién arrancada la app es `OTE`, base64 de 91; si has hecho antes la parte A, la primera página empieza en 96 y el cursor es `OTI`).
2. Inserta otra nota con el `POST` del paso 8.
3. Lee la página 2 con **tu** cursor: `curl "http://127.0.0.1:8000/notes?cursor=OTE&limit=5"` (cambia `OTE` por el valor que has copiado) → continúa justo después de la última nota que viste (90, 89, 88, 87, 86 recién arrancada la app).

**Ni duplicados ni saltos**: el cursor no dice "sáltate 5 posiciones", dice "después del id 91", y eso no cambia aunque lleguen notas nuevas (el "after id 16" de la diapositiva).

## Puntos a Considerar

- Ten siempre un tamaño de página por defecto y uno máximo; documenta si un valor mayor se recorta al máximo o se rechaza (como aquí, con un `422`).
- Offset va bien para datos pequeños o estáticos y para interfaces de "ir a la página 7"; para feeds y datos que cambian, mejor cursores.
- Mantén el cursor opaco: los clientes no deben construirlo ni decodificarlo, así puedes cambiar lo que lleva dentro sin romperles nada.
- La paginación necesita un orden estable. Aquí es `id` descendente; con offset además pagas contar el `total` y saltar filas en cada petición.
- Los datos están en memoria: al reiniciar la aplicación vuelven las 95 notas de ejemplo. `fastapi dev` también recarga la aplicación cuando guardas `app.py`, lo que también reinicia los datos.

¡Buena suerte con la implementación! Si tienes dudas, no dudes en consultar.
