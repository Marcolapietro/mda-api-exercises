# Ejercicio 6: Implementación de Paginación en Endpoints (API de Notas)

## Inicio Rápido

```bash
cd exercises/06-pagination
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
python app.py
```

La API arranca en `http://127.0.0.1:5000` con **95 notas de ejemplo** (ids del 1 al 95), para que haya algo que paginar.

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
   - Solo `Flask` (ver `requirements.txt`). `base64` viene con Python.

2. **Estructura de la API:**
   - `GET /notes`: lista paginada (ver las reglas más abajo).
   - `POST /notes`, `GET /notes/<id>`, `PUT /notes/<id>`, `PATCH /notes/<id>`, `DELETE /notes/<id>`: igual que en el ejercicio 05 (`POST` devuelve `201` + `Location`, `DELETE` devuelve `204`).

3. **Reglas de paginación de `GET /notes`:**
   - `limit`: por defecto `20`, máximo `100`. **Un valor mayor se recorta a `100`** (no es un error); `page.limit` te dice el valor que se ha usado de verdad. Un `limit` que no es entero o es `< 1` es un `400`.
   - **Modo offset** cuando envías `offset` (entero `>= 0`). El objeto `page` incluye `total`.
   - **Modo cursor** en otro caso: sin `cursor` obtienes la primera página; después envías el `next_cursor` que has recibido. El objeto `page` incluye `next_cursor`.
   - Enviar `offset` **y** `cursor` a la vez es un `400`. Un cursor inválido es un `400`.
   - Cuerpo de la respuesta: `{"data": [...], "page": {...}}`, donde `page.next` / `page.prev` son URLs completas (o `null`).
   - Cabecera `Link` (RFC 8288) con `rel="next"` y, cuando hay página anterior, `rel="prev"`.
   - En modo cursor la paginación solo avanza (como un feed infinito): `page.prev` siempre es `null`. Para volver atrás, el cliente reutiliza un cursor que ya tiene.

4. **Pruebas:**
   - Usa Postman o `curl` para pedir distintas páginas y tamaños de página, seguir los enlaces `next` y comprobar los errores.
   - Haz el experimento de inserción que hay más abajo.

## Pasos Detallados

1. **Lee `app.py`:** el CRUD y la función `problem()` son los del ejercicio 05. El código nuevo está en la sección *Pagination helpers* y en `GET /notes`.

2. **Tamaño de página por defecto y máximo (`parse_limit`):** devuelve `min(limit, MAX_LIMIT)`.

3. **Modo offset (`offset_page`):** corta la lista ordenada con `ordered[offset:offset + limit]` y calcula dónde empieza la página siguiente.

4. **Modo cursor (`cursor_page`):**
   - Rechaza con un `400` un cursor que no se puede decodificar.
   - Las notas van de la más nueva a la más antigua, así que las que vienen *después* del cursor son las de id **menor**.
   - Si quedan más notas, `next_cursor` apunta a la **última** nota de la página actual.

5. **Mezclar modos (`list_notes`):** `offset` + `cursor` a la vez es un `400`.

6. **Enlaces de navegación (`paged_response`):** completa los tipos de relación de la cabecera `Link`: `next` y `prev`.

## Ejemplo de Código

El cursor opaco es simplemente base64 (apto para URLs, sin el relleno `=`) del último id que ha visto el cliente. El cliente no debe construirlo ni preocuparse de qué lleva dentro: solo devuelve lo que ha recibido.

```python
def encode_cursor(note_id):
    return base64.urlsafe_b64encode(str(note_id).encode()).decode().rstrip('=')   # 91 -> "OTE"


def decode_cursor(cursor):
    try:
        padded = cursor + '=' * (-len(cursor) % 4)
        raw = base64.urlsafe_b64decode(padded).decode('ascii')
    except ValueError:  # base64 incorrecto o contenido no ASCII
        return None
    if not raw.isdigit():
        return None
    return int(raw)
```

La cabecera `Link` pone las mismas URLs `next`/`prev` del cuerpo en un sitio estándar (RFC 8288):

```
Link: <http://127.0.0.1:5000/notes?offset=60&limit=20>; rel="next", <http://127.0.0.1:5000/notes?offset=20&limit=20>; rel="prev"
```

## Pruebas con Postman o `curl`

> **Windows:** en PowerShell usa `curl.exe` (en Windows PowerShell 5.1 `curl` es un alias de `Invoke-WebRequest`) y deja la URL entre comillas dobles por el `&`. Además, PowerShell 5.1 elimina las comillas internas de `-d '{...}'`, así que para el `POST` usa los ficheros listos para ejecutar: `example/commands_cmd.txt` (CMD) y `example/commands_powershell.txt` (PowerShell, que además hace el experimento completo por ti).

1. **Offset: una página del medio (`200`):**

   ```bash
   curl -i "http://127.0.0.1:5000/notes?offset=40&limit=20"
   ```

   ```
   HTTP/1.1 200 OK
   Content-Type: application/json
   Link: <http://127.0.0.1:5000/notes?offset=60&limit=20>; rel="next", <http://127.0.0.1:5000/notes?offset=20&limit=20>; rel="prev"
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
       "next": "http://127.0.0.1:5000/notes?offset=60&limit=20",
       "prev": "http://127.0.0.1:5000/notes?offset=20&limit=20"
     }
   }
   ```

