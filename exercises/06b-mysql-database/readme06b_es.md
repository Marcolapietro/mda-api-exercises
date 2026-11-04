# Ejercicio 6b: Una API sobre una base de datos MySQL (API de Biblioteca)

## Objetivo
Construir una API REST sobre una **base de datos MySQL real** que ya existe: conectarte a ella, convertir cada petición HTTP en SQL y convertir los errores de la base de datos en los errores HTTP correctos.

## Descripción
Hasta el ejercicio 06 las notas vivían en un diccionario de Python y se perdían en cada reinicio. En los proyectos reales los datos viven en una base de datos, y muchas veces **la base de datos ya existe** cuando llegas: alguien diseñó las tablas hace años y tu trabajo es poner una API delante.

Eso es este ejercicio. Recibes una base de datos MySQL (en Docker) con una biblioteca: **22 autores y 150 libros**. La API de biblioteca ya tiene casi todo el código; tú completas los huecos (`_____`) de `app.py`. Todo lo que aprendiste en 04-06 sigue valiendo (CRUD, `201` + `Location`, `204`, errores RFC 9457, paginación por offset). Lo nuevo es de dónde salen los datos:

| En 04-06 (diccionario) | Aquí (MySQL) |
|---|---|
| `notes[note_id]` | `SELECT ... WHERE id = %s` |
| `next_id += 1` | MySQL genera el id (`AUTO_INCREMENT`) y lo lees con `cur.lastrowid` |
| `notes[id] = note` | `INSERT` / `UPDATE` + `conn.commit()` |
| `del notes[id]` | `DELETE` (`cur.rowcount` dice si la fila existía) |
| `sorted(...)[offset:offset + limit]` | `ORDER BY id LIMIT %s OFFSET %s` |
| Compruebas los duplicados a mano (o no los compruebas) | MySQL los rechaza (`UNIQUE`, claves foráneas) y tú respondes `409` |
| Los datos se pierden al reiniciar | Los datos se quedan |

En este ejercicio **no hay autenticación** ni **ORM**: escribes el SQL, así que ves exactamente qué le pide cada endpoint a la base de datos.

## Inicio Rápido

Necesitas **Docker Desktop** (o Rancher Desktop) arrancado y Python 3.12 o superior.

```bash
cd exercises/06b-mysql-database

# 1. La base de datos: copia la configuración y arranca MySQL
#    (la primera vez Docker descarga las imágenes, unos cientos de MB: ejecuta `docker compose pull` antes de clase)
cp .env.example .env            # Windows CMD: copy .env.example .env
docker compose up -d --wait

# 2. La API
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
# Completa los huecos de arriba abajo; la app arranca cuando están completos los decoradores de PATCH y DELETE (con el `status_code=` de DELETE) y el `le=` del límite
fastapi dev app.py
```

La API arranca en `http://127.0.0.1:8000` (documentación automática en `/docs`).

`docker compose up -d --wait` arranca dos contenedores: **MySQL** en el puerto `3306` y **Adminer** en `http://127.0.0.1:8080`, una página web para ver las tablas. Entra en Adminer con Sistema `MySQL`, Servidor `mysql`, Usuario `library`, Contraseña `library-pass`, Base de datos `library`. Tenlo abierto mientras pruebas: después de cada petición, mira qué ha cambiado en la tabla.

Mientras quede un hueco en un decorador, `fastapi dev` se para con un `AttributeError` que señala `@app._____`. Cuando lo arreglas, el `status_code=_____` de DELETE da un `NameError`, y un `le=_____` sin completar también impide el arranque: el error termina en `'le' must be coercible to an integer` (en Python 3.13 o anterior, un `NameError` que señala la línea de `limit`), porque FastAPI lee las reglas de `Query(...)` al registrar la ruta. Los demás huecos están dentro de funciones o de cadenas SQL, así que solo fallan cuando les llega una petición (un `500` o una respuesta incorrecta).

## La base de datos

`db/init.sql` crea las dos tablas y carga los datos. Docker lo ejecuta **solo la primera vez**, cuando el volumen de datos está vacío.

```
authors                          books
---------------------------      --------------------------------------------
id          INT PK AUTO_INC      id          INT PK AUTO_INC
name        VARCHAR UNIQUE       title       VARCHAR NOT NULL
country     VARCHAR              isbn        CHAR(13) UNIQUE
birth_year  SMALLINT             year        SMALLINT
                                 author_id   INT  -> authors.id (clave foránea)
                                 created_at  TIMESTAMP (lo pone MySQL)
                                 updated_at  TIMESTAMP (lo pone MySQL en cada UPDATE)
```

Tres reglas viven **en la base de datos**, no en Python, y la API las convierte en errores HTTP:

- `isbn` es `UNIQUE`: un segundo libro con el mismo ISBN se rechaza → `409 Conflict`.
- `authors.name` es `UNIQUE`: lo mismo para un autor repetido → `409 Conflict`.
- `books.author_id` es una **clave foránea**: un libro no puede apuntar a un autor que no existe (→ `422`), y no se puede borrar un autor que todavía tiene libros (→ `409`).

Los títulos, autores y años son reales. Los ISBN son inventados (13 dígitos con un dígito de control válido).

## Requisitos

1. **Dependencias** (`requirements.txt`): `fastapi[standard]`, `PyMySQL` (el driver de MySQL), `cryptography` (lo necesita PyMySQL para iniciar sesión en MySQL 8) y `python-dotenv` (lee el `.env`).

2. **Estructura de la API:**

   **Libros** (CRUD completo, aquí están los huecos)

   | Método | URI | SQL | Éxito | Errores |
   |--------|-----|-----|-------|---------|
   | `GET` | `/books?limit=20&offset=0&author_id=2&q=sol` | `SELECT ... JOIN authors ... LIMIT %s OFFSET %s` | `200` | `422` |
   | `GET` | `/books/{id}` | `SELECT ... WHERE b.id = %s` | `200` | `404` |
   | `POST` | `/books` | `INSERT` | `201` + `Location` | `409` ISBN repetido, `422` `author_id` desconocido o cuerpo no válido |
   | `PUT` | `/books/{id}` | `UPDATE` de todos los campos | `200` | `404`, `409`, `422` |
   | `PATCH` | `/books/{id}` | `UPDATE` solo de los campos enviados | `200` | `404`, `409`, `422` |
   | `DELETE` | `/books/{id}` | `DELETE` | `204`, sin cuerpo | `404` |

   **Autores** (ya escritos, léelos)

   | Método | URI | Éxito | Errores |
   |--------|-----|-------|---------|
   | `GET` | `/authors?q=garcia` | `200` | |
   | `GET` | `/authors/{id}` | `200` (incluye `book_count`) | `404` |
   | `POST` | `/authors` | `201` + `Location` (también puede crear los libros del autor, en una transacción) | `409`, `422` |
   | `DELETE` | `/authors/{id}` | `204` | `404`, `409` si el autor todavía tiene libros |

   Un libro tiene este aspecto. `id`, `created_at` y `updated_at` los pone MySQL; `author` sale de un `JOIN` con la tabla `authors`:

   ```json
   {"id": 5, "title": "Cien años de soledad", "isbn": "9788410395954", "year": 1967,
    "author": {"id": 2, "name": "Gabriel García Márquez"},
    "created_at": "2026-11-04T09:30:00Z", "updated_at": "2026-11-04T09:30:00Z"}
   ```

   - `GET /books`: libros por `id`. `limit` (por defecto `20`, entre `1` y `100`; por encima de `100` es un `422`), `offset` (por defecto `0`), `author_id` (solo los libros de ese autor) y `q` (parte del título; dan igual los acentos y las mayúsculas). El objeto `page` tiene `limit`, `offset`, `total` y los enlaces `next`/`prev`, que conservan tus filtros.
   - `BookCreate` (cuerpo de `POST` y `PUT`): `title` (obligatorio), `author_id` (obligatorio), `isbn` (13 dígitos, opcional) y `year` (opcional). `PUT` envía el libro completo: un campo que no envías se queda en `null`.
   - `BookUpdate` (cuerpo de `PATCH`): todos los campos opcionales; un cuerpo vacío es un `422`.
   - Todos los errores son RFC 9457 `application/problem+json`, como en 04-06.