2. **Offset: primera y última página:** la primera tiene `"prev": null` y solo `rel="next"`; la última tiene `"next": null` y solo `rel="prev"`.

   ```bash
   curl -i "http://127.0.0.1:5000/notes?offset=0&limit=5"
   curl -i "http://127.0.0.1:5000/notes?offset=90&limit=5"
   ```

3. **Cursor: primera página (`200`):** sin `offset` y sin `cursor`.

   ```bash
   curl -i "http://127.0.0.1:5000/notes?limit=5"
   ```

   ```json
   {
     "data": ["... notas 95, 94, 93, 92, 91 ..."],
     "page": {
       "mode": "cursor",
       "limit": 5,
       "next_cursor": "OTE",
       "next": "http://127.0.0.1:5000/notes?cursor=OTE&limit=5",
       "prev": null
     }
   }
   ```

4. **Cursor: página siguiente:** devuelve el `next_cursor` (o simplemente sigue `page.next`). Obtienes las notas 90 a 86. En la última página `next_cursor` y `next` son `null`.

   ```bash
   curl -i "http://127.0.0.1:5000/notes?cursor=OTE&limit=5"
   ```

5. **Tamaño de página por defecto y máximo:** `GET /notes` devuelve 20 notas; `?limit=500` se recorta y `page.limit` vale `100`.

   ```bash
   curl -i "http://127.0.0.1:5000/notes"
   curl -i "http://127.0.0.1:5000/notes?limit=500"
   ```

6. **Errores (`400`, `application/problem+json`):**

   ```bash
   curl -i "http://127.0.0.1:5000/notes?offset=0&cursor=OTE"         # offset y cursor a la vez
   curl -i "http://127.0.0.1:5000/notes?cursor=not-a-real-cursor"   # cursor inválido
   curl -i "http://127.0.0.1:5000/notes?limit=0"                    # limit inválido
   curl -i "http://127.0.0.1:5000/notes?offset=-1"                  # offset inválido
   ```

   ```json
   {"type": "about:blank", "title": "Bad Request", "status": 400, "detail": "Use either offset or cursor, not both."}
   ```

7. **Crear una nota (`201` + `Location`)**, necesaria para el experimento:

   ```bash
   curl -i -X POST http://127.0.0.1:5000/notes -H "Content-Type: application/json" -d '{"title": "Inserted while paginating"}'
   ```

## Experimento: ¿Qué Pasa con Offset si Alguien Inserta un Registro Mientras Paginas?

Reinicia la aplicación (`python app.py`) para empezar desde las 95 notas de ejemplo.

**A. Offset**

1. Lee la página 1: `curl "http://127.0.0.1:5000/notes?offset=0&limit=5"` → notas **95, 94, 93, 92, 91**.
2. Alguien inserta una nota: ejecuta el `POST` del paso 7 → recibe el id **96** y se coloca la primera (las más nuevas van primero).
3. Lee la página 2: `curl "http://127.0.0.1:5000/notes?offset=5&limit=5"` → notas **91, 90, 89, 88, 87**.

La nota **91 sale dos veces**. El offset cuenta posiciones, y la nota nueva ha empujado todo una posición hacia abajo. Es el diagrama de la diapositiva con otros números: allí un elemento nuevo 21 hace que el elemento 16 aparezca dos veces. (Si se *elimina* una nota entre las dos peticiones pasa lo contrario: una nota se *salta* y no la ves nunca. Pruébalo con `DELETE /notes/95`.)

**B. Cursor**

1. Lee la página 1: `curl "http://127.0.0.1:5000/notes?limit=5"` y copia `page.next_cursor` (recién arrancada la app es `OTE`, base64 de 91; si has hecho antes la parte A, la primera página empieza en 96 y el cursor es `OTI`).
2. Inserta otra nota con el `POST` del paso 7.
3. Lee la página 2 con **tu** cursor: `curl "http://127.0.0.1:5000/notes?cursor=OTE&limit=5"` (cambia `OTE` por el valor que has copiado) → continúa justo después de la última nota que viste (90, 89, 88, 87, 86 recién arrancada la app).

**Ni duplicados ni saltos**: el cursor no dice "sáltate 5 posiciones", dice "después del id 91", y eso no cambia aunque lleguen notas nuevas (el "after id 16" de la diapositiva).

## Puntos a Considerar

- Ten siempre un tamaño de página por defecto y uno máximo; documenta si un valor mayor se recorta (como aquí) o se rechaza con un `400`.
- Offset va bien para datos pequeños o estáticos y para interfaces de "ir a la página 7"; para feeds y datos que cambian, mejor cursores.
- Mantén el cursor opaco: los clientes no deben construirlo ni decodificarlo, así puedes cambiar lo que lleva dentro sin romperles nada.
- La paginación necesita un orden estable. Aquí es `id` descendente; con offset además pagas contar el `total` y saltar filas en cada petición.
- Los datos están en memoria: al reiniciar la aplicación vuelven las 95 notas de ejemplo.
- El modo debug está desactivado por defecto. Para activarlo: `FLASK_DEBUG=1 python app.py` (PowerShell: `$env:FLASK_DEBUG="1"; python app.py`).

¡Buena suerte con la implementación! Si tienes dudas, no dudes en consultar.