3. **Pruebas:** usa Postman, `curl` o `/docs`, y mira las tablas en Adminer.

## Pasos Sugeridos

1. **Lee `app.py` desde arriba:**
   - `MYSQL` lee la configuración de conexión del `.env`.
   - `db()` abre **una conexión por petición** y siempre la cierra. `autocommit` está desactivado: no se guarda nada hasta que llamas a `conn.commit()`.
   - `integrity_error()` traduce los códigos de error de MySQL (1062 duplicado, 1451 todavía referenciado, 1452 clave foránea desconocida) a errores HTTP.
   - `BOOK_SELECT` es el `SELECT ... JOIN` que comparten todos los endpoints que devuelven libros, y `to_book()` convierte una fila en un `Book`.
   - El manejador del `503`: si MySQL no está arrancado, todas las peticiones responden `503` con un mensaje que te dice qué hacer.

2. **Completa los huecos (`_____`) de `app.py`:**

   ```python
   # integrity_error: un valor repetido -> ¿qué código de estado?
   return HTTPException(status_code=_____, detail=...)

   # get_book_or_404: el marcador del id (nunca pegues valores en el SQL)
   cur.execute(BOOK_SELECT + " WHERE b.id = _____", (book_id,))

   # POST /books: el id que generó MySQL, guardar y dónde vive el nuevo libro
   book_id = cur._____
   conn._____()
   response.headers["_____"] = ...

   # PATCH y DELETE: los decoradores y el 204
   @app._____("/books/{book_id}")
   @app._____("/books/{book_id}", status_code=_____)
   if cur._____ == 0:              # ¿cuántas filas ha borrado el DELETE?
   return Response(status_code=_____)

   # GET /books: la página más grande, y solo una página
   limit: Annotated[int, Query(ge=1, le=_____)] = 20
   "... ORDER BY b.id LIMIT _____ OFFSET _____"
   ```

   Los comentarios junto a cada hueco te dan una pista. La solución completa está en `example/example06b.py` (¡inténtalo primero!).

3. **Arranca la aplicación** con `fastapi dev app.py` y pruébala (siguiente apartado).

4. **Lee `POST /authors`** (ya escrito): es la transacción del recuadro "Transacciones" de más abajo.

## Prueba la API

`-i` muestra la línea de estado y las cabeceras. Estos comandos suponen una **base de datos recién creada** (ver "Reiniciar los datos"); con otros datos los ids pueden cambiar.

> **Windows:** en PowerShell usa `curl.exe` (en Windows PowerShell 5.1 `curl` es un alias de `Invoke-WebRequest`). Incluso con `curl.exe`, PowerShell 5.1 quita las comillas interiores de `-d '{...}'` y el JSON llega roto. Usa en su lugar los ficheros listos para ejecutar: `example/commands_cmd.txt` (CMD) y `example/commands_powershell.txt` (PowerShell, con `Invoke-WebRequest`).
>
> Los terminales de Windows no siempre envían los acentos (`á`, `ñ`) en UTF-8, y la API responde `400` "There was an error parsing the body". Por eso los cuerpos JSON de abajo no llevan acentos. En Postman y en `/docs` los acentos funcionan bien.

- **Listar libros (`200`):**
  ```bash
  curl -i "http://127.0.0.1:8000/books?limit=2"
  ```
  ```json
  {
    "data": [
      {"id": 1, "title": "Don Quijote de la Mancha", "isbn": "9788410079199", "year": 1605, "author": {"id": 1, "name": "Miguel de Cervantes"}, "created_at": "...", "updated_at": "..."},
      {"id": 2, "title": "Novelas ejemplares", "isbn": "9788410158382", "year": 1613, "author": {"id": 1, "name": "Miguel de Cervantes"}, "created_at": "...", "updated_at": "..."}
    ],
    "page": {"limit": 2, "offset": 0, "total": 150, "next": "http://127.0.0.1:8000/books?offset=2&limit=2", "prev": null}
  }
  ```

- **Última página (`next` es `null`) y una página demasiado grande (`422`):**
  ```bash
  curl -i "http://127.0.0.1:8000/books?offset=145&limit=5"
  curl -i "http://127.0.0.1:8000/books?limit=500"
  ```

- **Filtros (`200`):** los libros de García Márquez cuyo título contiene "soledad".
  ```bash
  curl -i "http://127.0.0.1:8000/books?author_id=2&q=soledad"
  ```

- **Obtener un libro (`200`, o `404` si no existe):**
  ```bash
  curl -i http://127.0.0.1:8000/books/1
  curl -i http://127.0.0.1:8000/books/999
  ```

- **Crear un libro (`201` + `Location`):** MySQL genera el id y las fechas.
  ```bash
  curl -i -X POST http://127.0.0.1:8000/books -H "Content-Type: application/json" -d '{"title": "El maestro de esgrima", "isbn": "9788490000014", "year": 1988, "author_id": 7}'
  ```
  ```
  HTTP/1.1 201 Created
  location: http://127.0.0.1:8000/books/151

  {"id": 151, "title": "El maestro de esgrima", "isbn": "9788490000014", "year": 1988, "author": {"id": 7, "name": "Arturo Pérez-Reverte"}, "created_at": "...", "updated_at": "..."}
  ```
  Refresca la tabla `books` en Adminer: la fila está ahí.

- **ISBN repetido (`409`):** el ISBN del Quijote. MySQL lo rechaza porque la columna es `UNIQUE`.
  ```bash
  curl -i -X POST http://127.0.0.1:8000/books -H "Content-Type: application/json" -d '{"title": "Copy", "isbn": "9788410079199", "author_id": 1}'
  ```
  ```json
  {"type": "about:blank", "title": "Conflict", "status": 409, "detail": "'9788410079199' already exists and must be unique.", "instance": "/books"}
  ```

- **Autor desconocido (`422`):** la clave foránea no deja que un libro apunte al autor 999.
  ```bash
  curl -i -X POST http://127.0.0.1:8000/books -H "Content-Type: application/json" -d '{"title": "Orphan", "author_id": 999}'
  ```

- **Sustituir con PUT (`200`) y luego cambiar solo el año con PATCH (`200`):**
  ```bash
  curl -i -X PUT http://127.0.0.1:8000/books/151 -H "Content-Type: application/json" -d '{"title": "El maestro de esgrima (revised)", "isbn": "9788490000014", "year": 1988, "author_id": 7}'
  curl -i -X PATCH http://127.0.0.1:8000/books/151 -H "Content-Type: application/json" -d '{"year": 2000}'
  ```
  Fíjate en `updated_at`: lo ha cambiado MySQL solo (`ON UPDATE CURRENT_TIMESTAMP`).

- **PATCH vacío (`422`):**
  ```bash
  curl -i -X PATCH http://127.0.0.1:8000/books/151 -H "Content-Type: application/json" -d '{}'
  ```

- **Borrar (`204`, cuerpo vacío) y volver a pedirlo (`404`):**
  ```bash
  curl -i -X DELETE http://127.0.0.1:8000/books/151
  curl -i http://127.0.0.1:8000/books/151
  ```

- **Autores (`200`):**
  ```bash
  curl -i "http://127.0.0.1:8000/authors?q=garcia"
  curl -i http://127.0.0.1:8000/authors/2
  ```

- **Borrar un autor que todavía tiene libros (`409`) y uno que no tiene ninguno (`204`):**
  ```bash
  curl -i -X DELETE http://127.0.0.1:8000/authors/1
  curl -i -X DELETE http://127.0.0.1:8000/authors/22
  ```
  ```json
  {"type": "about:blank", "title": "Conflict", "status": 409, "detail": "Author 1 still has books. Delete or move them first.", "instance": "/authors/1"}
  ```
  Tu código Python nunca comprueba esto: la clave foránea protege los datos aunque el código se olvide.

- **La transacción: todo o nada.** Crea un autor junto con dos libros. El segundo ISBN vuelve a ser el del Quijote, así que falla (`409`)...
  ```bash
  curl -i -X POST http://127.0.0.1:8000/authors -H "Content-Type: application/json" -d '{"name": "Rosa Montero", "country": "Spain", "birth_year": 1951, "books": [{"title": "La loca de la casa", "isbn": "9788490000021", "year": 2003}, {"title": "Copy", "isbn": "9788410079199"}]}'
  ```
  ...y **no se ha guardado nada**: ni el autor ni el primer libro.
  ```bash
  curl -i "http://127.0.0.1:8000/authors?q=montero"
  ```
  ```json
  {"data": []}
  ```
  Ahora con dos libros válidos (`201`):
  ```bash
  curl -i -X POST http://127.0.0.1:8000/authors -H "Content-Type: application/json" -d '{"name": "Rosa Montero", "country": "Spain", "birth_year": 1951, "books": [{"title": "La loca de la casa", "isbn": "9788490000021", "year": 2003}, {"title": "Historia del rey transparente", "isbn": "9788490000038", "year": 2005}]}'
  ```
  Mira el nuevo id: es `24`, no `23`. El intento fallido usó el `23`, y un rollback no devuelve los números de `AUTO_INCREMENT`. Los ids son identificadores, no contadores.

- **Los datos se quedan:** para `fastapi dev` (`Ctrl+C`), vuelve a arrancarlo y pide a Rosa Montero: sigue ahí. Compáralo con los ejercicios 04-06.
  ```bash
  curl -i "http://127.0.0.1:8000/authors?q=montero"
  ```

## Inyección SQL: siempre `%s`

Nunca construyas el SQL pegando el texto del usuario en la cadena:

```python
# MAL: q pasa a formar parte del SQL
cur.execute(f"SELECT * FROM books WHERE title LIKE '%{q}%'")
```

Con `q = "' OR '1'='1"` la consulta cambia de significado, y con un texto peor un atacante puede leer o borrar otras tablas. Con un marcador, PyMySQL envía el texto **como un valor**, así que nunca puede convertirse en SQL:

```python
# BIEN
cur.execute("SELECT * FROM books WHERE title LIKE %s", (f"%{q}%",))
```

Prueba `curl -i "http://127.0.0.1:8000/books?q=%27%20OR%20%271%27=%271"`: obtienes una lista vacía, no la tabla entera. En `PATCH`, los **nombres** de columna del `UPDATE` salen de nuestro propio modelo (nunca del cliente) y los valores siguen viajando como `%s`.

## `commit()` y transacciones

`db()` abre la conexión con `autocommit` desactivado, así que cada `INSERT`, `UPDATE` o `DELETE` queda **pendiente** hasta `conn.commit()`. Si la petición falla antes, la conexión hace rollback y se cierra, y la base de datos se queda como estaba.

Una **transacción** es un grupo de sentencias que se guarda **entero o nada**. `POST /authors` ejecuta un `INSERT` del autor y otro por cada libro; hace commit solo si todos han ido bien, y llama a `conn.rollback()` si alguno falla. Sin ella, un libro fallido dejaría medio autor en la base de datos.

## Reiniciar los datos

- `docker compose down` para los contenedores y **conserva** los datos (viven en el volumen `library-data`).
- `docker compose down -v` borra también el volumen. En el siguiente `docker compose up -d --wait`, `init.sql` se ejecuta otra vez y vuelves a tener los 22 autores y 150 libros originales.
- Cambiar `init.sql` no hace nada hasta que reinicias con `-v`: Docker solo lo ejecuta con el volumen vacío.

## Problemas Frecuentes

- **`503 Service Unavailable` "Cannot connect to MySQL"**: Docker no está arrancado, o MySQL todavía está arrancando. Ejecuta `docker compose up -d --wait` en esta carpeta (y `docker compose ps` para ver el estado). No hace falta reiniciar la API.
- **`Ports are not available` o `port is already allocated` en el 3306**: ya tienes un MySQL en tu ordenador. Pon `MYSQL_PORT=3307` en `.env` y vuelve a ejecutar `docker compose up -d --wait`; la API lee el mismo `.env`. Lo mismo con Adminer en el 8080: cambia `ADMINER_PORT`.
- **`503` "refused the connection: Access denied"**: el usuario o la contraseña del `.env` no coinciden con la base de datos. Si los cambiaste después del primer arranque, el volumen conserva los antiguos: `docker compose down -v` y vuelve a arrancar.
- **`500 Internal Server Error`**: todavía queda un hueco o una cadena SQL está mal. Mira el terminal donde corre `fastapi dev`: `TypeError: not all arguments converted during string formatting` significa que falta un marcador `%s` (todavía hay un `_____` en el SQL); `You have an error in your SQL syntax` viene de MySQL.
- **pip falla con un error de ruta larga en Windows**: copia el repositorio a una carpeta corta como `C:\edem` (ver el README principal).

## Resultados Esperados

- `GET /books` devuelve 20 libros por página con `total`, `next` y `prev`; `?limit=500` es un `422`.
- `POST /books` devuelve `201` con `Location`, y la nueva fila aparece en Adminer.
- Un ISBN repetido es un `409`, un `author_id` desconocido es un `422` y borrar un autor con libros es un `409`; todos los errores son `application/problem+json`.
- `PATCH` con un campo cambia solo ese campo; `DELETE` devuelve `204` sin cuerpo.
- Un `POST /authors` fallido no deja nada.
- Los datos sobreviven a un reinicio de la API; `docker compose down -v` devuelve los datos originales.

## Retos Opcionales

1. **Paginación por cursor en SQL:** añade `?cursor=` a `GET /books` como en el ejercicio 06. Pista: `WHERE b.id > %s ORDER BY b.id LIMIT %s` (sin `OFFSET`, y sigue siendo rápido con millones de filas).
2. **Préstamos, con una transacción:** añade una tabla `loans` (`book_id`, `borrower`, `loaned_at`, `returned_at`) y `POST /books/{id}/loan`. En una transacción, comprueba que el libro no tiene un préstamo abierto e inserta el préstamo; responde `409` si ya está prestado.
3. **Un ORM:** reescribe `/books` con [SQLModel](https://sqlmodel.tiangolo.com/) (del autor de FastAPI). Compara: ¿qué código desaparece y qué SQL ya no puedes ver?

## Recursos Adicionales

- [Documentación de PyMySQL](https://pymysql.readthedocs.io/)
- [MySQL 8.4: CREATE TABLE y claves foráneas](https://dev.mysql.com/doc/refman/8.4/en/create-table-foreign-keys.html)
- [Docker Hub: la imagen oficial de MySQL](https://hub.docker.com/_/mysql)
- [OWASP: Inyección SQL](https://owasp.org/www-community/attacks/SQL_Injection)
- [FastAPI: bases de datos SQL](https://fastapi.tiangolo.com/tutorial/sql-databases/)
